import re
import os
import zipfile
import wget
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import warnings
import glob

# Suppress only the InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

from bs4 import BeautifulSoup
from loguru import logger

from src.settings import RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR

'''
1 Process Census Functions
'''

def get_all_census_shp_name(base_url):
    """
    Get the road file names for a specific state.

    Parameters:
    - base_url (str): The base URL for the road files.
    - state_fips_code (str): The FIPS code for the state of interest.
    """
    try:
        logger.info(
            f"Getting census names from {base_url}"
        )
        response = requests.get(base_url)
        response.raise_for_status()

        # Parse the webpage
        soup = BeautifulSoup(response.text, "html.parser")

        # Regex pattern to match the road files for the given state
        pattern = re.compile(f"tl_2020_[0-9]+_tract.zip")

        # Extract all matching road files
        census_files = []
        for link in soup.find_all("a", href=True):
            match = pattern.match(link["href"])
            if match:
                census_files.append(match.group(0))

        logger.info(
            f"Found {len(census_files)} census files USA"
        )
        return census_files

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def download_and_prepare_census_shp_data(
    raw_data_path=RAW_DATA_DIR,
    interim_data_path=INTERIM_DATA_DIR,
):
    """
    Download and prepare road data for a specific state and save the resulting shapefile.

    Parameters:
    - state_name (str): The name of the state.
    - state_fips_code (str): The FIPS code for the state of interest.
    - raw_data_path (str): The path to the raw road shapefiles.
                           Default is `src.settings.RAW_DATA_DIR`.
    - interim_data_path (str): The directory where the resulting shapefile will be saved.
                               Default is `src.settings.INTERIM_DATA_DIR`.
    """

    # Check for cached output
    output_path = f"{interim_data_path}/census/all_census.shp.zip"
    if os.path.exists(output_path):
        logger.info(
            f"Cached output found at {output_path}. Skipping download and processing."
        )
        return

    logger.info("Downloading and processing census tract shp data.")
    # Create the directory if it doesn't exist
    if not os.path.exists(f"{raw_data_path}/census/"):
        os.makedirs(f"{raw_data_path}/census/")
    if not os.path.exists(f"{interim_data_path}/census"):
        os.makedirs(f"{interim_data_path}/census")

    list_ = []
    url = "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/"

    #tract_files_name = get_census_shp_name(url)

    census_file_names = get_all_census_shp_name(url)

    for file_name in tqdm(census_file_names):
        file_path = f"{raw_data_path}/census/{file_name}"
        # logger.info(
        #     f"Downloading {file_name} Census Tract Shp data to {file_path}."
        # )
        if not os.path.exists(file_path):
            try:
                full_url = url + file_name
                #wget.download(full_url, out=f"{raw_data_path}/road/{state_name}", no_check_certificate=True)
                download_file(full_url, f"{raw_data_path}/census/{file_name}", verify_ssl=False)
            except Exception as e:
                if str(e) == "HTTP Error 404: Not Found":
                    continue
                else:
                    logger.error(f"Error {e} when downloading file {file_name}")
                    continue
        try:
            gdf = gpd.read_file(file_path, index_col=None, header=0)
            list_.append(gdf)
        except Exception as e:
            logger.error(f"Error {e} when reading file {file_name}")

    frame = pd.concat(list_, axis=0, ignore_index=True)

    # Save the processed data
    frame.to_file(output_path)
    logger.info(f"Saved census data to {output_path}")

