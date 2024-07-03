import pandas as pd
import numpy as np


def __assign_workplaces__(tract, people, od, us_tract_id_work):
    """
    Assign workplaces to individuals based on their home census tract and provided OD matrix and establishment size distribution.

    Parameters:
    - tract: Census tract data for the home location.
    - people: DataFrame containing individual data including age and workplace information.
    - od: Origin-Destination matrix containing commuting information.
    - dp: DataFrame containing establishment size distribution.

    Returns:
    - Modified 'people' DataFrame with workplace information assigned.
    """
    """
    if the destination tract of a worker is not in our DP dataset
    then we assign his wp to 'DTIDw', otherwise 'DTIDw#'

    the actual size distribution of establishments is lognormal
    https://www.princeton.edu/~erossi/fsdae.pdf
    """
    # destination tracts and numbers
    # print("tract number is",tract.name, type(tract.name))
    #
    #print("- Step 2.1 Assigning Work-")
    # print("od")
    # print(od.head())
    # print('tract name type', type(tract.name))

    tract_with_number_jobs = od[od['home'] == tract.name].set_index('work').S000  # set work index, used to be td
    tract_with_number_jobs = tract_with_number_jobs.apply(np.ceil).astype(
        int)  # from this tract to others, used to be td
    # print(tract_with_number_jobs.index)
    # print("--------after apply ceil--------")
    # print(td.head())

    # 58.5%: US population (16+) - employment rate
    # https://data.bls.gov/timeseries/LNS12300000

    # Determine the total number of employed individuals
    total_employed = len(people[people.age >= 18])

    # Determine the total number of workplaces needed
    total_workplaces = tract_with_number_jobs.sum()

    # Check if there are more workplaces than employed individuals
    if total_workplaces > total_employed:
        # Randomly select employed individuals
        employed = people[people.age >= 18].index
        # destination_tract = np.repeat(tract_with_number_jobs.index.values, tract_with_number_jobs.values)).sample(total_employed).tolist()
        # Randomly select destination tracts based on the total number of employed individuals
        destination_tract = pd.Series(
            np.repeat(tract_with_number_jobs.index.values, tract_with_number_jobs.values)).sample(total_employed)

    else:
        # Select all employed individuals
        # employed = people[people.age >= 18].index
        employed = people[people.age >= 18].sample(total_workplaces).index
        # Repeat destination tracts based on the total number of workplaces needed
        destination_tract = pd.Series(np.repeat(tract_with_number_jobs.index.values, tract_with_number_jobs.values))

    # print(type(destination_tract))
    # Assign workplace tracts to employed individuals
    people.loc[employed, "wp"] = destination_tract.apply(lambda x: generate_workplace_id(x, us_tract_id_work)).values


#
def generate_workplace_id(tract_id, us_tract_id_work):
    """
    Generate a workplace ID based on the destination tract and establishment size distribution.
    """
    if tract_id in us_tract_id_work.index:
        wp_cnt = us_tract_id_work.loc[tract_id, "WP_CNT"]
        wp_proba = us_tract_id_work.loc[tract_id, "WP_PROBA"]

        # Check if workplace count is greater than 0
        if wp_cnt > 0:
            # Ensure wp_proba sums to 1, as required by np.random.choice
            if np.sum(wp_proba) != 1:
                wp_proba = wp_proba / np.sum(wp_proba)

            workplace_id = f"{tract_id}w{np.random.choice(wp_cnt, p=wp_proba)}"
        else:
            # Handle zero or negative workplace count
            workplace_id = f"{tract_id}wNone"
    else:
        # If tract_id not found, handle appropriately, perhaps by logging an error or setting a default
        workplace_id = f"{tract_id}wNotFound"

    return workplace_id