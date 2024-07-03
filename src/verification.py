import pandas as pd
import geopandas as gpd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

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

# Plot Age Group Tables
def PlotVerificationAge_Difference(data):
    # Figure
    plt.figure(figsize=(25, 10))
    # this is for plotting purpose

    index = np.arange(len(data.Type)) + 1
    # data['Differences_Male'] =   data['SPop_Male'] - data['Good_Census_Male']
    # data['Differences_Female'] = data['SPop_Female'] - data['Good_Census_Female']

    data['Differences_Male'] = (data['SPop_Male'] - data['Census_Male']) / data['Census_Male'] * 100
    data['Differences_Female'] = (data['SPop_Female'] - data['Census_Female']) / data['Census_Female'] * 100
    # Dot
    plt.scatter(index, data.Differences_Male, s=30, marker='o', color='gray')
    plt.scatter(index + 0.2, data.Differences_Female, s=30, marker='o', color='orange')

    # axis
    plt.ylim(-0.1, 0.1)
    plt.xticks(index)
    # Lable
    plt.ylabel('Difference', fontsize=24, fontname="Arial")
    plt.xlabel('Age Group Type', fontsize=24, fontname="Arial")

    # Legend
    plt.legend(('Difference of Male', 'Difference of Female'),
               fancybox=True, framealpha=1, shadow=True,
               loc='best', ncol=2, prop={'size': 18})
    # Title
    # plt.title('CT')
    plt.show()


# Age Group by Tract Not used for now
def VerfiyAgeGroupTract(census, goodCensus, pop):
    # good census popualtion under each age group
    censusAgeGroup = goodCensus.iloc[:, 7:21].tolist()

    # loop to get the age range
    for lowerLimit in range(0, 85, 5):
        upperLimit = lowerLimit + 4
        typeAge = 'Age ' + str(lowerLimit) + ' to ' + str(upperLimit)

        popAgeGroup = len(pop[(pop.age >= lowerLimit) & (pop.age <= upperLimit)])
        # tractAgeGroup = popAgeGroup.groupby(['tract']).sum().reset_index()

    resultsDataFrame = pd.DataFrame()
    return resultsDataFrame


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
