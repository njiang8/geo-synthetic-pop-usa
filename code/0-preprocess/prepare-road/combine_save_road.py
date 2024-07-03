from tqdm import tqdm
from loguru import logger
import pandas as pd
import geopandas as gpd

import glob

# Path where the ZIP files are stored
path_to_zip_files = 'data/interim-data/road/*.zip'

# Use glob to list all ZIP files in the directory
zip_files = glob.glob(path_to_zip_files)

logger.info(f"All zipfiles path and name {zip_files}'s Road Network.")

# Initialize an empty list to store dataframes
dataframes = []

# Loop through the ZIP files and read them into GeoDataFrames
for zip_file in tqdm(zip_files):
    # GeoPandas can read from "zip://" URIs directly
    gdf = gpd.read_file(f"zip://{zip_file}")
    dataframes.append(gdf)

# Concatenate all GeoDataFrames into one
all_geodata = gpd.GeoDataFrame(pd.concat(dataframes, ignore_index=True)).to_crs('epsg:4326')
#logger.info(f"Downloading {all_geodata.hea}'s Road Network.")
logger.info(all_geodata.head())
type_list = ['S1400', 'S1200', 'S1740']
local_road = all_geodata[all_geodata['MTFCC'].isin(type_list)]


#local_road.to_file('data/interim-data/all_us_local_road.shp.zip')
dask_road_gdf.to_file('../data/interim-data/all_us_local_road.gpkg', layer='roads', driver='GPKG')

logger.info(f"Done!")
