# pmtools
Tools for PM extraction and analysis

These tools take data from the EPA database, extracted using the https://aqs.epa.gov API that was extracted to a CSV file and reformat them to simpler formats for ingest into analysis software.  The code is not general and has specifics for our application in Fairbanks, Alaska.

Note that some data from the AQS have commas (the delimiter) in a field of the CSV file, which gives the file more columns on that row, causing these codes to crash.  You could write code to eliminate lines with more columns than the header or edit these spurious lines out of the file.  Generally output is in tab-delimited separated value (.tsv) format with datetimes in YYYY-MM-DD HH:MM:SS time format.

**python3 reformat-epa-csv.py filename.csv** extracts a timeseries (in UTC time) for a single parameter from "filename".  It would generally be used for hourly data or as a snippet of code to bring data into python / pandas and build larger analysis codes.

**python3 reformat-epa-speciation-csv.py filename.csv** extracts a daily timeseries (using local date) of 24-hour sampled speciation data and does some reformatting and basic editing.  It has a set of parameter codes that it looks for that should be in the input file.  It tries to deal with multiple paramater occurence codes (POCs), but may not do this right for an arbirary site.  It tries to extract information about the carbon speciation sampler and methods used.

**python3 ocec-corr.py filename.tsv** takes the output of the speciation reformatter and corrects the EC/OC data based upon Fairbanks correlations between methods and samplers.  It also applies blank corrections (with hard-coded historic values for Fairbanks) and does some simple analysis.