'''
2 Process Road Functions
'''
def get_road_file_names(base_url, state_fips_code):
    """
    Get the road file names for a specific state.

    Parameters:
    - base_url (str): The base URL for the road files.
    - state_fips_code (str): The FIPS code for the state of interest.
    """
    try:
        logger.info(
            f"Getting road file names for state FIPS code {state_fips_code} from {base_url}"
        )
        response = requests.get(base_url)
        response.raise_for_status()

        # Parse the webpage
        soup = BeautifulSoup(response.text, "html.parser")

        # Regex pattern to match the road files for the given state
        pattern = re.compile(f"tl_2020_{state_fips_code}[0-9]+_roads.zip")

        # Extract all matching road files
        road_files = []
        for link in soup.find_all("a", href=True):
            match = pattern.match(link["href"])
            if match:
                road_files.append(match.group(0))

        logger.info(
            f"Found {len(road_files)} road files for state FIPS code {state_fips_code}"
        )
        return road_files

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def richard_download_and_prepare_road_data(
    state_fips_code,
    state_name,
    raw_data_path=RAW_DATA_DIR,
    interim_data_path=INTERIM_DATA_DIR,
):
    """
    Download and prepare road data for a specific state and save the resulting shapefile.

    Parameters:
    - state_name (str): The name of the state.
    - state_fips_code (str): The FIPS code for the state of interest.
    - raw_data_path (str): The path to the raw road shapefiles.
                           Default is `src.settings.RAW_DATA_DIR`.
    - interim_data_path (str): The directory where the resulting shapefile will be saved.
                               Default is `src.settings.INTERIM_DATA_DIR`.
    """

    # Check for cached output
    output_path = f"{interim_data_path}/road/{state_name}_road.shp.zip"
    if os.path.exists(output_path):
        logger.info(
            f"Cached output found at {output_path}. Skipping download and processing."
        )
        return

    logger.info("Downloading and processing road data.")
    # Create the directory if it doesn't exist
    if not os.path.exists(f"{raw_data_path}/road/{state_name}"):
        os.makedirs(f"{raw_data_path}/road/{state_name}")
    if not os.path.exists(f"{interim_data_path}/road"):
        os.makedirs(f"{interim_data_path}/road")

    list_ = []
    url = "https://www2.census.gov/geo/tiger/TIGER2020/ROADS/"

    road_file_names = get_road_file_names(url, state_fips_code)

    for file_name in tqdm(road_file_names):
        file_path = f"{raw_data_path}/road/{state_name}/{file_name}"
        if not os.path.exists(file_path):
            try:
                full_url = url + file_name
                #wget.download(full_url, out=f"{raw_data_path}/road/{state_name}", no_check_certificate=True)
                download_file(full_url, f"{raw_data_path}/road/{state_name}/{file_name}", verify_ssl=False)
            except Exception as e:
                if str(e) == "HTTP Error 404: Not Found":
                    continue
                else:
                    logger.error(f"Error {e} when downloading file {file_name}")
                    continue
        try:
            gdf = gpd.read_file(file_path, index_col=None, header=0)
            list_.append(gdf)
        except Exception as e:
            logger.error(f"Error {e} when reading file {file_name}")

    frame = pd.concat(list_, axis=0, ignore_index=True)

    # Save the processed data
    frame.to_file(output_path)
    logger.info(f"Saved road data to {output_path}")

def process_interim_road_data(
    state_name,
    interim_data_path=INTERIM_DATA_DIR,
    processed_data_path=PROCESSED_DATA_DIR,
):
    """
    Process road data for a specific state and save the resulting shapefile.

    Parameters:
    - state_name (str): The name of the state.
    - interim_data_path (str): The directory where the interim files will be saved.
                               Default is `src.settings.INTERIM_DATA_DIR`.
    - processed_data_path (str): The directory where the processed shapefile will be saved.
                                 Default is `src.settings.PROCESSED_DATA_DIR`.
    """

    # Check for cached output
    output_dir = f"{processed_data_path}/road"
    output_path = f"{output_dir}/{state_name}_road_cleaned.shp.zip"
    if os.path.exists(output_path):
        logger.info(f"Cached road data found at {output_path}. Skipping processing.")
        return

    component_csv_path = (
        f"{interim_data_path}/road/grass_output/{state_name}_road_component.csv"
    )
    # Check if the required files exist
    if not os.path.exists(component_csv_path):
        logger.error(f"Component CSV file {component_csv_path} does not exist.")
        logger.error(
            "Please process road network data using GRASS GIS as described in the README file."
        )
        return
    logger.info(f"Reading component CSV from {component_csv_path}")
    components = pd.read_csv(component_csv_path, usecols=[0])

    cleaned_shp_path = f"{interim_data_path}/road/grass_output/{state_name}_road_cleaned.shp"
    # Check if the required files exist
    if not os.path.exists(cleaned_shp_path):
        logger.error(f"Cleaned shapefile {cleaned_shp_path} does not exist.")
        logger.error(
            "Please process road network data using GRASS GIS as described in the README file."
        )
        return
    logger.info(f"Reading cleaned shapefile from {cleaned_shp_path}")
    cleaned = gpd.read_file(cleaned_shp_path)

    col_list = ["LINEARID", "MTFCC", "geometry"]
    roads = cleaned.loc[:, col_list].join(components)

    logger.info(f"Roads DataFrame shape: {roads.shape}")
    logger.info(f"Roads DataFrame head:\n{roads.head()}")

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        logger.info(f"Creating directory {output_dir}")
        os.makedirs(output_dir)

    # Save as a shapefile
    logger.info(f"Saving processed data to {output_path}")
    roads.to_file(output_path)

