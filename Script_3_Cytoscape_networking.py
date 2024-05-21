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

def write_table_to_excel(writer, df, sheet_name):
    """
    Write a dataframe to an excel sheet. The column width will be set to the size of the header text.

    Inputs:
    writer: ExcelWriter object
    df: DataFrame to write to the sheet
    sheet_name: Name of the sheet to write to

    return: None
    """
    df.to_excel(writer, sheet_name = sheet_name, index = False)
    # Format the excel sheets so that the column width matches the size of the header text
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df):  # loop through all columns
        series = df[col]
        # Set max_len to the length of only the header text
        max_len = len(str(series.name)) + 1
        worksheet.set_column(idx, idx, max_len)  # set column width
    return
   
def format_column(worksheet, df):
    for idx, col in enumerate(df):  # loop through all columns
        series = df[col]
        # Set max_len to the length of only the header text
        max_len = len(str(series.name)) + 1
        worksheet.set_column(idx, idx, max_len)  # set column width
        # Make the top header "sticky" so that it is always visible
        worksheet.freeze_panes(1, 0)
    return

"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
OUTPUT_FOLDER = r'output'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from INPUT_FOLDER to get relevant parameters for job to run. Use the excel tab "Job to Run"
METADATA_OVERALL_FILENAME = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
METADATA_JOB_TAB = 'Job to Run'

# GNPS Output folder (later, change this to be just the job_name in TEMP_OVERALL_FOLDER, rather than a testing folder)
gnps_output_folder = pjoin(TEMP_OVERALL_FOLDER, 'Anid_HE_TJGIp11_pos_20210511_manual_GNPS_output_download')

cytoscape_inputs_folder_name = 'Cytoscape_inputs'

# Cytoscape style .xml filenames (located in cytoscape_inputs_folder)
cytoscape_style_filename = 'styles_7.xml'
cytoscape_style_filtered_filename = 'styles_7_filter_node_emphasis.xml'

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
    'shared name', 'precursor mass', 'RTMean', 'Best Ion', 'GNPSGROUP:EXP', 'GNPSGROUP:CTRL', 'log2.FC.', 'p.value', 'number of spectra', 'Compound_Name', 'GNPSLibraryURL', 'Analog:MQScore', 'SpectrumID', 'Analog:SharedPeaks', 'Instrument', 'PI', 'MassDiff', 'GNPSLinkout_Network', 'GNPSLinkout_Cluster', 'componentindex', 'sum(precursor intensity)', 'NODE_TYPE', 'neutral M mass', 'Correlated Features Group ID', 'Annotated Adduct Features ID', 'ATTRIBUTE_GROUP'
    ]

# Filtering Parameters
CTRL_LOG10_CUTOFF = 5 # Log10 of CTRL must be less than this value
RATIO_CUTOFF = 3 # Ratio of EXP to CTRL must be greater than this value
EXP_LOG10_CUTOFF = 5 # Log10 of EXP must be greater than this value

# Filters for upregulated likely host metabolites
HOST_CTRL_LOG10_CUTOFF = 3 # Log10 of CTRL must be greater than this value
HOST_RATIO_CUTOFF = 10 # Ratio of EXP to CTRL must be greater than this value

# Set deviation amounts for RT and m/z (for identifying specific peaks, such as standards)
MZ_DEV = 0.1
RT_DEV = 0.5

# Standard Peaks
# ABMBA standard peak
ABMBA_MZ_POS  = 229.9811 #m/z 229.9811
ABMBA_RT_POS = 4.685 #4.685 minutes
# ABMBA_MZ_NEG = 227.9655 #m/z 227.9655
# ABMBA_RT_NEG = 4.8 #4.8 min

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Main Part 1: Prepare Cytoscape Network and Format Node Table
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
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
gnps_quant_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, gnps_quant_filename))
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
log2fc_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, metaboanalyst_output_folder_name, log2fc_filename))
node_table_add_columns(log2fc_data, log2fc_cols_to_keep, network_suid, 'shared_name')

# Import and load t-test data. Values <0.05 are significant.
t_test_filename = job_name + metaboanalyst_ttest_filename_post_str
t_test_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, metaboanalyst_output_folder_name, t_test_filename))
node_table_add_columns(t_test_data, t_test_cols_to_keep, network_suid, 'shared_name')

