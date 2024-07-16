import glob
import pandas as pd
from loguru import logger

import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt

def read_clean_pums_tract_relationship(path):
    # Define the columns which you expect to have leading zeros
    cols_with_leading_zeros = ['STATEFP', 'COUNTYFP', 'TRACTCE','PUMA5CE']
    # Use dtype to specify string type for these columns
    relationship_data = pd.read_csv(path, dtype={col: str for col in cols_with_leading_zeros})
    relationship_data['PUMAID'] = relationship_data[['STATEFP', 'PUMA5CE']].apply(lambda x: ''.join(x), axis=1)
    relationship_data['GEOID'] = relationship_data[['STATEFP', 'COUNTYFP', 'TRACTCE']].apply(lambda x: ''.join(x), axis=1)
    return relationship_data


def read_pums_file(path):
    us_pums_files = f'{path}/*.csv'
    pums_csv_files = glob.glob(us_pums_files)

    dataframes = []
    # Loop through the ZIP files and read them into GeoDataFrames
    for pums_csv_file in pums_csv_files:
        try:
            df = pd.read_csv(pums_csv_file)
            dataframes.append(df)
            logger.info(f'Loaded file {pums_csv_file} with shape {df.shape}')
        except Exception as e:
            logger.error(f'Failed to load file {pums_csv_file}. Error: {e}')

    if not dataframes:
        logger.warning('No data loaded to process.')
        return pd.DataFrame()

    # Concatenate all DataFrames into one
    combine_df = pd.DataFrame(pd.concat(dataframes, ignore_index=True))
    logger.info(f'combined with shape {combine_df.shape}')
    return combine_df

def get_aggregate_pums_data(data_pums):
    """
    Aggregates PUMS data by age group and gender.
    """
    # Age group categorization
    data_pums.loc[data_pums["AGEP"] <= 4, "AGEG"] = str(0).zfill(2)
    #for lower, upper, group in zip(range(5, 80, 5), range(9, 85, 5), range(1, 16)):
    for lower, upper, group in zip(range(5, 85, 5), range(9, 90, 5), range(1, 17)):
        data_pums.loc[(data_pums["AGEP"] >= lower) & (data_pums["AGEP"] <= upper), "AGEG"] = str(group).zfill(2)
    data_pums.loc[data_pums["AGEP"] >= 85, "AGEG"] = str(17)

    # State and PUMA code formatting
    data_pums['ST'] = data_pums['ST'].apply('{:0>2}'.format)
    data_pums['PUMA'] = data_pums['PUMA'].apply('{:0>5}'.format)
    # Creating a combined identifier
    data_pums['PUMAID'] = data_pums[['ST', 'PUMA']].apply(lambda x: ''.join(x), axis=1)
    # Select specific columns for output
    puma_select = data_pums.loc[:, ["PUMAID", "AGEG", "SEX"]]

    # Generate column names based on gender and age groups
    n1, n2 = 2, 18
    pums_aggregate_col_name = np.empty((n1 * n2), dtype="U10")  # Flatten the array
    index = 0
    for gender in range(n1):
        for age in range(n2):
            pums_aggregate_col_name[index] = str(gender + 1) + str(age).zfill(2)
            index += 1

    # Assuming 'puma_select' is a DataFrame that has been defined earlier
    pums_aggregate_id = sorted(set(puma_select['PUMAID'].to_list()))  # Extract, deduplicate, and sort PUMA IDs

    # Create DataFrame with PUMA IDs as index and initialized with zeros
    pums_aggregate_df = pd.DataFrame(0, index=pums_aggregate_id, columns=pums_aggregate_col_name)

    df = puma_select.groupby(["PUMAID", "AGEG", "SEX"]).size()
    for idx, item in df.items():
        pumaid = idx[0]
        col_name = str(str(idx[2]) + str(idx[1]).zfill(2))  # sex 1 is male, 2 is female
        pums_aggregate_df.at[pumaid, col_name] = int(item)

    return pums_aggregate_df

