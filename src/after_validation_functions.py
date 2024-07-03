import pandas as pd
import geopandas as gpd
import numpy as np
import os

from scipy import stats
import matplotlib.pyplot as plt
from loguru import logger
from sklearn.metrics import mean_absolute_error, mean_squared_error
from math import sqrt


#Load data
def load_census_data(census_path, error_census_path, state_abbreviation):
    '''
    :param census_path:
    :param error_census_path:
    :return: two gdf, all, good
    '''
    if os.path.exists(error_census_path):
        error_census_df = pd.read_csv(error_census_path)
        if 'tract' not in error_census_df.columns:
            error_tract_id = list(error_census_df['Tract_Name']) if not error_census_df.empty else []
        else:
            error_tract_id = list(error_census_df['tract']) if not error_census_df.empty else []
            logger.info(f"Loaded Error Tracts log for {state_abbreviation}")
    else:
        error_tract_id = []
        logger.warning(f"Error log file not found: {error_census_path}")

    if os.path.exists(census_path):
        census_gdf = gpd.read_file(census_path)
        logger.info(f"Loaded census data - Count before removing errors: {len(census_gdf)}")

        good_census_gdf = census_gdf[~census_gdf['GEOID'].isin(error_tract_id)]
        logger.info(f"Count after removing errors: {len(good_census_gdf)}")
        return census_gdf, good_census_gdf
    else:
        logger.warning(f"Census data file not found: {census_path}")


def load_population_data(population_path, state_abbreviation):
    if os.path.exists(population_path):
        logger.info(f"Loading {state_abbreviation} population..")
        population_gdf = gpd.read_file(population_path)

        #logger.info(f"Loaded Population data - Count before removing nans in 'id': {len(population_gdf)}")
        #population_gdf = population_gdf.dropna(subset=['id'])
        logger.info(f"{state_abbreviation} Population Size': {len(population_gdf)}")
        return population_gdf
    else:
        logger.warning(f"Population data file not found: {population_path}")

def load_workplace_data(workplace_path, state_abbreviation):
    if os.path.exists(workplace_path):
        logger.info(f"Loading {state_abbreviation} workplaces..")
        workplace_gdf = gpd.read_file(workplace_path)

        logger.info(f"Loaded workplace data - Count before removing nans in 'id': {len(workplace_gdf)}")
        workplace_gdf = workplace_gdf.dropna(subset=['wp'])
        logger.info(f"Count after removing nans in 'wp': {len(workplace_gdf)}")
        return workplace_gdf
    else:
        logger.warning(f"Population data file not found: {workplace_path}")

def load_clean_population_data(population_path, state_abbreviation):
    if os.path.exists(population_path):
        logger.info(f"Loading {state_abbreviation} population..")
        population_gdf = gpd.read_file(population_path)

        if population_gdf['id'].isna().any() or population_gdf['wp'].isna().any():
            logger.info(f"Loaded Population data - Count before removing nans in 'id': {len(population_gdf)}")
            population_gdf = population_gdf.dropna(subset=['id'])

            nan_count_id = population_gdf['id'].isna().sum()
            logger.info(f'Number of NaN values in the -id- column: {nan_count_id}')

            # population_gdf['wp'].fillna(population_gdf['hhold'], inplace=True)
            population_gdf['wp'] = population_gdf['wp'].fillna(population_gdf['hhold'])
            nan_count_wp = population_gdf['wp'].isna().sum()
            logger.info(f'Number of NaN values in the -wp- column: {nan_count_wp}')
            logger.info(f"Count after removing nans in 'id': {len(population_gdf)} Saving New Population Data")
            # Check if the file exists and delete it to ensure fresh saving without errors
            if os.path.exists(population_path):
                os.remove(population_path)

            population_gdf.to_file(population_path)
            logger.info(f"New population data file Saved to {population_path}")
            return population_gdf
        else:
            logger.info(f"Loaded Population data - No nans in 'id': {len(population_gdf)}")
            return population_gdf
    else:
        logger.warning(f"Population data file not found: {population_path}")