'''
2 Process Commute Data Functions
'''
def download_lodes_data(state_name, raw_data_dir=RAW_DATA_DIR):
    """
    Download LODES data for a specific state and save the resulting csv file.

    Parameters:
    - state_name (str): The name of the state.
    - raw_data_path (str): The path to the raw LODES data.
                           Default is `src.settings.RAW_DATA_DIR`.
    """
    for lodes_type in ["aux", "main"]:
        lodes_filename = f"{state_name.lower()}_od_{lodes_type}_JT00_2010.csv.gz"
        lodes_full_path = os.path.join(raw_data_dir, "work_commute", lodes_filename)
        if os.path.exists(lodes_full_path):
            logger.info(
                f"Cached LODES data found at {lodes_full_path}. Skipping download."
            )
            continue
        logger.info(
            f"Downloading LODES data {lodes_filename} to {os.path.join(raw_data_dir, 'work_commute')}"
        )
        #url = f"https://lehd.ces.census.gov/data/lodes/LODES7/{state_name.lower()}/od/{lodes_filename}"
        url = f"https://lehd.ces.census.gov/data/lodes/LODES8/{state_name.lower()}/od/{lodes_filename}"
        wget.download(url, out=lodes_full_path)
        logger.info(f"Saved LODES data to {lodes_full_path}")


def download_and_prepare_work_commute_data(
    state_name,
    city_name,
    raw_data_dir=RAW_DATA_DIR,
    interim_data_path=INTERIM_DATA_DIR,
    processed_data_path=PROCESSED_DATA_DIR,
):
    """
    Download and prepare work commute data for a specific city and save the resulting csv file.

    Parameters:
    - state_name (str): The name of the state.
    - city_name (str): The name of the city.
    - raw_data_path (str): The path to the raw LODES data.
                           Default is `src.settings.RAW_DATA_DIR`.
    - interim_data_path (str): The directory where the interim files are saved.
                               Default is `src.settings.INTERIM_DATA_DIR`.
    - processed_data_path (str): The directory where the processed files will be saved.
                                 Default is `src.settings.PROCESSED_DATA_DIR`.
    """

    od_filename = f"{state_name}_{city_name}_tract_od.csv"
    od_full_path = os.path.join(processed_data_path, "work_commute", od_filename)
    # Check for cached output
    if os.path.exists(od_full_path):
        logger.info(f"Cached OD data found at {od_full_path}. Skipping processing.")
        return
    download_lodes_data(state_name, raw_data_dir)
    lodes_aux_filename = f"{state_name.lower()}_od_aux_JT00_2010.csv.gz"
    lodes_aux_full_path = os.path.join(raw_data_dir, "work_commute", lodes_aux_filename)
    lodes_main_filename = f"{state_name.lower()}_od_main_JT00_2010.csv.gz"
    lodes_main_full_path = os.path.join(
        raw_data_dir, "work_commute", lodes_main_filename
    )

    logger.info("Reading interim city census tract shapefile.")
    city_census = gpd.read_file(
        os.path.join(
            interim_data_path,
            "census_tract",
            f"{state_name}_{city_name}_census_tract.shp.zip",
        )
    )

    logger.info("Reading downloaded LODES data.")
    # We are interested in these columns only (ripping off the rest by usecols=range(6)):
    # - S000: Total number of jobs
    # - SA01: Number of jobs of workers age 29 or younger
    # - SA02: Number of jobs for workers age 30 to 54
    # - SA03: Number of jobs for workers age 55 or older
    out_county = pd.read_csv(
        lodes_aux_full_path,
        dtype={"w_geocode": str, "h_geocode": str},
    ).iloc[:, 0:6]
    in_county = pd.read_csv(
        lodes_main_full_path,
        dtype={"w_geocode": str, "h_geocode": str},
    ).iloc[:, 0:6]

    wf = pd.concat([out_county, in_county]).reset_index(drop=True)
    logger.info(f"Shape of LODES data: {wf.shape}")
    logger.info(f"Head of LODES data:\n{wf.head()}")

    wf["work"] = wf.w_geocode.astype(str).str[:11]
    wf["home"] = wf.h_geocode.astype(str).str[:11]

    od = wf[(wf.work.isin(city_census.GEOID10)) | (wf.home.isin(city_census.GEOID10))]
    od = od.groupby(["work", "home"]).sum()
    logger.info(f"Saving processed work commute data to {od_full_path}.")
    od.reset_index().to_csv(od_full_path, index=False)


