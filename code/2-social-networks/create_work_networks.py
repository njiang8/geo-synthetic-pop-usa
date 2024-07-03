import os
from pathlib import Path
import pandas as pd
from loguru import logger
from src.create_social_networks import create_network, to_csv


def create_us_work_network(folder_path):
    try:
        # Ensuring the directory exists
        output_dir = Path(folder_path) / "1-us"
        output_dir.mkdir(parents=True, exist_ok=True)
        work_nx_path = output_dir / "us_work_network.csv"

        # Load population
        logger.info("Loading work population")
        population_path = output_dir / "us_work_population.csv"
        population = pd.read_csv(population_path)

        if not work_nx_path.exists():
            logger.info("No Networks, Creating US Work network...")
            # Assuming create_network function exists and works as expected
            new_network = create_network(population.set_index('id'), "Work")
            # Saving
            to_csv(new_network, population.set_index('id'), work_nx_path)
        else:
            logger.info('Work Network already exists')

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    logger.info("Creating US Work Network...")
    data_path = '../../data/results-data/'
    create_us_work_network(data_path)
    logger.info("Done!")