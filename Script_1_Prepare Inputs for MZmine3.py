"""
LCMSMS Data Analysis Workflow, Script 1: Prepare Inputs for MZmine3

@author: Lazarina Butkovich

Features include:
    Create metadata .tsv file in temp folder
"""
import pandas as pd
import os
from os.path import join as pjoin

"""
Values
""" 
input_folder = r'input' 
temp_folder = r'temp'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from input_folder to get relevant parameters for job to run. Use the excel tab "Job to Run"
metadata_filename = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
metadata_job_tab = 'Job to Run'

"""
Create GNPS and MetaboAnalyst Metadata .tsv files
"""
# Import metadata table for job
metadata = pd.read_excel(pjoin(input_folder, metadata_filename), sheet_name = metadata_job_tab)

# Extract relevant information
job_name = metadata['Job Name'][0]
ionization = metadata['Ionization'][0]
exp_rep_num = metadata['EXP num replicates'][0]
ctrl_rep_num = metadata['CTRL num replicates'][0]

# Format of metadata .tsv: two columns, Filename and Class. List the filenames from folder Job Name, where filenames with 'CTRL' in them are in the 'CTRL' class and filenames without 'CTRL' in them are in the 'EXP' class.
# Create metadata .tsv file in temp folder
metadata_filename = job_name + '_metadata.tsv'
metadata_filepath = pjoin(temp_folder, metadata_filename)

# Use pandas to create metadata .tsv file
metadata_df = pd.DataFrame(columns = ['Filename', 'Class'])
# Make list of filenames in ctrl_folder_name
mzml_filenames = os.listdir(pjoin(input_folder, job_name))
ctrl_filenames = [filename for filename in mzml_filenames if filename.endswith('.mzML') and 'CTRL' in filename]
# Make list of filenames in exp_folder_name
exp_filenames = [filename for filename in mzml_filenames if filename.endswith('.mzML') and 'CTRL' not in filename]

# Add filenames to metadata_df
metadata_df['Filename'] = ctrl_filenames + exp_filenames
metadata_df['Class'] = ['CTRL']*len(ctrl_filenames) + ['EXP']*len(exp_filenames)
metadata_df.to_csv(metadata_filepath, sep = '\t', index = False)


