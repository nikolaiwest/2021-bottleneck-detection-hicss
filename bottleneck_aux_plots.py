#%% Plot right skewed distribution (FIGURE 4)

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skewnorm

# Set up standard values for both distributions 
maxValue = 1
skewness = 10 # Negative values are left skewed, positive values are right skewed.
sample_size = 10**6 # used **8 for the paper (computation...)

# Set up two sample sets for distribution plot 
data_10 = skewnorm.rvs(a=skewness, loc=1, size=sample_size) * 10 # Skewnorm function
data_12 = skewnorm.rvs(a=skewness, loc=1, size=sample_size) * 12 # Skewnorm function

# Get occurence and value via histogram
occ_10, x_10, _ = plt.hist(data_10, bins=1000, histtype=u'step')
occ_12, x_12, _ = plt.hist(data_12, bins=1000, histtype=u'step')

# Get centers of histogram bars
smooth_10 = 0.5*(x_10[1:] + x_10[:-1])
smooth_12 = 0.5*(x_12[1:] + x_12[:-1])

# Define max limit for all y values in plot 
y_max = max(occ_10.max(), occ_12.max())

plt.clf() # clear

# Set limits for X and Y
plt.xlim(5, 60)
plt.ylim(0, (y_max/sample_size)*1.05)

# Plot distribution and process time mean
plt.plot(smooth_10, occ_10/sample_size, color='forestgreen', label='Non-bottleneck') # using bin centers instead of edges
plt.vlines(data_10.mean(), 0, y_max*1.02, linestyles='--', linewidth=0.5, color='forestgreen', label='Non-bottleneck (mean)')

# Plot distribution and process time mean 
plt.plot(smooth_12, occ_12/sample_size, color='firebrick', label='Bottleneck (with +20%)') 
plt.vlines(data_12.mean(), 0, y_max*1.02, linestyles='--', linewidth=0.5, color='firebrick', label='Bottleneck (mean)')

# Set plot title
plt.title('Right-skewed distribution of process times')

# Set label names
plt.ylabel('Probability distribution')
plt.xlabel('Process time')

# Set legends and show plot
plt.legend()
plt.tight_layout()
plt.show()

print('mean 10: ' + str(data_10.mean()))
print('mean 12: ' + str(data_12.mean()))

#%% Plot one example of the later matrix plot (FIGURE 5)

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

# Set up counter variable and list for diagonal matrix plotting (used for subplot numbering)
#lst = []
#counter = 0 
#for c in range(0,11):
    #lst += list(range(c*10+1+c,(c+1)*10+1))

# Set up bottleneck types and name for later iteration
bottleneck_type = ['itv']
bottleneck_name = ['Interdeparture Time Variance (ITV)']

# Create new figure for matrix plot 
fig = plt.figure(figsize=(6,4))

# Loop all types
for bn_type, bn_name in zip(bottleneck_type, bottleneck_name):

    # Set up counter variable for matrix plotting
    counter = 1

    # Print current type
    if True: 
        print('Bottleneck type: ' + bn_type)

    # 
    bn_pt = 12
    m = 2
    n= 5

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
    ax = fig.add_subplot(111)
    
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
    ax.scatter(range(len(data)), data['bottleneck_' + bn_type], s=50, alpha=0.5)

    # Set X- and Y-Axis on lower edge plots
    ax.set_yticklabels(['M{}'.format(i) for i in range(1,8)], fontsize=12)
    ax.set_xticklabels(['0', '5k', '10k', '15k', '20k'])

    # Increment counter by one
    counter += 1

    #
    ax.set_ylabel('Detected bottleneck station') 
    ax.set_xlabel('Simulation time') 

    # Adjust plot layout
    fig.subplots_adjust(wspace=0.05, hspace=0.05)
    
    # Close the current figure
    plt.show()
    plt.close()

#%% Plot ratio comparison (FIGURE 9) 

import pandas as pd
import matplotlib.pyplot as plt

# Create new figure for comparison plot 
fig = plt.figure(figsize=(6,4))
ax = fig.add_subplot(111)

# Import results from csv
data = pd.read_csv('results_of_method_comparison_listed.csv', delimiter=';', decimal=',')

# Set x values
x = data.bn_pt

# List of labels
labels = ['BNW vs. APM', 'BNW vs. ITV', 'ITV vs. APM']

# Loop over comparisons
for comparison, label in zip(data.columns[-3:], labels):

    plt.plot(x, data[comparison], label=label)

# Set axes
plt.ylabel('Total ratio of agreement [%]')
plt.xlabel('Percentage of additional process time for bottlenecks')
plt.ylim(0.3, 1)


# Define ticks
ax.xaxis.set_ticks(range(11,21,1))
ax.xaxis.set_ticklabels(['{}0%'.format(i) for i in range(1,11)], rotation=45)

# Set a title
plt.title('Comparison')
plt.grid(color='silver')
plt.legend(loc=4)

# Show plot
plt.show()

#%%
