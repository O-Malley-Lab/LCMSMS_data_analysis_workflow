import os
from os.path import join as pjoin
import pandas as pd
import py4cytoscape as p4c
import numpy as np
"""""""""""""""""""""""""""""""""""""""""""""
!!! Prior to running, you need to manually open Cytoscape !!!
"""""""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""""""""""
Functions
"""""""""""""""""""""""""""""""""""""""""""""
def node_table_add_columns(df, cols_to_keep, network_suid, key_col_df, key_col_node='name'):
    """
    df: pandas dataframe
        Data table with new data columns to add
    key_col: str
    network_suid: int
        Cytoscape network SUID to add the columns to

    return: None
    """
    # Change data type of key_col column of df to string, to match shared name of node table
    df[key_col_df] = df[key_col_df].astype(str)

    # Specify columns to keep
    df = df[cols_to_keep]

    # Load data into the node table
    p4c.tables.load_table_data(df, data_key_column=key_col_df, table_key_column=key_col_node, network=network_suid)
    return

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
cytoscape_style_filename = 'styles_7.xml'

# MetaboAnalyst Outputs of Interest
metaboanalyst_output_folder_name = 'MetaboAnalystR_Output'
metaboanalyst_log2FC_filename_post_str = "_fold_change.csv"
metaboanalyst_ttest_filename_post_str = "_t_test.csv"
metaboanalyst_norm_peak_area_filename_post_str = "_normalized_data_transposed.csv"

# Columns from MetaboAnalyst Outputs to add to Cytoscape node table
log2fc_cols_to_keep = ['shared_name', 'log2.FC.']
t_test_cols_to_keep = ['shared_name', 'p.value']

# Cytoscape column names to keep (and their order) in the exported node table (input for filtering script)
cytoscape_cols_to_keep = [
    'shared name', 'precursor mass', 'RTMean', 'Best Ion', 'GNPSGROUP:EXP', 'GNPSGROUP:CTRL', 'log2.FC.', 'p.value', 'number of spectra', 'Compound_Name', 'GNPSLibraryURL', 'Analog:MQScore', 'SpectrumID', 'Analog:SharedPeaks', 'Instrument', 'PI', 'MassDiff', 'GNPSLinkout_Network', 'GNPSLinkout_Cluster', 'cluster index', 'sum(precursor intensity)', 'NODE_TYPE', 'neutral M mass', 'Correlated Features Group ID', 'componentindex', 'Annotated Adduct Features ID', 'ATTRIBUTE_GROUP'
    ]

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
Import GNPS Quant Data (raw Peak Area values)
"""""""""""""""""""""""""""""""""""""""""""""
# From temp folder, import the GNPS quant data (job_name + "_gnps_quant.csv")
gnps_quant_filename = job_name + '_gnps_quant.csv'
gnps_quant_data = pd.read_csv(pjoin(temp_job_folder, gnps_quant_filename))
# Sort by 'row ID'
gnps_quant_data = gnps_quant_data.sort_values(by='row ID')
# Identify peak area columns to keep (column name ends in Peak area)
peak_area_cols_to_keep = ['row ID']
peak_area_cols_raw_data = [col for col in gnps_quant_data.columns if col.endswith('Peak area')]
peak_area_cols_to_keep.extend(peak_area_cols_raw_data)
# Add peak_area_cols_to_keep to cytoscape_cols_to_keep
cytoscape_cols_to_keep.extend(peak_area_cols_to_keep)
# Load peak area data into the node table
node_table_add_columns(gnps_quant_data, peak_area_cols_to_keep, network_suid, 'row ID')


"""""""""""""""""""""""""""""""""""""""""""""
Import MetaboAnalyst Data
"""""""""""""""""""""""""""""""""""""""""""""
# Import and load log2fc data. Values >0 are upregulated in EXP.
log2fc_filename = job_name + metaboanalyst_log2FC_filename_post_str
log2fc_data = pd.read_csv(pjoin(temp_job_folder, metaboanalyst_output_folder_name, log2fc_filename))
node_table_add_columns(log2fc_data, log2fc_cols_to_keep, network_suid, 'shared_name')

# Import and load t-test data. Values <0.05 are significant.
t_test_filename = job_name + metaboanalyst_ttest_filename_post_str
t_test_data = pd.read_csv(pjoin(temp_job_folder, metaboanalyst_output_folder_name, t_test_filename))
node_table_add_columns(t_test_data, t_test_cols_to_keep, network_suid, 'shared_name')

