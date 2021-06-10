import pandas as pd

from numpy.core.numeric import NaN
from pandas.io.formats.format import DataFrameFormatter

pd.options.mode.chained_assignment = None # for convenience

# Calculate bottleneck according to Interdeparture Time Variance
def calculate_itv_bottleneck(df, station_count, variance_intervall, append_aux_variables):
    ''' Returns one new column per station with the interdeparture times variances, and a new attribute 
    "bottleneck_itv" that gives the station number of the current interdeparture time bottleneck. '''

    # Create a supporting df containing only the interdeparture times
    df_itv = df[df.columns[2*station_count+1:]]

    # Calculate interdeparture time variances with rolling window
    df_itv = df_itv.rolling(variance_intervall, axis=0, min_periods=2).var(skipna=True)

    # Rename columns to itv_m
    df_itv.columns = ['itv_m{}'.format(i) for i in range(1, station_count+1)]

    # Create new column with machine name with lowest ITV
    df_itv['bottleneck_itv'] = df_itv.idxmin(axis=1)

    # Substitute NaN bottlenecks for zero
    df_itv['bottleneck_itv'] = ['itv_m0' if pd.isna(bn) else bn for bn in df_itv['bottleneck_itv']]

    # Convert bottleneck column to int for easy plotting
    df_itv['bottleneck_itv'] = [int(bn[5:]) for bn in df_itv['bottleneck_itv']]

    # Append new columns to dataframe 
    if append_aux_variables: 
        df_itv = pd.concat([df, df_itv], axis=1)
    else: 
        df_itv = pd.concat([df, df_itv['bottleneck_itv']], axis=1)

    # Return all 
    return df_itv

# Calculate bottleneck according to Active Period Method 
def calculate_apm_bottleneck(df, station_count, append_aux_variables):
    ''' Determines the current bottleneck according to the active period method for each point in time, 
    and returns it as a new attribute called "bottleneck_apm".'''

    # Create a supporting df containing only the machine states
    df_apm = df[df.columns[station_count+1:2*station_count+1]]
    
    # Loop over all machines 
    for machine in range(1, station_count+1):

        # Get machine data as series
        machine_states = df_apm['ms_m{m}'.format(m=machine)]
        
        # Reset list and last state for APM calculation
        active_period_lengths = [] 
        last_state = 0 

        # Loop over entire simulation duration
        for state in machine_states:

            # Check if the machine continues to be active
            if (last_state==0 and state==0): 

                # Check for first observation and set default
                if (len(active_period_lengths)==0):
                    active_period_lengths += [1]
                # Increase the active period counter by one
                else: 
                    active_period_lengths += [active_period_lengths[-1]+1]
            
            # Reset active period counter by appending a zero
            else: 
                active_period_lengths += [0]

        # Return APM calculations to the supporting dataframe
        df_apm.loc[:, 'apm_m' + str(machine)] = active_period_lengths

    # Create new column with machine name with longest active period
    df_apm['bottleneck_apm'] = df_apm[df_apm.columns[station_count:]].idxmax(axis=1)

    # Convert bottleneck column to int for easy plotting
    df_apm['bottleneck_apm'] = [int(bottleneck[5:]) for bottleneck in df_apm['bottleneck_apm']]

    # Append new columns to the initial dataframe 
    if append_aux_variables: 
        df_apm = pd.concat([df, df_apm[df_apm.columns[station_count:]]], axis=1)
    else: 
        df_apm = pd.concat([df, df_apm['bottleneck_apm']], axis=1)

    # Return all APMs
    return df_apm

# Calculate bottleneck according to Arrow Method 
def calculate_bnw_bottleneck(df, station_count, buffer_capacity): 
    ''' Determines the current bottleneck according to the bottleneck walk for each point in time, and 
    returns it as a new attribute called "bottleneck_bnw".'''

    # Create a list to return bottleneck stations
    bottleneck_bnw = []

    # Limit data to buffer level 
    df_bnw = df.iloc[:, 0:station_count+1]

    # Calculate bottleneck limits 
    bnw_upper_limit = round(buffer_capacity*(2/3), ndigits=0) # 3
    bnw_lower_limit = round(buffer_capacity*(1/3), ndigits=0) # 2

    # Iterate over all observations
    for index, row in df_bnw.iterrows():

        # Iterate over one point in time
        for buffer_level, buffer_number in zip(row.values, range(len(row))):

            # Check is the first bottleneck is currently observed
            if buffer_number == 0: # Buffer level of B0 is always 1 (infinite)
                continue

            # Check if bottleneck is located downwards in the value stream
            if buffer_level > bnw_upper_limit:
                # IF so, continue for loop and check next buffer
                continue 

            # Check if the buffer level is at least above the lower limitation
            elif buffer_level > bnw_lower_limit:
                # Then no arrow can be placed, also continue the for loop
                continue

            # Turning of the arrow, indicated by a buffer level lower than the lower-limit
            elif buffer_level < bnw_lower_limit: 
                # Assign bottleneck to upstream station and break loop
                bottleneck_bnw += [buffer_number]
                # Exit row and return the number as bottleneck  
                break 

        # Check if no priority 1 bottleneck could be determined and assign station 7 as default ('customer bottleneck')
        if len(bottleneck_bnw)==index:
            # Use last as default for no assignments
            bottleneck_bnw += [station_count]

    # Add result list to return dataframe
    df_bnw['bottleneck_bnw'] = bottleneck_bnw

    # Return all (no aux variables to append)
    return pd.concat([df, df_bnw['bottleneck_bnw']], axis=1)