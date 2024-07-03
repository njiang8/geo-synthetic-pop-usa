import random
import pandas as pd
import numpy as np

'''
====================Assign Household Main Function====================

'''
def __assign_household_order__(tract, people):
    #print("==========Assign People a Household==========")
    #print("-Total population", len(people))
    #print('- Step 1.2 Assign People a Household-')

    # print(hhold_df_id_type)

    #if len(people) is not 0
    # 1.3 use hholdid and hhhold htype to find individuals
    people['assigned'] = 0
    #print("total pop", len(people))
    # print(len(people[(people['age'] >= 18) & (people['age'] <= 64) & (people['gender'] == 'm') & (people['assigned'] == 0)]))

    if tract.DP1_0132C == 0:  # if there is nor houshold record in the census tract, create groupquarter
        print("---only group quarter---")
        gq_df = __get_group_quarter__(tract, people)
        #print(gq_df.head())
        # print("after gp People Left", len(people[people['assigned'] == 0]))
        # print(gq_df)
        # left people
        #print(gq_df['hid'][0])
        people['hhold'] = gq_df['hid'][0]
        people['htype'] = 11
        people['assigned'] = 1
        # return gq_df
    else:
        # 1 get household and its member
        # 1.1 extract amount of each household type
        hhold_df_type = __get_hhold_type__(tract)
        #print(hhold_df_type)
        # print(tract.DP1_0132C)

        # add a col to indicate household type
        hhold_df_type['htype'] = hhold_df_type.index  # np.repeat(hhold_df_type.index, hhold_df_type)

        # 1.2 create hhold df with cols hid, htype using hhold_df_type
        # hhold_df_id_type = __creat_hhold_id__(tract, hhold_df_type)
        hhold_df = __creat_hhold_id__(tract, hhold_df_type)
        # print(hhold_df)

        # 1.3 find members using hhold type
        hhold_df['member'] = hhold_df.apply(lambda x: __find_members__(x, people), axis=1)
        # print(hhold_df)

        # 2, group unassigned population based on group quarters
        #print("People Left before gp", len(people[people['assigned'] == 0]))
        # 2.1 find gp population
        gp_df = __get_group_quarter__(tract, people)
        # 2.1 combine
        hhold_df = pd.concat([hhold_df, gp_df])
        #print("after gp People Left", len(people[people['assigned'] == 0]))

        # 3 , add two cols to people df: 1 is hhold, the other is hhold type
        def __hhhold_2_people__(hh, people):  ##hh is hhold_df
            for m in hh.member:
                # print(m)
                # print(hh.hid)
                # print(hh.htype)
                people.loc[m, 'hhold'] = hh.hid
                people.loc[m, 'htype'] = hh.htype

        hhold_df.apply(__hhhold_2_people__, args=(people,), axis=1)

        # 4 assign left population randomly to household other than alone household
        people[['hhold', 'htype', 'assigned']] = people.apply(
            lambda row: pd.Series(__assign_left_pop_hhold__(row, hhold_df)), axis=1)
        #print("after 1 to 4 People Left", len(people[people['assigned'] == 0]))

'''
====================1, Household ====================
'''
'''
 1.1 Extract the amount of each hhold type
'''