#ver for population
# Get the Age Group Tables
def verifiy_age_group(census, goodCensus, pop):
    # Get each group popualtion from orignal census
    # censusAge = census.iloc[:, 26:63].drop('DP0010039',1).sum()
    # censusAge = census.iloc[:, 29:63].drop('DP0010039',1).sum()
    censusAge = census.iloc[:, 14:51].drop('DP1_0049C', axis=1).sum()
    # print(censusAge.columns())
    censusMaleAgeList = censusAge[:18].tolist()  # male list
    censusFemaleAgeList = censusAge[18:].tolist()  # female list
    #print(censusMaleAgeList, "\n", censusFemaleAgeList)

    # Get each group popualtion from good census tract
    goodCensusAge = goodCensus.iloc[:, 14:51].drop('DP1_0049C', axis=1).sum()
    goodCensusMaleAgeList = goodCensusAge[:18].tolist()  # male list
    goodCensusFemaleAgeList = goodCensusAge[18:].tolist()  # female list"

    #print(goodCensusMaleAgeList, "\n", goodCensusFemaleAgeList)

    # get male and female dataframe

    maleDframe = pop[pop.gender == 'm'].copy()  # male
    femaleDframe = pop[pop.gender == 'f'].copy()  # female

    # s pop: population under each age group
    typeList = []  # name of each type
    mAgeGroupList = []  # male list
    fAgeGroupList = []  # female list

    for lowerLimit in range(0, 85, 5):
        upperLimit = lowerLimit + 4
        # print("Age lower limit is: ",lowerLimit, "; Upper Limits is: ", upperLimit)
        # a = 'AG'+ str(i+1)

        typeAge = 'Age ' + str(lowerLimit) + ' to ' + str(upperLimit)
        # print(typeAge)
        typeList.append(typeAge)

        mAgeGroup = len(maleDframe[(maleDframe.age >= lowerLimit) & (maleDframe.age <= upperLimit)])
        fAgeGroup = len(femaleDframe[(femaleDframe.age >= lowerLimit) & (femaleDframe.age <= upperLimit)])
        # print("Age(",lowerLimit, "to", upperLimit, ") male population is ",mAgeGroup," female population is", fAgeGroup,"\n")

        mAgeGroupList.append(mAgeGroup)  # male add
        fAgeGroupList.append(fAgeGroup)  # female add

    typeList.append("Age85+")
    # male age 85 +
    m85Plus = len(maleDframe[maleDframe.age >= 85])
    mAgeGroupList.append(m85Plus)

    # female age 85 plus
    f85Plus = len(femaleDframe[femaleDframe.age >= 85])
    fAgeGroupList.append(f85Plus)

    # print (typeList)
    # print (mAgeGroupList)
    # print (fAgeGroupList)

    resultsDataFram = pd.DataFrame()
    resultsDataFrame = pd.DataFrame({'Type': typeList, 'SPop_Male': mAgeGroupList, 'SPop_Female': fAgeGroupList,
                                     'Good_Census_Male': goodCensusMaleAgeList,
                                     'Good_Census_Female': goodCensusFemaleAgeList,
                                     'Census_Male': censusMaleAgeList, 'Census_Female': censusFemaleAgeList})

    return resultsDataFrame

# Plot Age Group Tables
def plot_ver_age_df(data, save_path):
    fig, ax = plt.subplots(figsize=(25, 10))

    index = np.arange(len(data['Type']))
    width = 0.13  # Width of the bars

    # Calculating the percentage differences
    #data['Perc_Diff_Male'] = ((data['SPop_Male'] - data['Census_Male']) / data['Census_Male']) * 100
    #data['Perc_Diff_Female'] = ((data['SPop_Female'] - data['Census_Female']) / data['Census_Female']) * 100

    # Plotting Male populations
    ax.bar(index, data['SPop_Male'] / 1000, width, color='#4474C4', label='Synthetic Male Population')
    ax.bar(index + width, data['Good_Census_Male'] / 1000, width, color='#589CD6', label='Good Census Male Population')
    ax.bar(index + 2*width, data['Census_Male'] / 1000, width, color='#6FAE45', label='All Census Male Population')

    # Plotting Female populations
    ax.bar(index + 3.2*width, data['SPop_Female'] / 1000, width, color='#FFC101', label='Synthetic Female Population')
    ax.bar(index + 4.2*width, data['Good_Census_Female'] / 1000, width, color='orange', label='Good Census Female Population')
    ax.bar(index + 5.2*width, data['Census_Female'] / 1000, width, color='#e41a1c', label='All Census Female Population')

    # Setting axis labels
    ax.set_ylabel('Population (K)', fontsize=20, fontname="Arial")
    ax.set_xlabel('Age Group Type', fontsize=20, fontname="Arial")

    # Setting x-axis ticks to be in the middle of the group of bars for each age group
    ax.set_xticks(index + 1.5*width)
    ax.set_xticklabels(data['Type'], fontsize=15, rotation=45)

    # Displaying the legend
    ax.legend(fontsize=15)

    # Save the figure
    plt.savefig(save_path, format='png', dpi=300)  # Adjust format and DPI as needed
    plt.close(fig)


