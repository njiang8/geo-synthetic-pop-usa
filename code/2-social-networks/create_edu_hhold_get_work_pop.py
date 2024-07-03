import os
from pathlib import Path
import pandas as pd

from tqdm import tqdm
#from tqdm.notebook import tqdm

from loguru import logger
from src.settings import state_codes, state_dict

from src.create_social_networks import create_networks_types

def create_by_state():
    results_path = '../../data/results-data'

    work_population = pd.DataFrame()

    for state_code in tqdm(state_codes):
        state_abbreviation = state_dict[state_code].lower()
        logger.info(f"========{state_abbreviation}========")
        state_abbreviation = state_dict[state_code].lower()

        state_population_path = os.path.join(results_path, f"{state_abbreviation}/{state_abbreviation}_population.pickle")

        final_population_path = os.path.join(results_path, "1-us/us_work_population.csv")
        # todo check cache file
        state_population = pd.read_pickle(state_population_path).loc[:, ['id', 'age', 'hhold', 'wp']]
        # Create Social Network (Edu and Household)
        create_networks_types(state_population, results_path, state_abbreviation)

        work_population = pd.concat([work_population,
                                     state_population[(state_population.age >= 18) &
                                                      (state_population.wp.str.contains("w"))]], axis=0
                                    )

    if not Path(final_population_path).exists():
        work_population.to_csv(final_population_path, index=False)
    else:
        logger.info("US work population already exists")

if __name__ == '__main__':
    logger.info("Starting Creating and Getting Work Population")
    create_by_state()
    logger.info("Done!!!")