def __get_hhold_type__(tract):
    # hhold_info = (tract[71:-1]).astype(int) #HOUSEHOLDS BY TYPE

    """
    Extract the amount of each household type from the census tract data.

    Parameters:
    - tract: Census tract data containing household type information.

    Returns:
    - DataFrame: DataFrame with columns 'amount' indicating the amount of each household type.
     1.1 Extract the amout of each hhold type
    Extract the amount of each household type from the census tract data.

    Parameters:
    - tract: Census tract data containing household type information.

    Returns:
    - DataFrame: DataFrame with columns 'amount' indicating the amount of each household type.
    #hhold_list = ['DP1_0112C', 'DP1_0113C', 'DP1_0114C', 'DP1_0115C', 'DP1_0116C', 'DP1_0117C', 'DP1_0118C', 'DP1_0119C',
        #'DP1_0120C', 'DP1_0121C', 'DP1_0122C', 'DP1_0123C', 'DP1_0124C', 'DP1_0125C', 'DP1_0126C', 'DP1_0127C',
        #'DP1_0128C', 'DP1_0129C', 'DP1_0130C', 'DP1_0131C', 'DP1_0132C', 'DP1_0133C', 'DP1_0134C', 'DP1_0135C',
        #'DP1_0136C', 'DP1_0137C', 'DP1_0138C', 'DP1_0139C', 'DP1_0140C', 'DP1_0141C', 'DP1_0142C', 'DP1_0143C',
        #'DP1_0144C', 'DP1_0145C', 'DP1_0146C']
    #hhold_info = ('DP1_0112C', 'DP1_0113C', 'DP1_0114C', 'DP1_0115C', 'DP1_0116C', 'DP1_0117C', 'DP1_0118C', 'DP1_0119C',
        #'DP1_0120C', 'DP1_0121C', 'DP1_0122C', 'DP1_0123C', 'DP1_0124C', 'DP1_0125C', 'DP1_0126C', 'DP1_0127C',
        #'DP1_0128C', 'DP1_0129C', 'DP1_0130C', 'DP1_0131C', 'DP1_0132C', 'DP1_0133C', 'DP1_0134C', 'DP1_0135C',
        #'DP1_0136C', 'DP1_0137C', 'DP1_0138C', 'DP1_0139C', 'DP1_0140C', 'DP1_0141C', 'DP1_0142C', 'DP1_0143C',
        #'DP1_0144C', 'DP1_0145C', 'DP1_0146C').astype(int)  #HOUSEHOLDS BY TYPE
    #print(hhold_info)
    """

    hhold_type_amount = pd.Series(np.zeros(11), dtype=int)

    # 0 married         : DP1_0133C - DP1_0134C
    hhold_type_amount[0] = tract.DP1_0133C - tract.DP1_0134C
    # print(hhold_type_amount[0] * 2)
    # hhold_type_amount[0] = 1
    # print(hhold_type_amount[0])
    # 1 marrie with kids: DP1_0134C
    hhold_type_amount[1] = tract.DP1_0134C
    # print(hhold_type_amount[1] * 4)

    # print(hhold_type_amount[1])
    # 2 cocahbiting          : DP1_0135C - DP1_0136C
    hhold_type_amount[2] = tract.DP1_0135C - tract.DP1_0136C
    # print(hhold_type_amount[2])
    # 3 cocahbiting with Kids: DP1_0136C
    hhold_type_amount[3] = tract.DP1_0136C

    # 4 male live alone        :DP1_0138C - DP1_0139C
    hhold_type_amount[4] = tract.DP1_0138C - tract.DP1_0139C
    # 5 male senior live alone :DP1_0139C
    hhold_type_amount[5] = tract.DP1_0139C

    # 6 male with kids         :DP1_0140C
    hhold_type_amount[6] = tract.DP1_0140C

    # 7  female live alone        :DP1_0142C - DP1_0143C
    # print("in get hhold count", tract.DP1_0142C, tract.DP1_0143C)
    hhold_type_amount[7] = tract.DP1_0142C - tract.DP1_0143C

    # 8  female senior live alone :DP1_0143C
    hhold_type_amount[8] = tract.DP1_0143C

    # 9  female with kids         :DP1_0144C
    hhold_type_amount[9] = tract.DP1_0144C

    # 10 non-family group         : (DP1_0137C - DP1_0138C - DP1_0140C) + (DP1_0141C - DP1_0142C - DP1_0144C)
    hhold_type_amount[10] = (tract.DP1_0137C - tract.DP1_0138C - tract.DP1_0140C) + (
                tract.DP1_0141C - tract.DP1_0142C - tract.DP1_0144C)
    # hhold_type_amount[10] = non_female + non_male
    # print(hhold_type_amount[10])

    hhold_type_amount = pd.DataFrame({'amount': hhold_type_amount})

    # print(hhold_type_amount)
    #print("--getting hhold type from census", hhold_type_amount.sum(), "--census", tract.DP1_0132C)

    return hhold_type_amount


