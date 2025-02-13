"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 5: A. nidulans vs. Yeast Heterologous Expression GNPS Analysis
@author: Lazarina Butkovich

This script has the following features for analyzing GNPS output for comparing A. nidulans and Yeast heterologous expression of the same gut fungal proteinID. This script takes GNPS output from the "METABOLOMICS-SNETS-V2" workflow, also known as the "Molecular Networking" data analysis workflow.

In METADATA_FILENAME excel, describe the following:
- Job_Name: Name of the job
- Grouping_Type: 1 = 2 EXP vs CTRL pairs compared, 2 = 3 EXP vs CTRL pairs compared, 3 = 3 EXPs compared to 1 shared CTRL

"""""""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""""""""""
!!! Prior to running, you need to manually open Cytoscape !!!
Additionally, you must download GNPS job result files:
- First, create in GNPS_OUTPUT_FOLDER --> {job folder for POS and NEG}. Folder name template: "Grouping_" + job_name + "_POS" OR "Grouping_" + job_name + "_NEG". These job folders are where you will place GNPS output files per job.
- Second, use "Download Bucket Table" to get raw abundance data values. The script will use these values to filter features for those detected in experimtnal samples and not controls. Only the .tsv bucket file will be used so all other unzipped files can be deleted. 
- Third, use "Download Clustered Spectra as MGF" option. The .graphml file will be in the sub-folder containing "graphml" in its name. The .mgf file can be manually uploaded to SIRIUS after running the script. From this unzip, only the .graphml file will be used by the script.
"""""""""""""""""""""""""""""""""""""""""""""


import os
from os.path import join as pjoin
import pandas as pd
import py4cytoscape as p4c
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple
import time
start = time.time()


"""""""""""""""""""""""""""""""""""""""""""""
Functions
"""""""""""""""""""""""""""""""""""""""""""""
def node_table_add_columns(df, cols_to_keep, network_suid, key_col_df, key_col_node='name'):
    """
    Add new columns to the node table in Cytoscape. The key column values of the dataframe must match up with the key column values of the node table.

    Inputs
    df: pandas dataframe
        Data table with new data columns to add
    cols_to_keep: list of str
        List of column names to keep in the node table
    network_suid: int
        Cytoscape network SUID to add the columns to
    key_col_df: str
        Column name of the key column in the dataframe
    key_col_node: str
        Column name of the key column in the node table

    Outputs
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

    Inputs
    writer: ExcelWriter object
    df: DataFrame to write to the sheet
    sheet_name: Name of the sheet to write to

    Outputs
    return: None
    """
    df.to_excel(writer, sheet_name = sheet_name, index = False)
    # Format the excel sheets so that the column width matches the size of the header text
    worksheet = writer.sheets[sheet_name]
    
    for idx, col in enumerate(df):  # loop through all columns
        series = df[col]
        # Set max_len to the length of only the header text
        max_len = len(str(series.name)) + 1
        worksheet.set_column(idx, idx, max_len)  # set column width
    return
   
def format_column(worksheet, df):
    """
    Format excel sheet column width to match the size of the header text.

    Inputs
    worksheet: ExcelWriter worksheet object
    df: DataFrame to format

    Outputs
    return: None
    """
    for idx, col in enumerate(df):  # loop through all columns
        series = df[col]
        # Set max_len to the length of only the header text
        max_len = len(str(series.name)) + 1
        worksheet.set_column(idx, idx, max_len)  # set column width
        # Make the top header "sticky" so that it is always visible
        worksheet.freeze_panes(1, 0)
    return

