import os
from tqdm import tqdm
from loguru import logger
from src.preprocess_data import download_and_prepare_road_data, unzip_files
from src.settings import state_codes,state_dict


for code in tqdm(state_codes):
    # download road and process road data by state
    state_abbreviation = state_dict[code]
    logger.info(f"Downloading {state_abbreviation}'s Road Network.")
    download_and_prepare_road_data(code, state_abbreviation)

    #unzip the downloaded road file for next step with GRASS
    zip_files_path = '../data/interim-data/road/*.zip'
    extract_path = '../data/interim-data/road/shp'
    unzip_files(zip_files_path, extract_path)
logger.info(f"Finished!")