def prepare_employment_data(
    state_name,
    city_name,
    raw_data_path=RAW_DATA_DIR,
    interim_data_path=INTERIM_DATA_DIR,
    processed_data_path=PROCESSED_DATA_DIR,
):
    """
    Prepare employment data for a specific city and save the resulting shapefile.

    Parameters:
    - state_name (str): The name of the state.
    - city_name (str): The name of the city.
    - raw_data_path (str): The path to raw data.
                           Default is `src.settings.RAW_DATA_DIR`.
    - interim_data_path (str): The directory where the interim data is saved.
                               Default is `src.settings.INTERIM_DATA_DIR`.
    - processed_data_path (str): The directory where the processed shapefile will be saved.
                                 Default is `src.settings.PROCESSED_DATA_DIR`.
    """

    output_path = os.path.join(
        processed_data_path,
        "census_tract",
        f"{state_name}_{city_name}_tracts_with_work.shp.zip",
    )
    # Check for cached output
    if os.path.exists(output_path):
        logger.info(f"Cached output found at {output_path}. Skipping processing.")
        return

    # commute information
    processed_work_commute_path = os.path.join(
        processed_data_path, "work_commute", f"{state_name}_{city_name}_tract_od.csv"
    )
    logger.info(
        f"Reading processed work commute data from {processed_work_commute_path}"
    )
    od = pd.read_csv(processed_work_commute_path, dtype={"work": str, "home": str})
    logger.info(f"Shape of processed work commute data: {od.shape}")
    logger.info(f"Head of processed work commute data:\n{od.head()}")

    tract_employed_df = od[["work", "S000"]].groupby("work").sum().reset_index()
    tract_employed_df = tract_employed_df.astype({"work": str})

    logger.info(f"Shape of tract_employed_df: {tract_employed_df.shape}")
    logger.info(f"Head of tract_employed_df:\n{tract_employed_df.head()}")

    # county employed
    tract_employed_df["county"] = tract_employed_df.work.astype(str).str[:5]
    county_employed_df = (
        tract_employed_df[["county", "S000"]].groupby("county").sum().reset_index()
    )
    tract_employed_df.drop(columns=["county"], inplace=True)

    logger.info(f"Shape of county_employed_df: {county_employed_df.shape}")
    logger.info(f"Head of county_employed_df:\n{county_employed_df.head()}")

    # demographic data (census tract)
    interim_census_tract_path = os.path.join(
        interim_data_path,
        "census_tract",
        f"{state_name}_{city_name}_census_tract.shp.zip",
    )
    logger.info(f"Reading interim census tract data from {interim_census_tract_path}")
    dp = gpd.read_file(interim_census_tract_path)  # .set_index('GEOID10')
    dp["county"] = dp["GEOID10"].str[:5]

    logger.info(f"Shape of city census tract demographic profile: {dp.shape}")
    logger.info(f"Head of city census tract demographic profile:\n{dp.head()}")

    dp = (
        pd.merge(dp, tract_employed_df, left_on="GEOID10", right_on="work")
        .drop(columns=["work"])
        .rename(columns={"S000": "tract_employed"})
    )
    dp = pd.merge(dp, county_employed_df, on="county").rename(
        columns={"S000": "county_employed"}
    )

    cbp = get_workplace_data(raw_data_path)
    dp = pd.merge(dp, cbp, on="county").rename(columns={"ESTAB": "wp_cty"})
    dp["WP_CNT"] = dp["wp_cty"] * (dp["tract_employed"] / dp["county_employed"])
    dp["WP_CNT"] = dp["WP_CNT"].astype(int)

    # drop duplicated rows
    dp = dp.drop_duplicates(subset=["GEOID10"], keep="first")

    # Save the processed data
    logger.info(
        f"Saving processed city census tract demographic profile with employment statistics to {output_path}"
    )
    dp.to_file(output_path)


