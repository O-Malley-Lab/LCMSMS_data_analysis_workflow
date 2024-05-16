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

# MetaboAnalyst Outputs of Interest
metaboanalyst_output_folder_name = 'MetaboAnalystR_Output'
metaboanalyst_log2FC_filename_post_str = "_fold_change.csv"
metaboanalyst_ttest_filename_post_str = "_t_test.csv"
metaboanalyst_norm_peak_area_filename_post_str = "_normalized_data_transposed.csv"

# Columns from MetaboAnalyst Outputs to add to Cytoscape node table
log2fc_cols_to_keep = ['shared_name', 'log2.FC.']
t_test_cols_to_keep = ['shared_name', 'p.value']

# Cytoscape column names to keep (and their order) in the exported node table (input for filtering script)
cytoscape_cols_to_keep = ['shared name', 'precursor mass', 'RTMean', 'Best Ion', 'GNPSGROUP:EXP', 'GNPSGROUP:CTRL', 'log2.FC.', 'p.value', 'number of spectra', 'GNPSLibraryURL', 'Analog:MQScore', 'SpectrumID', 'Analog:SharedPeaks', 'Instrument', 'PI', 'MassDiff', 'GNPSLinkout_Network', 'GNPSLinkout_Cluster', 'cluster index', 'sum(precursor intensity)', 'NODE_TYPE', 'neutral M mass', 'Correlated Features Group ID', 'componentindex', 'Annotated Adduct Features ID', 'ATTRIBUTE_GROUP']

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
# Destroy any networks already in the Cytsocape session
p4c.networks.delete_all_networks()

# GNPS Outputs are located in temp_folder
# Find the .graphml file in the GNPS output folder. Upload into Cytoscape
gnps_graphml_file = [f for f in os.listdir(gnps_output_folder) if f.endswith('.graphml')][0]

# Import the GNPS output into Cytoscape
p4c.import_network_from_file(pjoin(gnps_output_folder, gnps_graphml_file))

# Assuming 'network_suid' is the SUID of the network you want to rename
p4c.networks.rename_network(job_name)

# Get the SUID of the network
network_suid = p4c.networks.get_network_suid(job_name)


"""""""""""""""""""""""""""""""""""""""""""""
Import MetaboAnalyst Data
"""""""""""""""""""""""""""""""""""""""""""""
# Import log2fc data. Values >0 are upregulated in EXP.
log2fc_filename = job_name + metaboanalyst_log2FC_filename_post_str
log2fc_data = pd.read_csv(pjoin(temp_job_folder, metaboanalyst_output_folder_name, log2fc_filename))

# Import t-test data. Values <0.05 are significant.
t_test_filename = job_name + metaboanalyst_ttest_filename_post_str
t_test_data = pd.read_csv(pjoin(temp_job_folder, metaboanalyst_output_folder_name, t_test_filename))

# Import normalized peak area data
norm_peak_area_filename = job_name + metaboanalyst_norm_peak_area_filename_post_str
norm_peak_area_data = pd.read_csv(pjoin(temp_job_folder, metaboanalyst_output_folder_name, norm_peak_area_filename))

# Indicate which columns to keep in the imported MetaboAnalyst data
log2fc_data = log2fc_data[log2fc_cols_to_keep]
t_test_data = t_test_data[t_test_cols_to_keep]
# Keep all normalized peak area columns except for MetaboAnalyst_ID
norm_peak_area_data = norm_peak_area_data.drop(columns=['MetaboAnalyst_ID'])

# Rename normalized data columns (not shared_name) to end with '_normalized'
norm_peak_area_data.columns = [col + '_normalized' if col != 'shared_name' else col for col in norm_peak_area_data.columns]
norm_data_cols_to_keep = norm_peak_area_data.columns
# Add norm_data_cols_to_keep to cytoscape_cols_to_keep
cytoscape_cols_to_keep.extend(norm_data_cols_to_keep)

# For all tables, change data type of 'shared_name' column to strings, in order to match the data type in the Cytoscape network
log2fc_data['shared_name'] = log2fc_data['shared_name'].astype(str)
t_test_data['shared_name'] = t_test_data['shared_name'].astype(str)
norm_peak_area_data['shared_name'] = norm_peak_area_data['shared_name'].astype(str)

# Line up the data against the nodes in the network
# 'shared name' is the key column that we will use to align the data. table='node' by default. table_key_column='name' by default, and 'name' is the same as 'shared name'
p4c.tables.load_table_data(log2fc_data, data_key_column='shared_name',network=network_suid)
p4c.tables.load_table_data(t_test_data, data_key_column='shared_name',network=network_suid)
p4c.tables.load_table_data(norm_peak_area_data, data_key_column='shared_name',network=network_suid)

# print data type of values in log2fc_data column shared_name
print(log2fc_data['shared_name'].dtype)

"""""""""""""""""""""""""""""""""""""""""""""
Export Entire Node Table
"""""""""""""""""""""""""""""""""""""""""""""
# Export the entire node table to an excel file
node_table = p4c.tables.get_table_columns(network=network_suid, table='node')
# Specify columns and their order to keep in the exported node table
node_table = node_table[cytoscape_cols_to_keep]
# Export the node table to an excel file
node_table.to_excel(pjoin(temp_job_folder, job_name + '_Cytoscape_node_table.xlsx'), index=False)


"""""""""""""""""""""""""""""""""""""""""""""
Set Visual Style
"""""""""""""""""""""""""""""""""""""""""""""
# Import the style from the cytoscape_inputs_folder
p4c.import_visual_styles(pjoin(cytoscape_inputs_folder, cytoscape_style_filename))

# identify the file extension in cytoscape_style_filename and remove to generate cytoscape_style_name
cytoscape_style_name = cytoscape_style_filename.split('.')[0]

# Set the visual style to cystocape_style_filename, without the file extension in the cytoscape_style_filename
p4c.set_visual_style(cytoscape_style_name)






