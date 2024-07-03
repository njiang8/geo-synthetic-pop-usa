import os
import re

import wget
import pandas as pd
import geopandas as gpd

from tqdm import tqdm
#from tqdm.notebook import tqdm
# Register tqdm with pandas
tqdm.pandas()
import time

#general packages
import timeit
import random
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import warnings



# Suppress only the InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

from bs4 import BeautifulSoup
from loguru import logger
from src.settings import RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, state_codes, state_dict
#Synthesize Functions
from src.ctreate_individuals import __create_individuals__
from src.assign_household import __assign_household_order__
from src.create_space import __create_home_location__

from src.assign_workplace import __assign_workplaces__
from src.create_space import __create_work_location__
from src.assign_education_site import __assign_education_site__

from src.tools import check_urban
from src.tools import __verfication__
from src.tools import __collect_results__

logger.info(f'Start Running...')

#tract_id_work = pd.read_csv('../data/processed-data/us_tract_number_work.csv')
tract_id_work = pd.read_json('../../data/processed-data/us_tract_number_work.json', orient='records', lines=True)
tract_id_work['GEOID'] = tract_id_work['GEOID'].astype(str)
tract_id_work = tract_id_work.sort_values(by = 'GEOID').set_index('GEOID')
logger.info(f"US Tract and Work Reading Done!")


def __synthesize__(tract, od, road, us_tract_id_work, school, daycare, urban,  # data
                        population_list, workplace_list, ver_list, error_list  # list
                        ):
    '''
    :param tract:
    :param od: od dataframe containing commute pattern
    :param road: road network shapefile
    :param us_tract_id_work: census tract dataset
    :param school: school data
    :param daycare: daycare data
    :param urban: urban data
    :param population_list: an empty list defined outside the function
    :param workplace_list: an empty list defined outside the function
    :param ver_list: an empty list defined outside the function
    :param error_list: an empty list defined outside the function
    :return: None
    '''
    start_time = timeit.default_timer()
    logger.info(f"{tract.name} started")

    try:
        # Step 1: Create demographic information
        # 1.1 Create Individuals
        people = __create_individuals__(tract)
        # 1.2 Group individual household
        __assign_household_order__(tract, people)
        # __assign_household__(tract, people)
        # 1.3 Create household location on road network
        home_location = __create_home_location__(tract, tract.DP1_0132C + 1, road)  # + 1 means group quarter
        people['geometry'] = people.hhold.map(home_location)  # attach geometry to people based on household location

        # Step 2: Assign Daytime Location
        # 2.1 Assign people to work and create workplace location on road network
        __assign_workplaces__(tract, people, od, us_tract_id_work)
        # 2.2 Create workplace location on road network
        work_location = __create_work_location__(tract, road)
        # 2.3 Assign Kid to Education Sites based on its household location
        __assign_education_site__(tract, people, school, daycare)

        # Step 3: Check Urban population
        people['urban'] = people.apply(lambda row: check_urban(row, urban), axis=1)

        # Step 4: Verification
        ver_df = __verfication__(tract, people)

        # Append results to lists
        population_list.append(people)
        workplace_list.append(work_location)
        ver_list.append(ver_df)

    except Exception as e:
        logger.error(f"{tract.name} has a problem: {e}", exc_info=True)
        error_list.append((tract.name, str(e)))

    elapsed_time = timeit.default_timer() - start_time
    logger.info(f'{tract.name} now ended ({elapsed_time:.1f} secs)')

