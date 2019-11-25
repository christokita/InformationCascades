#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 11:45:37 2019

@author: ChrisTokita
"""

import numpy as np

def evaluate_behavior(states, thresholds, stimuli, types, behavior_df):
    # Evaluates the behavior of active individuals in the cascade and updates data on correct/incorrect behavior.
    #
    # INPUTS:
    # - states:       array listing the behavioral state of every individual (numpy array).
    # - thresholds:   array of thresholds for each individual (numpy array).
    # - stimuli:      array of stimuli/infromation values (numpy array).
    # - types:        array of type assignments for each individual (numpy array).
    # - behavior_df:  dataframe to store the behavioral performance of individuals (pandas dataframe).
    
    # Assess what all individuals would have done if they had sampled info directly
    true_stim = np.dot(types, np.transpose(stimuli))
    correct_behavior = true_stim > thresholds
    
    # Assess error types
    true_positive = (states == 1) & correct_behavior #did behavior when they should have
    true_negative = (states == 0) & ~correct_behavior  #did NOT do behavior when they should NOT have
    false_positive = (states == 1) & ~correct_behavior  #did behavior when they should NOT have
    false_negative = (states == 0) & correct_behavior  #did NOT do behavior when they should have
    
    # Update behavior tracking data
    behavior_df['true_positive'] = behavior_df['true_positive'] + np.ndarray.flatten(true_positive)
    behavior_df['true_negative'] = behavior_df['true_negative'] + np.ndarray.flatten(true_negative)
    behavior_df['false_positive'] = behavior_df['false_positive'] + np.ndarray.flatten(false_positive)
    behavior_df['false_negative'] = behavior_df['false_negative'] + np.ndarray.flatten(false_negative)
    correct_behavior = np.ndarray.flatten(correct_behavior)
    return correct_behavior, behavior_df