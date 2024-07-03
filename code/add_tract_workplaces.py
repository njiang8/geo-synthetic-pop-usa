import os
import warnings

# Suppress only the InsecureRequestWarning
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

import pandas as pd
import geopandas as gpd

from loguru import logger
from tqdm import tqdm
from src.preprocess_data import get_number_of_wp
from src.settings import INTERIM_DATA_DIR, PROCESSED_DATA_DIR, state_codes, state_dict

# 1 Read Data
#print(INTERIM_DATA_DIR)
cbp_path = os.path.join(INTERIM_DATA_DIR, "cbp/workplace_cbp.csv")
logger.info(f"Reading county company data from {cbp_path}")
cbp = pd.read_csv(cbp_path).iloc[:,1:]
cbp['county'] = cbp['county'].astype(str)
logger.info(cbp.head())

census_path = os.path.join(INTERIM_DATA_DIR, "census/census_demo_4326.shp.zip")
logger.info(f"Reading Census Tract data from {census_path }")
census_gdf = gpd.read_file(census_path)

#for code in tqdm(state_codes[:2]):
for code in tqdm(state_codes):
        # for code in state_code[:2]:
        state_abbreviation = state_dict[code]
        logger.info(f" {state_abbreviation}'s Data.")

        full_census_path = os.path.join(PROCESSED_DATA_DIR, f"census/{state_abbreviation.lower()}-tracts-demo-work.shp.zip")

        if not os.path.exists(full_census_path):
                od_path = os.path.join(INTERIM_DATA_DIR, f"od/{state_abbreviation.lower()}-tract-od-2020.csv")

                # logger.info(f"Reading in OD data from  {od_path}")
                od_df = pd.read_csv(od_path).reset_index(drop=True)  # od
                state_census = census_gdf[census_gdf['STATEFP'] == code].copy()  # census

                # apply function
                error_tract = []  # list to hold the error tract
                state_census['WP_CNT'] = state_census.apply(get_number_of_wp, args=(od_df, cbp, code, error_tract),
                                                            axis=1)
                # logger.info(state_census.head()) #check
                # save tracts with demo and work info to zip in processes data folder to csv
                census_path = os.path.join(PROCESSED_DATA_DIR, "census")
                if not os.path.exists(census_path):
                        os.makedirs(census_path)

                logger.info(f"Saving census tract to {full_census_path}")
                state_census.to_file(full_census_path)


                # save error to csv
                # Check if the directory exists
                error_path = os.path.join(PROCESSED_DATA_DIR, "workplaces_error")
                if not os.path.exists(error_path):
                        logger.info(f"creating path {error_path}")
                        # If it does not exist, create the directory
                        os.makedirs(error_path)
                        #print(f"Directory created: {error_path}")
                #else:
                        #print(f"Directory already exists: {error_path}")

                full_error_path = os.path.join(error_path,f"{state_abbreviation.lower()}-work-tract-error.csv")
                logger.info(f"Saving error tract to {full_error_path}")
                error_tract_df = pd.DataFrame(error_tract, columns=['tract'])  # covert from list to df
                error_tract_df.to_csv(full_error_path, index=False)  # Save to CSV

        else:
                logger.info(f"{state_abbreviation} Census gdf with demo and work info data already exists.")

logger.info("All Done!")