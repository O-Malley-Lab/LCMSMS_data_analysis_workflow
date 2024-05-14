import os
from os.path import join as pjoin
import xlsxwriter
import pandas as pd
import py4cytoscape as p4c
"""""""""""""""""""""""""""""""""""""""""""""
!!! Prior to running, you need to manually open Cytoscape !!!
"""""""""""""""""""""""""""""""""""""""""""""


"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from INPUT_FOLDER to get relevant parameters for job to run. Use the excel tab "Job to Run"
METADATA_OVERALL_FILENAME = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
METADATA_JOB_TAB = 'Job to Run'

# GNPS Output folder (later, change this to be just the job_name in TEMP_OVERALL_FOLDER (=temp_job_folder), rather than a testing folder)
gnps_output_folder = pjoin(TEMP_OVERALL_FOLDER, 'Anid_HE_TJGIp11_pos_20210511_manual_GNPS_output_download')

cytoscape_inputs_folder_name = 'Cytoscape_inputs'

# Cytoscape style .xml filename (located in cytoscape_inputs_folder)
cytoscape_style_filename = 'styles_6.xml'

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

# Define cytoscape inputs folder 
cytoscape_inputs_folder = pjoin(INPUT_FOLDER, 'Cytoscape_inputs')

"""""""""""""""""""""""""""""""""""""""""""""
Open Cytoscape network from GNPS output .graphml
"""""""""""""""""""""""""""""""""""""""""""""
# GNPS Outputs are located in temp_folder

# Find the .graphml file in the GNPS output folder. Upload into Cytoscape
gnps_graphml_file = [f for f in os.listdir(gnps_output_folder) if f.endswith('.graphml')][0]

# Import the GNPS output into Cytoscape
p4c.import_network_from_file(pjoin(gnps_output_folder, gnps_graphml_file))

# Assuming 'network_suid' is the SUID of the network you want to rename
p4c.networks.rename_network(job_name)

"""""""""""""""""""""""""""""""""""""""""""""
Set Visual Style
"""""""""""""""""""""""""""""""""""""""""""""
# Import the style from the cytoscape_inputs_folder
p4c.import_visual_styles(pjoin(cytoscape_inputs_folder, cytoscape_style_filename))

# identify the file extension in cytoscape_style_filename and remove to generate cytoscape_style_name
cytoscape_style_name = cytoscape_style_filename.split('.')[0]

# Set the visual style to cystocape_style_filename, without the file extension in the cytoscape_style_filename
p4c.set_visual_style(cytoscape_style_name)

# to-do: import MetaboAnalyst outputs to align