def __creat_hhold_id__(tract, df_type):
    """
        1.2 create hhold based on the hhold type;
        Create household IDs and types based on the provided census tract data and household type DataFrame.

    Parameters:
        -  tract: Census tract data containing information about the tract.
        - df_type: DataFrame containing household type information.

    Returns:
        - DataFrame: DataFrame with columns 'hid' for household IDs and 'htype' for household types.
    """
    # print(df_type.head())
    hid_list = []
    type_list = []

    # Generate household IDs and types
    current_hid = 0

    for index, row in df_type.iterrows():
        # print(row)
        htype = row['htype']
        amount = row['amount']
        for _ in range(amount):
            hid_list.append(tract.name + 'h' + str(current_hid))
            type_list.append(htype)
            current_hid += 1

    # Create DataFrame from the lists
    df = pd.DataFrame({'hid': hid_list, 'htype': type_list})
    # custom_order = [4, 5, 7, 8, 0, 2, 1, 3, 6, 9, 10]

    # custom_order = [7, 8, 4, 5, 0, 2, 1, 3, 6, 9, 10]
    #custom_order = [8, 0, 1, 2, 3, 4, 5, 7, 6, 9, 10]
    #custom_order = [8, 10, 0, 1, 2, 3, 4, 5, 7, 6, ]
    custom_order = [4, 5, 7, 8, 0, 1, 2, 3, 9, 10, 6]
    df['htype'] = pd.Categorical(df['htype'], categories=custom_order, ordered=True)
    df_type = df.sort_values(by='htype').reset_index(drop=True)
    df_type['htype'] = df_type['htype'].astype(int)

    # print(df_type.dtypes)
    # print("====in create hhold id type 7", len(df_type[df_type.htype == 7]))
    # print("====in create hhold id type 8", len(df_type[df_type.htype == 8]))
    # print("====in create hhold ordered df", len(df_type))

    return df_type


def __find_members__(hhold, people):
    '''
    1.3 use hholdid and hhhold type to find individuals
    '''
    # print(hhold)
    member = __htype_find_members__(hhold['htype'], people)

    return member


