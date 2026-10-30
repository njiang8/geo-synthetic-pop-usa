import os
import re

import wget
import pandas as pd
import geopandas as gpd

from tqdm import tqdm
#from tqdm.notebook import tqdm
# Register tqdm with pandas
tqdm.pandas()
import argparse
import sys
import time

#general packages
from time import perf_counter
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import warnings



# Suppress only the InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

from bs4 import BeautifulSoup
from loguru import logger
from src.settings import RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR, state_codes, state_dict
from src.cli import add_geography_args, resolve_geography, in_counties, run_name
from src.seeding import add_seed_arg, seed_everything
from src.timing import RunTiming
#Synthesize Functions
from src.ctreate_individuals import __create_individuals__
from src.assign_household import __assign_household_order__
from src.create_space import __create_home_location__

from src.assign_workplace import __assign_workplaces__
from src.create_space import __create_work_location__
from src.assign_education_site import __assign_education_site__, EducationSites

from src.tools import check_urban
from src.tools import __verfication__
from src.tools import __collect_results__


def load_tract_id_work():
    #tract_id_work = pd.read_csv('../data/processed-data/us_tract_number_work.csv')
    tract_id_work = pd.read_json(os.path.join(PROCESSED_DATA_DIR, 'us_tract_number_work.json'), orient='records', lines=True, dtype={'GEOID': str})
    tract_id_work['GEOID'] = tract_id_work['GEOID'].astype(str)
    tract_id_work = tract_id_work.sort_values(by = 'GEOID').set_index('GEOID')
    logger.info(f"US Tract and Work Reading Done!")
    return tract_id_work


def __synthesize__(tract, od, road, us_tract_id_work, school, daycare, urban,  # data
                        population_list, workplace_list, ver_list, error_list,  # list
                        rng=None, timing=None):
    '''
    :param tract:
    :param od: od dataframe containing commute pattern
    :param road: road network shapefile
    :param us_tract_id_work: census tract dataset
    :param school: EducationSites for schools (enrollment counter shared across tracts)
    :param daycare: EducationSites for daycares (enrollment counter shared across tracts)
    :param urban: urban data
    :param population_list: an empty list defined outside the function
    :param workplace_list: an empty list defined outside the function
    :param ver_list: an empty list defined outside the function
    :param error_list: an empty list defined outside the function
    :param rng: numpy Generator from seed_everything(); Python `random` must already be seeded
    :param timing: optional collector shared across tracts for the run's timing summary
    :return: None
    '''
    timing = RunTiming() if timing is None else timing
    start_time = perf_counter()
    first_row = len(timing.rows)
    status = 'success'

    def measured(stage, function, *args):
        return timing.call(stage, function, *args, tract=tract.name, scope='tract_stage')

    logger.info(f"{tract.name} started")
    edu_snapshots = measured('education snapshot', lambda: (school.snapshot(), daycare.snapshot()))

    try:
        # Step 1: Create demographic information
        # 1.1 Create Individuals
        people = measured('individual creation', __create_individuals__, tract, rng)
        # 1.2 Group individual household
        measured('household assignment', __assign_household_order__, tract, people, rng)
        # __assign_household__(tract, people)
        # 1.3 Create household location on road network
        with timing.measure('home placement', tract.name, 'tract_stage'):
            home_location = __create_home_location__(tract, tract.DP1_0132C + 1, road, rng)  # + 1 means group quarter
            people['geometry'] = people.hhold.map(home_location)

        # Step 2: Assign Daytime Location
        # 2.1 Assign people to work and create workplace location on road network
        measured('job assignment', __assign_workplaces__, tract, people, od, us_tract_id_work, rng)
        # 2.2 Create workplace location on road network
        work_location = measured('workplace placement', __create_work_location__, tract, road, rng)
        # 2.3 Assign Kid to Education Sites based on its household location
        measured('education assignment', __assign_education_site__, tract, people, school, daycare)

        # Step 3: Check Urban population
        with timing.measure('urban classification', tract.name, 'tract_stage'):
            people['urban'] = people.apply(lambda row: check_urban(row, urban), axis=1)

        # Step 4: Verification
        ver_df = measured('verification', __verfication__, tract, people)

        # Append results to lists
        population_list.append(people)
        workplace_list.append(work_location)
        ver_list.append(ver_df)

    except Exception as e:
        status = 'failed'
        logger.error(f"{tract.name} has a problem: {e}", exc_info=True)
        error_list.append((tract.name, str(e)))
        # a failed tract's children are dropped, so release their school/daycare places
        with timing.measure('education rollback', tract.name, 'tract_stage'):
            school.restore(edu_snapshots[0])
            daycare.restore(edu_snapshots[1])

    elapsed_time = perf_counter() - start_time
    timing.finish_tract(first_row, tract.name, elapsed_time, status)
    logger.info(f'{tract.name} now ended ({elapsed_time:.1f} secs)')