def generate_filter_df(node_table, nodes_to_keep_list, nodes_to_keep_componentindex, componentindex_list, key_col):
    """
    Generate a dataframe to filter the Cytoscape network based on the nodes to keep. See p4c_get_filtered_nodes_and_clusters for more information.

    Inputs
    node_table: DataFrame
        Node table of the Cytoscape network
    nodes_to_keep_list: list of bool
        List of TRUE and FALSE values for the nodes to keep
    nodes_to_keep_componentindex: list of bool
        List of TRUE and FALSE values for the nodes to keep based on componentindex
    componentindex_list: list of int
        List of componentindex values (necessary for determining which singleton nodes (componentindex of -1) to keep)
    key_col: str
        Column name of the key column (shared name)

    Outputs
    return: DataFrame
        Dataframe with columns 'shared name', 'componentindex', 'keep_node', 'keep_componentindex'
    """
    filter_df = pd.DataFrame({key_col: node_table[key_col], 'componentindex': componentindex_list, 'keep_node': nodes_to_keep_list, 'keep_componentindex': nodes_to_keep_componentindex})
    # Convert data type of componentindex column to int
    filter_df['componentindex'] = filter_df['componentindex'].astype(int)
    # For rows with componentindex of -1 AND keep_node of false, set keep_componentindex to false
    filter_df.loc[(filter_df['componentindex'] == -1) & (filter_df['keep_node'] == False), 'keep_componentindex'] = False
    return filter_df

def p4c_get_filtered_nodes_and_clusters(node_table, nodes_to_keep, key_col, componentindex_colname):
    """
    Generate a dataframe to filter the Cytoscape network based on the nodes to keep. Based on those nodes, also keep nodes that are clustered (ie: connected by edges); determine this based on the componentindex value. Note that componentindex of -1 just indicates singleton nodes; only keep singleton nodes that are in the nodes_to_keep_list (ie: satisfy the original filtering criteria).
    This function uses the generate_filter_df function.

    Inputs
    node_table: DataFrame
        Node table of the Cytoscape network
    nodes_to_keep: list of bool
        List of TRUE and FALSE values for the nodes to keep
    key_col: str
        Column name of the key column (shared name)
    componentindex_colname: str
        Column name of the componentindex

    Outputs
    return: DataFrame
        Dataframe with columns 'shared name', 'componentindex', 'keep_node', 'keep_componentindex'
    """
    # Get the list of componentindex values to keep
    componentindex_to_keep = node_table.copy()
    componentindex_to_keep = componentindex_to_keep[nodes_to_keep][componentindex_colname].tolist()
    # remove duplicates
    componentindex_to_keep = list(set(componentindex_to_keep))
    # Make a pandas of true and false values for the nodes to keep, with keys of shared name.
    nodes_to_keep_componentindex = node_table.copy()
    nodes_to_keep_componentindex = nodes_to_keep_componentindex[componentindex_colname].isin(componentindex_to_keep)
    # Create list of nodes_to_keep and nodes_to_keep_componentindex to be lists of TRUE and FALSE values for the nodes/clusters to keep.
    nodes_to_keep_list = nodes_to_keep.tolist()
    nodes_to_keep_componentindex = nodes_to_keep_componentindex.tolist()
    # Fetch list of componentindex values (use this to determine with singletons to remove)
    componentindex_list = node_table.copy()
    componentindex_list = componentindex_list['componentindex'].tolist()
    # Generate the dataframe to filter the network
    filter_df = generate_filter_df(node_table, nodes_to_keep_list, nodes_to_keep_componentindex, componentindex_list, key_col)
    return filter_df

def p4c_import_and_apply_cytoscape_style(dir, cytoscape_style_filename, suid, network_rename):
    """
    Import and apply a Cytoscape style to the network. Additionally, name the network.

    Inputs
    dir: str
        Directory of the Cytoscape style file
    cytoscape_style_filename: str
        Filename of the Cytoscape style file
        
    Outputs
    return None

    """
    # If the style is not already in Cytoscape, import it
    cytoscape_style_filtered_name = cytoscape_style_filename.split('.')[0]
    if cytoscape_style_filtered_name not in p4c.get_visual_style_names():
        p4c.import_visual_styles(dir)
    p4c.set_visual_style(cytoscape_style_filtered_name)
    p4c.networks.rename_network(network_rename, suid)
    return