def __htype_find_members__(type, people):
    '''
    Finds members based on household type.

    :param type: Household type.
    :param people: People data.
    :return: List of member indices.
    '''
    # use type to find people index
    member_list = []

    if type == 4:
        #print(" male alone")
        type4_list = people[
            (people['age'] >= 18) & (people['age'] < 65) & (people['gender'] == 'm') & (people['assigned'] == 0)].index
        if type4_list.any():
            member_index = random.choice(type4_list)
            # member_index = random.choice(people[(people['age'] >= 18) & (people['gender'] == 'm') & (people['assigned'] == 0)].index)
            people.loc[member_index, 'assigned'] = 1  # affter picked change from 0 to 1
            # return member_index
            member_list.append(member_index)
        else:
            #print(type, "pass")
            pass

    if type == 5:
        #print(" male 65 + alone")
        type5_list = people[(people['age'] >= 65) & (people['gender'] == 'm') & (people['assigned'] == 0)].index
        if type5_list.any():
            member_index = random.choice(type5_list)
            people.loc[member_index, 'assigned'] = 1  # affter picked change from 0 to 1
            member_list.append(member_index)
        else:
            #print(type, "pass")
            pass

    if type == 7:
        #print(" female alone")
        type7_list = people[
            (people['age'] >= 18) & (people['age'] < 65) & (people['gender'] == 'f') & (people['assigned'] == 0)].index
        # print("==in find 7 if stat show candidate count", len(type7_list))
        if type7_list.any():
            member_index = random.choice(type7_list)
            # print("==in find 7 if stat show candidate id", member_index)
            people.loc[member_index, 'assigned'] = 1  # affter picked change from 0 to 1
            member_list.append(member_index)
        # return member_list
        else:
            #print(type, "pass")
            pass

    if type == 8:
        #print(" female 65 + alone")
        type8_list = people[(people['age'] >= 65) & (people['gender'] == 'f') & (people['assigned'] == 0)].index
        if type8_list.any():
            member_index = random.choice(type8_list)
            people.loc[member_index, 'assigned'] = 1  # affter picked change from 0 to 1
            member_list.append(member_index)
        else:
            #print(type, "pass")
            pass

    # married and cohabit, add the wife or parterner type 0,1,2,3
    # pair couples
    # if type in [0,1,2,3]:
    if type in [0, 1, 2, 3]:
        # print("in 2nd if find partner")
        #print(type, "married and couple")
        # hhold head
        # if np.random.beta(3, 1) > 0.6:
        # print("male head")
        type0_4_list = people[(people['age'] >= 20) & (people['gender'] == 'm') & (people['assigned'] == 0)].index
        if len(type0_4_list) == 0:
            #print(type, "pass due to can not find head")
            pass
        else:
            head_id = random.choice(type0_4_list)
            # else:
            # print("female head")
            # head_id = random.choice(people[(people['age'] >= 21) & (people['age'] <= 64) & (people['gender'] == 'f') & (people['assigned'] == 0)].index)
            # print(head_id)
            people.loc[head_id, 'assigned'] = 1
            member_list.append(head_id)

            # if people.loc[head_id, 'age'] in range(20:24):
            # print("in 3rd if")
            head_age = people.loc[head_id, 'age']
            # if people.loc[head_id, 'age'] >= 20 and people.loc[head_id, 'age'] <= 25:#if husband is 21~24
            if head_age >= 20 and head_age <= 25:  # if husband is 21~24
                # print("in 2.1 if", people.loc[head_id, 'age'])
                member_index = random.choice(people[(people['age'] >= 18) &
                                                    (people['age'] <= head_age + 15) &
                                                    (people['gender'] == 'f') &
                                                    (people['assigned'] == 0)].index)
                # iindex = pot[pot.isin(range(people.code+17,people.code+20))].index[0]
                people.loc[member_index, 'assigned'] = 1
                member_list.append(member_index)
            else:
                # print("in 2.2 if", people.loc[head_id, 'age'])
                p_list = people[(people['age'] >= head_age - 5) &
                                (people['age'] <= head_age + 15) &
                                (people['gender'] == 'f') &
                                (people['assigned'] == 0)].index
                if len(p_list) == 0:
                    p_list_1 = people[(people['age'] >= 20) &
                                      (people['age'] <= people.age.max()) &
                                      (people['gender'] == 'f') &
                                      (people['assigned'] == 0)].index

                    # if len(p_list_1) == 0:
                    #     print(print("hhold type", type, "pass due to can not find wife", "age", head_age))
                    #     print("another range", len(people[(people['age'] >= head_age - 15) & (people['gender'] == 'f') &
                    #                                       (people['age'] <= people.age.max()) & (
                    #                                                   people['assigned'] == 0)].index))
                    # else:
                    member_index = random.choice(p_list_1)
                    # iindex = pot[pot.isin(range(people.code+17,people.code+20))].index[0]
                    people.loc[member_index, 'assigned'] = 1
                    member_list.append(member_index)
                else:
                    member_index = random.choice(p_list)
                    people.loc[member_index, 'assigned'] = 1
                    member_list.append(member_index)

    # hhold with kids get kids
    # 1 marrie with kids
    # 3 cocahbiting with Kids
    # 6 male with kids
    # 9  female with kids
    # https://www.census.gov/hhes/families/files/graphics/FM-3.pdf
    if type in [1, 3, 6, 9]:
        if type in [1, 3]:
            #print(type, "Find kids")
            # print("-in 3.1 if find kids")
            # print("-hhold type", type)
            # print("have member:", len(member_list))
            # print(member_list)
            # get kids max and min age
            kids_age_max, kids_age_min = __get_kids_max_min_age__(member_list, people)
            # print(__get_kids__(kids_age_max, kids_age_min,people))
            num_of_child = max(1, abs(int(np.random.normal(2))))  # gaussian touch
            member_list.append(__get_kids_or_friend__(kids_age_max, kids_age_min, people, num_of_child))

        if type == 6:
            #print(type, "-male with kids")
            # print("-hhold type", type)
            type6_list = people[(people['age'] >= 18) & (people['gender'] == 'm') & (people['assigned'] == 0)].index

            if type6_list.any():
                head_id = random.choice(type6_list)
                people.loc[head_id, 'assigned'] = 1
                member_list.append(head_id)

                num_of_child = max(1, abs(int(np.random.normal(1.6))))
                kids_age_max, kids_age_min = __get_kids_max_min_age__(head_id, people)
                member_list.append(__get_kids_or_friend__(kids_age_max, kids_age_min, people, num_of_child))
            # return member_list
            else:
                #print(type, "pass")
                pass

        if type == 9:
            #print(type, "-female with kids")
            # print("-hhold type", type)

            type9_list = people[(people['age'] >= 18) & (people['gender'] == 'f') & (people['assigned'] == 0)].index
            if type9_list.any():
                head_id = random.choice(type9_list)
                people.loc[head_id, 'assigned'] = 1
                member_list.append(head_id)

                num_of_child = max(1, abs(int(np.random.normal(1.6))))
                kids_age_max, kids_age_min = __get_kids_max_min_age__(head_id, people)
                member_list.append(__get_kids_or_friend__(kids_age_max, kids_age_min, people, num_of_child))
            # return member_list
            else:
                #print(type, "pass")
                pass

    if type == 10:
        #print(type, "-non family group")
        type10_list = people[(people['age'] >= 18) & (people['assigned'] == 0)].index
        if type10_list.any():
            #head_id = random.choice(people[(people['age'] >= 18) & (people['assigned'] == 0)].index)
            head_id = random.choice(type10_list)
            people.loc[head_id, 'assigned'] = 1
            member_list.append(head_id)

            # get roommate or friend
            num_of_friend = max(1, abs(int(np.random.normal(1.5))))
        # print(num_of_friend)

            if people.loc[head_id, 'age'] >= 18 and people.loc[head_id, 'age'] <= 22:
                firend_age_min = 18
                firend_age_max = people.loc[head_id, 'age'].min() + 15
            else:
                firend_age_min = people.loc[head_id, 'age'].min() - 15
                firend_age_max = people.loc[head_id, 'age'].min() + 15

        #print("---kids_age_max", firend_age_max)
        #print("---kids_age_min", firend_age_min)

        #friend_age_max, firend_age_min = __get_kids_max_min_age__(head_id, people)
            member_list.append(__get_kids_or_friend__(firend_age_max, firend_age_min, people, num_of_friend))
        else:
            pass

    return member_list

