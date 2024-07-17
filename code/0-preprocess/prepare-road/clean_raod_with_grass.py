import os
from tqdm import tqdm
from loguru import logger

import warnings
# Suppress only the InsecureRequestWarning
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

from src.preprocess_data import process_interim_road_data
from src.settings import state_codes, state_dict

os.environ.update(dict(
    GRASSBIN="/Applications/GRASS-7.8.app/Contents/MacOS/GRASS.sh"
))
# the next line starts the GRASS GIS session
from grass_session import Session
import grass.script as gscript

# create a Session instance
PERMANENT = Session()
gisdata = 'data/grass'
p_location = 'clean_road'
mapset = 'PERMANENT'
# create a PERMANENT mapset
PERMANENT.open(gisdb= gisdata, location = p_location,
               create_opts='EPSG:4326')

def prcess_state_road_grass(state, road_shp, cleaned_road_shp, road_csv):
    '''
    Processes road data for a specific state using GRASS GIS tools.

    :param state: State abbreviation (e.g., 'TX' for Texas)
    :param road_shp: Path to the input road shapefile
    :param cleaned_road_shp: Path where the cleaned road shapefile will be saved
    :param road_csv: Path where the road data in CSV format will be saved
    :return: None
    '''

    # Start a new GRASS session
    with Session(gisdb=gisdata, location='clean_road', mapset=mapset, create_opts="EPSG:4326"):
        # Import the shapefile into GRASS
        # gscript.run_command('v.in.ogr', input=input_road_shp, flags='oe', overwrite=True)
        gscript.run_command('v.in.ogr',
                            input=road_shp, output='road_data',
                            flags='oe', overwrite=True)

        if not os.path.exists(cleaned_road_shp):
            # Clean the road data
            gscript.run_command('v.clean', input='road_data', output='cleaned_road_data',
                                tool='snap,break,rmdupl,rmsa', threshold='0.0001,0.0,0.0,0.0',
                                overwrite=True)

            # Export the cleaned road data
            gscript.run_command('v.out.ogr', input='cleaned_road_data', output=cleaned_road_shp,
                                format='ESRI_Shapefile')
            logger.info(f"shp save as {cleaned_road_shp}")
        else:
            logger.info("Cleaned road shp data already exists. No need to overwrite.")

        if not os.path.exists(road_csv):
            # Find the largest connected component
            gscript.run_command('v.net.components', input='cleaned_road_data', output='largest_component',
                                method='weak', overwrite=True)
            # export the largest component
            gscript.run_command('v.out.ogr', input='largest_component', output=road_csv, format='CSV')
            logger.info(f"csv save as {road_csv}")
        else:
            logger.info("Cleaned road csv data already exists. No need to overwrite.")

        logger.info(f"Processing completed shp + csv {state}'s Road.")
        # print("Processing completed. Files saved to:", output_directory)


if __name__ == "__main__":

    input_directory = 'data/interim-data/road/shp/'
    output_directory = 'data/interim-data/road/'

    #use GRASS to claen the road data
    for code in tqdm(state_codes):
        state_abbreviation = state_dict[code]
        logger.info(f" {state_abbreviation}'s Road.")

        input_road_shp = os.path.join(input_directory, f"{state_abbreviation}_road.shp.shp")
        logger.info(f"Path of {input_road_shp}'s Road.")

        output_road_shp = os.path.join(output_directory, f"grass_output/{state_abbreviation}_road_cleaned.shp")
        logger.info(f"Path of {output_road_shp}'s Road.")

        output_road_csv = os.path.join(output_directory, f"csv/{state_abbreviation}_road_component.csv")
        logger.info(f"Path of {output_road_csv}'s Road.")

        # apply functions
        prcess_state_road_grass(state_abbreviation, input_road_shp, output_road_shp, output_road_csv)

    #Final preprocess Combine cleaned shp and csv from last step
    for code in tqdm(state_codes):
        state_abbreviation = state_dict[code]
        logger.info(f"Final Process {state_abbreviation}'s Road Network.")
        process_interim_road_data(state_abbreviation)

    logger.info(f"All Done!")