def get_aggregate_pums20_data(data_pums):
    """
    Aggregates PUMS data by age group and gender.
    """
    # Age group categorization
    data_pums.loc[data_pums["AGEP"] <= 4, "AGEG"] = str(0).zfill(2)
    #for lower, upper, group in zip(range(5, 80, 5), range(9, 85, 5), range(1, 16)):
    for lower, upper, group in zip(range(5, 85, 5), range(9, 90, 5), range(1, 17)):
        data_pums.loc[(data_pums["AGEP"] >= lower) & (data_pums["AGEP"] <= upper), "AGEG"] = str(group).zfill(2)
    data_pums.loc[data_pums["AGEP"] >= 85, "AGEG"] = str(17)

    # State and PUMA code formatting
    data_pums = data_pums[data_pums['PUMA20'] != -9].copy()
    data_pums['ST'] = data_pums['ST'].apply('{:0>2}'.format)
    data_pums['PUMA'] = data_pums['PUMA20'].apply('{:0>5}'.format)
    # Creating a combined identifier
    data_pums['PUMAID'] = data_pums[['ST', 'PUMA']].apply(lambda x: ''.join(x), axis=1)
    # Select specific columns for output
    puma_select = data_pums.loc[:, ["PUMAID", "AGEG", "SEX"]]

    # Generate column names based on gender and age groups
    n1, n2 = 2, 18
    pums_aggregate_col_name = np.empty((n1 * n2), dtype="U10")  # Flatten the array
    index = 0
    for gender in range(n1):
        for age in range(n2):
            pums_aggregate_col_name[index] = str(gender + 1) + str(age).zfill(2)
            index += 1

    # Assuming 'puma_select' is a DataFrame that has been defined earlier
    pums_aggregate_id = sorted(set(puma_select['PUMAID'].to_list()))  # Extract, deduplicate, and sort PUMA IDs

    # Create DataFrame with PUMA IDs as index and initialized with zeros
    pums_aggregate_df = pd.DataFrame(0, index=pums_aggregate_id, columns=pums_aggregate_col_name)

    df = puma_select.groupby(["PUMAID", "AGEG", "SEX"]).size()
    for idx, item in df.items():
        pumaid = idx[0]
        col_name = str(str(idx[2]) + str(idx[1]).zfill(2))  # sex 1 is male, 2 is female
        pums_aggregate_df.at[pumaid, col_name] = int(item)

    return pums_aggregate_df

def get_aggregate_spop_data(spop, pums_id_tract):
    """
    Aggregates spop data by age group and gender and saves the result.
    """
    # create a colum constants tract id (GEOID) using individial id
    spop['id'] = spop['id'].astype(str)

    # Split by 'i' and fill the part before 'i' to 11 digits by adding leading zeros
    def fill_id(x):
        parts = x.split('i')
        if len(parts[0]) < 11:
            parts[0] = parts[0].zfill(11)
        return parts[0]

    spop['GEOID'] = spop['id'].apply(fill_id)

    # assigning age group
    spop.loc[spop["age"] <= 4, "AGEG"] = str(0).zfill(2)
    # for lower, upper, group in zip(range(5, 80, 5), range(9, 85, 5), range(1, 16)):
    for lower, upper, group in zip(range(5, 85, 5), range(9, 90, 5), range(1, 17)):
        spop.loc[(spop["age"] >= lower) & (spop["age"] <= upper), "AGEG"] = str(group).zfill(2)
    spop.loc[spop["age"] >= 85, "AGEG"] = str(17)

    # change gender code m to 1 f to 2
    spop['gender'] = spop['gender'].replace({'m': 1, 'f': 2})
    # idenfiy the PUMA area for each individual
    spop = spop.merge(pums_id_tract, on='GEOID', how='left').loc[:, ['PUMAID', 'AGEG', 'gender']]
    logger.info(f'Before aggregation size: {len(spop)}')

    # Generate column names based on gender and age groups
    n1, n2 = 2, 18
    spop_aggregate_col_name = np.empty((n1 * n2), dtype="U10")  # Flatten the array
    index = 0
    for gender in range(n1):
        for age in range(n2):
            spop_aggregate_col_name[index] = str(gender + 1) + str(age).zfill(2)
            index += 1

    # Assuming 'puma_select' is a DataFrame that has been defined earlier
    spop_aggregate_id = sorted(set(spop['PUMAID'].to_list()))  # Extract, deduplicate, and sort PUMA IDs

    # Create DataFrame with PUMA IDs as index and initialized with zeros
    spop_aggregate_df = pd.DataFrame(0, index=spop_aggregate_id, columns=spop_aggregate_col_name)

    df = spop.groupby(['PUMAID', 'AGEG', 'gender']).size()
    for idx, item in df.items():
        pumaid = idx[0]
        col_name = str(str(idx[2]) + str(idx[1]).zfill(2))  # sex 1 is male, 2 is female
        spop_aggregate_df.at[pumaid, col_name] = int(item)

    #logger.info(f'After aggregation size: {len(spop_aggregate_df)}; Saving to {state_save_path}')
    #spop_aggregate_df.to_csv(state_save_path)

    return spop_aggregate_df


def get_cosine_similarity(A, B):
    # Sample data array 'cos' (cosine similarity values)
    cos = np.sum(A * B, axis=1) / (norm(A, axis=1) * norm(B, axis=1))

    # Create the figure and axes objects
    fig, ax = plt.subplots(figsize=(16, 10))

    # Create a histogram on the axes
    ax.hist(cos, 20, color='grey')
    ax.set_xlabel('Cosine Similarity', fontsize=20, fontname="Arial")  # Set the size of the x-axis label
    ax.set_ylabel('Number of PUMAs', fontsize=20, fontname="Arial")

    # Optionally, adjust the tick label sizes
    ax.tick_params(axis='both', which='major', labelsize=14)

    # Saving the figure
    fig.savefig('cos_sim_fig.eps', bbox_inches='tight', pad_inches=0.05)

    # Calculate and print the proportion of values higher than 0.95
    proportion_high = np.count_nonzero(cos > 0.95) / len(cos)
    logger.info('Proportion higher than 0.95: ', proportion_high)

