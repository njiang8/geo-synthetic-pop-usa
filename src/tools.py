import pandas as pd
import numpy as np
import geopandas as gpd
import random
from loguru import logger
from shapely import Point
from math import sin, cos, sqrt, atan2, radians
from sklearn.preprocessing import normalize

#==================
# 1 Preprocessing
#==================
def number_of_wp_old(data, od, cbp):
    """
    calculate number of workplaces for each tract
    wp_tract = wp_cty * (tract_employed / county_employed)
    """
    try:
        tract_number = data.GEOID10#.astype(int)
        county_number = tract_number[:5]
        #print("the tract number is:", tract_number)
        #print("+++++++")
        #print("the county number is:", county_number)
        #employed
        #tract employed
        tract_employed_df = od[['work','S000']].groupby('work').sum().reset_index()
        tract_employed_df = tract_employed_df.astype({"work": str})

        #print(tract_employed_df.head())
        #print(tract_employed_df.work.unique())

        tract_employed = tract_employed_df.loc[tract_employed_df.work == tract_number, 'S000'].values[0]

        #print(tract_employed)
        #county employed
        tract_employed_df['county'] = tract_employed_df.work.astype(str).str[:5]
        #print(tract_employed_df.head())
        county_employed_df = tract_employed_df[['county','S000']].groupby('county').sum().reset_index()
        #print(county_employed_df.head())

        #county wrk place establishment number
        cbp['county'] = cbp.GEO_ID.astype(str).str[-5:]
        cbp = cbp[cbp.county == county_number].copy()#.groupby('county').sum().reset_index()
        cbp = cbp.astype({"ESTAB": int})
        #print(cbp)
        county_wrk_count = cbp.groupby('county').sum().reset_index()
        county_df = county_employed_df.merge(county_wrk_count, on="county", how="inner")
        #print(county_df)

        wp_cty = county_df.loc[county_df.county == county_number, 'ESTAB'].values[0]
        county_employed = county_df.loc[county_df.county == county_number, 'S000'].values[0]
        #print (wp_cty)
        #print(county_employed)

        return int(wp_cty * (tract_employed / county_employed))
    except:
        return 0



def number_of_wp(data, od, cbp):
    """
    calculate number of workplaces for each tract
    wp_tract = wp_cty * (tract_employed / county_employed)
    """
    try:
        """
        calculate number of workplaces for each tract
        wp_tract = wp_cty * (tract_employed / county_employed) #commute peaple amout
        """

        #print("++++++++++")
        # use "od data" to get number of jobs in each census tract
        # and number of jobs in each county
        tract_number = data.GEOID#.astype(int)
        tract_jobs_df = od[['work','S000']].groupby('work').sum().reset_index()
        tract_jobs_df = tract_jobs_df.astype({"work": str})
        tract_jobs_number = int(tract_jobs_df.loc[tract_jobs_df.work == tract_number, 'S000'].values[0]) # total number of job in each tract
        #print("Tract", tract_number, "has", tract_jobs_number, "jobs")

        #county total number of job
        county_number = tract_number[:5]
        tract_jobs_df['county'] = tract_jobs_df.work.astype(str).str[:5]
        county_job_df = tract_jobs_df[['county','S000']].groupby('county').sum().reset_index()
        county_job_number = int(county_job_df.S000[0])
        #print("County", county_number, "has", county_job_number, "jobs")
        #print("++++++++++")

        #use company number
        #county wrk place establishment number
        #cbp['county'] = cbp.GEO_ID.astype(str).str[-5:]
        #print("==========")
        campany_df = cbp.loc[:,['county', 'NAME', 'ESTAB']]
        county_campany_number = int(campany_df[campany_df.county == county_number].ESTAB.values[0])
        #print("County", county_number, "has", county_campany_number, "company")

        tract_wp_number = int(county_campany_number * (tract_jobs_number / county_job_number))

        #print("Tract",  tract_number, "has", tract_wp_number, "companys")
        return tract_wp_number
    except:
        print(tract_number, "has issue")
        return 0


