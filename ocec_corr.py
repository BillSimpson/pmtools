#!/usr/bin/python
import os
import sys
import datetime
import math
import pandas as pd
import numpy as np

outputdtformat = '%Y-%m-%d'

ocec_possible_types = ['NIOSH_TOT_SASS', 'IMPROVE_TOR_SASS', 'IMPROVE_TOR_URG']

def num_data(arr):
   mask = np.logical_not(np.isnan(arr))
   return mask.sum()

def sel_qc(PM25, recon, arr):
   arr_qc = np.copy(arr)
   absdiff = abs(PM25-recon)
   avg = (PM25+recon)/2
   target = 3.5 + 0.10*avg ## threshold = 3.5 microgram + 10%
   mask = absdiff < target
   arr_qc[mask] = np.nan
   return arr_qc

def nan2zero(arr):
   arr0 = np.copy(arr)
   arr0[np.isnan(arr0)] = 0
   return arr0
   
def calc_OPM (Si, Ti, Ca, Fe, Cl):
   Si0 = nan2zero(Si)
   Ti0 = nan2zero(Ti)
   Ca0 = nan2zero(Ca)
   Fe0 = nan2zero(Fe)
   Cl0 = nan2zero(Cl)
   return (2.49 * Si0 + 1.94 * Ti0 + 1.63 * Ca0 + 2.42 * Fe0 + 1.8 * Cl0)

def SO2sulfate(SO2_ppb, Temp_C):
   return (96.0 * 1.0e6 * SO2_ppb * 1.0e-9 * 1.0e5 / (8.314 * (Temp_C + 273.15)))

##### start main code ######

# try to get the input filename
try:
   infilename = sys.argv[1]
except:
   print ('usage: '+sys.argv[0]+ ' rawfile')
   exit(1)

# manipulate filenames
prefix, extension = os.path.splitext(infilename)
outfilename = prefix+'-corr'+extension
basedir, infileroot = os.path.split(infilename)
site = infileroot.split('-')[0]+'-'

# input the data
dtformat = '%Y-%m-%d'
customdateparser = lambda x: datetime.datetime.strptime(x, dtformat)

spec_data = pd.read_csv(infilename, delimiter = '\t', na_values = ['', 'NaN'],index_col=0, parse_dates = True, date_parser = customdateparser)

# determine the type of OC/EC data
avail_meas_types = []
for meas_type in ocec_possible_types:
   full_meas_type = 'OC_'+meas_type+'_ugm3'
   if full_meas_type in spec_data.columns:
      # check if there is actually data
      if num_data(spec_data[full_meas_type]) > 0:
         avail_meas_types.append(meas_type)

if len(avail_meas_types)>1:
   print ('multiple measurement types not yet supported, using first')
ocec_meas_type = avail_meas_types[0]
print ('OC/EC measurement type is '+ocec_meas_type)

## read data and do calculations
# correct PM2.5 for the blank
spec_data['PM25_grav_corr_ugm3'] = spec_data['PM25_grav_ugm3'] - 0.762

# take average of the FRM and GRAV mass concentration, ignoring NaNs
spec_data['PM25_corr_ugm3'] = np.nanmean((spec_data['PM25_grav_corr_ugm3'], spec_data['PM25_frm_ugm3']), axis = 0)

# correct EC, TC and calculate OC
full_oc = 'OC_'+ocec_meas_type+'_ugm3'
full_ec = 'EC_'+ocec_meas_type+'_ugm3'
if ocec_meas_type == 'NIOSH_TOT_SASS':
   spec_data['EC_corr_ugm3'] = spec_data[full_ec] - 0.025
   spec_data['TC_corr_ugm3'] = spec_data[full_oc] - 1.212 + spec_data['EC_corr_ugm3']
if ocec_meas_type == 'IMPROVE_TOR_SASS':
   spec_data['EC_corr_ugm3'] = 0.800 * spec_data[full_ec]
   spec_data['TC_corr_ugm3'] = 1.000 * ( spec_data[full_oc] - 0.687 + spec_data[full_ec] )
if ocec_meas_type == 'IMPROVE_TOR_URG':
   spec_data['EC_corr_ugm3'] = 0.800 * spec_data[full_ec]
   spec_data['TC_corr_ugm3'] = 1.268 * ( spec_data[full_oc] - 0.137 + spec_data[full_ec] )
# now calculate OC = TC - EC
spec_data['OC_corr_ugm3'] = spec_data['TC_corr_ugm3'] - spec_data['EC_corr_ugm3']

# correct OC, OCM, and OPM
spec_data['OCM_ugm3'] = 1.4 * spec_data['OC_corr_ugm3']
spec_data['OPM_ugm3'] = calc_OPM(spec_data['Si_ugm3'],spec_data['Ti_ugm3'],spec_data['Ca_ugm3'],spec_data['Fe_ugm3'],spec_data['Cl_ugm3'])

# background correct ions
spec_data['SO4_corr_ugm3'] = spec_data['SO4_ugm3'] - 0.051  ## Sulfate
spec_data['NO3_corr_ugm3'] = spec_data['NO3_ugm3'] - 0.027  ## Nitrate
spec_data['NH4_corr_ugm3'] = spec_data['NH4_ugm3'] - 0.006  ## Ammonium 

# calculate inorganics and recon
spec_data['IM_ugm3'] = spec_data['SO4_corr_ugm3'] + spec_data['NO3_corr_ugm3'] + spec_data['NH4_corr_ugm3']
spec_data['recon_ugm3'] = spec_data['OCM_ugm3'] + spec_data['EC_corr_ugm3'] + spec_data['IM_ugm3'] + spec_data['OPM_ugm3']

# calculate total potential sulfate NOTE this needs 24-hour averaged SO2, not there yet
# spec_data['SO4_tot_pot_ugm3'] = spec_data['SO4_corr_ugm3'] + SO2sulfate(spec_data['SO2_ppb'],spec_data['Temp_C'])
# calculate NH4 to neutralize
spec_data['NH4_neut_ugm3'] = 0.375 * spec_data['SO4_corr_ugm3'] + 0.290 * spec_data['NO3_corr_ugm3']

PM25_sel = np.copy(spec_data['PM25_corr_ugm3'])
low_mask = PM25_sel < 5
PM25_sel[low_mask] = np.nan
spec_data['SO4_PM25_ratio'] = spec_data['SO4_corr_ugm3'] / PM25_sel
spec_data['NO3_PM25_ratio'] = spec_data['NO3_corr_ugm3'] / PM25_sel
spec_data['OC_PM25_ratio'] = spec_data['OC_corr_ugm3'] / PM25_sel
spec_data['EC_PM25_ratio'] = spec_data['EC_corr_ugm3'] / PM25_sel
spec_data['K_PM25_ratio'] = spec_data['K_ugm3'] / PM25_sel

for colname in spec_data.columns:
   if colname.find('ratio') >= 0:
      print('Mean for {:} is {:.4f}'.format(colname,spec_data[colname].mean()))

print ('writing file <{:}>'.format(outfilename))
spec_data.to_csv(outfilename, sep = '\t', na_rep = 'NaN', date_format = outputdtformat)
