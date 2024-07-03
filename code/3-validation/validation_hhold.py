import os
import pandas as pd
import geopandas as gpd

from tqdm import tqdm

from loguru import logger
from src.settings import state_codes, state_dict
from src.verification import get_hholde_type_amount, plot_hhold_df

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", message="findfont: Font family")

def get_state_us_ver_hhold_dfs_plots():
    census_path = '../../data/processed-data/census'
    results_path = '../../data/results-data'

    final_hhold_ver_df = pd.DataFrame()  # hhold vali

    for state_code in tqdm(state_codes):
    #for state_code in tqdm(state_codes[7:9]):
        state_abbreviation = state_dict[state_code].lower()
        logger.info(f"========{state_abbreviation}========")

        # hhold ver path- resulting
        state_hhold_ver_df_final_path = os.path.join(results_path,
                                                     f"{state_abbreviation}/{state_abbreviation}_hhold_verification.csv")
        plot_hhold_final_path = os.path.join(results_path,
                                             f"{state_abbreviation}/{state_abbreviation}_hhold_ver_plot.png")

        #read in path
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
                state_census_gdf = gpd.read_file(state_census_path)
                logger.info(f"Loaded census data - Count before removing errors: {len(state_census_gdf)}")

                good_state_census_gdf = state_census_gdf[~state_census_gdf['GEOID'].isin(error_tract_id)]
                logger.info(f"Count after removing errors: {len(good_state_census_gdf)}")
            else:
                logger.warning(f"Census data file not found: {state_census_path}")
                continue

            if os.path.exists(state_population_path):
                state_population_gdf = gpd.read_file(state_population_path)
            else:
                logger.warning(f"Population data file not found: {state_population_path}")
                continue

            #hhold
            state_hhold_ver_df = get_hholde_type_amount(state_census_gdf, good_state_census_gdf, state_population_gdf)
            state_hhold_ver_df.to_csv(state_hhold_ver_df_final_path)

            # plot
            plot_hhold_df(state_hhold_ver_df, plot_hhold_final_path)

            # concat all
            final_hhold_ver_df = pd.concat([final_hhold_ver_df, state_hhold_ver_df], axis=0)

        except Exception as e:
            (logger.error(f"An error occurred while processing {state_abbreviation}: {str(e)}"))

    if not os.path.exists(f"{results_path}/1-us/"):
        logger.info("Create U.S. path")
        os.makedirs(f"{results_path}/1-us/")

    us_hhold_ver_df_path = os.path.join(results_path, "1-us/us_hhold_ver_df.csv")
    us_hhold_ver_plot_path = os.path.join(results_path, "1-us/us_hhold_ver_plot.png")

    final_hhold_ver_df = final_hhold_ver_df.reset_index().rename(columns={'index': 'Type'})
    us_hhold_by_type = final_hhold_ver_df.groupby('Type').sum().reset_index()
    us_hhold_by_type.to_csv(us_hhold_ver_df_path)
    logger.info("Saved U.S. hhold verification DataFrtame results!!!")

    plot_hhold_df(us_hhold_by_type, us_hhold_ver_plot_path)
    logger.info("Saved U.S. hhold verification Plot!!!")

if __name__ == '__main__':
    logger.info("Starting verification state")
    get_state_us_ver_hhold_dfs_plots()
    logger.info("Done!!!")