if __name__ == '__main__':
    r_seed = 42
    random.seed(r_seed)

    #input data path
    tract_path = '../../data/processed-data/census'
    od_path = '../../data/processed-data/od'
    road_path = '../../data/processed-data/road'
    edu_path = '../../data/processed-data/edu'
    urban_path = '../../data/processed-data/urban'
    
    #saving path
    result_path = '../../data/results-data'


    # Loop through the state using state code
    for state_code in state_codes:
        state_abbreviation = state_dict[state_code].lower()
        logger.info(f"========{state_abbreviation}========")

        # Step 1 Load Data
        # 1 Tract (gdf, shp)
        state_tract_path = os.path.join(tract_path, f"{state_abbreviation}-tracts-demo-work.shp.zip")
        logger.info(f"{state_abbreviation} Census Tract Path {state_tract_path}")
        state_tract = gpd.read_file(state_tract_path)
        state_tract = state_tract[state_tract['DP1_0001C'] > 0] #select tract with population
        state_tract['GEOID'] = state_tract['GEOID'].astype(str)
        state_tract = state_tract.sort_values(by='GEOID').set_index('GEOID')
        logger.info(f"{state_abbreviation} Census Tract Coord is {state_tract.crs}")

        # 2 Origin and destination (df, csv)
        state_od_path = os.path.join(od_path, f"{state_abbreviation}-tract-od-2020.csv")
        logger.info(f"{state_abbreviation} OD Path {state_od_path}")
        state_od = pd.read_csv(state_od_path)
        state_od['work'] = state_od['work'].astype(str)
        state_od['home'] = state_od['home'].astype(str)

        # 3 Road (gdf, shp)
        state_road_path = os.path.join(road_path, f"{state_abbreviation.upper()}_road_cleaned.shp.zip")
        logger.info(f"{state_abbreviation} Road Path {state_road_path}")
        state_road = gpd.read_file(state_road_path)
        logger.info(f"{state_abbreviation} Road Coord is {state_road.crs}")

        # 4.1 Education site-school(gdf, gpkg)
        state_school_path = os.path.join(edu_path, f"{state_abbreviation}_school_id.gpkg")
        logger.info(f"{state_abbreviation} School Path {state_school_path}")
        state_school = gpd.read_file(state_school_path)
        logger.info(f"{state_abbreviation} School Coord is {state_school.crs}")

        # 4.2 Education site-daycare (gdf, gpkg)
        state_daycare_path = os.path.join(edu_path, f"{state_abbreviation}_daycare_id.gpkg")
        logger.info(f"{state_abbreviation} Daycare Path {state_daycare_path}")
        state_daycare = gpd.read_file(state_daycare_path)
        logger.info(f"{state_abbreviation} Daycare Coord is {state_daycare.crs}")

        # 5 Urban area (gdf, gpkg)
        state_urban_path = os.path.join(urban_path, f"{state_abbreviation.upper()}_urban.gpkg")
        logger.info(f"{state_abbreviation} urban shp Path {state_urban_path}")
        state_urban = gpd.read_file(state_urban_path)
        logger.info(f"{state_abbreviation} Urban Area Coord is {state_urban.crs}")

        # list to save results
        population = []
        workplaces = []
        verification = []
        error_log = []

        # Run the __synthesize__ function
        state_tract.progress_apply(
            lambda x: __synthesize__(x, state_od, state_road, tract_id_work, state_school, state_daycare,
                                          state_urban,  # input datasets
                                          population, workplaces, verification, error_log  # resulting list
                                          ), axis=1)

        # Collect Data and Save Results
        logger.info(f"Saving Results")
        state_results_path = os.path.join(result_path, f'{state_abbreviation}')

        if not os.path.exists(state_results_path):
            logger.info(f"Creating Path {state_results_path}")
            os.makedirs(state_results_path)

        population_path = os.path.join(state_results_path, f'{state_abbreviation}_population')
        population_df = __collect_results__(population, "Pop")

        if population_df['id'].isna().any() or population_df['wp'].isna().any():
            logger.info(f"Population data Have nans in 'id': {len(population_df)}")
            population_df = population_df.dropna(subset=['id'])

            nan_count_id = population_df['id'].isna().sum()
            logger.info(f'Number of NaN values in the -id- column: {nan_count_id}')

            population_df['wp'] = population_df['wp'].fillna(population_df['hhold'])#assign home work population
            nan_count_wp = population_df['wp'].isna().sum()
            logger.info(f'Number of NaN values in the -wp- column: {nan_count_wp}')

            logger.info(f"Total Population Generated for {state_abbreviation}: {len(population_df)}")
            logger.info(f"Saving {state_abbreviation} Population to: {population_path}")
            population_df.to_file(population_path + ".gpkg", driver='GPKG')
            population_df.to_csv(population_path + ".csv")
            logger.info(f"Saved {state_abbreviation} Population to: {population_path}")

        else:
            logger.info(f"Total Population Generated for {state_abbreviation}: {len(population_df)}")
            logger.info(f"Saving {state_abbreviation} Population to: {population_path}")
            population_df.to_file(population_path + ".gpkg", driver='GPKG')
            logger.info(f"Saved {state_abbreviation} Population to: {population_path}")

        workplace_path = os.path.join(state_results_path, f'{state_abbreviation}_workplace')
        workplace_df = __collect_results__(workplaces, "Work")
        workplace_df.to_file(workplace_path + ".gpkg", driver='GPKG')
        logger.info(f"Total Workplaces Generated for {state_abbreviation}: {len(workplace_df)}")
        logger.info(f"Saving {state_abbreviation} Workplaces to: {workplace_path}")

        ver_path = os.path.join(state_results_path, f'{state_abbreviation}_verification.csv')
        verification_df = __collect_results__(verification, "Verification")
        verification_df.to_csv(ver_path)
        logger.info(f"Saving {state_abbreviation} Verification to: {ver_path}")

        if len(error_log) > 0:
            error_log_path = os.path.join(state_results_path, f'{state_abbreviation}_error_log.csv')
            error_log_df = __collect_results__(error_log, "ErrorLog")
            error_log_df.to_csv(error_log_path)
            logger.info(f"Saving {state_abbreviation} ErrorLog to: {error_log_path}")
        else:
            logger.info(f"No Error Tracts Found")
            pass

        logger.info(f"Done!")
