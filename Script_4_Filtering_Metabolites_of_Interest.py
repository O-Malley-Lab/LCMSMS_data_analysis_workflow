
"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 4: Filtering Metabolites of Interest

@author: Lazarina Butkovich

Features include:
Output excel with the following:
- All peaks with relevant parameters
- Peaks of interest (based on GNPS FBMN analysis)
- Upregulated likely host metabolites
- Peaks with compound matches to databases
- Peaks with compound matches to databases (excluding suspect compounds)
- Potential ABMBA standard peaks
- Parameters used in this script

"""""""""""""""""""""""""""""""""""""""""""""
"""
This script is designed to pick peaks of interest from GNPS FBMN analyzed
LC-MS/MS data, specifically for positive ionization mode data. The FBMN pipeline requires pre-processing through MZmine. In 
MZmine, you can visually validate peaks of interest. The FBMN pipeline should
ensure similar/same m/z and RT data for (i) GNPS-determined peaks of interest 
and (ii) for the peaks of interest you visually determine from the MZmine TIC
view of your data.
"""

import pandas as pd
import numpy as np
import os
from os.path import join as pjoin


"""""""""""""""""""""""""""""""""""""""""""""
Functions
"""""""""""""""""""""""""""""""""""""""""""""
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


"""""""""""""""""""""""""""""""""""""""""""""
Main
"""""""""""""""""""""""""""""""""""""""""""""
"""
Get Job Name from the metadata file
"""
# Import metadata file
metadata_overall_file = pjoin(INPUT_FOLDER, METADATA_OVERALL_FILENAME)
metadata_overall = pd.read_excel(metadata_overall_file, sheet_name = METADATA_JOB_TAB)

# Extract relevant information
job_name = metadata_overall['Job Name'][0]
control_folder_name = metadata_overall['Control Folder'][0]
ionization = metadata_overall['Ionization'][0]
exp_rep_num = metadata_overall['EXP num replicates'][0]
ctrl_rep_num = metadata_overall['CTRL num replicates'][0]


"""
Import GNPS nodes table
"""
# Located in job_name folder in temp folder
nodes_filename = job_name + '_Cytoscape_node_table.xlsx'
# Import the nodes table as a pandas dataframe
# Note, the nodes table already includes relevent MetaboAnalyst and Peak Area data (See Script 3 Cytoscape file for details). 
nodes_table = pd.read_excel(pjoin(TEMP_OVERALL_FOLDER, job_name, nodes_filename))
# Note that some values in EXP:CTRL_ratio were originally inf but set to E10 for Cytoscape (error raised when inf in value)

# Sort table by name (default ID name in GNPS Cytoscape)
nodes_table = nodes_table.sort_values(by = 'name')

# Reset index
nodes_table = nodes_table.reset_index(drop = True)


"""
Copy the node table to filter for peaks of interest
"""
table_filtered = nodes_table.copy()

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
table_host_upreg = nodes_table.copy()

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
table_ABMBA = nodes_table.copy()

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
table_all_matched_cmpds= nodes_table.copy()

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

table_formatted = nodes_table[columns_of_interest].copy()

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
nodes_table.to_excel(writer, sheet_name = 'All', index = False)
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
        format_column(worksheet, nodes_table)
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