def get_workplace_data(raw_data_path):
    """
    Get raw workplace data as a dataframe.

    Parameters:
    - raw_data_path (str): The path to the raw road shapefiles.
                           Default is `src.settings.RAW_DATA_DIR`.
    """
    raw_workplace_path = os.path.join(raw_data_path, "workplace", "CB2000CBP.dat")
    logger.info(f"Reading raw workplace data from {raw_workplace_path}")
    cbp = pd.read_csv(
        raw_workplace_path,
        sep="|",
        usecols=["GEO_ID", "EMPSZES_LABEL", "ESTAB", "NAICS2017"],
    )
    cbp = cbp.astype({"ESTAB": int})
    cbp = cbp[cbp["GEO_ID"].str.len() == 14]
    cbp["county"] = cbp.GEO_ID.astype(str).str[-5:]
    cbp = cbp[cbp["EMPSZES_LABEL"] == "All establishments"]
    cbp = cbp[
        (cbp["EMPSZES_LABEL"] == "All establishments") & (cbp["NAICS2017"] == "00")
    ]
    cbp = cbp[["county", "ESTAB"]].groupby("county").sum().reset_index()

    logger.info(f"Shape of the workplace data: {cbp.shape}")
    logger.info(f"Head of the workplace data:\n{cbp.head()}")

    return cbp

def download_file(url, output_path, verify_ssl=False):
    try:
        # If verify_ssl is False, SSL verification is disabled. Caution: this is insecure.
        # Typically, you'd use verify=certifi.where() to specify a path to a CA bundle
        response = requests.get(url, stream=True, verify=verify_ssl)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        #print(f"Downloaded file saved to {output_path}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error occurred: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")





def download_lodes_2020_data(state_name, raw_data_dir=RAW_DATA_DIR):
    """
    Download LODES data for a specific state and save the resulting csv file.

    Parameters:
    - state_name (str): The name of the state.
    - raw_data_path (str): The path to the raw LODES data.
                           Default is `src.settings.RAW_DATA_DIR`.
    """
    for lodes_type in ["aux", "main"]:
        logger.info(f"Downloading LODES data for {lodes_type}")
        lodes_filename = f"{state_name.lower()}_od_{lodes_type}_JT00_2020.csv.gz"
        lodes_full_path = os.path.join(raw_data_dir, "work_commute", lodes_filename)
        logger.info(f"Downloading LODES to {lodes_full_path}")
        if os.path.exists(lodes_full_path):
            logger.info(
                f"Cached LODES data found at {lodes_full_path}. Skipping download."
            )
            continue
        logger.info(
            f"Downloading LODES data {lodes_filename} to {os.path.join(raw_data_dir, 'work_commute')}"
        )
        # url = f"https://lehd.ces.census.gov/data/lodes/LODES7/{state_name.lower()}/od/{lodes_filename}"
        url = f"https://lehd.ces.census.gov/data/lodes/LODES8/{state_name.lower()}/od/{lodes_filename}"

        try:
            # full_url = url
            #download_file(url, f"{lodes_full_path}/lodes8/{lodes_filename}", verify_ssl=False)
            #download_file(url, f"{raw_data_dir}/work_commute/{state_name}/{lodes_filename}", verify_ssl=False)
            download_file(url, lodes_full_path, verify_ssl=False)
        except Exception as e:
            if str(e) == "HTTP Error 404: Not Found":
                continue
            else:
                logger.error(f"Error {e} when downloading file {lodes_filename}")
                continue
        # wget.download(url, out=lodes_full_path)
        logger.info(f"Saved LODES data to {lodes_full_path}")



