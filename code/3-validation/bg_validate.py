import os
import pandas as pd
import geopandas as gpd
#import fiona
from tqdm import tqdm
import matplotlib.pyplot as plt

from src.bg_validate_functions import pop_to_geo_df, prepare_bg_spop_gdf
from src.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR, state_codes, state_dict
from loguru import logger

logger.info('Loading US BG data..')
us_bg_boundary_pop = gpd.read_file('data/processed-data/acs/acs_bg_boundary_population.gpkg')

# Function to calculate Spearman correlation for each group
# def spearman_corr(group):
#     from scipy.stats import spearmanr
#     corr, _ = spearmanr(group['B01001e1'], group['count'])
#     return corr
# Function to calculate Spearman correlation for each group
def spearman_corr(group):
    from scipy.stats import spearmanr
    if group['B01001e1'].nunique() == 1 or group['count'].nunique() == 1:
        # Return NaN if any of the columns is constant (i.e., all values are identical)
        return float('nan')
    corr, _ = spearmanr(group['B01001e1'], group['count'])
    return corr
def get_spc_tract():
    results = []
    for state_code in tqdm(state_codes):

        state_abbreviation = state_dict[state_code]
        logger.info(f'Processing {state_abbreviation}...')
        # load spop
        logger.info(f'Loading {state_abbreviation} Population...')
        state_population_path = os.path.join(RESULTS_DIR, f"{state_abbreviation.lower()}/{state_abbreviation.lower()}_population.pickle")
        state_population = pd.read_pickle(state_population_path).loc[:,['id', 'long', 'lat', 'geometry']]

        # convert spop from pickle to gpd
        logger.info(f'Converting {state_abbreviation} Population to gpd...')
        state_population_gdf = pop_to_geo_df(state_population, 'EPSG:4269')

        #get bg population gdf from the us file using state code
        logger.info(f'Getting {state_abbreviation} BG Population...')
        state_bg_population = us_bg_boundary_pop[us_bg_boundary_pop['STATEFP'] == state_code]

        #process bg and spop
        state_bg_vali_df = prepare_bg_spop_gdf(state_bg_population, state_population_gdf)

        # Group by 'tract' and calculate Spearman correlation
        state_spearman_corrs = state_bg_vali_df.groupby('tract').apply(spearman_corr, include_groups=False).reset_index()
        state_spearman_corrs.columns = ['tract', 'spearman_correlation']

        #save a csv for each state
        state_spc_save_path = os.path.join(RESULTS_DIR,
                                             f"{state_abbreviation.lower()}/{state_abbreviation.lower()}_spc_tract.csv")
        logger.info(f'Saving spc state {state_abbreviation} data to {state_spc_save_path}')
        state_spearman_corrs.to_csv(state_spc_save_path)

        #
        over_5_corr = len(state_spearman_corrs[state_spearman_corrs['spearman_correlation'] >= 0.5])
        over_5_ratio = len(state_spearman_corrs[state_spearman_corrs['spearman_correlation'] >= 0.5]) / len(state_spearman_corrs)

        results.append({
            'state_abv': state_abbreviation,
            'count': over_5_corr,
            'all' : len(state_spearman_corrs),
            'ratio': over_5_ratio
        })
    return pd.DataFrame(results)

if __name__ == '__main__':
    state_data_df = get_spc_tract()
    logger.info(f"Data collected for states:\n{state_data_df}")
    #logger.info(f"Tracts with Spearman correlation >= 0.5: {tract_over5_count}")
    #logger.info(f"Ratio of tracts with Spearman correlation >= 0.5: {tract_over5_ratio:.2%}")
    state_data_df.to_csv("state_spearman_correlation.csv", index=False)
    logger.info("CSV saved as state_spearman_correlation.csv")
