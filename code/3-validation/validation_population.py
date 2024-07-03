import os

import pandas as pd
import geopandas as gpd

from tqdm import tqdm
from loguru import logger

from src.settings import state_codes, state_dict
from src.after_validation_functions import verifiy_age_group, plot_ver_age_df

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", message="findfont: Font family")

def get_state_us_age_ver_dfs_plots():
    census_path = '../../data/processed-data/census'
    results_path = '../../data/results-data'

    final_age_ver_df = pd.DataFrame()

    for state_code in tqdm(state_codes):
        state_abbreviation = state_dict[state_code].lower()
        logger.info(f"========{state_abbreviation}========")

        state_age_ver_df_final_path = os.path.join(results_path,
                                                   f"{state_abbreviation}/{state_abbreviation}_age_verification.csv")
        plot_final_path = os.path.join(results_path, f"{state_abbreviation}/{state_abbreviation}_age_ver_plot.png")

        state_census_path = os.path.join(census_path, f"{state_abbreviation}-tracts-demo-work.shp.zip")
        state_population_path = os.path.join(results_path,
                                             f"{state_abbreviation}/{state_abbreviation}_population.gpkg")
        state_error_tract_path = os.path.join(results_path,
                                              f"{state_abbreviation}/{state_abbreviation}_error_log.csv")

        try:
            if os.path.exists(state_error_tract_path):
                state_error_df = pd.read_csv(state_error_tract_path)
                if 'tract' not in state_error_df.columns:
                    error_tract_id = list(state_error_df['Tract_Name']) if not state_error_df.empty else []
                else:
                    error_tract_id = list(state_error_df['tract']) if not state_error_df.empty else []
                logger.info(f"Loaded error log for {state_abbreviation}")
            else:
                error_tract_id = []
                logger.warning(f"Error log file not found: {state_error_tract_path}")

            if os.path.exists(state_census_path):
                state_census_gdf = gpd.read_file(state_census_path)#all census
                logger.info(f"Loaded census data - Count before removing errors: {len(state_census_gdf)}")
                good_state_census_gdf = state_census_gdf[~state_census_gdf['GEOID'].isin(error_tract_id)]#census remove error tracts
                logger.info(f"Count after removing errors: {len(good_state_census_gdf)}")
            else:
                logger.warning(f"Census data file not found: {state_census_path}")
                continue

            if os.path.exists(state_population_path):
                logger.info(f"Loading {state_abbreviation} population..")
                state_population_gdf = gpd.read_file(state_population_path)
                logger.info(f"Loaded Population data - Count before removing nans in 'id': {len(state_population_gdf)}")
                state_population_gdf = state_population_gdf.dropna(subset=['id'])
                logger.info(f"Count after removing nans in 'id': {len(state_population_gdf)}")
            else:
                logger.warning(f"Population data file not found: {state_population_path}")
                continue

            state_age_ver_df = verifiy_age_group(state_census_gdf, good_state_census_gdf, state_population_gdf)
            state_age_ver_df.to_csv(state_age_ver_df_final_path)

            plot_ver_age_df(state_age_ver_df, plot_final_path)

            final_age_ver_df = pd.concat([final_age_ver_df, state_age_ver_df], axis=0)

        except Exception as e:
            (logger.error(f"An error occurred while processing {state_abbreviation}: {str(e)}"))

if __name__ == '__main__':
    logger.info("Starting verification state")
    get_state_us_age_ver_dfs_plots()
    logger.info("Done!!!")

