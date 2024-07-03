from loguru import logger
from tqdm import tqdm
from src.preprocess_data import download_lodes_2020_data, combine_in_out_county_data
from src.settings import state_codes, state_dict


if __name__ == "__main__":

    for code in tqdm(state_codes):
        state_abbreviation = state_dict[code].lower()
        logger.info(f"Downloading {state_abbreviation}'s LODES8.")
        download_lodes_2020_data(state_abbreviation)
        logger.info(f"Combining {state_abbreviation}'s in and out state.")
        combine_in_out_county_data(state_abbreviation, code)
    logger.info(f"Finished downloading and Combining LODES8.")        #download_lodes_2020_data(code, state_abbreviation)