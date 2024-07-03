import geopandas as gpd
import pandas as pd
import numpy as np
from shapely import MultiLineString, Point, ops, LineString

def __hash_geom__(g):
    '''
    Hash geometric, create space, shapely geometries are not hashable, here is my hash function to check the duplicates
    :param g:
    :return: coordinates (latitude, longitude)
    '''
    #print("Get the lat and long of the road segment and output to tuple")
    if g.geom_type == 'MultiLineString':
        #print("MultiLineString")
        #print(g.geoms)
        cord_list = []
        for line in g.geoms:
            for lat,lon in line.coords[:]:
                #print((round(lat,6),round(lon,6)))
                cord_list.append((round(lat,6),round(lon,6)))
        #print(cord_list)
        cord_tuple = tuple(item for item in cord_list)
        #print("Tuple")
        #print(cord_tuple)
        return tuple(item for item in cord_list)
    else:
        #print("Line")
        #print(tuple((round(lat,6),round(lon,6)) for lat,lon in g.coords[:]))
        return tuple((round(lat,6),round(lon,6)) for lat,lon in g.coords[:]) #shaply older version
        #return tuple((round(lat,6),round(lon,6)) for lat,lon in g.geoms) #shapely 2.0 or later version


def __create_home_location__(tract, household_count, road):
    '''
    creat home loaction
    :param tract: row of census tract
    :param hcnt: hhold count
    :param road:
    :return:
    '''


    # Find roads intersecting with census tract geometry
    #print("- Step 1.3 Creating home_location-")
    mask = road.intersects(tract.geometry)
    home_mask = mask & road['MTFCC'].str.contains(
        'S1400|S1740')  # * Home Road: S1400 Local Neighborhood Road, Rural Road, City Street, S1740 Private Road for service vehicles (logging, oil fields, ranches, etc.)
    home_roads = road[home_mask].intersection(tract.geometry)
    home_roads = home_roads[home_roads.geom_type.isin(['LineString', 'MultiLineString'])]
    home_roads = home_roads[~home_roads.apply(
        __hash_geom__).duplicated()]  # remove the duplicate lat and long by returning boolean Series denoting duplicate rows (using .duplicated()).

    # Interpolate points along home roads
    interpolation_density = 0.0005
    interpolated_points = home_roads.apply(lambda x: pd.Series([x.interpolate(seg)
                                                                for seg in np.arange(interpolation_density, x.length,
                                                                                     interpolation_density)]))

    # Flatten the interpolated points
    flattened_points = interpolated_points.unstack().dropna().reset_index(drop=True)

    # Sample home locations
    sampled_homes = flattened_points.sample(n=household_count, replace=True).reset_index(drop=True)
    sampled_homes.index = tract.name + 'h' + sampled_homes.index.to_series().astype(str)

    return gpd.GeoSeries(sampled_homes)


def __create_work_location__(tract, road):
    '''
    Creates work place on a primary road, secondary road and intersection of home road.

    :param tract: GeoDataFrame containing census tract data.
    :param road: GeoDataFrame containing road data.
    :return: GeoSeries representing work locations.
    '''

    # from shapely import MultiLineString, Point, ops, LineString
    # primary road, secondary road
    #print("- Step 2.2 Creating Work location on Road Networks-")
    mask = road.intersects(tract.geometry)  # get the road with in the census tract
    work_mask = mask & road.MTFCC.str.contains('S1200')  # * Work Road: S1100 Primary Road; S1200 Secondary Road

    work_road = road[work_mask].intersection(tract.geometry)  # get the geometry of work road
    work_road = work_road[work_road.geom_type.isin(['LinearRing', 'LineString', 'MultiLineString'])]
    work_road = work_road[~work_road.apply(
        __hash_geom__).duplicated()]  # remove the duplicate lat and long by returning boolean Series denoting duplicate rows (using .duplicated()).

    interpolation_density = 0.0002
    interpolated_points = work_road.apply(lambda x: pd.Series(
        [x.interpolate(seg) for seg in np.arange(interpolation_density, x.length, interpolation_density)]))  # Get the

    # home road interections
    home_mask = mask & road['MTFCC'].str.contains(
        'S1400|S1740')  # * Home Road: S1400 Local Neighborhood Road, Rural Road, City Street, S1740 Private Road for service vehicles (logging, oil fields, ranches, etc.)
    home_roads = road[home_mask].intersection(tract.geometry)
    home_roads = home_roads[home_roads.geom_type.isin(['LineString', 'MultiLineString'])]
    home_roads = home_roads[~home_roads.apply(__hash_geom__).duplicated()]

    intersection_points = home_roads.apply(
        lambda x: Point(x.coords[0]) if type(x) != MultiLineString else Point(x.geoms[0].coords[0]))

    work_place = pd.DataFrame()
    # print(wrk_point)
    if len(interpolated_points) > 0:
        flattened_points = interpolated_points.unstack().dropna().reset_index(drop=True)
        # temp = wrk_point.unstack().dropna().reset_index(drop=True)
        work_place = pd.concat([flattened_points, intersection_points])

    else:
        work_place = intersection_points

    work_place = work_place.sample(n=tract.WP_CNT, replace=True).reset_index(drop=True)
    work_place.index = tract.name + 'w' + work_place.index.to_series().astype(str)
    # print("workplace")
    # print(wrk_place)'

    return gpd.GeoSeries(work_place)