#Veri for hhold
# get the hhold amound from census
def get_hholde_type_amount(census, goodcensus, s_pop):
    census_hhold_amount = get_11_hhold_type_amount(census)
    goodcensus_hhold_amount = get_11_hhold_type_amount(goodcensus)

    hhold_df = s_pop.drop_duplicates(subset=['hhold'], keep='first')
    spop_hhold_amount = []
    for i in range(0, 11):
        spop_hhold_amount.append(len(hhold_df[hhold_df.htype == i]))
        # print(i)
    # print(spop_hhold_amount)
    resultsDataFrame = pd.DataFrame({'Spop_hhold': spop_hhold_amount, 'Census_hhold': census_hhold_amount,
                                     'Goodcensus_hhold': goodcensus_hhold_amount})

    return resultsDataFrame


def get_11_hhold_type_amount(data):
    # Married without kids: DP1_0133C - DP1_0134C
    hhold_type_amount_0 = data.loc[:, 'DP1_0133C'].sum() - data.loc[:, 'DP1_0134C'].sum()

    # Married with kids: DP1_0134C
    hhold_type_amount_1 = data.loc[:, 'DP1_0134C'].sum()

    # Cohabiting without kids: DP1_0135C - DP1_0136C
    hhold_type_amount_2 = data.loc[:, 'DP1_0135C'].sum() - data.loc[:, 'DP1_0136C'].sum()

    # Cohabiting with kids: DP1_0136C
    hhold_type_amount_3 = data.loc[:, 'DP1_0136C'].sum()

    # Male living alone: DP1_0138C - DP1_0139C
    hhold_type_amount_4 = data.loc[:, 'DP1_0138C'].sum() - data.loc[:, 'DP1_0139C'].sum()

    # Male senior living alone: DP1_0139C
    hhold_type_amount_5 = data.loc[:, 'DP1_0139C'].sum()

    # Male with kids: DP1_0140C
    hhold_type_amount_6 = data.loc[:, 'DP1_0140C'].sum()

    # Female living alone: DP1_0142C - DP1_0143C
    hhold_type_amount_7 = data.loc[:, 'DP1_0142C'].sum() - data.loc[:, 'DP1_0143C'].sum()

    # Female senior living alone: DP1_0143C
    hhold_type_amount_8 = data.loc[:, 'DP1_0143C'].sum()

    # Female with kids: DP1_0144C
    hhold_type_amount_9 = data.loc[:, 'DP1_0144C'].sum()

    # Non-family group: (DP1_0137C - DP1_0138C - DP1_0140C) + (DP1_0141C - DP1_0142C - DP1_0144C)
    hhold_type_amount_10 = (data.loc[:, 'DP1_0137C'].sum() - data.loc[:, 'DP1_0138C'].sum() - data.loc[:,
                                                                                              'DP1_0140C'].sum()) + \
                           (data.loc[:, 'DP1_0141C'].sum() - data.loc[:, 'DP1_0142C'].sum() - data.loc[:,
                                                                                              'DP1_0144C'].sum())

    # Return all household type amounts as a list or a dictionary
    return [
        hhold_type_amount_0,
        hhold_type_amount_1,
        hhold_type_amount_2,
        hhold_type_amount_3,
        hhold_type_amount_4,
        hhold_type_amount_5,
        hhold_type_amount_6,
        hhold_type_amount_7,
        hhold_type_amount_8,
        hhold_type_amount_9,
        hhold_type_amount_10
    ]


def plot_hhold_df(data, save_path):
    fig, ax = plt.subplots(figsize=(16, 10))

    index = np.arange(len(data.index))
    width = 0.1  # Width of the bars

    # Plotting hhold
    ax.bar(index, data['Spop_hhold'] / 1000, width, color='green', label='Synthetic Household')
    ax.bar(index + 0.1, data['Goodcensus_hhold'] / 1000, width, color='orange', label='Census Household')
    ax.bar(index + 0.2, data['Census_hhold'] / 1000, width, color='blue', label='Census Household')

    # Setting axis labels
    ax.set_ylabel('Household Amount (K)', fontsize=20, fontname="Arial")
    ax.set_xlabel('Household Type', fontsize=20, fontname="Arial")

    # Setting x-axis ticks to be in the middle of the group of bars for each age group
    ax.set_xticks(index + width)
    # ax.set_xticklabels(data.index, fontsize=15, rotation=45)
    ax.set_xticklabels(data.index, fontsize=15)
    # Displaying the legend
    ax.legend(fontsize=15)

    # Save the figure
    plt.savefig(save_path, format='png', dpi=300)  # Adjust format and DPI as needed
    plt.close(fig)
    #plt.show()