def combine_in_out_county_data(state_ab, state_code, inter_data_dir=INTERIM_DATA_DIR):
    # print('=========In Combining=========')
    path_to_gz_files = f'data/raw-data/work_commute/{state_ab}_*_JT00_*.gz'
    gz_files = glob.glob(path_to_gz_files)
    # print(len(gz_files))
    # print(gz_files)

    dataframes = []
    # Loop through the ZIP files and read them into GeoDataFrames
    for gz_file in gz_files:
        try:
            df = pd.read_csv(gz_file)
            dataframes.append(df)
            logger.info(f'Loaded file {gz_file} with shape {df.shape}')
        except Exception as e:
            logger.error(f'Failed to load file {gz_file}. Error: {e}')

    if not dataframes:
        logger.warning('No data loaded to process.')
        return pd.DataFrame()

    # Concatenate all DataFrames into one
    combine_df = pd.DataFrame(pd.concat(dataframes, ignore_index=True))
    logger.info(f'combined with shape {combine_df.shape}')

    output_path = os.path.join(inter_data_dir, f"od/{state_ab}-tract-od-2020.csv")
    logger.info(f'Saving to {output_path}')

    if state_code in ['01', '02', '04', '05', '06', '08', '09']:
        combine_df['work'] = combine_df.w_geocode.astype(str).str[:10]
        combine_df['home'] = combine_df.h_geocode.astype(str).str[:10]
        temp_df = combine_df.loc[:, ['work', 'home', 'S000']]
        temp_od = temp_df.groupby(['work', 'home']).sum()
        od_final = temp_od.reset_index()
        od_final = od_final.astype({"work": str, "home": str})
        od_final.to_csv(output_path)
    else:
        combine_df['work'] = combine_df.w_geocode.astype(str).str[:11]
        combine_df['home'] = combine_df.h_geocode.astype(str).str[:11]
        temp_df = combine_df.loc[:, ['work', 'home', 'S000']]
        temp_od = temp_df.groupby(['work', 'home']).sum()
        od_final = temp_od.reset_index()
        od_final = od_final.astype({"work": str, "home": str})
        od_final.to_csv(output_path)


def get_number_of_wp(data, od, campany_df, state_code, error_tract):
    """
    calculate number of workplaces for each tract
    wp_tract = wp_cty * (tract_employed / county_employed)
    """
    try:
        """
        calculate number of workplaces for each tract
        wp_tract = wp_cty * (tract_employed / county_employed) #commute peaple amout
        """

        # print("++++++++++")
        # use "od data" to get number of jobs in each census tract
        # and number of jobs in each county
        tract_number = str(data.GEOID)  # .astype(str)
        tract_jobs_df = od[['work', 'S000']].groupby('work').sum().reset_index()

        tract_jobs_df = tract_jobs_df.astype({"work": str})
        tract_jobs_number = int(tract_jobs_df.loc[tract_jobs_df.work == tract_number, 'S000'].values[
                                    0])  # total number of job in each tract

        # print("Tract", tract_number, "has", tract_jobs_number, "jobs")
        def get_county_and_job_number(state_code, tract_jobs_df):
            # county total number of job
            if state_code in ['01', '02', '04', '05', '06', '08', '09']:
                # county_number = tract_number[:4]
                tract_jobs_df['county'] = tract_jobs_df.work.astype(str).str[:4]
                county_job_df = tract_jobs_df[['county', 'S000']].groupby('county').sum().reset_index()
                return int(county_job_df.S000[0]), tract_number[:4]
            else:
                # county_number = tract_number[:5]
                tract_jobs_df['county'] = tract_jobs_df.work.astype(str).str[:5]
                county_job_df = tract_jobs_df[['county', 'S000']].groupby('county').sum().reset_index()
                # county_job_number = int(county_job_df.S000[0])
                return int(county_job_df.S000[0]), tract_number[:5]

        county_job_number, county_number = get_county_and_job_number(state_code, tract_jobs_df)
        # print("County", county_number, "has",county_job_number, "company")

        # print("Job Number", county_job_number, "")
        # print(campany_df)
        county_company_number = int(campany_df[campany_df.county == county_number].ESTAB.values[0])
        tract_wp_number = int(county_company_number * (tract_jobs_number / county_job_number))
        # print("Tract",  tract_number, "has", tract_wp_number, "companys")
        return tract_wp_number

    except:
        logger.info(f"{tract_number} has issue")
        error_tract.append(tract_number)
        return 0


