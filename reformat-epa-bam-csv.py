# a script to mine out epa data output and pull BAM codes
# uses local date/time!!!
#
# Parameter code 88501 is raw BAM
# 88502 is corrected BAM (to agree with FRM data).
# FRM data is 88101
#
import sys
import pandas as pd
import os

inputdtformat = '%Y-%m-%d %H:%M'
outputdtformat = '%Y-%m-%d %H:%M:%S'

extract_pcs = {
    88101: 'frm_ugm3', 
    88501: 'raw_bam_ugm3',
    88502: 'corr_bam_ugm3'
}

try:
    filename = sys.argv[1]
    fileroot, fileext = os.path.splitext(filename)
    outfilename = fileroot+'.tsv'
    dailyfilename = fileroot+'-daily.tsv'
    if outfilename == filename:
        outfilename = fileroot+'-conv.tsv'       
except:
    print('could not read file -- bailing')
    exit(1)
    
# read EPA data data
epa_data = pd.read_csv(filename, delimiter = ',', na_values = {'', 'NaN'})

# create a column in the dataframe that is the datetime_utc and is converted to a datetime64 object
epa_data['datetime_akst'] = pd.to_datetime(epa_data['date_local']+' '+epa_data['time_local'], format=inputdtformat)

# make the index this column
epa_data.index = epa_data['datetime_akst']
if not epa_data.index.is_monotonic:
    print ('warning -- input data are not monotonic in time')

# select data that are only the parameter codes you want
first_loop = True
for pc in extract_pcs:
    mask = epa_data['parameter_code'] == pc
    new_data = epa_data[mask]['sample_measurement']
    new_data.name = extract_pcs[pc]
    new_df = new_data.to_frame()
    if first_loop:
        full_df = new_df
        first_loop = False
    else:
        full_df = full_df.join(new_df, how = 'outer')

# write data
full_df.to_csv(outfilename, sep = '\t', na_rep = 'NaN', date_format = outputdtformat)

# re-average daily
daily_df = full_df.resample('D').mean()
daily_df.to_csv(dailyfilename, sep = '\t', na_rep = 'NaN', date_format = outputdtformat)