# Import normalized peak area data
norm_peak_area_filename = job_name + metaboanalyst_norm_peak_area_filename_post_str
norm_peak_area_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, metaboanalyst_output_folder_name, norm_peak_area_filename))
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

# Generate a EXP:CTRL_ratio column
node_table_temp['EXP:CTRL_ratio'] = node_table_temp['GNPSGROUP:EXP'] / node_table_temp['GNPSGROUP:CTRL']
# Replace inf values with a large number [np.inf, -np.inf], 10000000000 (E10)
node_table_temp['EXP:CTRL_ratio'] = node_table_temp['EXP:CTRL_ratio'].replace([np.inf, -np.inf], 10000000000)
# Round to 2 decimal places
node_table_temp['EXP:CTRL_ratio'] = node_table_temp['EXP:CTRL_ratio'].apply(lambda x: round(x, 2))
# Add EXP:CTRL_ratio to cytoscape_cols_to_keep
cytoscape_cols_to_keep.append('EXP:CTRL_ratio')
# Load EXP:CTRL_ratio data into the node table
node_table_add_columns(node_table_temp, ['name', 'EXP:CTRL_ratio'], network_suid, 'name')
# Reset index
node_table_temp = node_table_temp.reset_index(drop=True)


"""""""""""""""""""""""""""""""""""""""""""""
Export Entire Node Table
"""""""""""""""""""""""""""""""""""""""""""""
# Export the entire node table to an excel file
node_table = p4c.tables.get_table_columns(network=network_suid, table='node')
# Specify columns and their order to keep in the exported node table
node_table_simplified = node_table.copy()
node_table_simplified = node_table_simplified[cytoscape_cols_to_keep]
# Export the node table to an excel file
node_table_simplified.to_excel(pjoin(TEMP_OVERALL_FOLDER, job_name, job_name + '_Cytoscape_node_table.xlsx'), index=False)


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


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Main Part 2: Filtering Script for Output Excel
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
Copy the node table to filter for peaks of interest
"""
table_filtered = node_table.copy()

# First, filter for peaks that have a GNPSGROUP:CTRL_log10 less than the cutoff
table_filtered = table_filtered[table_filtered['GNPSGROUP:CTRL_log10'] < CTRL_LOG10_CUTOFF]

# Second, filter for peaks that have a GNPSGROUP:EXP_log10 greater than the cutoff
table_filtered = table_filtered[table_filtered['GNPSGROUP:EXP_log10'] > EXP_LOG10_CUTOFF]

# Third, filter for peaks that have a EXP:CTRL_ratio greater than the cutoff
table_filtered = table_filtered[table_filtered['EXP:CTRL_ratio'] > RATIO_CUTOFF]

# Sort table_filtered in descending order by GNPSGROUP:EXP_log10
table_filtered = table_filtered.sort_values(by = 'GNPSGROUP:EXP_log10', ascending = False)
# Reset index
table_filtered = table_filtered.reset_index(drop = True)


"""
Create new dataframe of upregulated likely host metabolites
"""
table_host_upreg = node_table.copy()

# First, filter for peaks that have a GNPSGROUP:CTRL_log10 greater than the cutoff
table_host_upreg = table_host_upreg[table_host_upreg['GNPSGROUP:CTRL_log10'] > HOST_CTRL_LOG10_CUTOFF]

# Second, filter for peaks that have a EXP:CTRL_ratio greater than the HOST_RATIO_CUTOFF
table_host_upreg = table_host_upreg[table_host_upreg['EXP:CTRL_ratio'] > HOST_RATIO_CUTOFF]

# Sort table_host_upreg in descending order by GNPSGROUP:EXP_log10
table_host_upreg = table_host_upreg.sort_values(by = 'GNPSGROUP:EXP_log10', ascending = False)
# Reset index
table_host_upreg = table_host_upreg.reset_index(drop = True)


"""
Write a table listing potential ABMBA standard peaks
"""
table_ABMBA = node_table.copy()

# First, filter for peaks that have a m/z ('precursor mass') within the deviation of the ABMBA standard m/z
table_ABMBA = table_ABMBA[(table_ABMBA['precursor mass'] > ABMBA_MZ_POS - MZ_DEV) & (table_ABMBA['precursor mass'] < ABMBA_MZ_POS + MZ_DEV)]

# Second, filter for peaks that have a RT ('RTMean') within the deviation of the ABMBA standard RT
table_ABMBA = table_ABMBA[(table_ABMBA['RTMean'] > ABMBA_RT_POS - RT_DEV) & (table_ABMBA['RTMean'] < ABMBA_RT_POS + RT_DEV)]

# Sort table_ABMBA in ascending order by name
table_ABMBA = table_ABMBA.sort_values(by = 'name', ascending = True)
# Reset index
table_ABMBA = table_ABMBA.reset_index(drop = True)


"""
Write a table with all peaks with compound matches to databases. This includes potential primary metabolites. Have a version without suspect compounds and a version with suspect compounds.
"""
table_all_matched_cmpds= node_table.copy()

# First, filter for peaks that have a 'Compound_Name' that is not NaN
table_all_matched_cmpds = table_all_matched_cmpds[table_all_matched_cmpds['Compound_Name'].notna()]

# table_matched_cmpds_no_suspect is table_all_matched_cmpds with any 'Compound_Name' that contains string 'Suspect' removed
table_matched_cmpds_no_suspect = table_all_matched_cmpds.copy()
table_matched_cmpds_no_suspect = table_all_matched_cmpds[~table_all_matched_cmpds['Compound_Name'].str.contains('Suspect', na = False)]


"""
Formatted Simplest Table
"""
# Make an easy-to-read formatted table with all peaks
columns_of_interest = ['shared name', 'precursor mass', 'RTMean', 'log2.FC.', 'p.value', 'GNPSGROUP:EXP','GNPSGROUP:CTRL', 'GNPSGROUP:EXP_log10','GNPSGROUP:CTRL_log10', 'EXP:CTRL_ratio', 'Best Ion', 'GNPSLinkout_Cluster','Compound_Name','Analog:MQScore'] 

table_formatted = node_table[columns_of_interest].copy()

# Make the values in "GNPSGROUP:EXP","GNPSGROUP:CTRL", "GNPSGROUP:EXP_log10","GNPSGROUP:CTRL_log10", 'EXP:CTRL_ratio' be in scientific notation and rounded to 2 decimal places
columns_sci_notation = ['GNPSGROUP:EXP','GNPSGROUP:CTRL', 'p.value']
# Make in scientific notation and round to 2 decimal places
table_formatted[columns_sci_notation] = table_formatted[columns_sci_notation].applymap(lambda x: '{:.2e}'.format(x))

columns_to_round = ['log2.FC.','GNPSGROUP:EXP_log10','GNPSGROUP:CTRL_log10']
# Round to 2 decimal places
table_formatted[columns_to_round] = table_formatted[columns_to_round].applymap(lambda x: round(x, 2))


"""
Make a table of the parameters used in this script
"""
parameters = pd.DataFrame({'Parameter': ['CTRL_LOG10_CUTOFF', 'RATIO_CUTOFF', 'EXP_LOG10_CUTOFF', 'HOST_CTRL_LOG10_CUTOFF', 'HOST_RATIO_CUTOFF', 'MZ_DEV', 'RT_DEV','ABMBA_MZ_POS','ABMBA_RT_POS'], 'Value': [CTRL_LOG10_CUTOFF, RATIO_CUTOFF, EXP_LOG10_CUTOFF, HOST_CTRL_LOG10_CUTOFF, HOST_RATIO_CUTOFF, MZ_DEV, RT_DEV, ABMBA_MZ_POS, ABMBA_RT_POS]})


"""
Write each dataframe to a different sheet in output excel
"""
output_filename = job_name + '_Filtered_Peaks_of_Interest.xlsx'
# If it does not exist already, create a folder for job_name in the output folder
if not os.path.exists(pjoin(OUTPUT_FOLDER, job_name)):
    os.makedirs(pjoin(OUTPUT_FOLDER, job_name))

# https://xlsxwriter.readthedocs.io/example_pandas_multiple.html
writer = pd.ExcelWriter(pjoin(OUTPUT_FOLDER, job_name, output_filename), engine='xlsxwriter')

# Write each dataframe to a different sheet (with no index column)
table_formatted.to_excel(writer, sheet_name = 'All Peaks Simple', index = False)
node_table.to_excel(writer, sheet_name = 'All', index = False)
table_filtered.to_excel(writer, sheet_name = 'Filtered Peaks of Interest', index = False)
table_host_upreg.to_excel(writer, sheet_name = 'Upreg Likely Host Metabolites', index = False)
table_all_matched_cmpds.to_excel(writer, sheet_name = 'All Cmpd Matches', index = False)
table_matched_cmpds_no_suspect.to_excel(writer, sheet_name = 'Cmpd Matches No Sus', index = False)
table_ABMBA.to_excel(writer, sheet_name = 'ABMBA Standard', index = False)
parameters.to_excel(writer, sheet_name = 'Filter Parameters', index = False)

# Format the excel sheets so that the column width matches the size of the header text
workbook = writer.book
# For each table and corresponding excel tab, format width
for sheet_name in writer.sheets:
    worksheet = writer.sheets[sheet_name]
    if sheet_name == 'All Peaks Simple':
        format_column(worksheet, table_formatted)
    elif sheet_name == 'All':
        format_column(worksheet, node_table)
    elif sheet_name == 'Filtered Peaks of Interest':
        format_column(worksheet, table_filtered)
    elif sheet_name == 'Upreg Likely Host Metabolites':
        format_column(worksheet, table_host_upreg)
    elif sheet_name == 'All Cmpd Matches':
        format_column(worksheet, table_all_matched_cmpds)
    elif sheet_name == 'Cmpd Matches No Sus':
        format_column(worksheet, table_matched_cmpds_no_suspect)
    elif sheet_name == 'ABMBA Standard':
        format_column(worksheet, table_ABMBA)
    elif sheet_name == 'Filter Parameters':
        format_column(worksheet, parameters)
    else:
        print('Error: sheet name ' + sheet_name + ' not recognized; column width not formatted. Consider adjusting script to include target sheet.')

# Close the Pandas Excel writer and output the Excel file. XlsxWriter object has no attribute 'save'. Use 'close' instead
writer.close()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Main Part 3: Create Filtered Cytoscape Networks for Peaks of Interest
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Copy the network to a new network for the following filtered tables: table_filtered, table_host_upreg, table_matched_cmpds_no_suspect

# Create a new network for each filtered table
# Filtered Peaks of Interest
# p4c.networks.create_from(network=network_suid, base_network_name=job_name + '_Filtered_Peaks_of_Interest')
# # Upregulated Likely Host Metabolites
# p4c.networks.create_from(network=network_suid, base_network_name=job_name + '_Upreg_Likely_Host_Metabolites')
# # All Compound Matches
# p4c.networks.create_from(network=network_suid, base_network_name=job_name + '_All_Cmpd_Matches')
# # Compound Matches without Suspect
# p4c.networks.create_from(network=network_suid, base_network_name=job_name + '_Cmpd_Matches_No_Suspect')



# Get the SUID of the new networks
# network_filtered_suid = p4c.networks.get_network_suid(job_name + '_Filtered_Peaks_of_Interest')
# network_host_upreg_suid = p4c.networks.get_network_suid(job_name + '_Upreg_Likely_Host_Metabolites')
# network_all_cmpd_suid = p4c.networks.get_network_suid(job_name + '_All_Cmpd_Matches')
# network_cmpd_no_sus_suid = p4c.networks.get_network_suid(job_name + '_Cmpd_Matches_No_Suspect')

# # Filter the new networks based on the filtered tables. Keep 'componentindex' values that appear in the corresponding table
# # Filtered Peaks of Interest
# componentindex_to_keep = table_filtered['componentindex'].tolist()
# # If there are repeats of the same componentindex, remove duplicates
# componentindex_to_keep = list(set(componentindex_to_keep))
# # Filter the network for the componentindex in componentindex_to_keep
# # p4c.filter.create('componentindex', 'in', componentindex_to_keep, network=network_filtered_suid)

"""
Run test Cytoscape filter first
"""
# Copy the original network to a new network for the test filter. clone_network returns new SUID.
network_test_filter_suid = p4c.clone_network()

# Create a pandas of TRUE and FALSE values for the nodes to keep, with keys of shared name. We will keep nodes that have a 'EXP:CTRL_ratio' greater than the RATIO_CUTOFF
nodes_to_keep = node_table_temp['EXP:CTRL_ratio'] > RATIO_CUTOFF

# Get the list of componentindex values to keep
componentindex_to_keep = node_table_temp[nodes_to_keep]['componentindex'].tolist()
# If there are repeats of the same componentindex, remove duplicates
componentindex_to_keep = list(set(componentindex_to_keep))
# Make a pandas of true and false values for the nodes to keep, with keys of shared name.
nodes_to_keep_componentindex = node_table_temp['componentindex'].isin(componentindex_to_keep)

# Create list of nodes_to_keep and nodes_to_keep_componentindex to be lists of TRUE and FALSE values for the nodes/clusters to keep.
nodes_to_keep_list = nodes_to_keep.tolist()
nodes_to_keep_componentindex = nodes_to_keep_componentindex.tolist()

# Fetch list of componentindex values
componentindex_list = node_table_temp['componentindex'].tolist()

# Create filter dataframe with one column of shared name, and two columns of TRUE and FALSE values, one column for nodes to keep and one column for componentindex to keep.
filter_df = pd.DataFrame({'shared name': node_table_temp['name'], 'componentindex': componentindex_list, 'keep_node': nodes_to_keep_list, 'keep_componentindex': nodes_to_keep_componentindex})

# Convert data type of componentindex column to int
filter_df['componentindex'] = filter_df['componentindex'].astype(int)

# For rows with componentindex of -1 AND keep_node of false, set keep_componentindex to false
filter_df.loc[(filter_df['componentindex'] == -1) & (filter_df['keep_node'] == False), 'keep_componentindex'] = False

# Add the 2 lists (nodes and componentindex) of TRUE and FALSE values to the network, using function node_table_add_columns
node_table_add_columns(filter_df, ['shared name', 'keep_componentindex'], network_test_filter_suid, 'shared name')
node_table_add_columns(filter_df, ['shared name', 'keep_node'], network_test_filter_suid, 'shared name')

# Create and apply the filter to the network. Select the nodes to delete.
# https://py4cytoscape.readthedocs.io/en/latest/reference/generated/py4cytoscape.filters.create_column_filter.html#py4cytoscape.filters.create_column_filter
# p4c.create_column_filter(filter_name = 'test_filter', column = 'EXP:CTRL_ratio', criterion = RATIO_CUTOFF, predicate = 'LESS_THAN_OR_EQUAL', type = 'nodes', network = network_test_filter_suid)
p4c.create_column_filter(filter_name = 'test_filter', column = 'keep_componentindex', criterion = False, predicate = 'IS', type = 'nodes', network = network_test_filter_suid)

# The above step only selects nodes that meet the filter criteria. To remove the unselected nodes, use the following command
# https://py4cytoscape.readthedocs.io/en/0.0.10/reference/generated/py4cytoscape.network_selection.delete_selected_nodes.html
p4c.network_selection.delete_selected_nodes(network = network_test_filter_suid)

# Reorganize network to remove gaps
p4c.layout_network('force-directed', network_test_filter_suid)

# For nodes that are in nodes_to_keep, indicate in the network by increasing the node size
# https://py4cytoscape.readthedocs.io/en/latest/reference/generated/py4cytoscape.style_mappings.set_node_size_mapping.html#py4cytoscape.style_mappings.set_node_size_mapping
# p4c.style_mappings.set_node_size_mapping('keep_node', table_column_values = [True, False], sizes = [75, 50], mapping_type = 'd', style_name = cytoscape_style_name, network = network_test_filter_suid)

# # Import style for filtered network
# p4c.import_visual_styles(pjoin(cytoscape_inputs_folder, cytoscape_style_filtered_filename))
# cytoscape_style_name_filtered = cytoscape_style_filtered_filename.split('.')[0]
# # Set new suid to the filtered network style
# p4c.set_visual_style(cytoscape_style_name_filtered, network_test_filter_suid)

# Import the style from the cytoscape_inputs_folder
p4c.import_visual_styles(pjoin(cytoscape_inputs_folder, cytoscape_style_filtered_filename))

# identify the file extension in cytoscape_style_filename and remove to generate cytoscape_style_name
cytoscape_style_filtered_name = cytoscape_style_filtered_filename.split('.')[0]

# Set the visual style to cystocape_style_filename, without the file extension in the cytoscape_style_filename
p4c.set_visual_style(cytoscape_style_filtered_name)

# Rename network
p4c.networks.rename_network(job_name + '_test_filter', network_test_filter_suid)

