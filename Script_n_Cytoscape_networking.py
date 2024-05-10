import os
from os.path import join as pjoin
import xlsxwriter
import pandas as pd
import py4cytoscape as p4c

"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from INPUT_FOLDER to get relevant parameters for job to run. Use the excel tab "Job to Run"
METADATA_OVERALL_FILENAME = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
METADATA_JOB_TAB = 'Job to Run'

# GNPS Output folder (later, change this to be just the job_name in TEMP_OVERALL_FOLDER, rather than a testing folder)

"""""""""""""""""""""""""""""""""""""""""""""
Get Job Info
"""""""""""""""""""""""""""""""""""""""""""""
# Import metadata table for job
metadata = pd.read_excel(pjoin(INPUT_FOLDER, METADATA_OVERALL_FILENAME), sheet_name = METADATA_JOB_TAB)

# Extract relevant information
job_name = metadata['Job Name'][0]
control_folder_name = metadata['Control Folder'][0]
ionization = metadata['Ionization'][0]
exp_rep_num = metadata['EXP num replicates'][0]
ctrl_rep_num = metadata['CTRL num replicates'][0]

# Define temp_folder (job_name folder in TEMP_OVERALL_FOLDER)
temp_job_folder = pjoin(TEMP_OVERALL_FOLDER, job_name)

"""""""""""""""""""""""""""""""""""""""""""""
Import GNPS Outputs
"""""""""""""""""""""""""""""""""""""""""""""
# GNPS Outputs in temp_folder
# 