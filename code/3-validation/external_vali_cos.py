import os

import pandas as pd
from tqdm import tqdm

from urllib3.exceptions import InsecureRequestWarning
import warnings
# Suppress only the InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

from loguru import logger
from src.settings import state_codes, state_dict, RESULTS_DIR
from src.external_validation import (read_pums_file,get_aggregate_spop_data,
                                     get_aggregate_pums20_data, read_clean_pums_tract_relationship,
                                     get_cosine_similarity)

def get_us_aggregate_spop_data(pums_id_tract):
    ### Prepare Spop each state
    us_agg_spop_data = pd.DataFrame()

    for state_code in tqdm(state_codes):
        #results_path = '../data/results-data'RESULTS_DIR
        results_path = RESULTS_DIR

        state_abbreviation = state_dict[state_code].lower()
        logger.info(f"========{state_abbreviation}========")
        state_abbreviation = state_dict[state_code].lower()

        state_population_path = os.path.join(results_path,
                                             f"{state_abbreviation}/{state_abbreviation}_population.pickle")
        state_population = pd.read_pickle(state_population_path).loc[:, ['id', 'age', 'gender']]
        logger.info(f'Loaded {state_abbreviation} population-0 Size: {len(state_population)}')

        state_spop_agg_df = get_aggregate_spop_data(state_population, pums_id_tract)
        us_agg_spop_data = pd.concat([us_agg_spop_data, state_spop_agg_df], axis=0)
    #us_agg_spop_data.head()
    #save_us_agg_path = os.path.join(results_path, f"1-us/us_agg_spop.csv")
    #us_agg_spop_data.to_csv(save_us_agg_path)
    return us_agg_spop_data

def get_us_aggregate_pums_data(pums_path):
    pums_us = read_pums_file(pums_path)
    us_agg_pums_data = get_aggregate_pums20_data(pums_us)
    return us_agg_pums_data

if __name__ == '__main__':
    logger.info('Start...')
    #PUMS and Census Tract Relationships
    pums_tract_path = 'data/raw-data/puma/2020_Census_Tract_to_2020_PUMA.csv'
    pums_tract_relationship = read_clean_pums_tract_relationship(pums_tract_path)
    #Get Aggregated data from spop
    us_agg_spop_data = get_us_aggregate_spop_data(pums_tract_relationship)

    #Get Aggregated data from spop
    pums_data_path = 'data/raw-data/puma/csv_pus_2022'
    us_agg_pums_data = get_us_aggregate_pums_data(pums_data_path)

    #caculate cosine similarity
    A = us_agg_pums_data.to_numpy()
    B = us_agg_spop_data.to_numpy()
    get_cosine_similarity(A, B)

    logger.info("Done!!!")