def __get_kids_max_min_age__(indi_list, people):
    #print("in __get_kids_max_min_age__")
    if (people.loc[indi_list, 'age'].min() - 18) > 18:
        age_max = 18
    else:
        age_max = people.loc[indi_list, 'age'].min() - 18
        #print("---kids_age_max", age_max)
    age_min = 0
    #print(age_max, age_min)
    return age_max, age_min


def __get_kids_or_friend__(age_max, age_min, people, number):
    # print("---in __get_kids__")

    selected_index_list = list(people[(people['age'] <= age_max) &
                                      (people['age'] >= age_min) &
                                      (people['assigned'] == 0)].index)

    if len(selected_index_list) >= number:
        # Sample num_of_child unique indices from the eligible_indices list
        id_index = random.sample(selected_index_list, number)
        people.loc[id_index, 'assigned'] = 1
        # print("---in 3rd if find kids kids index", kids_index)
        return id_index
        # member_list.append(kids_index)
    else:

        # Handle the case where there are not enough eligible indices
        # print("**********not enough slected child selec random**********")
        selected_index_list = list(people[(people['age'] >= 18) & (people['assigned'] == 0)].index)
        if len(selected_index_list) == 0:
            pass
        else:
            #print("friends", len(selected_index_list))
            id_index = random.sample(selected_index_list, number)
            people.loc[id_index, 'assigned'] = 1
            return id_index