def wp_proba(x):
    """
    probability of an employee working in that workplace is lognormal:
    http://www.haas.berkeley.edu/faculty/pdf/wallace_dynamics.pdf
    """
    if x == 0: return np.zeros(0)
    b = np.random.lognormal(mean=2,size=x).reshape(-1, 1)
    return np.sort(normalize(b,norm='l1',axis=0).ravel())



#==================
# 2 Verification
#==================

def get_errors(tract,people):
    """Percentage errors"""
    err = {}
    #portion = tract.geometry.area / tract.Shape_Area # what portion of the tract is included
    #senior_actual = int(tract.DP0150001 * portion) # Households with individuals 65 years and over
    senior_actual = int(tract.DP0150001)
    #minor_actual = int(tract.DP0140001 * portion) # Households with individuals under 18 years
    minor_actual = int(tract.DP0140001)
    #err['tract'] = tract.name
    err['population'] = tract.DP0010001
    err['in_gq'] = tract.DP0120014
    avg_synthetic_family = people[people.htype<6].groupby('hhold').size().mean()
    err['avg_family'] = 100*(avg_synthetic_family - tract.DP0170001) / tract.DP0170001
    err['avg_hh'] = 100*(people[people.htype!=11].groupby('hhold').size().mean() - tract.DP0160001) / tract.DP0160001
    err['senior_hh'] = 100*(people[people.age>=65].hhold.nunique() - senior_actual) / senior_actual
    err['minor_hh'] = 100*(people[people.age<18].hhold.nunique() - minor_actual) / minor_actual
    return pd.Series(err,name=tract.name)