def apply_exp_ctrl_filter(node_table_to_filter, exp_colname, ctrl_colname, exp_cutoff, ctrl_cutoff):
    """
    Apply a filter to the node table based on the intensity cutoffs for the experimental and control groups.

    Inputs
    node_table_to_filter: DataFrame
        Node table of the Cytoscape network
    exp_colname: str
        Column name of the experimental group intensity
    ctrl_colname: str
        Column name of the control group intensity
    exp_cutoff: float
        Intensity cutoff for the experimental group (greater than this value)
    ctrl_cutoff: float
        Intensity cutoff for the control group (less than this value)

    Outputs
    return: list of bool
        List of TRUE and FALSE values for the nodes to keep, aligning with the rows of the node table
    """
    nodes_to_keep = (node_table_to_filter[exp_colname] > exp_cutoff) & (node_table_to_filter[ctrl_colname] < ctrl_cutoff)
    return nodes_to_keep

"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
GNPS_OUTPUT_FOLDER = r'GNPS_output'
OUTPUT_FOLDER = r'output'
# Within the GNPS_OUTPUT_FOLDER is a folder with job folders for grouping analysis. These job folders contain the GNPS output files (need to manually place downloaded GNPS results).
GROUPING_INPUT_FOLDER_NAME = "Grouping_Analysis_Folders"

METADATA_FILENAME = 'Anid_vs_Yeast_HE_Groupings_Metadata.xlsx'
METADATA_JOB_TAB = 'Multi-jobs'
EXP_VS_CTRL_TEMP_FOLDER_COL_NAMES = ['G1_temp_folder', 'G2_temp_folder', 'G3_temp_folder', 'G4_temp_folder', 'G5_temp_folder', 'G6_temp_folder']

# Filter for metabolites with intensity above this value in experimental sample groups
EXP_INTENSITY_CUTOFF = 0
# Filter for metabolites with intensity below this value in control sample groups
CTRL_INTENSITY_CUTOFF = 1
# Columns of interest
COLUMNS_OF_INTEREST = ['shared name', 'precursor mass', 'RTMean', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'Compound_Name', 'MQScore', 'Smiles', 'INCHI', 'GNPSLibraryURL', 'componentindex', 'DefaultGroups']

GROUP_NAME_COLUMNS = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']

# Create a named tuple to store the filenames of the experimental and control groups
ExpCtrlGroups = namedtuple('FileGroups', ['exp_filenames', 'ctrl_filenames'])
GroupToValue = namedtuple('GtoJob', ['group_name', 'value'])

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Iterate over each job_name in metadata
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Import metadata table for job
metadata = pd.read_excel(pjoin(INPUT_FOLDER, METADATA_FILENAME), sheet_name = METADATA_JOB_TAB)

