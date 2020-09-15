# a script to mine out epa data output and pull multiple parameter codes
# uses local date (no time)
#
import sys
import pandas as pd
import os
import numpy as np

inputdtformat = '%Y-%m-%d %H:%M'
outputdtformat = '%Y-%m-%d'

prefer_sample_duration = '24 HOUR'
prefer_poc = 5

# dictionary defining the parameter code to new name mapping
species = {88403: 'SO4_ugm3',
           88306: 'NO3_ugm3',
           88301: 'NH4_ugm3',
           88302: 'Na_ion_ugm3',
           88303: 'K_ion_ugm3',
           88169: 'S_ugm3',
           88111: 'Ca_ugm3',
           88115: 'Cl_ugm3',
           88167: 'Zn_ugm3',
           88184: 'Na_ugm3',
           88180: 'K_ugm3',
           88165: 'Si_ugm3',
           88161: 'Ti_ugm3',
           88126: 'Fe_ugm3',
           88109: 'Br_ugm3',
           88104: 'Al_ugm3',
           88355: 'OC_IMPROVE_TOT_ugm3',
           88357: 'EC_IMPROVE_TOT_ugm3',
           88370: 'OC_IMPROVE_TOR_ugm3',
           88380: 'EC_IMPROVE_TOR_ugm3',
           88502: 'PM25_grav_ugm3',
           68105: 'Temp_C',
           88101: 'PM25_frm_ugm3'}

# these species need sampler determined from the "method" variable
species_needing_sampler = {88355: 'OC_IMPROVE_TOT_ugm3',
                           88357: 'EC_IMPROVE_TOT_ugm3',
                           88370: 'OC_IMPROVE_TOR_ugm3',
                           88380: 'EC_IMPROVE_TOR_ugm3'}

# these are the samplers that are possible
sampler_strings = ['SASS', 'URG']

# dictionary defining the site code to new name mapping
site = {34: 'ncore',
        35: 'hurst',
        10: 'sob',
        40: 'ast',
        4101: 'uafast',
        4102: 'uaftg',
        4103: 'uafrr'}

# dictionary defining the site code to UAF sitenumber
uafsite = {10: 0,
           34: 1,
           35: 2,
           40: 3,
           4101: 3,
           4102: 4,
           4103: 5}

try:
    filename = sys.argv[1]
    fileroot, fileext = os.path.splitext(filename)
except:
    print('could not read file -- bailing')
    exit(1)
    
# read EPA data data
epa_data = pd.read_csv(filename, delimiter = ',', na_values = {'', 'NaN'})

# create a column in the dataframe that is the datetime_utc and is converted to a datetime64 object
epa_data['sampledate'] = pd.to_datetime(epa_data['date_local']+' '+epa_data['time_local'], format=inputdtformat)

# make the index this column
epa_data.index = epa_data['sampledate']
if not epa_data.index.is_monotonic:
    print ('warning -- input data are not monotonic in time')

# only keep preferred sample duration
mask = epa_data['sample_duration'] == prefer_sample_duration
epa_data = epa_data[mask]

# discover POCs in file
file_pocs = list(set(epa_data['poc']))
# reorder the POCS to have the preferred first
if prefer_poc in file_pocs:
    file_pocs.remove(prefer_poc)
    file_pocs.insert(0,prefer_poc)
else:
    print('WARNING: does not have preferred POC')

num_pocs = len(file_pocs)
if num_pocs > 0:
    epa_data_poc = []
    for poc in file_pocs:
        mask = epa_data['poc'] == poc
        epa_data_poc.append(epa_data[mask])
print ('ordered list of pocs ',file_pocs)
epa_data = epa_data_poc[0]

# determine site
file_sites = set(epa_data['site_number'])
if len(file_sites) > 1:
    print('file contains multiple sites, please separate -- bailing')
    exit(1)
sitename = site[list(file_sites)[0]]
print ('data are at site <{:}>'.format(sitename))
uafsitenum = uafsite[list(file_sites)[0]]

# determine years in the file
years = set([dt.year for dt in epa_data['sampledate']])
if len(years) > 1:
    siteyear = 'multiyear'
else:
    siteyear = str(list(years)[0])
print ('data are during year <{:}>'.format(siteyear))

# iterate through species
firsttime = True
for selected_pc in species:
    # select data that are only the parameter code you want
    for ix in range(num_pocs):
        mask = epa_data_poc[ix]['parameter_code'] == selected_pc
        new_series = epa_data_poc[ix][mask]['sample_measurement']
        new_series.name = species[selected_pc]
        num_new = len(new_series)
        curr_poc = file_pocs[ix]
        if num_new > 0:
            break
    if selected_pc in species_needing_sampler:
        methods = list(set(epa_data_poc[ix][mask]['method']))
        for method in methods:
            for sampler in sampler_strings:
                if method.find(sampler) >= 0: # found method
                    newname = new_series.name
                    new_series.name = newname.replace('_ugm3','_'+sampler+'_ugm3')
    print('extracting data from poc {:} for {:}, found {:} data points'.format(curr_poc,new_series.name,len(new_series)))
    if firsttime:
        # convert series to dataframe
        full_df = new_series.to_frame()
        # add columns for sitename and num then reverse column order
        full_df['uafsitenum'] = uafsitenum
        full_df['sitename'] = sitename
        cols = full_df.columns.tolist()
        cols.reverse()
        full_df = full_df[cols]
        firsttime = False
    else:
        new_df = new_series.to_frame()
        try:
            full_df = full_df.join(new_df, how='outer')
        except:
            print('mismatch in number of values for {:}'.format(species[selected_pc]))
            

# write data
outfilename = sitename+'-'+siteyear+'.tsv'
if outfilename == filename:
    outfilename = fileroot+'-conv.tsv'
print ('writing file <{:}>'.format(outfilename))
full_df.to_csv(outfilename, sep = '\t', na_rep = 'NaN', date_format = outputdtformat)