## 3 Verification Function census vs ours (i.e., data from census - genreated)
def __verfication__(tract, people):
    """[ 'DP1_0025C', 'DP1_0026C',	'DP1_0027C',	'DP1_0028C',	'DP1_0029C',	'DP1_0030C',	'DP1_0031C',	'DP1_0032C',	'DP1_0033C',	'DP1_0034C',	'DP1_0035C',	'DP1_0036C',	'DP1_0037C',	'DP1_0038C',	'DP1_0039C',	'DP1_0040C',	'DP1_0041C',	'DP1_0042C',	'DP1_0043C',	'DP1_0049C', 'DP1_0050C',	'DP1_0051C',	'DP1_0052C',	'DP1_0053C',	'DP1_0054C',	'DP1_0055C',	'DP1_0056C',	'DP1_0057C',	'DP1_0058C',	'DP1_0059C',	'DP1_0060C',	'DP1_0061C',	'DP1_0062C',	'DP1_0063C',	'DP1_0064C',	'DP1_0065C',	'DP1_0066C',	'DP1_0067C']"""
    ver_df = {}
    # 3.1 population uder each age group
    # total_pop_tract = tract.tract.DP1_0001C
    # total_pop_genertate = len(people)
    ver_df['pop_diff'] = tract.DP1_0001C - len(people)
    # age 0 to 19
    # ver_row['kids_diff'] = tract.D
    # age 20 to 64
    ver_df['male_adults_diff'] = tract.DP1_0025C - len(people[people.gender == 'm'])
    ver_df['female_adults_diff'] = tract.DP1_0049C - len(people[people.gender == 'f'])

    ver_df['m_diff_0_4'] = tract.DP1_0026C - len(people[(people.gender == 'm') & (people.age >= 0) & (people.age <= 4)])
    ver_df['m_diff_5_9'] = tract.DP1_0027C - len(people[(people.gender == 'm') & (people.age >= 5) & (people.age <= 9)])
    ver_df['m_diff_10_14'] = tract.DP1_0028C - len(
        people[(people.gender == 'm') & (people.age >= 10) & (people.age <= 14)])
    ver_df['m_diff_15_19'] = tract.DP1_0029C - len(
        people[(people.gender == 'm') & (people.age >= 15) & (people.age <= 19)])
    ver_df['m_diff_20_24'] = tract.DP1_0030C - len(
        people[(people.gender == 'm') & (people.age >= 20) & (people.age <= 24)])
    ver_df['m_diff_25_29'] = tract.DP1_0031C - len(
        people[(people.gender == 'm') & (people.age >= 25) & (people.age <= 29)])
    ver_df['m_diff_30_34'] = tract.DP1_0032C - len(
        people[(people.gender == 'm') & (people.age >= 30) & (people.age <= 34)])
    ver_df['m_diff_35_39'] = tract.DP1_0033C - len(
        people[(people.gender == 'm') & (people.age >= 35) & (people.age <= 39)])
    ver_df['m_diff_40_44'] = tract.DP1_0034C - len(
        people[(people.gender == 'm') & (people.age >= 40) & (people.age <= 44)])
    ver_df['m_diff_45_49'] = tract.DP1_0035C - len(
        people[(people.gender == 'm') & (people.age >= 45) & (people.age <= 49)])
    ver_df['m_diff_50_54'] = tract.DP1_0036C - len(
        people[(people.gender == 'm') & (people.age >= 50) & (people.age <= 54)])
    ver_df['m_diff_55_59'] = tract.DP1_0037C - len(
        people[(people.gender == 'm') & (people.age >= 55) & (people.age <= 59)])
    ver_df['m_diff_60_64'] = tract.DP1_0038C - len(
        people[(people.gender == 'm') & (people.age >= 60) & (people.age <= 64)])
    ver_df['m_diff_65_69'] = tract.DP1_0039C - len(
        people[(people.gender == 'm') & (people.age >= 65) & (people.age <= 69)])
    ver_df['m_diff_70_74'] = tract.DP1_0040C - len(
        people[(people.gender == 'm') & (people.age >= 70) & (people.age <= 74)])
    ver_df['m_diff_75_79'] = tract.DP1_0041C - len(
        people[(people.gender == 'm') & (people.age >= 75) & (people.age <= 79)])
    ver_df['m_diff_80_84'] = tract.DP1_0042C - len(
        people[(people.gender == 'm') & (people.age >= 80) & (people.age <= 84)])
    ver_df['m_diff_85'] = tract.DP1_0043C - len(people[(people.gender == 'm') & (people.age >= 85)])

    ver_df['f_diff_0_4'] = tract.DP1_0050C - len(people[(people.gender == 'f') & (people.age >= 0) & (people.age <= 4)])
    ver_df['f_diff_5_9'] = tract.DP1_0051C - len(people[(people.gender == 'f') & (people.age >= 5) & (people.age <= 9)])
    ver_df['f_diff_10_14'] = tract.DP1_0052C - len(
        people[(people.gender == 'f') & (people.age >= 10) & (people.age <= 14)])
    ver_df['f_diff_15_19'] = tract.DP1_0053C - len(
        people[(people.gender == 'f') & (people.age >= 15) & (people.age <= 19)])
    ver_df['f_diff_20_24'] = tract.DP1_0054C - len(
        people[(people.gender == 'f') & (people.age >= 20) & (people.age <= 24)])
    ver_df['f_diff_25_29'] = tract.DP1_0055C - len(
        people[(people.gender == 'f') & (people.age >= 25) & (people.age <= 29)])
    ver_df['f_diff_30_34'] = tract.DP1_0056C - len(
        people[(people.gender == 'f') & (people.age >= 30) & (people.age <= 34)])
    ver_df['f_diff_35_39'] = tract.DP1_0057C - len(
        people[(people.gender == 'f') & (people.age >= 35) & (people.age <= 39)])
    ver_df['f_diff_40_44'] = tract.DP1_0058C - len(
        people[(people.gender == 'f') & (people.age >= 40) & (people.age <= 44)])
    ver_df['f_diff_45_49'] = tract.DP1_0059C - len(
        people[(people.gender == 'f') & (people.age >= 45) & (people.age <= 49)])
    ver_df['f_diff_50_54'] = tract.DP1_0060C - len(
        people[(people.gender == 'f') & (people.age >= 50) & (people.age <= 54)])
    ver_df['f_diff_55_59'] = tract.DP1_0061C - len(
        people[(people.gender == 'f') & (people.age >= 55) & (people.age <= 59)])
    ver_df['f_diff_60_64'] = tract.DP1_0062C - len(
        people[(people.gender == 'f') & (people.age >= 60) & (people.age <= 64)])
    ver_df['f_diff_65_69'] = tract.DP1_0063C - len(
        people[(people.gender == 'f') & (people.age >= 65) & (people.age <= 69)])
    ver_df['f_diff_70_74'] = tract.DP1_0064C - len(
        people[(people.gender == 'f') & (people.age >= 70) & (people.age <= 74)])
    ver_df['f_diff_75_79'] = tract.DP1_0065C - len(
        people[(people.gender == 'f') & (people.age >= 75) & (people.age <= 79)])
    ver_df['f_diff_80_84'] = tract.DP1_0066C - len(
        people[(people.gender == 'f') & (people.age >= 80) & (people.age <= 84)])
    ver_df['f_diff_85'] = tract.DP1_0067C - len(people[(people.gender == 'f') & (people.age >= 85)])

    hhold_df = people.drop_duplicates(subset=['hhold'], keep='first')

    if tract.DP1_0132C == 0:
        ver_df['htye0'] = 0
        # print(hhold_type_amount[0] * 2)
        # hhold_type_amount[0] = 1
        # print(hhold_type_amount[0])
        # 1 marrie with kids: DP1_0134C
        ver_df['htye1'] = 0
        # print(hhold_type_amount[1] * 4)

        # print(hhold_type_amount[1])
        # 2 cocahbiting          : DP1_0135C - DP1_0136C
        ver_df['htye2'] = 0
        # print(hhold_type_amount[2])
        # 3 cocahbiting with Kids: DP1_0136C
        ver_df['htye3'] = 0

        # 4 male live alone        :DP1_0138C - DP1_0139C
        ver_df['htye4'] = 0
        # 5 male senior live alone :DP1_0139C
        ver_df['htye5'] = 0

        # 6 male with kids         :DP1_0140C
        ver_df['htye6'] = 0

        # 7  female live alone        :DP1_0142C - DP1_0143C
        ver_df['htye7'] = 0
        # print("---in ver fuc type 7 from census", (tract.DP1_0142C - tract.DP1_0143C))
        # print("---in ver fuc type 7 from pop", len(hhold_df[(hhold_df.htype == 7)]))

        # 8  female senior live alone :DP1_0143C
        ver_df['htye8'] = 0
        # print("---in ver fuc type 8 from census", tract.DP1_0143C)
        # print("---in ver fuc type 8 from pop", len(hhold_df[(hhold_df.htype == 8)]))

        # 9  female with kids         :DP1_0144C
        ver_df['htye9'] = 0

        # 10 non-family group         : (DP1_0137C - DP1_0138C - DP1_0140C) + (DP1_0141C - DP1_0142C - DP1_0144C)
        ver_df['htye10'] = 0

        # only group quarter
        ver_df['htye11'] = len(hhold_df[(hhold_df.htype == 11)])

        # ver_df['diff_hhold_size'] = (tract.DP1_0001C / tract.DP1_0132C) -

    else:
        # print("--In Ver Fuc H type", hhold_df.htype.unique())
        ver_df['htye0'] = (tract.DP1_0133C - tract.DP1_0134C) - len(hhold_df[(hhold_df.htype == 0)])
        # print(hhold_type_amount[0] * 2)
        # hhold_type_amount[0] = 1
        # print(hhold_type_amount[0])
        # 1 marrie with kids: DP1_0134C
        ver_df['htye1'] = tract.DP1_0134C - len(hhold_df[(hhold_df.htype == 1)])
        # print(hhold_type_amount[1] * 4)

        # print(hhold_type_amount[1])
        # 2 cocahbiting          : DP1_0135C - DP1_0136C
        ver_df['htye2'] = (tract.DP1_0135C - tract.DP1_0136C) - len(hhold_df[(hhold_df.htype == 2)])
        # print(hhold_type_amount[2])
        # 3 cocahbiting with Kids: DP1_0136C
        ver_df['htye3'] = tract.DP1_0136C - len(hhold_df[(hhold_df.htype == 3)])

        # 4 male live alone        :DP1_0138C - DP1_0139C
        ver_df['htye4'] = (tract.DP1_0138C - tract.DP1_0139C) - len(hhold_df[(hhold_df.htype == 4)])
        # 5 male senior live alone :DP1_0139C
        ver_df['htye5'] = tract.DP1_0139C - len(hhold_df[(hhold_df.htype == 5)])

        # 6 male with kids         :DP1_0140C
        ver_df['htye6'] = tract.DP1_0140C - len(hhold_df[(hhold_df.htype == 6)])

        # 7  female live alone        :DP1_0142C - DP1_0143C
        ver_df['htye7'] = (tract.DP1_0142C - tract.DP1_0143C) - len(hhold_df[(hhold_df.htype == 7)])
        # print("---in ver fuc type 7 from census", (tract.DP1_0142C - tract.DP1_0143C))
        # print("---in ver fuc type 7 from pop", len(hhold_df[(hhold_df.htype == 7)]))

        # 8  female senior live alone :DP1_0143C
        ver_df['htye8'] = tract.DP1_0143C - len(hhold_df[(hhold_df.htype == 8)])
        # print("---in ver fuc type 8 from census", tract.DP1_0143C)
        # print("---in ver fuc type 8 from pop", len(hhold_df[(hhold_df.htype == 8)]))

        # 9  female with kids         :DP1_0144C
        ver_df['htye9'] = tract.DP1_0144C - len(hhold_df[(hhold_df.htype == 9)])

        # 10 non-family group         : (DP1_0137C - DP1_0138C - DP1_0140C) + (DP1_0141C - DP1_0142C - DP1_0144C)
        ver_df['htye10'] = ((tract.DP1_0137C - tract.DP1_0138C - tract.DP1_0140C) + (
                    tract.DP1_0141C - tract.DP1_0142C - tract.DP1_0144C)) - len(hhold_df[(hhold_df.htype == 10)])

        ver_df['htye11'] = len(hhold_df[(hhold_df.htype == 11)])

    # ver_df['hh_pop'] = (tract.DP1_0133C - tract.DP1_0134C) * 2 - len(people[(people.htype == 0)])
    # print(len(people[(people.htype == 0)]))

    # 3.2 AVG hhold size
    return pd.Series(ver_df, name=tract.name)

