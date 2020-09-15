# a script that just removes lines from EPA CSV files
# that have different number of comma-delimited values as compared to
# the header
#
import sys
import os

delimiter = ','

try:
    filename = sys.argv[1]
    fileroot, fileext = os.path.splitext(filename)
    outfilename = fileroot+'-clean.csv'
except:
    print('could not read file -- bailing')
    exit(1)
    
# read EPA data data
infile = open(filename, 'r')
infilelines = infile.readlines()
infile.close()

outfile = open(outfilename, 'w')

header = infilelines[0]
numcols = len(header.split(delimiter))
outfile.write(header)

for line in infilelines[1:]:
    if len(line.split(delimiter)) == numcols:
        outfile.write(line)
    else:
        print ('bad line: '+line.strip())

outfile.close()