# Import normalized peak area data
norm_peak_area_filename = job_name + metaboanalyst_norm_peak_area_filename_post_str
norm_peak_area_data = pd.read_csv(pjoin(temp_job_folder, metaboanalyst_output_folder_name, norm_peak_area_filename))
# Keep all normalized peak area columns except for MetaboAnalyst_ID
norm_peak_area_data = norm_peak_area_data.drop(columns=['MetaboAnalyst_ID'])
# Rename normalized data columns (not shared_name) to end with '_normalized'
norm_peak_area_data.columns = [col + '_normalized' if col != 'shared_name' else col for col in norm_peak_area_data.columns]
norm_data_cols_to_keep = norm_peak_area_data.columns
# Add norm_data_cols_to_keep to cytoscape_cols_to_keep
cytoscape_cols_to_keep.extend(norm_data_cols_to_keep)
# Load normalized peak area data into the node table
node_table_add_columns(norm_peak_area_data, norm_data_cols_to_keep, network_suid, 'shared_name')


"""""""""""""""""""""""""""""""""""""""""""""
Generate log10 values of Peak Area and Average Peak Area Columns
"""""""""""""""""""""""""""""""""""""""""""""
# Generate log10 values of the peak area columns (peak_area_cols_raw_data). Label as the original column name with '_log10'
log10_peak_area_cols = [col + '_log10' for col in peak_area_cols_raw_data]
# Add data for log10 values
for col in peak_area_cols_raw_data:
    gnps_quant_data[col + '_log10'] = gnps_quant_data[col].apply(lambda x: None if x == 0 else np.log10(x))

# Add log10_peak_area_cols to cytoscape_cols_to_keep
cytoscape_cols_to_keep.extend(log10_peak_area_cols)

# Add the key column (row ID) to the log10 peak area columns
log10_peak_area_cols.insert(0, 'row ID')

# Load log10 peak area data into the node table
node_table_add_columns(gnps_quant_data, log10_peak_area_cols, network_suid, 'row ID')

# Average peak area columns: GNPSGROUP:CTRL and GNPSGROUP:EXP
# Generate log10 values for average peak area columns (GNPSGROUP:CTRL and GNPSGROUP:EXP). Label as the original column name with '_log10'
avg_peak_area_cols = ['GNPSGROUP:CTRL', 'GNPSGROUP:EXP']
# Get the node table as a dataframe
node_table_temp = p4c.tables.get_table_columns(network=network_suid, table='node')
# Add data for log10 average peak area columns. GNPSGROUP:CTRL and GNPSGROUP:EXP are from the node table, not the gnps_quant_data
avg_peak_area_cols_log10 = []
for col in avg_peak_area_cols:
    new_col = col + '_log10'
    avg_peak_area_cols_log10.append(new_col)
    node_table_temp[new_col] = node_table_temp[col].apply(lambda x: None if x == 0 else np.log10(x))

avg_peak_area_cols_log10.insert(0, 'name')

# Add avg_peak_area_cols with _log10 to cytoscape_cols_to_keep
cytoscape_cols_to_keep.extend(avg_peak_area_cols_log10)

# Load log10 average peak area data into the node table
node_table_add_columns(node_table_temp, avg_peak_area_cols_log10, network_suid, 'name')


"""""""""""""""""""""""""""""""""""""""""""""
Export Entire Node Table
"""""""""""""""""""""""""""""""""""""""""""""
# Export the entire node table to an excel file
node_table = p4c.tables.get_table_columns(network=network_suid, table='node')
# Specify columns and their order to keep in the exported node table
node_table_simplified = node_table.copy()
node_table_simplified = node_table_simplified[cytoscape_cols_to_keep]
# Export the node table to an excel file
node_table_simplified.to_excel(pjoin(temp_job_folder, job_name + '_Cytoscape_node_table.xlsx'), index=False)


"""""""""""""""""""""""""""""""""""""""""""""
Reload the Simplified Node Table into Cytoscape to Replace the Current Node Table
"""""""""""""""""""""""""""""""""""""""""""""
# Delete all columns of the current node table except for 'name', 'SUID', 'shared name', 'selected', which are immutable
node_table_cols_complex = p4c.tables.get_table_column_names(network=network_suid, table='node')
node_table_cols_complex.remove('name')
node_table_cols_complex.remove('SUID')
node_table_cols_complex.remove('shared name')
node_table_cols_complex.remove('selected')

for col in node_table_cols_complex:
    p4c.tables.delete_table_column(col, table='node', network=network_suid)

# Load the simplified node table into Cytoscape
p4c.tables.load_table_data(node_table_simplified, data_key_column='name', table_key_column='name', network=network_suid)


"""""""""""""""""""""""""""""""""""""""""""""
Set Visual Style
"""""""""""""""""""""""""""""""""""""""""""""
# Import the style from the cytoscape_inputs_folder
p4c.import_visual_styles(pjoin(cytoscape_inputs_folder, cytoscape_style_filename))

# identify the file extension in cytoscape_style_filename and remove to generate cytoscape_style_name
cytoscape_style_name = cytoscape_style_filename.split('.')[0]

# Set the visual style to cystocape_style_filename, without the file extension in the cytoscape_style_filename
p4c.set_visual_style(cytoscape_style_name)

# For each job folder in input folder, print the job name
for job_folder in os.listdir(INPUT_FOLDER):
    print(job_folder)