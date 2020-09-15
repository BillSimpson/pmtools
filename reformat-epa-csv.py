# a script to mine out epa data output and pull one parameter code
# uses UTC date/time 
#
import sys
import pandas as pd
import os

inputdtformat = '%Y-%m-%d %H:%M'
outputdtformat = '%Y-%m-%d %H:%M:%S'
selected_pc = 88501
selected_name = 'raw_bam_pm25_ugm3'

try:
    filename = sys.argv[1]
    fileroot, fileext = os.path.splitext(filename)
    outfilename = fileroot+'.tsv'
    if outfilename == filename:
        outfilename = fileroot+'-conv.tsv'       
except:
    print('could not read file -- bailing')
    exit(1)
    
# read EPA data data
epa_data = pd.read_csv(filename, delimiter = ',', na_values = {'', 'NaN'})

# create a column in the dataframe that is the datetime_utc and is converted to a datetime64 object
epa_data['datetime_utc'] = pd.to_datetime(epa_data['date_gmt']+' '+epa_data['time_gmt'], format=inputdtformat)

# make the index this column
epa_data.index = epa_data['datetime_utc']
if not epa_data.index.is_monotonic:
    print ('warning -- input data are not monotonic in time')

# select data that are only the parameter code you want (corrected BAM PM2.5 hourly)
mask = epa_data['parameter_code'] == selected_pc

pm25_data = epa_data[mask]['sample_measurement']
pm25_data.name = selected_name

# write data
pm25_data.to_csv(outfilename, sep = '\t', na_rep = 'NaN', date_format = outputdtformat)