'''
====================2, Group Quarter====================
'''
'''
    2 use group quarter info to assign population to group quarter
    2.1 get the population under  each group quarter type then find individuals 
'''


def __get_group_quarter__(tract, people):
    '''
    2 use group quarter info to assign population to group quarter
    2.1 get the population under  each group quarter type then find individuals
    '''
    # tract.DP1_0127C
    members = []
    # print('---in get group quarter---')
    # gp_id = tract.name + 'h' + str(tract.DP1_0132C)
    # print(gp_id)
    #print(tract.DP1_0125C, "in gp")
    # Institutionalized population:!!Male
    #
    if tract.DP1_0127C == 0:
        pass
    else:
        # print('1Institutionalized population:!!Male:', tract.DP1_0127C)
        # members = __get_group_quarter_ids__('male', people, 64, 18, tract.DP1_0127C)
        members.append(__get_group_quarter_ids__('male', people, 64, 18, tract.DP1_0127C))
    # Institutionalized population:!!Female

    #
    if tract.DP1_0128C == 0:
        pass
    else:
        # print('2Institutionalized population:!!Female:', tract.DP1_0128C)
        # members = __get_group_quarter_ids__('female', people, 64, 18, tract.DP1_0128C)
        members.append(__get_group_quarter_ids__('female', people, 64, 18, tract.DP1_0128C))
    # print('3Non-Institutionalized population:!!Male:', tract.DP1_0130C)

    if tract.DP1_0130C == 0:
        pass
    else:
        # print('3Non-Institutionalized population:!!Female:', tract.DP1_0130C)
        # members = __get_group_quarter_ids__('male', people, 100, 65, tract.DP1_0130C)
        members.append(__get_group_quarter_ids__('male', people, 100, 18, tract.DP1_0130C))

    if tract.DP1_0131C == 0:
        pass
    else:
        # print('4Non-Institutionalized population:!!Female:', tract.DP1_0131C)
        # members = __get_group_quarter_ids__('female', people, 100, 65, tract.DP1_0131C)
        members.append(__get_group_quarter_ids__('female', people, 100, 18, tract.DP1_0131C))

    gp_data = {
        'hid': tract.name + 'h' + str(tract.DP1_0132C),
        'htype': 11,
        'member': members
    }
    # print(pd.DataFrame(gp_data))
    return pd.DataFrame(gp_data)


def __get_group_quarter_ids__(x, people, upper_age, lower_age, number):
    '''
    2.2 use census to get group quarter member ids
    '''
    member_list = []
    #print(len(people[people['assigned'] == 0]))
    #print("get gp age max",people.age.max())
    #print("get gp age min",people.age.min())
    # if len(member_list) < x.
    if x == 'male':
        selected_index_list = people[(people['age'] <= upper_age) &
                                          (people['age'] >= lower_age) &
                                          (people['gender'] == 'm') &
                                          (people['assigned'] == 0)].index

        if len(selected_index_list) >= number:
            id_index = random.sample(list(selected_index_list), number)
            people.loc[id_index, 'assigned'] = 1
            # people.loc[id_index, 'htype'] = 11
            member_list.append(id_index)
        else:
            #print('Not enough people')
            # Handle the case where there are not enough eligible indices
            selected_index_list = people[(people['age'] >= 0) & (people['gender'] == 'm') & (people['assigned'] == 0)].index
            if len(selected_index_list) >= number:
                id_index = random.sample(list(selected_index_list), number)
                people.loc[id_index, 'assigned'] = 1
                # people.loc[id_index, 'htype'] = 11
                member_list.append(id_index)
            else:
                pass

    if x == 'female':
        # print("female")
        selected_index_list = people[(people['age'] <= upper_age) &
                                          (people['age'] >= lower_age) &
                                          (people['gender'] == 'f') &
                                          (people['assigned'] == 0)].index

        if len(selected_index_list) >= number:
            id_index = random.sample(list(selected_index_list), number)
            people.loc[id_index, 'assigned'] = 1
            # people.loc[id_index, 'htype'] = 11
            member_list.append(id_index)
        else:
            # Handle the case where there are not enough eligible indices
            #print('gp female Not enough people')
            selected_index_list = people[(people['age'] >= 0) & (people['gender'] == 'f') & (people['assigned'] == 0)].index
            if len(selected_index_list) >= number:
                id_index = random.sample(list(selected_index_list), number)
                people.loc[id_index, 'assigned'] = 1
                # people.loc[id_index, 'htype'] = 11
                member_list.append(id_index)
            else:
                pass
    # print(member_list)
    return member_list


