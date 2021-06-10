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

#Set up counter variable and list for diagonal matrix plotting
#lst = []
#counter = 0 
#for c in range(0,11):
    #lst += list(range(c*10+1+c,(c+1)*10+1))

# Set up bottleneck types and name for later iteration
bottleneck_type = ['bnw', 'apm', 'itv']
bottleneck_name = ['Bottleneck Walk (BNW)', 'Active Period Method (APM)', 'Interdeparture Time Variance (ITV)']

# Loop all bottleneck process times
for bn_pt in range(11, 21, 1): # not for calculations, just used to loop files

    # Loop all types
    for bn_type, bn_name in zip(bottleneck_type, bottleneck_name):

        # Create new figure for matrix plot 
        fig = plt.figure(figsize=(20,20))

        # Set up counter variable for matrix plotting
        counter = 1

        # Print current bottleneck type
        if True: 
            print('Bottleneck type: ' + bn_type)

        # Loop over all buffer-bottleneck-combinations
        for m in range(1,6):
            for n in range(1,6):

                # Get file path as string for import
                file_path = 'results_bn-pt_{bn_pt}/result_25k_bn({bn1},{bn2})_bn-pt({bn_pt}).csv'.format(bn1=m, bn2=n, bn_pt=bn_pt)

                # Load data 
                data = pd.read_csv(file_path, names=column_names).reset_index(drop=True)

                # Determine bottlenecks 
                if bn_type=='itv':
                    # Interdeparture Time Variance
                    data = calculate_itv_bottleneck(df=data, 
                                                    station_count=station_count, 
                                                    variance_intervall=5000, 
                                                    append_aux_variables=False)
                elif bn_type=='apm':
                    # Active Period Method
                    data = calculate_apm_bottleneck(df=data, 
                                                    station_count=station_count, 
                                                    append_aux_variables=False)
                elif bn_type=='bnw':
                    # Bottleneck Walk
                    data = calculate_bnw_bottleneck(df=data, 
                                                    station_count=station_count, 
                                                    buffer_capacity=5)

                # Limit observations to all observations after the system is swung in
                data = data[5000:25000]

                # Set up ax for subplot (5 x 5 plot for seven stations)
                ax = fig.add_subplot(station_count-2, station_count-2, counter)
                
                # Specify axis
                ax.grid(color='lightgray')

                # Adjust gridlines for bottleneck stations 
                grid_lines = ax.get_ygridlines()
                grid_lines[m].set_color('black')
                grid_lines[m].set_linestyle('--')
                grid_lines[n].set_color('black')
                grid_lines[n].set_linestyle('--')

                # Adjust general settings for X- and Y-axis in result view
                ax.set_ylim(0,8)
                ax.yaxis.set_ticks(range(1,8))
                ax.yaxis.set_ticklabels([])
                ax.set_xticks([0, 5000, 10000, 15000, 20000])
                ax.xaxis.set_ticklabels([])

                # Plot data as scatter plot
                ax.scatter(range(len(data)), data['bottleneck_' + bn_type], s=10, alpha=0.5)

                # Set X- and Y-Axis on lower edge plots
                if n==1:
                    ax.set_yticklabels(['M{}'.format(i) for i in range(1,8)], fontsize=12)
                if m==5:
                    ax.set_xticklabels(['0', '5k', '10k', '15k', '20k'])

                # Increment counter by one
                counter += 1

        # Add title to figure 
        fig.suptitle('{bn_name}: bn pt={bn_pt}'.format(bn_name=bn_name, bn_pt=bn_pt))

        # Adjust plot layout
        fig.subplots_adjust(wspace=0.05, hspace=0.05)
        # Save figure
        fig.savefig('5x5_Plot_bn-pt({bn_pt})_{bn_type}.png'.format(bn_pt=bn_pt, bn_type=bn_type))
        # Close the current figure
        plt.close()
