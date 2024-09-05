import geopandas as gpd

from shapely import Point

def pop_to_geo_df(data, coord_name):
    #lat long, lat:40.xxxx, long: -78.xxxx
    #data['geometry'] = data.apply(lambda x: Point((float(x.lat), float(x.long))), axis=1)#combine lat and lon column to a shapely Point() object
    data['geometry'] = data.apply(lambda x: Point((float(x.long), float(x.lat))),
                                  axis=1)  # combine lat and lon column to a shapely Point() object
    gdf = gpd.GeoDataFrame(data, geometry='geometry')
    #WGS84 Coordinate System
    #gdf.crs = {'init' :'epsg:4326'}
    gdf = gdf.to_crs(coord_name)
    return gdf


def prepare_bg_spop_gdf(bg_gdf, s_pop_gdf):
    joined_bg_gdf = gpd.sjoin(bg_gdf, s_pop_gdf, how="inner", predicate='intersects')
    joined_bg_gdf['count'] = 1

    bg_spop = joined_bg_gdf.groupby('GEOID20')['count'].sum()  # .head()
    bg_gdf_two_pop = bg_gdf.merge(bg_spop, on='GEOID20', how='left')

    return bg_gdf_two_pop.loc[:, ['GEOID20', 'tract', 'urban', 'B01001e1', 'count']].dropna()