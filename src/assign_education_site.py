from src.tools import new_distance
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import MultiLineString
from shapely.geometry import Polygon
from shapely import Point
import random

def __assign_education_site__(tract, people, school, daycare):
    '''
    All kis go to school and daycare
    :param tract:
    :param people:
    :param school:
    :param daycare:
    :return:
    '''

    #print('- Step 2.3 Assign Education Sites -')
    # Assign School
    school_kids_index = people[(people['age'] >= 5) & (people['age'] <= 17)].index
    for idx in school_kids_index:
        people.at[idx, "wp"] = __assign_eduID__(idx, tract, people, school)

    # Assign Daycare
    daycare_kids_index = people[(people['age'] <= 4)].index
    for idx in daycare_kids_index:
        people.at[idx, "wp"] = __assign_eduID__(idx, tract, people, daycare)  # .at is used to assign single value


def __assign_eduID__(data, tract, people, edu_df):
    '''

    :param data: kids info
    :param tract: row of census tract
    :param people: people generated in previous steps with geo-location info, this is used to get the kids info
    :param edu_df: daycare or school df
    :return: daycare or school id
    '''

    # print('====in __assign_shcools__====')
    edu_df = edu_df.set_index('eduID')
    # print(edu_df.head())
    # print(tract.name)

    '''
    show polygon and its buffer
    x1, y1 = tract.geometry.exterior.xy
    plt.plot(x1,y1)
    x, y = buff.exterior.xy
    # Plot the polygon
    plt.plot(x, y)
    '''

    buff = tract.geometry.buffer(0.1)  # 0.1 degrees * 111,320 meters/degree ≈ 1113.2 meters
    geo_loc = people.loc[data, 'geometry']
    kid_x = geo_loc.y
    kid_y = geo_loc.x

    if people.loc[data, 'age'] <= 4:# daycare id
        # print('dc')
        # return 'dc'
        edu_site_in_buffer = edu_df[edu_df.intersects(buff)]
        if len(edu_site_in_buffer) > 0:
            return __find_edu_ID__(kid_x, kid_y, edu_site_in_buffer, edu_df)
        else:
            # print("No education found with in 1113.2m, try 2226.4m")
            buff = tract.geometry.buffer(0.9)  # 0.1 degrees * 111,320 meters/degree ≈ 1113.2 meters
            # edu_in_age = edu_df[(edu_df['s_age'] <= people.loc[data, 'age']) & (edu_df['e_age'] >= people.loc[data, 'age'])]
            edu_site_in_buffer = edu_df[edu_df.intersects(buff)]
            # print("School count in buffer", len(edu_site_in_buffer))

            return __find_edu_ID__(kid_x, kid_y, edu_site_in_buffer, edu_df)

    else:# school Id
        edu_in_age = edu_df[(edu_df['s_age'] <= people.loc[data, 'age']) & (edu_df['e_age'] >= people.loc[data, 'age'])]
        edu_site_in_buffer = edu_in_age[edu_in_age.intersects(buff)]  # .copy()
        # print("School count in buffer", len(edu_site_in_buffer))
        # print("people lat long", people_x,", ", people_y)

        if len(edu_site_in_buffer) > 0:
            return __find_edu_ID__(kid_x, kid_y, edu_site_in_buffer, edu_df)
        else:
            # print("No education found with in 1113.2m, try 2226.4m")
            buff = tract.geometry.buffer(0.9)  # 0.1 degrees * 111,320 meters/degree ≈ 1113.2 meters
            edu_in_age = edu_df[
                (edu_df['s_age'] <= people.loc[data, 'age']) & (edu_df['e_age'] >= people.loc[data, 'age'])]
            edu_site_in_buffer = edu_in_age[edu_in_age.intersects(buff)]  # .copy()
            # print("School count in buffer", len(edu_site_in_buffer))

            return __find_edu_ID__(kid_x, kid_y, edu_site_in_buffer, edu_df)


def __find_edu_ID__(kx, ky, edu_site_in_buffer, edu_df):
    sx = edu_site_in_buffer.loc[:, 'LATITUDE'].tolist()
    sy = edu_site_in_buffer.loc[:, 'LONGITUDE'].tolist()

    dist = []  # distance list
    for j in range(len(edu_site_in_buffer)):
        d = new_distance(kx, ky, sx[j], sy[j])
        dist.append(d)

    edu_id = edu_site_in_buffer.index
    df_edu_in = pd.DataFrame({'eduID': edu_id, 'Dist': dist}).sort_values(by='Dist')

    sch_AgeDistAccept = [s for s in df_edu_in.eduID if edu_df.loc[s, 'count'] < edu_df.loc[s, 'ENROLLMENT']]

    if sch_AgeDistAccept:
        return sch_AgeDistAccept[0]
    else:
        return random.choice(edu_site_in_buffer.index)