#==================
# 3 After Analysis
#==================
def __collect_results__(results, X):
    # Check if the operation is for Population data
    if X == "Pop":
        # print("Population")
        logger.info("--Collecting Population")
        temp_df = pd.DataFrame()
        # Concatenate all DataFrame results into a single DataFrame
        for i in results:
            temp_df = pd.concat([temp_df, i])

        # Reset index for the combined DataFrame and drop the 'code' column
        temp_df = temp_df.reset_index().drop(['code'], axis=1)
        # Rename the first column to 'id'
        temp_df.rename(columns={temp_df.columns[0]: 'id'}, inplace=True)
        # Convert the DataFrame to a GeoDataFrame, specifying the 'geometry' column
        pop_gdf = gpd.GeoDataFrame(temp_df, geometry='geometry')
        # Set the CRS to EPSG:4269
        pop_gdf = pop_gdf.set_crs('EPSG:4269', allow_override=True)

        # Extract longitude and latitude from the 'geometry' column
        pop_gdf['long'] = pop_gdf['geometry'].x
        pop_gdf['lat'] = pop_gdf['geometry'].y
        # print("=====Final Population Data=====")
        # print(pop_gdf.head())
        # Return the GeoDataFrame with Population data
        return pop_gdf

    # Check if the operation is for Work data
    elif X == "Work":
        # print("Work")
        logger.info("--Collecting Workplaces")
        wp = pd.DataFrame()
        # Concatenate all DataFrame results into a single DataFrame
        for j in results:
            wp = pd.concat([wp, j])
        # Reset index for the combined DataFrame
        wp = wp.reset_index()
        # Rename the first two columns to 'wp' and 'geometry'
        wp.rename(columns={wp.columns[0]: 'wp', wp.columns[1]: 'geometry'}, inplace=True)

        wp_gdf = gpd.GeoDataFrame(wp, geometry='geometry')
        # Set the CRS to EPSG:4269
        wp_gdf = wp_gdf.set_crs('EPSG:4269', allow_override=True)
        #wp_gdf.set_crs('EPSG:4269', inplace=True)
        # Extract longitude and latitude from the 'geometry' column
        wp_gdf['long'] = wp_gdf['geometry'].x
        wp_gdf['lat'] = wp_gdf['geometry'].y

        # print("=====Work Data=====")
        # print(wp_gdf.head())
        # Return the DataFrame with Work data
        return wp_gdf

    # Handle other types of data for verification
    elif X == "Verification":
        # print("Collection Verification DF")
        logger.info("--Collecting Verification")
        ver_df = pd.DataFrame()
        # Concatenate and transpose each result, then combine into a single DataFrame
        for i in results:
            ver_df = pd.concat([ver_df, i.transpose()], axis=1)
        # Return the transposed and combined DataFrame
        return ver_df.T

    else:
        logger.info("--Collecting Tract with error")
        if len(results) != 0:
            err_df = pd.DataFrame()
            for _ in results:
                err_df = pd.concat([err_df, pd.DataFrame(_).transpose()])
            # print(err_df)
            err_df = err_df.reset_index(drop=True)
            # err_df = pd.DataFrame(err_df, columns=['Tract_Name', 'Error_Message'])
            err_df.rename(columns={err_df.columns[0]: 'tract', err_df.columns[1]: 'error_message'}, inplace=True)
            # print(err_df)
            return err_df
        else:
            logger.info("--No Error Tract")


