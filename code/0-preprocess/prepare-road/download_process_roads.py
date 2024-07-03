import os
from tqdm import tqdm
from loguru import logger
from src.preprocess_data import richard_download_and_prepare_road_data, process_interim_road_data
from src.settings import state_codes,state_dict

for code in tqdm(state_codes):
    state_abbreviation = state_dict[code]
    #download
    #unzip
    #clean with grass

    logger.info(f"Downloading {state_abbreviation}'s Road Network.")
    richard_download_and_prepare_road_data(code, state_abbreviation)

    #combine shp and csv
    #process_interim_road_data(state_abbreviation)
logger.info(f"Finished!")