def __assign_left_pop_hhold__(individual, hhold_df):
    # print("in assign left")

    if individual.assigned == 0:
        if individual.age < 18:
            hhold_for_kid_list = list(hhold_df[hhold_df['htype'].isin([1, 3, 6, 9])].hid)
            # Assuming some logic to choose a household for the kid here
            if hhold_for_kid_list:
                probabilities = [0.45 if hhold_type in [1, 3] else 0.1 for hhold_type in
                                 hhold_df.loc[hhold_df['hid'].isin(hhold_for_kid_list), 'htype']]
                # Normalize probabilities
                probabilities /= np.sum(probabilities)
                # Randomly choose household with probabilities
                household_id = np.random.choice(hhold_for_kid_list, p=probabilities)
                assigned_household = household_id
                assigned_htype = hhold_df.loc[hhold_df['hid'] == household_id, 'htype'].iloc[0]
                assigned_status = 1
                # print(f"Assigned kid to household {assigned_household} type {assigned_htype}")
                return assigned_household, assigned_htype, assigned_status
            else:
                hhold_for_kid_list = list(hhold_df[hhold_df['htype'].isin([10])].hid)
                if hhold_for_kid_list:
                    household_id = np.random.choice(hhold_for_kid_list)
                    assigned_household = household_id
                    assigned_htype = hhold_df.loc[hhold_df['hid'] == household_id, 'htype'].iloc[0]
                    assigned_status = 1
                    # print(f"Assigned kid to household {assigned_household} type {assigned_htype}")
                    return assigned_household, assigned_htype, assigned_status
                else:
                    print("No suitable households available for kids")
        elif individual.age == 18:
            hhold_for_nonfam_list = list(hhold_df[hhold_df['htype'].isin([1, 3, 10])].hid)
            # Assuming some logic to choose a household for the adult here
            if hhold_for_nonfam_list:
                probabilities = [0.2 if hhold_type in [1, 3] else 0.6 for hhold_type in
                                 hhold_df.loc[hhold_df['hid'].isin(hhold_for_nonfam_list), 'htype']]
                probabilities /= np.sum(probabilities)
                household_id = np.random.choice(hhold_for_nonfam_list, p=probabilities)
                assigned_household = household_id
                assigned_htype = hhold_df.loc[hhold_df['hid'] == household_id, 'htype'].iloc[0]
                assigned_status = 1
                # print(f"Assigned 18 ad to household {assigned_household} type {assigned_htype}")
                return assigned_household, assigned_htype, assigned_status
            else:
                print("No suitable households available for 18 adults")

        elif individual.age > 18:
            hhold_for_nonfam_list = list(hhold_df[hhold_df['htype'].isin([0, 1, 2, 3, 10])].hid)
            # Assuming some logic to choose a household for the adult here
            if hhold_for_nonfam_list:
                probabilities = [0.6 if hhold_type in [10] else 0.1 for hhold_type in
                                 hhold_df.loc[hhold_df['hid'].isin(hhold_for_nonfam_list), 'htype']]
                probabilities /= np.sum(probabilities)
                household_id = np.random.choice(hhold_for_nonfam_list, p=probabilities)
                assigned_household = household_id
                assigned_htype = hhold_df.loc[hhold_df['hid'] == household_id, 'htype'].iloc[0]
                assigned_status = 1
                # print(f"Assigned adult to household {assigned_household} type {assigned_htype}")
                return assigned_household, assigned_htype, assigned_status
            else:
                print("No suitable households available for adults")

    else:
        return individual.hhold, individual.htype, individual.assigned
