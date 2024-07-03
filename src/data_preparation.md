# Data Preparation

## Data Directory Structure

The data directory structure is as follows:

    data
      ├── raw            <- The original, immutable data dump.
      ├── interim        <- Intermediate data that has been transformed.
      ├── processed      <- The final, canonical data sets for modeling.
      └── output         <- Output data from the project.

## Datasets

### 2010 U.S. Census Tracts

- Download from https://www.census.gov/geographies/mapping-files/2010/geo/tiger-data.html (choose `Census Tracts [391 MB]` under `Demographic Profile 1 - ShapeFile Format`).
- Unzip and save into your raw data folder `data/raw`. The file should look like:
   ```bash
   data/raw/
     └── Tract_2010Census_DP1/
           ├── DP_TableDescriptions.xls
           ├── Tract_2010Census_DP1.dbf
           ├── Tract_2010Census_DP1.prj
           ├── Tract_2010Census_DP1.shp
           └── Tract_2010Census_DP1.shx
   ```

### Road Network

- The script `scripts/create_synthetic_population.py` will download the road data from https://www2.census.gov/geo/tiger/TIGER2010/ROADS/. The data will be saved into `data/raw/road/{STATE_NAME}`. For example, for California (CA), the data will be saved into:
   ```
   data/raw/road/CA
     ├── tl_2010_06001_roads.zip
     ├── tl_2010_06003_roads.zip
     ├── ...
   ```
- The script will then combine all the road data into one file and save it into `data/interim/road/{STATE_NAME}_road.shp.zip`. For CA, it is:
   ```
   data/interim/road
     └── CA_road.shp.zip
   ```
- You will need to further process the road data with [GRASS GIS](https://grass.osgeo.org). Two steps to clean and get the giant connected component from the road shapefile.
  * Run GRASS `v.clean.advanced` tools `snap`, `break`, `rmdupl`, `rmsa` with tolerance values `0.0001`, `0.0`, `0.0`, `0.0`, save the result to `{STATE_NAME}_cleaned.shp`.
  * Run GRASS `v.net.components` tool (`weak` or `strong` does not matter since the network is undirected), save the result as `{STATE_NAME}_giant_component.csv`.
  * Put above files into `data/interim/grass_output` folder. For CA, it is:
      ```
      data/interim/grass_output
        ├── ...
        ├── CA_cleaned.shp
        ├── ...
        └── CA_giant_component.csv
      ```
- Run again the script `scripts/create_synthetic_population.py`. It will read the above two files and combine them into `data/processed/road/{STATE_NAME}_road_cleaned.shp.zip`. For CA, it is:
   ```
   data/processed/road
     └── CA_road_cleaned.shp.zip
   ```

### Buildings

If you want to use the building data, you will need to add it into the config file and put it into `data/raw/building` folder. For example, for San Francisco, in its `CA_SF.yaml` config file, the following is added:
   ```yaml
   buildings_data:
     filename: "SF_nearby_buildings_red.shp"
   ```
The file for San Francisco is:
   ```bash
   data/raw/building
     ├── SF_nearby_buildings_red.cpg
     ├── SF_nearby_buildings_red.dbf
     ├── SF_nearby_buildings_red.prj
     ├── SF_nearby_buildings_red.qmd
     ├── SF_nearby_buildings_red.shp
     └── SF_nearby_buildings_red.shx
   ```

### City Boundary

If you want to use the city boundary data, you will need to add it into the config file and put it into `data/raw/city` folder. For example, for St. Louis, in its `MO_SL.yaml` config file, the following is added:
   ```yaml
   study_area:
     city_boundary_filename: "stl_boundary.shp"
   ```
The file for St. Louis is:
   ```bash
   data/raw/city
     ├── stl_boundary.cpg
     ├── stl_boundary.dbf
     ├── stl_boundary.prj
     ├── stl_boundary.shp
     └── stl_boundary.shx
   ```

### Work Commute Data (LODES)

The script `scripts/create_synthetic_population.py` will download the LODES data `{state_name}_od_aux_JT00_2010.csv.gz` and `{state_name}_od_main_JT00_2010.csv.gz` from https://lehd.ces.census.gov/data/lodes/LODES7. The data will be saved into `data/raw/work_commute` folder. For example, for California (CA), the data will be saved into:
   ```
   data/raw/work_commute
     ├── ca_od_aux_JT00_2010.csv.gz
     └── ca_od_main_JT00_2010.csv.gz
   ```
The script `scripts/create_synthetic_population.py` with then prepare LODES data and save it as `data/processed/work_commute/{STATE_NAME}_{CITY_NAME}_tract_od.csv`. For example, for the city of San Francisco (SF) in state California (CA), the data will be saved as:
   ```
   data/processed/work_commute
     └── CA_SF_tract_od.csv
   ```

### Workplace

Download and unzip `CB2000CBP.zip` from https://www2.census.gov/programs-surveys/cbp/data/2020/ to `data/raw/workplace`. The file should look like:
   ```bash
   data/raw/workplace
     └── CB2000CBP.dat
   ```

### Education

Download and unzip `ORNL_Education.zip` from [this link](https://edg.epa.gov/metadata/catalog/search/resource/details.page?uuid=%7B9C49AE4B-F175-43D0-BCC6-A928FF54C329%7D), and save it into `data/raw`. The file should look like:
   ```bash
   data/raw/ORNL_Education
     └── Education.gdb/
   ```

The script `scripts/create_synthetic_population.py` will extract layers and save them into individual csv files to the same folder:
   ```bash
   data/raw/ORNL_Education
     ├── CollegesUniversities.csv
     ├── DayCareCenters.csv
     ├── PrivateSchools.csv
     ├── PublicSchools.csv
     ├── SupplementalColleges.csv
     └── Education.gdb/
   ```
 The script `script/create_synthetic_population.py` will then prepare the education data (daycare centers, public & private schools) and save them into `data/processed/education`. For example, for the city of San Francisco (SF) in state California (CA), the prepared data will be saved as:
   ```
   data/processed/education
     ├── CA_SF_dc_gdf.shp.zip
     └── CA_SF_school_gdf.shp.zip
   ```