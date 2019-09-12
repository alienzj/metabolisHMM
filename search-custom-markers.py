#! /usr/bin/env python 

###############################################################
# metabolisHMM - A tool for exploring and visualizing the distribution and evolutionary histories of metabolic markers
# search-custom-markers to get statistics and visualization of a set of HMM markers
# Written by Elizabeth McDaniel emcdaniel@wisc.edu
# November 2018
# This program is free software under the GNU General Public License version 3.0
###############################################################

import os, sys, glob, argparse, subprocess
import pandas as pd 
from Bio import BiopythonExperimentalWarning
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore', BiopythonExperimentalWarning)
    from Bio import SearchIO

# Arguments and Setup
parser = argparse.ArgumentParser(description = "Search custom directory of HMMs")
parser._action_groups.pop()
required = parser.add_argument_group("required arguments")
optional = parser.add_argument_group("optional arguments")
required.add_argument('--input', metavar='GENOMEDIR', help='Directory where genomes to be screened are held')
required.add_argument('--output', metavar='OUTPUT', help="Directory to store results and intermediate files")
required.add_argument('--markers_list', metavar='MARKERLIST', help="Ordered list of markers to run custom search on ")
optional.add_argument('--summary', metavar='OUTFILE', default='custom-markers-results.csv', help='Output statistics of custom marker searches in .csv format')
optional.add_argument('--heatmap', metavar='HEATOUT', default='metabolic-summary-results-heatmap.pdf', help="Summary heatmap of metabolic markers in PDF format. If you provide a custom name, it must end in .pdf" )
optional.add_argument('--metadata', metavar='METADATA', help='Metadata file with taxonomical classifications or groups associated with genome file names')
optional.add_argument('--aggregate', metavar='AGG', default='OFF', help="Aggregate metadata names by group = ON, visualize each genome individually = OFF" )

# if no arguments given, print help message
if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

# version to print
def version():
    versionFile = open('VERSION')
    return versionFile.read()
VERSION = version()

args = parser.parse_args()
GENOMEDIR = args.inputs
OUTFILE = args.output

os.mkdir("out")
os.mkdir("results")
genomes=glob.glob(os.path.join(GENOMEDIR, '*.faa'))
markers=glob.glob(os.path.join(MARKERDIR, "*.hmm"))
FNULL = open(os.devnull, 'w')

# Run HMMs
for genome in genomes: 
    name=os.path.basename(genome).replace(".faa", "").strip().splitlines()[0]
    dir=name
    os.mkdir("out/"+dir)
    for marker in markers:
        prot=os.path.basename(marker).replace(".hmm", "").strip().splitlines()[0]
        outname= "out/"+dir+"/"+name + "-" + prot + ".out"
        cmd = ["hmmsearch","--cut_tc","--tblout="+outname, marker, genome]
        subprocess.call(cmd, stdout=FNULL)
        print("Running HMMsearch on " + name + " and " + prot + " marker")

# Parse HMM file to results matrix/dataframe
print("Parsing all results...")
all_dicts={}
result_dirs = os.walk("out/")
for path, dirs, files in result_dirs:
    genome_dict={}
    for file in files:
        genome = file.split("-")[0]
        prot = file.replace(".out", "").split("-")[1]
        result = "out/"+genome+"/"+file
        with open(result, "rU") as input:
            for qresult in SearchIO.parse(input, "hmmer3-tab"):
                hits = qresult.hits
                num_hits = len(hits)
                genome_dict[prot] = num_hits
                all_dicts[os.path.basename(file).split("-")[0]]=genome_dict
df=pd.DataFrame.from_dict(all_dicts, orient="index", dtype=None)

# Reformat dataframe in order of marker function, find markers in none of the genomes and input NaN for all
all_cols=[]
absent_cols=[]
existing_markers = df.columns
for marker in markers:
    prot=os.path.basename(marker).replace(".hmm", "")
    if prot not in existing_markers:
        all_cols.append(prot)
for col in existing_markers:
    all_cols.append(col)
df_all=df.reindex(columns=all_cols)
df_all.fillna(0, inplace=True)
df_all.to_csv(OUTFILE)