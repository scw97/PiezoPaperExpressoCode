# -*- coding: utf-8 -*-
"""
Created on Wed Dec 07 10:39:45 2016

@author: Fruit Flies
"""
from __future__ import division

from my_wavelet_denoise import wavelet_denoise
import numpy as np
from scipy import signal, interpolate

from changepy import pelt
from changepy.costs import normal_mean

from expresso_gui_params import analysisParams
#---------------------------------------------------------------------------------------
def bout_analysis(dset,frames,var_user=analysisParams['var_user'],var_user_flag= False, mad_thresh = analysisParams['mad_thresh']):

    wlevel = analysisParams['wlevel'] 
    wtype = analysisParams['wtype']
    medfilt_window = analysisParams['medfilt_window']
    #var_scale = .5
    #var_scale_testdata = 2*(1.3e-4)
    #mad_thresh = analysisParams['mad_thresh']
    #var_user = analysisParams['var_user']
    min_bout_duration = analysisParams['min_bout_duration']
    min_bout_volume = analysisParams['min_bout_volume']
    
    #---------------------------------------------------------------------------------------
    
    dset_denoised = wavelet_denoise(dset, wtype, wlevel) 
    
    dset_denoised_med = signal.medfilt(dset_denoised,medfilt_window)
    
    sp_dset = interpolate.InterpolatedUnivariateSpline(frames, np.squeeze(dset_denoised_med))
    sp_der = sp_dset.derivative(n=1)
    
    dset_der = sp_der(frames)
    
    if var_user_flag == False:
        iq_range = np.percentile(dset_der,75) - np.percentile(dset_der,25)
        var_user = np.power(iq_range,2.0)/2.0
    #---------------------------------------------------------------------------------------
    
    #dset_var = np.var(dset_der)
    changepts = pelt(normal_mean(dset_der,var_user),len(dset_der)) #var_scale*dset_var #var_scale_testdata*len(dset_der)
    #changepts = pelt(normal_meanvar(dset_der),len(dset_der))
    N = len(dset_der) - 1 
    
    if 0 not in changepts:
        changepts.insert(0,0)
    #if len(dset_der) not in changepts:
    #    changepts.append(len(dset_der))
    if N not in changepts:
        changepts.append(N)
            
    #print(changepts)
    
    #---------------------------------------------------------------------------------------
    
    piecewise_fits = np.empty(len(changepts)-1)
    piecewise_fit_dist = np.empty_like(dset_der)
    
    for i in range(0,len(changepts)-1):
        ipt1 = changepts[i]
        ipt2 = changepts[i+1] + 1
        fit_temp = np.median(dset_der[ipt1:ipt2])
        piecewise_fits[i] = fit_temp
        piecewise_fit_dist[ipt1:ipt2] =  fit_temp*np.ones_like(dset_der[ipt1:ipt2])
    
    
    #mean_pw_slope = np.mean(piecewise_fit_dist)
    #std_pw_slope = np.std(piecewise_fit_dist)
    mad_slope = np.median(np.abs(np.median(dset_der)-dset_der))
    
    piecewise_fits_dev = (piecewise_fits - np.median(dset_der)) / mad_slope
    bout_ind = (piecewise_fits_dev < mad_thresh) #~z score of 1 #(mean_pw_slope - std_pw_slope)
    bout_ind = bout_ind.astype(int)
    bout_ind_diff = np.diff(bout_ind)
    
    #plt.figure()
    #plt.plot(bout_ind)
    
    bouts_start_ind = np.where(bout_ind_diff == 1)[0] + 1 
    bouts_end_ind = np.where(bout_ind_diff == -1)[0] + 1
    
    #print(bouts_start_ind)
    #print(bouts_end_ind)
    
    if len(bouts_start_ind) != len(bouts_end_ind):
        minLength = np.min([len(bouts_start_ind), len(bouts_end_ind)])
        bouts_start_ind = bouts_start_ind[0:minLength]
        bouts_end_ind = bouts_end_ind[0:minLength]
        
    #print(bouts_start_ind)
    #print(bouts_end_ind)
    
    changepts_array = np.asarray(changepts)
    bouts_start = changepts_array[bouts_start_ind]
    bouts_end = changepts_array[bouts_end_ind]
    
    bouts = np.vstack((bouts_start, bouts_end))
    volumes = dset_denoised_med[bouts_start] - dset_denoised_med[bouts_end]
    
    bout_durations = bouts_end - bouts_start
    good_ind = (bout_durations > min_bout_duration) & (volumes > min_bout_volume)
    
    bouts = bouts[:,good_ind]
    volumes = volumes[good_ind]
    
    return (dset_denoised_med, bouts, volumes)
    
    