def unzip_files(zip_source, extraction_directory):
    """
    Unzips all files from a specified source directory into a target directory.

    :param zip_source: Path to the ZIP files with wildcard for multiple files (e.g., '../data/interim-data/road/*.zip')
    :param extraction_directory: Directory where contents of the zip files will be extracted
    """
    # Use glob to find all zip files in the specified source directory
    zip_files = glob.glob(zip_source)
    if not zip_files:
        logger.warning(f"No zip files found in {zip_source}")
        return

    # Check if the extraction directory exists, create if it doesn't
    if not os.path.exists(extraction_directory):
        os.makedirs(extraction_directory)
        logger.info(f"Created directory: {extraction_directory}")

    # Process each zip file
    for zip_file in zip_files:
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extraction_directory)
                logger.info(f"Extracted {zip_file} to {extraction_directory}")
        except zipfile.BadZipFile:
            logger.error(f"Bad zip file detected and skipped: {zip_file}")
        except Exception as e:
            logger.error(f"Failed to extract {zip_file}: {str(e)}")

    # Optionally, list the extracted files
    extracted_files = os.listdir(extraction_directory)
    logger.info(f"Extracted files in {extraction_directory}: {extracted_files}")


# Add starting and ending age for schools
def __school_start_age__(row):
    '''
    Assign School starting age and end age based on school type School
    Function to get start age for schools
    :param row:
    :return: age
    '''
    # print("+++++++ in function __school_start_end_age")
    # print(row.NAME)
    if row.LEVEL in ['Primary', 'Elementary']:
        # print(row.LEVEL)
        start_a = 5
        # end_a = 11

    elif row.LEVEL in ['Middle']:
        # print(row.LEVEL)
        start_a = 12
        # end_a = 14

    elif row.LEVEL in ['Secondary']:
        # print(row.LEVEL)
        start_a = 12
        # end_a = 17

    elif row.LEVEL in ['High']:
        # print(row.LEVEL)
        start_a = 15
        # end_a = 17

    else:
        # print(row.LEVEL)
        start_a = 5
        # end_a = 17
    # print(start_a)
    return start_a  # , end_a


def __school_end_age__(row):
    '''
    Function to get end age for schools
    :param row:
    :return: age
    '''
    # print("+++++++ in function __school_start_end_age")
    # print(row.NAME)
    if row.LEVEL in ['Primary', 'Elementary']:
        # print(row.LEVEL)
        # start_a = 5
        end_a = 11

    elif row.LEVEL in ['Middle']:
        # print(row.LEVEL)
        # start_a = 12
        end_a = 14

    elif row.LEVEL in ['Secondary']:
        # print(row.LEVEL)
        # start_a = 12
        end_a = 17

    elif row.LEVEL in ['High']:
        # print(row.LEVEL)
        # start_a = 15
        end_a = 17

    else:
        # print(row.LEVEL)
        # start_a = 5
        end_a = 17
    # print(end_a)
    return end_a