if __name__ == '__main__':
    command_start = perf_counter()
    parser = add_geography_args(argparse.ArgumentParser(description='Synthesize population by state'))
    parser.add_argument('--dry-run', action='store_true',
                        help='list the tracts that would be processed and exit')
    add_seed_arg(parser)
    args = parser.parse_args()
    try:
        run_state_codes, counties = resolve_geography(args)
    except argparse.ArgumentTypeError as e:
        parser.error(str(e))

    logger.info(f'Start Running...')

    # one seed for Python random and the numpy Generator passed to every drawing step
    rng = seed_everything(args.seed)
    logger.info(f"Seed {args.seed}")
    # GDAL otherwise stamps the write time into GeoPackage metadata, so same-seed
    # outputs would differ byte-wise; an explicit env value still wins
    os.environ.setdefault('OGR_CURRENT_DATE', '2000-01-01T00:00:00Z')

    #input data path
    tract_path = os.path.join(PROCESSED_DATA_DIR, 'census')
    od_path = os.path.join(PROCESSED_DATA_DIR, 'od')
    road_path = os.path.join(PROCESSED_DATA_DIR, 'road')
    edu_path = os.path.join(PROCESSED_DATA_DIR, 'edu')
    urban_path = os.path.join(PROCESSED_DATA_DIR, 'urban')

    #saving path
    result_path = RESULTS_DIR

    shared_timing = RunTiming()
    tract_id_work = None if args.dry_run else shared_timing.call(
        'load workplace weights (shared)', load_tract_id_work)

    # Loop through the state using state code
    for state_code in run_state_codes:
        state_start = perf_counter()
        timing = RunTiming()
        timing.rows.extend(dict(row) for row in shared_timing.rows)
        state_abbreviation = state_dict[state_code].lower()
        logger.info(f"========{state_abbreviation}========")

        # Step 1 Load Data
        # 1 Tract (gdf, shp)
        state_tract_path = os.path.join(tract_path, f"{state_abbreviation}-tracts-demo-work.shp.zip")
        logger.info(f"{state_abbreviation} Census Tract Path {state_tract_path}")
        with timing.measure('load and select tracts'):
            state_tract = gpd.read_file(state_tract_path)
            state_tract = state_tract[state_tract['DP1_0001C'] > 0] #select tract with population
            state_tract['GEOID'] = state_tract['GEOID'].astype(str)
            state_tract = state_tract[in_counties(state_tract['GEOID'], state_code, counties)]
            state_tract = state_tract.sort_values(by='GEOID').set_index('GEOID')
        logger.info(f"{state_abbreviation} Census Tract Coord is {state_tract.crs}")
        logger.info(f"{state_abbreviation} tracts selected: {len(state_tract)}")

        if args.dry_run:
            for geoid in state_tract.index:
                print(geoid)
            continue

        # 2 Origin and destination (df, csv)
        state_od_path = os.path.join(od_path, f"{state_abbreviation}-tract-od-2020.csv")
        logger.info(f"{state_abbreviation} OD Path {state_od_path}")
        with timing.measure('load commuting'):
            state_od = pd.read_csv(state_od_path, dtype={'work': str, 'home': str})

        # 3 Road (gdf, shp)
        state_road_path = os.path.join(road_path, f"{state_abbreviation.upper()}_road_cleaned.shp.zip")
        logger.info(f"{state_abbreviation} Road Path {state_road_path}")
        with timing.measure('load roads'):
            state_road = gpd.read_file(state_road_path)
        logger.info(f"{state_abbreviation} Road Coord is {state_road.crs}")

        # 4.1 Education site-school(gdf, gpkg)
        state_school_path = os.path.join(edu_path, f"{state_abbreviation}_school_id.gpkg")
        logger.info(f"{state_abbreviation} School Path {state_school_path}")
        with timing.measure('load schools'):
            state_school = gpd.read_file(state_school_path)
        logger.info(f"{state_abbreviation} School Coord is {state_school.crs}")

        # 4.2 Education site-daycare (gdf, gpkg)
        state_daycare_path = os.path.join(edu_path, f"{state_abbreviation}_daycare_id.gpkg")
        logger.info(f"{state_abbreviation} Daycare Path {state_daycare_path}")
        with timing.measure('load daycares'):
            state_daycare = gpd.read_file(state_daycare_path)
        logger.info(f"{state_abbreviation} Daycare Coord is {state_daycare.crs}")
        # one enrollment counter per site table for the whole state run
        with timing.measure('initialize education sites'):
            school_sites = EducationSites(state_school)
            daycare_sites = EducationSites(state_daycare)

        # 5 Urban area (gdf, gpkg)
        state_urban_path = os.path.join(urban_path, f"{state_abbreviation.upper()}_urban.gpkg")
        logger.info(f"{state_abbreviation} urban shp Path {state_urban_path}")
        with timing.measure('load urban polygons'):
            state_urban = gpd.read_file(state_urban_path)
        logger.info(f"{state_abbreviation} Urban Area Coord is {state_urban.crs}")

        # list to save results
        population = []
        workplaces = []
        verification = []
        error_log = []

        # Run the __synthesize__ function
        with timing.measure('synthesis loop'):
            state_tract.progress_apply(
                lambda x: __synthesize__(x, state_od, state_road, tract_id_work, school_sites, daycare_sites,
                                              state_urban,  # input datasets
                                              population, workplaces, verification, error_log,  # resulting list
                                              rng, timing), axis=1)
        logger.info(f"{state_abbreviation} education capacity fallbacks: "
                    f"school {len(school_sites.fallbacks)}, daycare {len(daycare_sites.fallbacks)}")

        # Collect Data and Save Results
        logger.info(f"Saving Results")
        state_results_path = os.path.join(result_path, f'{state_abbreviation}')
        name = run_name(state_abbreviation, counties)

        if not os.path.exists(state_results_path):
            logger.info(f"Creating Path {state_results_path}")
            os.makedirs(state_results_path)

        population_path = os.path.join(state_results_path, f'{name}_population')
        with timing.measure('collect population'):
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
            with timing.measure('write population GeoPackage'):
                population_df.to_file(population_path + ".gpkg", driver='GPKG')
            with timing.measure('write population CSV'):
                population_df.to_csv(population_path + ".csv")
            logger.info(f"Saved {state_abbreviation} Population to: {population_path}")

        else:
            logger.info(f"Total Population Generated for {state_abbreviation}: {len(population_df)}")
            logger.info(f"Saving {state_abbreviation} Population to: {population_path}")
            with timing.measure('write population GeoPackage'):
                population_df.to_file(population_path + ".gpkg", driver='GPKG')
            logger.info(f"Saved {state_abbreviation} Population to: {population_path}")

        workplace_path = os.path.join(state_results_path, f'{name}_workplace')
        with timing.measure('collect workplace'):
            workplace_df = __collect_results__(workplaces, "Work")
        with timing.measure('write workplace GeoPackage'):
            workplace_df.to_file(workplace_path + ".gpkg", driver='GPKG')
        logger.info(f"Total Workplaces Generated for {state_abbreviation}: {len(workplace_df)}")
        logger.info(f"Saving {state_abbreviation} Workplaces to: {workplace_path}")

        ver_path = os.path.join(state_results_path, f'{name}_verification.csv')
        with timing.measure('collect verification'):
            verification_df = __collect_results__(verification, "Verification")
        with timing.measure('write verification CSV'):
            verification_df.to_csv(ver_path)
        logger.info(f"Saving {state_abbreviation} Verification to: {ver_path}")

        if len(error_log) > 0:
            error_log_path = os.path.join(state_results_path, f'{name}_error_log.csv')
            with timing.measure('collect error_log'):
                error_log_df = __collect_results__(error_log, "ErrorLog")
            with timing.measure('write error_log CSV'):
                error_log_df.to_csv(error_log_path)
            logger.info(f"Saving {state_abbreviation} ErrorLog to: {error_log_path}")
        else:
            logger.info(f"No Error Tracts Found")
            pass

        state_elapsed = perf_counter() - state_start
        timing.rows.append(dict(scope='run', tract='', stage='state total',
                                elapsed_seconds=state_elapsed, status='success', tract_status=''))
        timing.report(os.path.join(state_results_path, f'{name}_timing.csv'))
        logger.info(f"Done! State elapsed: {state_elapsed:.3f} s ({state_elapsed / 60:.2f} min)")

    if not args.dry_run:
        command_elapsed = perf_counter() - command_start
        logger.info(f"Total command elapsed: {command_elapsed:.3f} s ({command_elapsed / 60:.2f} min)")