def get_hhold_mae_rmse(data, Predict_column, Ob_column):
    actual_hhold = data[Ob_column]
    predicted_hhold = data[Predict_column]

    # Calculate MAE and RMSE for household
    mae_hhold = mean_absolute_error(actual_hhold, predicted_hhold)
    rmse_hhold = sqrt(mean_squared_error(actual_hhold, predicted_hhold))

    logger.info(f"Household MAE: {mae_hhold}, Household RMSE: {rmse_hhold}")


def get_age_mae_rmse(data, Male_column, Female_column):
    # Extract the relevant columns for comparison
    actual_male = data[Male_column]
    actual_female = data[Female_column]

    predicted_male = data['SPop_Male']
    predicted_female = data['SPop_Female']

    # Calculate MAE and RMSE for male data
    mae_male = mean_absolute_error(actual_male, predicted_male)
    rmse_male = sqrt(mean_squared_error(actual_male, predicted_male))

    # Calculate MAE and RMSE for female data
    mae_female = mean_absolute_error(actual_female, predicted_female)
    rmse_female = sqrt(mean_squared_error(actual_female, predicted_female))

    logger.info(f"MAE Male {mae_male}, RMSE Male {rmse_male}, MAE Feale {mae_female}, RMSE Feale {rmse_female}")


def verifiy_avg_hhold_size(all_census, good_census, s_pop):
    '''
    :param all_census:
    :param good_census:
    :param s_pop: synthidc population
    :return:
    '''
    # get the avg from the spop
    tract_hhold_size = get_spop_avg_hhold_size(s_pop)

    # get avg hhold size from census and good census
    census_hhold_size = get_census_avg_hhold_size(all_census)
    good_census_hhold_size = get_census_avg_hhold_size(good_census)

    # merge three dfs
    merged_df = pd.merge(tract_hhold_size, good_census_hhold_size, on='tract')
    final_hhold_size_ver_df = pd.merge(merged_df, census_hhold_size, on='tract')
    return final_hhold_size_ver_df


def get_spop_avg_hhold_size(s_pop):
    tract_pop = s_pop.loc[:, ['id', 'hhold']].copy()
    tract_pop['tract'] = tract_pop['id'].str.split('i').str[0]  # Correctly apply split
    tract_pop['count'] = 1  # Adds a new column 'count' with all values set to 1

    # population in tract
    pop_tract = tract_pop.loc[:, ['tract', 'count']].groupby('tract').sum()
    pop_tract = pop_tract.rename(columns={'count': 'pop_count'})

    # household in tract
    hhold_tract = tract_pop.drop_duplicates(subset=['hhold'], keep='first')
    hhold_tract = hhold_tract.loc[:, ['tract', 'count']].groupby('tract').sum()
    # Rename a column: from 'old_column_name' to 'new_column_name'
    hhold_tract = hhold_tract.rename(columns={'count': 'hhold_count'})

    # get avg hhold size
    tract_avg_df = pop_tract.merge(hhold_tract, how='left', on='tract')
    tract_avg_df['avg_hhold_size_spop'] = tract_avg_df['pop_count'] / tract_avg_df['hhold_count']
    tract_avg_df = tract_avg_df.reset_index()
    tract_avg_df['tract'] = tract_avg_df['tract'].astype(str)

    return tract_avg_df


def get_census_avg_hhold_size(census_df):
    selected_census_df = census_df.loc[:, ['GEOID', 'DP1_0001C', 'DP1_0132C']]
    selected_census_df = selected_census_df.rename(
        columns={'GEOID': 'tract', 'DP1_0001C': 'population', 'DP1_0132C': 'hhold'})  # .set_index('tract')
    selected_census_df['avg_hhold_size_census'] = selected_census_df['population'] / selected_census_df['hhold']
    selected_census_df['tract'] = selected_census_df['tract'].astype(str)

    return selected_census_df