from shapely import Point
def pop_to_geo_df(data):
    #lat long, lat:40.xxxx, long: -78.xxxx
    #data['geometry'] = data.apply(lambda x: Point((float(x.lat), float(x.long))), axis=1)#combine lat and lon column to a shapely Point() object
    data['geometry'] = data.apply(lambda x: Point((float(x.long), float(x.lat))),
                                  axis=1)  # combine lat and lon column to a shapely Point() object
    gdf = gpd.GeoDataFrame(data, geometry='geometry')
    #WGS84 Coordinate System
    #gdf.crs = {'init' :'epsg:4326'}
    gdf = gdf.set_crs("EPSG:4326")
    return gdf


# From Geo Panda DataFram, change the data to spatial data
def edu_to_gpd(data):
    from shapely.geometry import Point
    # combine lat and lon column to a shapely Point() object
    data['geometry'] = data.apply(lambda x: Point((float(x.LONGITUDE), float(x.LATITUDE))), axis=1)
    data = gpd.GeoDataFrame(data, geometry='geometry')
    # WGS84 Coordinate System
    data.crs = {'init': 'epsg:4326'}

    return data


# Other functions
def new_distance(x1, y1, x2, y2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(x1)
    long1 = radians(y1)
    lat2 = radians(x2)
    long2 = radians(y2)

    dlon = long2 - long1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

# Random int generator based on normal distribution
def GenBoundedRandomNormal(meanVal, stdDev, lowerBound, upperBound):
    aRand = random.gauss(meanVal, stdDev)  # could also use: normalvariate()but gauss () is slightly faster.

    while (aRand < lowerBound or aRand > upperBound):
        aRand = random.gauss(meanVal, stdDev)
    return aRand

def check_urban(data, boundary):
    '''
    Check if the population's location is in the urban area.
    :param data: individual GeoDataFrame representing population locations.
    :param boundary: GeoDataFrame representing urban area boundary.
    :return: True if in the urban area, else False.
    '''
    return True in data.geometry.intersects(boundary.geometry).unique()