for job_index, job in enumerate(metadata['Job_Name']):
    """""""""""""""""""""""""""""""""""""""""""""
    Get Job Info
    """""""""""""""""""""""""""""""""""""""""""""
    job_name = metadata['Job_Name'][job_index]
    grouping_type = metadata['Grouping_Type'][job_index]
    # Get GtoJob named tuple
    job_group_names = []
    for group_column in GROUP_NAME_COLUMNS:
        job_group_names.append(GroupToValue(group_name = group_column, value = metadata[group_column][job_index]))
    # Get temp folder names for each experimental vs. control group
    exp_vs_ctrl_temp_folders = []
    for i, name in enumerate(EXP_VS_CTRL_TEMP_FOLDER_COL_NAMES):
        exp_vs_ctrl_temp_folders.append(GroupToValue(group_name = GROUP_NAME_COLUMNS[i], value = metadata[name][job_index]))
    # Get ionization
    ionization = metadata['Ionization'][job_index]
    # Get style template file
    cytoscape_style_filename = metadata['Cytoscape_Format_Template_File'][job_index]


    """""""""""""""""""""""""""""""""""""""""""""
    Create data_cols_dict to Organize Bucket Table Data Columns
    """""""""""""""""""""""""""""""""""""""""""""
    # Create data_cols_dict, a dictionary of job_name (keys) (from job_group_names list) with ExpCtrlGroups named tupeles (values). The ExpCtrlGroups named tuple contains the filenames of the experimental and control groups. These filenames are retrieved from TEMP_OVERALL_FOLDER --> exp_vs_ctrl_temp_folders for the group_name --> .tsv file with metadata in string. Import the metadata .tsv file, which has two columns: 'Filename' and 'Class' (CTRL or EXP). The Filename values should be organized into the ExpCtrlGroups named tuple, based on if the Class is EXP or CTRL. Additionally, the ".mzML" extension of the Filename strings should be removed.
    data_cols_dict = {}
    for group in job_group_names:
            # Skip if group value is NaN (if there is no job_name for this G#)
            if pd.isna(group.value):
                continue

            # Find matching temp folder for this group
            temp_folder = next((folder.value for folder in exp_vs_ctrl_temp_folders 
                            if folder.group_name == group.group_name), None)

            if temp_folder is not None and not pd.isna(temp_folder):
                # Find metadata file in temp folder by searching for file containing "metadata"
                temp_dir = pjoin(TEMP_OVERALL_FOLDER, temp_folder)
                metadata_files = [f for f in os.listdir(temp_dir) if 'metadata' in f.lower()]
                metadata_path = pjoin(temp_dir, metadata_files[0]) if metadata_files else None
                if os.path.exists(metadata_path):
                    group_metadata = pd.read_csv(metadata_path, sep='\t')

                    # Split into experimental and control groups
                    exp_files = group_metadata[group_metadata['Class'] == 'EXP']['Filename'].tolist()
                    ctrl_files = group_metadata[group_metadata['Class'] == 'CTRL']['Filename'].tolist()

                    # Remove .mzML extension
                    exp_files = [f.replace('.mzML', '') for f in exp_files]
                    ctrl_files = [f.replace('.mzML', '') for f in ctrl_files]

                    # Create ExpCtrlGroups named tuple and add to dictionary
                    data_cols_dict[group.value] = ExpCtrlGroups(
                        exp_filenames=exp_files,
                        ctrl_filenames=ctrl_files
                    )

    """""""""""""""""""""""""""""""""""""""""""""
    Import Abundance Data from Bucket Table and Organize Data Columns
    """""""""""""""""""""""""""""""""""""""""""""
    # Import bucket table (contains string "buckettable" in filename) from GNPS_OUTPUT_FOLDER --> GROUPING_INPUT_FOLDER_NAME -->  job_name folder
    job_folder = pjoin(GNPS_OUTPUT_FOLDER, GROUPING_INPUT_FOLDER_NAME, job_name)
    bucket_file = [f for f in os.listdir(job_folder) if 'buckettable' in f.lower()]
    bucket_path = pjoin(job_folder, bucket_file[0]) if bucket_file else None
    if bucket_path is not None:
        bucket_table = pd.read_csv(bucket_path, sep='\t')
    else:
        print(f"Bucket table not found for job {job_name}")

    # Change column name "#OTU ID" to "shared name"
    bucket_table.rename(columns={'#OTU ID': 'shared name'}, inplace=True)
    # bucket_table contains only columns shared name and the data column, each named as the exp_filenames and ctrl_filenames in data_cols_dict.
    # Organize the data columns as they appear in data_cols_dict. Start with the job_name for the first group in data_cols_dict, then move to the next group in data_cols_dict.
    data_cols = []
    data_cols_avgs = []
    for group in job_group_names:
        if group.value in data_cols_dict:
            # Add individual experimental columns
            data_cols.extend(data_cols_dict[group.value].exp_filenames)
            # Calculate and add experimental average with distinct name
            bucket_table[group.value + "_exp_avg"] = bucket_table[data_cols_dict[group.value].exp_filenames].mean(axis=1)
            data_cols.append(group.value + "_exp_avg")
            data_cols_avgs.append(group.value + "_exp_avg")
            
            # Add individual control columns
            data_cols.extend(data_cols_dict[group.value].ctrl_filenames)
            # Calculate and add control average with distinct name
            bucket_table[group.value + "_ctrl_avg"] = bucket_table[data_cols_dict[group.value].ctrl_filenames].mean(axis=1)
            data_cols.append(group.value + "_ctrl_avg")
            data_cols_avgs.append(group.value + "_ctrl_avg")
    # Order the columns
    data_cols = ['shared name'] + data_cols
    data_cols_avgs = ['shared name'] + data_cols_avgs
    bucket_table = bucket_table[data_cols]

    # Export bucket table to excel. Export to the OUTPUT_FOLDER --> job_name folder (create if it does not exist). Filename is job_name + "_bucket_table.xlsx". Replace previous file if it exists.
    bucket_table_filename = job_name + "_bucket_table.xlsx"
    bucket_table_path = pjoin(OUTPUT_FOLDER, job_name, bucket_table_filename)
    os.makedirs(pjoin(OUTPUT_FOLDER, job_name), exist_ok=True)
    bucket_table.to_excel(bucket_table_path, index=False)
    

    """""""""""""""""""""""""""""""""""""""""""""
    Open Cytoscape network from GNPS output .graphml
    """""""""""""""""""""""""""""""""""""""""""""
    # Destroy any networks already in the Cytsocape session
    p4c.networks.delete_all_networks()

    # Import .graphml file from GNPS_OUTPUT_FOLDER --> GROUPING_INPUT_FOLDER_NAME -->  job_name folder. Find the file in the folder containing "graphml" in its name.
    graphml_folder = [f for f in os.listdir(job_folder) if 'graphml' in f.lower()]
    graphml_file = [f for f in os.listdir(pjoin(job_folder, graphml_folder[0])) if f.endswith('.graphml')]
    graphml_path = pjoin(job_folder, graphml_folder[0], graphml_file[0]) if graphml_file else None
    # Handle if graphml file is not found
    if graphml_path is None:
        print(f"Graphml file not found for job {job_name}")
    else:
        # Import the network into Cytoscape
        p4c.import_network_from_file(graphml_path)

    # Get the SUID of the current network
    suid_main_network = p4c.get_network_suid()


    """""""""""""""""""""""""""""""""""""""""""""
    Import Abundance Data into the Cytoscape Node Table
    """""""""""""""""""""""""""""""""""""""""""""
    # Load data into the node table, using the shared name as the key column
    node_table_add_columns(bucket_table, data_cols_avgs, suid_main_network, 'shared name')


    """""""""""""""""""""""""""""""""""""""""""""
    Adjust Cytoscape Node Table Columns
    """""""""""""""""""""""""""""""""""""""""""""
    node_cols_to_keep = []
    # Make a copy of COLUMNS_OF_INTEREST
    node_cols_to_keep.extend(COLUMNS_OF_INTEREST)
    # After the first 3 columns of COLUMNS_OF_INTEREST, insert the data_cols_avgs (without the shared name column)
    node_cols_to_keep[3:3] = data_cols_avgs[1:] 

    # Get current node table
    node_table = p4c.tables.get_table_columns(table='node', network=suid_main_network)

    # Create a new DataFrame with only the desired columns in the specified order
    node_table_clean = pd.DataFrame()
    for col in node_cols_to_keep:
        if col in node_table.columns:
            node_table_clean[col] = node_table[col]

    # Rename column names G1, G2, G3, G4, G5, and G6 in node_table_clean to be the corresponding values in job_group_names. Rename these as the GNPS output spectral counts data type
    node_table_clean.rename(columns={group.group_name: group.value + "_spectral_counts" for group in job_group_names}, inplace=True)

    # Clear existing node table data
    cols_immutable = ['name', 'SUID', 'shared name', 'selected']
    for col in node_table.columns:
        if col not in cols_immutable:  # Don't delete required Cytoscape columns
            p4c.delete_table_column(col, table='node', network=suid_main_network)

    # Load the filtered and reordered data back into Cytoscape
    p4c.tables.load_table_data(node_table_clean, data_key_column='shared name', 
                              table_key_column='name', network=suid_main_network)


    """""""""""""""""""""""""""""""""""""""""""""
    Create new style file, using template style file as basis
    """""""""""""""""""""""""""""""""""""""""""""
    # For the style file, adjust the pie chart columns to match the new job_group_names values
    # Get the template Cytoscape style file info
    cytoscape_inputs_folder = pjoin(INPUT_FOLDER, 'Cytoscape_inputs')
    with open(pjoin(cytoscape_inputs_folder, cytoscape_style_filename), 'r') as file:
        filedata = file.read()

    # For the style file, G1, G3, and G5 are set to represent EXP type groups, and G2, G4, and G6 to represent CTRL type groups. When replacing text in filedata, ensure that the G# text is properly replaced by EXP vs CTRL type.
    exp_unused = ['G1', 'G3', 'G5']
    ctrl_unused = ['G2', 'G4', 'G6']
    for group_name, value in job_group_names:
        # if value is not a key in data_cols_dict, skip to next group_name
        if value not in data_cols_dict:
            continue
        # only use EXP groups from data_cols_dict to indicate the _exp_avg and _ctrl_avg columns to use in the pie charts
        if not exp_unused or not ctrl_unused:
            print('Error in renaming pie chart columns for job {job_name}.')
            break
        str_to_replace_exp = exp_unused.pop(0)
        str_to_replace_ctrl = ctrl_unused.pop(0)
        # use format .replace(f'&quot;{old_col_name}&quot;', f'&quot;{group_name}&quot;')
        print(f'&quot;{str_to_replace_exp}&quot;')
        print(f'&quot;{value}_exp_avg&quot;')
        filedata = filedata.replace(f'&quot;{str_to_replace_exp}&quot;', f'&quot;{value}_exp_avg&quot;')
        # If the exact same ctrl string has already been used, skip the renaming process (some EXP have the same CTRL)
        if f'&quot;{group_name}_exp_avg&quot;' not in filedata:
            print(f'&quot;{str_to_replace_ctrl}&quot;')
            print(f'&quot;{value}_ctrl_avg&quot;')
            filedata = filedata.replace(f'&quot;{str_to_replace_ctrl}&quot;', f'&quot;{value}_ctrl_avg&quot;')

    # Additionally, change "<visualStyle name="{cytoscape_style_filename_root}">, where {cytoscape_style_filename_root} is the string value for cytoscape_style_filename without ".xml", to be "<visualStyle name="{cytoscape_style_filename_new_root}">, where cytoscape_style_filename_new_root is the string value for cytoscape_style_filename_new without ".xml"
    cytoscape_style_filename_new = f'{job_name}_style.xml'
    cytoscape_style_filename_root = cytoscape_style_filename.split('.')[0]
    cytoscape_style_filename_new_root = cytoscape_style_filename_new.split('.')[0]
    filedata = filedata.replace(f'name="{cytoscape_style_filename_root}"', f'name="{cytoscape_style_filename_new_root}"')

    # Write the new style file in the cytoscape_inputs_folder
    with open(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), 'w') as file:
        file.write(filedata)


    """""""""""""""""""""""""""""""""""""""""""""
    Set Visual Style
    """""""""""""""""""""""""""""""""""""""""""""
    # Apply the Cytoscape style
    p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, suid_main_network, job_name)
