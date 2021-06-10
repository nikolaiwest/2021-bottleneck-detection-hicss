#%%
import pandas as pd 
import matplotlib.pyplot as plt

from bottleneck_determination import calculate_itv_bottleneck, calculate_apm_bottleneck, calculate_bnw_bottleneck

# Set total number of stations for import 
station_count = 7

# Set column names for all buffer level, machine states and process times
buffer_level_cols = ['bl_b{i}'.format(i=i) for i in range(station_count+1)] 
machine_state_cols = ['ms_m{i}'.format(i=i+1) for i in range(station_count)]
process_times_cols = ['pt_m{i}'.format(i=i+1) for i in range(station_count)]

# Column names for import
column_names = buffer_level_cols + machine_state_cols + process_times_cols

# Set up bottleneck types and name for later iteration
bottleneck_type = ['bnw', 'apm', 'itv']
bottleneck_name = ['Bottleneck Walk (BNW)', 'Active Period Method (APM)', 'Interdeparture Time Variance (ITV)']

# Set up list pairs of all three possible combinations of bottleneck detection methods 
combination_methods = [['bnw', 'apm'], ['apm', 'itv'], ['itv', 'bnw']]
combination_numbers = [[0, 1], [1, 2], [2, 0]]

# Create result DataFrame for comparison
cols = ['bn_pt', 'm', 'n', 'method_1', 'method_2' ]
df_comp = pd.DataFrame(columns=cols)

# Loop all bottleneck process times
for bn_pt in range(11, 21, 1): # not for calculations, just used to loop files

    # Print current bottleneck type
    if True: 
        print('Bottleneck process time: ' + str(bn_pt))

    # Loop over all buffer-bottleneck-combinations
    for m in range(1,6):
        for n in range(1,6):

            # Get file path as string for import
            file_path = 'results_bn-pt_{bn_pt}/result_25k_bn({bn1},{bn2})_bn-pt({bn_pt}).csv'.format(bn1=m, bn2=n, bn_pt=bn_pt)

            # Load data 
            data = pd.read_csv(file_path, names=column_names).reset_index(drop=True)

            # Calculate the bottleneck stations with all three detection methods
            data = calculate_itv_bottleneck(df=data, 
                                            station_count=station_count, 
                                            variance_intervall=5000, 
                                            append_aux_variables=False)
            data = calculate_apm_bottleneck(df=data, 
                                            station_count=station_count, 
                                            append_aux_variables=False)
            data = calculate_bnw_bottleneck(df=data, 
                                            station_count=station_count, 
                                            buffer_capacity=5)

            # Limit data to only bottleneck columns for comparison
            data = data[data.columns[-3:]]

            # Loop over the three possible combinations and append comparison dict
            for methods, numbers in zip(combination_methods, combination_numbers): 

                # Unpack ziped pairs to variables
                met1 = methods[0]
                met2 = methods[1]
                num1 = numbers[0]
                num2 = numbers[1]

                # Create result dict from cols 
                vals = dict.fromkeys(cols)
                # Current process time
                vals['bn_pt'] = bn_pt
                # Station number of current bottleneck stations
                vals['m'] = m
                vals['n'] = n
                # Name of compared detection method
                vals['method_1'] = met1
                vals['method_2'] = met2

                # Check for agreement on detected bottleneck stations
                comp = data[data.columns[num1]] == data[data.columns[num2]]
                # Calculate ratio of agreement and add it to the dict

                vals ['ratio'] = sum(comp)/len(comp)

                # Add dict to result dataframe
                df_comp = df_comp.append(vals, ignore_index=True)

# Group and calcuate average ratios (TABLE 1)
df_comp.groupby(['bn_pt', 'method_1', 'method_2'])['ratio'].mean().reset_index()

#%%

df_comp.groupby(['bn_pt', 'method_1', 'method_2'])['ratio'].mean().reset_index().to_csv('results_of_method_comparison_grouped.csv')