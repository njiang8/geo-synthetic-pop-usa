import os
import warnings

# Suppress only the InsecureRequestWarning
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

import pandas as pd
import geopandas as gpd

from loguru import logger
from tqdm import tqdm
from src.settings import state_codes, state_dict, RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR

def process_census_shp():
    #get demo df
    demp_dp_df = prepare_51state_demo_dp_df()

    #prepare us census tract shp + demo data
    prepare_us_census_tract(demp_dp_df)


def prepare_51state_demo_dp_df(raw_data_path = RAW_DATA_DIR):
    dp_path = os.path.join(raw_data_path, 'demographic-profile-20/DECENNIALDP2020.DP1-Data.csv')
    dp_df = pd.read_csv(dp_path).iloc[2:, :-1]



    demo_list = ['GEOID', 'DP1_0001C', 'DP1_0025C', 'DP1_0026C', 'DP1_0027C', 'DP1_0028C', 'DP1_0029C', 'DP1_0030C',
                 'DP1_0031C', 'DP1_0032C', 'DP1_0033C', 'DP1_0034C', 'DP1_0035C', 'DP1_0036C', 'DP1_0037C', 'DP1_0038C',
                 'DP1_0039C', 'DP1_0040C', 'DP1_0041C', 'DP1_0042C', 'DP1_0043C', 'DP1_0049C', 'DP1_0050C', 'DP1_0051C',
                 'DP1_0052C', 'DP1_0053C', 'DP1_0054C', 'DP1_0055C', 'DP1_0056C', 'DP1_0057C', 'DP1_0058C', 'DP1_0059C',
                 'DP1_0060C', 'DP1_0061C', 'DP1_0062C', 'DP1_0063C', 'DP1_0064C', 'DP1_0065C', 'DP1_0066C', 'DP1_0067C']

    hhold_list = [
        'DP1_0112C', 'DP1_0113C', 'DP1_0114C', 'DP1_0115C', 'DP1_0116C', 'DP1_0117C', 'DP1_0118C', 'DP1_0119C',
        'DP1_0120C', 'DP1_0121C', 'DP1_0122C', 'DP1_0123C', 'DP1_0124C', 'DP1_0125C', 'DP1_0126C', 'DP1_0127C',
        'DP1_0128C', 'DP1_0129C', 'DP1_0130C', 'DP1_0131C', 'DP1_0132C', 'DP1_0133C', 'DP1_0134C', 'DP1_0135C',
        'DP1_0136C', 'DP1_0137C', 'DP1_0138C', 'DP1_0139C', 'DP1_0140C', 'DP1_0141C', 'DP1_0142C', 'DP1_0143C',
        'DP1_0144C', 'DP1_0145C', 'DP1_0146C']

    ver_list = ['GEOID', 'DP1_0001C', 'DP1_0025C', 'DP1_0049C', 'DP1_0132C']

    #create GEOID based on a col
    dp_df['GEOID'] = dp_df['GEO_ID'].str[-11:]

    #get demo df
    demo_df = dp_df.loc[:, demo_list + hhold_list]

    return demo_df

def prepare_us_census_tract(demo_df, interim_data_path = INTERIM_DATA_DIR):
    census_boundary_path = os.path.join(interim_data_path, '/census/all_census.shp.zip')
    census_boundary = gpd.read_file(census_boundary_path)
    logger.info(f"Census Tracts Boundary Loaded: size is {len(census_boundary)}")

    census_shp = census_boundary.merge(demo_df, on="GEOID")
    selected_states = census_shp[census_shp['STATEFP'].isin(state_codes)]

    save_us_census_tract_demo_path = os.path.join(interim_data_path,'census/census_demo.shp.zip')

    logger.info(f"US Tracts saving to {save_us_census_tract_demo_path}")
    selected_states.to_file(save_us_census_tract_demo_path)

    #return selected_states

if __name__ == '__main__':
    logger.info("Start...")
    process_census_shp()
    logger.info("Done...")

