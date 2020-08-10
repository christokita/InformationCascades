
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  9 12:42:29 2017

@author: ChrisTokita

DESCRIPTION:
Function to run network-breaking cascade model
(one replicate simulation given certain parameter combination)
"""

####################
# Load libraries and packages
####################
import numpy as np
import pandas as pd
import cascade_models.social_networks as sn
import cascade_models.thresholds as th
import cascade_models.cascades as cs
import copy
import os

# Supress error warnings (not an issue for this script)
np.seterr(divide='ignore', invalid='ignore')

####################
# Define simulation function
####################

def sim_adjusting_network(replicate, n, k, gamma, psi, p, timesteps, outpath, network_type = "random") :
    # Simulates a single replicate simulation of the network-breaking information cascade model. 
    #
    # INPUTS:
    # - replicate:      id number of replicate (int or float).
    # - n:              number of individuals in social system (int). n > 0.
    # - k:              mean out-degree of initial social network (int). k > 0.
    # - gamma:          correlation between information sources (float). gamma = [-1, 1].
    # - psi:            prop. of individuals sampling info source every time step (float). psi = (0, 1].
    # - p:              probability that randomly selected individual forms a new connection (float). p = [0, 1].
    # - timesteps:      length of simulation (int).
    # - outpath:        path to directory where output folders and files will be created (str). 
    # - network_type:   type of network to intially generate. Default is random but accepts ["random", "scalefree"] (str).
        
    ########## Seed initial conditions ##########
    # Set overall seed
    seed = int( (replicate + 1 + gamma) * 323 )
    np.random.seed(seed)
    # Seed individual's thresholds
    thresh_mat = th.seed_thresholds(n = n, lower = 0, upper = 1)
    # Assign type
    type_mat = th.assign_type(n = n)
    # Set up social network
    adjacency = sn.seed_social_network(n, k, network_type = network_type)
    adjacency_initial = copy.deepcopy(adjacency)
    # Cascade size data
    cascade_size = pd.DataFrame(columns = ['t', 'samplers', 'samplers_active', 'sampler_A', 'sampler_B', 'total_active', 'active_A', 'active_B'])
    # Cascade behavior data (correct/incorrect behavior)
    behavior_data = pd.DataFrame(np.zeros(shape = (n, 5)),
                                          columns = ['individual', 'true_positive', 'false_negative', 'true_negative', 'false_positive'])
    behavior_data['individual'] = np.arange(n)
    
    ########## Run simulation ##########
    for t in range(timesteps):
        # Initial information sampling
        stim_sources, state_mat, samplers, samplers_active = cs.simulate_stim_sampling(n = n,
                                                                                       gamma = gamma,
                                                                                       psi = psi,
                                                                                       types = type_mat,
                                                                                       thresholds = thresh_mat)
        # Simulate information cascade 
        state_mat = cs.simulate_cascade(network = adjacency, 
                                        states = state_mat, 
                                        thresholds = thresh_mat)
        # Get cascade data for beginning and end of simulation
        if (t < 5000 or t >= timesteps - 5000):
            cascade_size = cs.get_cascade_stats(t = t,
                                                samplers = samplers,
                                                active_samplers = samplers_active,
                                                states = state_mat, 
                                                types = type_mat, 
                                                stats_df = cascade_size)
        # Evaluate behavior of individuals relative to threshold and stimuli
        correct_state, behavior_data = cs.evaluate_behavior(states = state_mat, 
                                                            thresholds = thresh_mat, 
                                                            stimuli = stim_sources, 
                                                            types = type_mat,
                                                            behavior_df = behavior_data)
#        # Randomly select one individual and if incorrect, break tie with one incorrect neighbor
#        adjacency = break_tie(network = adjacency,
#                              states = state_mat,
#                              correct_behavior = correct_state)
#        # Randomly select one individual to form new tie
#        adjacency = make_tie(network = adjacency, 
#                             connect_prob = p)
        
        # ALT model format: Adjust ties
        adjacency = adjust_tie(network = adjacency,
                               states = state_mat,
                               correct_behavior = correct_state)
    
    ########## Assess fitness ##########
    # Get fitness of individuals (based on behavior) and size of cascades
    fitness_behavior, fitness_size = cs.assess_fitness(n = n, 
                                                      gamma = gamma, 
                                                      psi = psi, 
                                                      trial_count = 10000, 
                                                      network = adjacency, 
                                                      thresholds = thresh_mat, 
                                                      types = type_mat)
    
    ########## Save files ##########
    # Create output folder
    output_name = "gamma" + str(gamma)
    data_dirs = ['cascade_data', 'social_network_data', 'thresh_data', 'type_data', 'behavior_data', 'fitness_data']
    data_dirs = [outpath + d + "/" for d in data_dirs]
    output_dirs = [d + output_name +  "/" for d in data_dirs]
    for x in np.arange(len(data_dirs)):
        # Check if directory already exisits. If not, create it.
        if not os.path.exists(data_dirs[x]):
            os.makedirs(data_dirs[x])
        # Check if specific run folder exists
        if not os.path.exists(output_dirs[x]):
            os.makedirs(output_dirs[x])
    # Save files
    rep_label = str(replicate)
    rep_label = rep_label.zfill(2)
    cascade_size.to_pickle(output_dirs[0] + "cascade_rep" + rep_label + ".pkl")
    np.save(output_dirs[1] + "sn_final_rep" + rep_label + ".npy", adjacency)
    np.save(output_dirs[1] + "sn_initial_rep" + rep_label + ".npy", adjacency_initial)
    np.save(output_dirs[2] + "thresh_rep" + rep_label + ".npy", thresh_mat)
    np.save(output_dirs[3] + "type_rep" + rep_label + ".npy", type_mat)
    behavior_data.to_pickle(output_dirs[4] + "behavior_rep" + rep_label + ".pkl")
    fitness_size.to_pickle(output_dirs[5] + "fitness_cascades_rep" + rep_label + ".pkl")
    fitness_behavior.to_pickle(output_dirs[5] + "fitness_behavior_rep" + rep_label + ".pkl")
    
####################
# Define model-specific functions
####################
def break_tie(network, states, correct_behavior):
    # Randomly selects active individual and breaks tie with active neighbor iff selected invidual is incorrect.
    #
    # INPUTS:
    # - network:      the network connecting individuals (numpy array).
    # - states:       matrix listing the behavioral state of every individual (numpy array).
    # - correct_behavior:   array indicating whether each individual behaved correctly (numpy array).
    
    actives = np.where(states == 1)[0]
    if sum(actives) > 0: #error catch when no individual are active
        breaker_active = np.random.choice(actives, size = 1)
        breaker_correct = correct_behavior[breaker_active]
        if not breaker_correct:
            breaker_neighbors = np.where(network[breaker_active,:] == 1)[1]
            perceived_incorrect = [ind for ind in actives if ind in breaker_neighbors] #which neighbors are active
            break_tie = np.random.choice(perceived_incorrect, size = 1, replace = False)
            network[breaker_active, break_tie] = 0
    return network
    
def make_tie(network, connect_prob):
    # Randomly selects individual and makes new tie with constant probability.
    #
    # INPUTS:
    # - network:      the network connecting individuals (numpy array).
    # - states:       matrix listing the behavioral state of every individual (numpy array).
    # - stims:         matrix of thresholds for each individual (numpy array).
    # - correct_behavior:   array indicating whether each individual behaved correctly (numpy array).
    
    n = network.shape[0] # Get number of individuals in system
    former_individual = np.random.choice(range(0, n), size = 1)
    form_connection = np.random.choice((True, False), p = (connect_prob, 1-connect_prob)) #determine if individual will form new tie
    former_connections = np.squeeze(network[former_individual,:]) #get individual's neighbors
    potential_ties = np.where(former_connections == 0)[0]
    potential_ties = np.delete(potential_ties, np.where(potential_ties == former_individual)) # Prevent self-loop
    if form_connection == True and len(potential_ties) > 0: #form connection only if selected to form connection and isn't already connected to everyone
        new_tie = np.random.choice(potential_ties, size = 1, replace = False)
        network[former_individual, new_tie] = 1
    return network

def adjust_tie(network, states, correct_behavior):
    # Randomly selects active individual and breaks tie if incorrect.
    # Another individual randomly forms like iff a tie is broken in that round.
    #
    # INPUTS:
    # - network:      the network connecting individuals (numpy array).
    # - states:       matrix listing the behavioral state of every individual (numpy array).
    # - correct_behavior:   array indicating whether each individual behaved correctly (numpy array).
    
    actives = np.where(states == 1)[0]
    if sum(actives) > 0: #error catch when no individual are active
        individual_active = np.random.choice(actives, size = 1)
        individual_correct = correct_behavior[individual_active]
        individual_neighbors = np.where(network[individual_active,:] == 1)[1]
        if not individual_correct:
            
            # Break ties with one randomly-selected "incorrect" neighbor
            perceived_incorrect = [ind for ind in actives if ind in individual_neighbors] #which neighbors are active
            break_tie = np.random.choice(perceived_incorrect, size = 1, replace = False)
            network[individual_active, break_tie] = 0
            
            # Randomly select another individual to form a new tie
            n = network.shape[0] # Get number of individuals in system
            former_individual = np.random.choice(range(0, n), size = 1)
            former_connections = np.squeeze(network[former_individual,:]) #get individual's neighbors
            potential_ties = np.where(former_connections == 0)[0]
            potential_ties = np.delete(potential_ties, np.where(potential_ties == former_individual)) # Prevent self-loop
            if len(potential_ties) > 0: #catch in case the individual is already attached to every other individual
                new_tie = np.random.choice(potential_ties, size = 1, replace = False)
                network[former_individual, new_tie] = 1
                
    return network