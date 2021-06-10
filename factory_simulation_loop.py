import simpy
import numpy as np
import pandas as pd

from tqdm import tqdm
from csv import writer
from datetime import datetime
from scipy.stats import skewnorm
from numpy.core.numeric import NaN

##############################
### Set up basic parameter ###

# Time steps to run the simulation for
SIMULATION_TIME = 25000

# Max capacity of all buffers
BUFFER_CAPACITY = 5

# Initial capacity of all buffers 
INITIAL_CAPACITY = 1

class Machine():

    def __init__(self, process_time, machine_name):
        '''Constructor for a single machine in the factory simulation.'''
        
        # Set process time 
        self.process_time = process_time
        # Set default name
        self.machine_name = machine_name
    
        # Set initial machine state
        self.machine_state = 0

        # Initialize departure time
        self.last_departure_time = 0
        # Initialize interdeparture time
        self.interdeparture_time = 0

        # Get name of upstream buffer
        self.buffer_upstream = 'b{}'.format(int(self.machine_name[1:])-1)
        # Get number downstream buffer 
        self.buffer_downstream = 'b{}'.format(self.machine_name[1:])

    def apply_variability(self, process_time):
        ''' Applies a Exponential distribution to the process time.'''
        return (skewnorm.rvs(a=10, loc=1, size=1)*process_time)[0]

    def run_machine(self, env):
        '''Run the machining process to consume material and produce (semi-) finished goods.'''

        while True:

            # Change machine state to starved 
            self.machine_state = 1
       
            # Get material from upstream buffer
            if self.buffer_upstream != 'b0': # infinite b0, since no material is ever 'really' taken from B0
                yield env.all_buffer[self.buffer_upstream].get(1)
            
            # Change machine state to active 
            self.machine_state = 0
            
            # Machining 
            yield env.timeout(self.apply_variability(self.process_time))

            # Calculate time since last finished product (inter-departure time)
            self.interdeparture_time = env.now - self.last_departure_time 

            # Reset last departure time for the next product
            self.last_departure_time = env.now 

            # Change machine state to blocked 
            self.machine_state = 2

            # Put finished good into downstream buffer
            yield env.all_buffer[self.buffer_downstream].put(1)

class Factory_Simulation():

    def __init__(self, process_times):
        ''' Constructor class for factory simulation.'''

        # Set up simpy environment
        self.env = simpy.Environment()

        # Define processing times according to scenario
        self.process_times = process_times
        # Define default machine names
        self.machine_names = ['m{i}'.format(i=i+1) for i in range(len(self.process_times))]
        # Define default buffer names
        self.buffer_names = ['b{i}'.format(i=i) for i in range(len(self.process_times)+1)]

        # Create dict for all machines
        self.all_machines = {}

        # Create dict for all buffers
        self.env.all_buffer = {}

        # Set up all buffers in dict
        for buffer in self.buffer_names:
            if buffer != 'b{}'.format(len(self.process_times)):
                self.env.all_buffer[buffer] = simpy.Container(self.env, capacity=BUFFER_CAPACITY, init=INITIAL_CAPACITY)
            else: # infinite customer buffer
                self.env.all_buffer[buffer] = simpy.Container(self.env, capacity=999999, init=INITIAL_CAPACITY) # virtually unlimited

        # Set up all machines in dict
        for name, time in zip(self.machine_names, self.process_times):
            self.all_machines[name] = Machine(time, name)

    # Required for BNW bottleneck detection
    def get_buffer_level(self):
        ''' Returns a list of the current level of all buffers.'''
        return [buffer.level for buffer in self.env.all_buffer.values()]

    # Required for ITV bottleneck detection
    def get_interdeparture_times(self):
        ''' Returns a list of the current interdeparture times of all machines.'''
        return [machine.interdeparture_time for machine in self.all_machines.values()]

    # Required for APM bottleneck detection
    def get_machine_states(self):
        ''' Returns a list of the current machine states of all machines.'''
        return [machine.machine_state for machine in self.all_machines.values()]

    # Manual reset of ITVs for each simulation run
    def reset_interdeparture_times(self):
        ''' Resets the interdeparture time for all machines back to zero.'''
        for machine in self.all_machines.values():
            machine.interdeparture_time = NaN

# Loop over all processing time scenarios
for pt_bottleneck in range(11, 21, 1): # from 10% to 100% extra time for bottlenecks

    # Print bottleneck percentage progressions
    print(datetime.now().strftime("%H:%M:%S")+ ' - Running simulations for {} bottleneck'.format(str(pt_bottleneck-10)+'0%'))

    # Loop over m stations
    for m in range(1,6): # M1 and M7 excluded, since the system boundaries are unlimited

        # Loop over n stations
        for n in range(1,6):

            # Create a new list of process times 
            PROCESS_TIMES = [10] * 7
            
            # Adjust list and set station m and n to bottleneck process times 
            PROCESS_TIMES[n] = pt_bottleneck
            PROCESS_TIMES[m] = pt_bottleneck

            # Print loop progression 
            if True:
                print('({},{})'.format(m,n))
                print(PROCESS_TIMES)

            # Reset seed to default number
            np.random.seed(seed=42)

            # Set up factory using the modified process times 
            factory = Factory_Simulation(PROCESS_TIMES)

            # Run all machines
            for name, machine in factory.all_machines.items(): 
                # Execute all processing steps
                factory.env.process(machine.run_machine(factory.env))

            # Iter over simulation time 
            for t in tqdm(range(1, SIMULATION_TIME)):

                # Reset ITV of all machines (not required for buffer level or machine states)
                factory.reset_interdeparture_times()
                
                # Run env until t
                factory.env.run(until=t)
                
                # Save results as csv (writer is much faster than using pandas...)
                with open('results_bn-pt_{}/result_25k_bn({},{})_bn-pt({}).csv'.format(pt_bottleneck,m,n,pt_bottleneck), 'a+', newline='') as result_file:
                    # Get observations as list
                    new_line = [t] + factory.get_buffer_level() + factory.get_machine_states() + factory.get_interdeparture_times()
                    # Append list to csv 
                    writer_object = writer(result_file)
                    writer_object.writerow(new_line)
                    result_file.close()
