"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 5: A. nidulans vs. Yeast Heterologous Expression GNPS Analysis
@author: Lazarina Butkovich

This script has the following features for analyzing GNPS output for comparing A. nidulans and Yeast heterologous expression of the same gut fungal proteinID. This script takes GNPS output from the "METABOLOMICS-SNETS-V2" workflow, also known as the "Molecular Networking" data analysis workflow.

In METADATA_FILENAME excel, describe the following:
- Job_Name: Name of the job
[to-do: fill in remaining]

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
import itertools
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

def p4c_network_add_filter_columns(filter_name, node_table, nodes_to_keep, network_to_clone_suid, key_col='shared name', componentindex_colname='componentindex'):
    """
    Add columns to the node table of the network to filter based on the nodes to keep. This function uses the p4c_get_filtered_nodes_and_clusters function.

    Inputs
    filter_name: str
        Name of the filter to create
    node_table: DataFrame
        Node table of the Cytoscape network
    nodes_to_keep: list of bool
        List of TRUE and FALSE values for the nodes to keep
    network_to_clone_suid: int  
        SUID of the network to clone
    key_col: str
        Column name of the key column (shared name)

    Outputs
    return: int
        SUID of the filtered network
    """
    # Create the filtered network
    network_filter_suid = p4c.clone_network(network=network_to_clone_suid)
    # Generate the dataframe filter_df to filter the network
    filter_df = p4c_get_filtered_nodes_and_clusters(node_table, nodes_to_keep, key_col, componentindex_colname)
    # Add the 2 lists (nodes and componentindex) of TRUE and FALSE values to the network, using function node_table_add_columns
    node_table_add_columns(filter_df, ['shared name', 'keep_componentindex'], network_filter_suid, 'shared name')
    node_table_add_columns(filter_df, ['shared name', 'keep_node'], network_filter_suid, 'shared name')
    p4c.create_column_filter(filter_name = filter_name, column = 'keep_componentindex', criterion = False, predicate = 'IS', type = 'nodes', network = network_filter_suid)
    # The above step only selects nodes that meet the filter criteria. To remove the unselected nodes, use the following command
    # https://py4cytoscape.readthedocs.io/en/0.0.10/reference/generated/py4cytoscape.network_selection.delete_selected_nodes.html
    p4c.network_selection.delete_selected_nodes(network = network_filter_suid)

    # Reorganize network to remove gaps
    p4c.layout_network('force-directed', network_filter_suid)
    return network_filter_suid

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

def create_exp_ctrl_mapping(data_cols_dict):
    """
    Create a dictionary mapping experimental columns to their control columns using FinalExpCtrlMapping named tuples.
    Takes into account cases where multiple experimental groups share the same control group.

    Inputs
    data_cols_dict: dict
        Dictionary where keys are group names and values are ExpCtrlGroups named tuples
        containing experimental and control filenames

    Outputs
    return: dict
        Dictionary where keys are experimental column names and values are FinalExpCtrlMapping 
        named tuples containing the experimental and control group names
    """
    exp_ctrl_mapping = {}
    ctrl_groups_seen = {}  # Track control groups we've seen

    for group_name, group_data in data_cols_dict.items():
        exp_col = f"{group_name}_exp_avg"
        ctrl_col = f"{group_name}_ctrl_avg"
        
        # Create tuple of sorted control filenames to use as dictionary key
        ctrl_files = tuple(sorted(group_data.ctrl_filenames))
        
        if ctrl_files in ctrl_groups_seen:
            # This control group has been seen before
            original_ctrl_group = ctrl_groups_seen[ctrl_files]
            mapping = FinalExpCtrlMapping(
                exp_group=exp_col,
                ctrl_group=f"{original_ctrl_group}_ctrl_avg"
            )
        else:
            # This is a new control group
            ctrl_groups_seen[ctrl_files] = group_name
            mapping = FinalExpCtrlMapping(
                exp_group=exp_col,
                ctrl_group=ctrl_col
            )
            
        exp_ctrl_mapping[exp_col] = mapping
        
    return exp_ctrl_mapping

def add_log10_columns(df):
    """
    Add log10 columns for any columns ending with _exp_avg or _ctrl_avg.
    Values of 0 have already been replaced with 1/5th of the minimum non-zero value before taking log10.
    Log10 values are rounded to 2 decimal places.

    Inputs
    df: DataFrame
        DataFrame containing the columns to transform

    Outputs
    return: DataFrame
        DataFrame with additional log10 columns
    """
    # Find all columns ending with _exp_avg or _ctrl_avg
    avg_cols = [col for col in df.columns if col.endswith('_exp_avg') or col.endswith('_ctrl_avg')]
    
    # For each average column
    for col in avg_cols:
        # Create new column name
        log_col = col + '_log10'
        # Calculate log10 values
        df[log_col] = np.log10(df[col])
        # Round to 2 decimal places
        df[log_col] = df[log_col].round(2)
    
    return df

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
EXP_INTENSITY_CUTOFF = 1000000
# Filter for metabolites with intensity below this value in control sample groups
CTRL_INTENSITY_CUTOFF = 1000000
# Columns of interest
COLUMNS_OF_INTEREST = ['shared name', 'precursor mass', 'RTMean', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'Compound_Name', 'MQScore', 'Smiles', 'INCHI', 'GNPSLibraryURL', 'componentindex', 'DefaultGroups']

GROUP_NAME_COLUMNS = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']

# Create a named tuple to store the filenames of the experimental and control groups
ExpCtrlGroups = namedtuple('FileGroups', ['exp_filenames', 'ctrl_filenames'])
# All group_name should be converted to string
GroupToValue = namedtuple('GtoJob', ['group_name', 'value'])
FinalExpCtrlMapping = namedtuple('ExpCtrlMapping', ['exp_group', 'ctrl_group'])

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Iterate over each job_name in metadata
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Import metadata table for job
metadata = pd.read_excel(pjoin(INPUT_FOLDER, METADATA_FILENAME), sheet_name = METADATA_JOB_TAB)
# Convert all GROUP_NAME_COLUMNS to string
metadata[GROUP_NAME_COLUMNS] = metadata[GROUP_NAME_COLUMNS].astype(str)

for job_index, job in enumerate(metadata['Job_Name']):
    """""""""""""""""""""""""""""""""""""""""""""
    Get Job Info
    """""""""""""""""""""""""""""""""""""""""""""
    job_name = metadata['Job_Name'][job_index]
    # Get GtoJob named tuple
    job_group_names = []
    for group_column in GROUP_NAME_COLUMNS:
        job_group_names.append(GroupToValue(group_name = group_column, value = metadata[group_column][job_index]))
    # Remove tuples where value is 'nan'. These represent empty spaces in the metadata excel input. For example, only 2 groups are being compared instead of 3.
    job_group_names = [group for group in job_group_names if group.value != 'nan']
        
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
    Import Abundance Data from Bucket Table and Organize Data Columns.
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

    # Of all values in bucket_table data columns (not the shared name column) find the lowest non-zero value. 1/5th of this value will be used to replace all 0 values in the data columns.
    min_val = bucket_table[bucket_table.columns[1:]].replace(0, np.nan).min().min()
    replace_val = min_val / 5
    # Replace all 0 values in the data columns with replace_val (do not replace any values in the shared name column)
    bucket_table[bucket_table.columns[1:]] = bucket_table[bucket_table.columns[1:]].replace(0, replace_val)

    # bucket_table contains only columns shared name and the data column, each named as the exp_filenames and ctrl_filenames in data_cols_dict.
    # Organize the data columns as they appear in data_cols_dict. Start with the job_name for the first group in data_cols_dict, then move to the next group in data_cols_dict.
    data_cols = []
    data_cols_avgs = []
    for group in job_group_names:
        # Skip if group value is NaN
        if pd.isna(group.value):
            continue
            
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
    # For bucket table to export, make all data columns be in scientific notation. Additionally, use conditional formatting to color the cells based on the value of the cell. The color scale should be from red to green, with the lowest value in red and the highest value in green.
    bucket_table_to_export = bucket_table.copy()
    bucket_table_path = pjoin(OUTPUT_FOLDER, job_name, job_name + "_bucket_table.xlsx")
    
    # Create Excel writer object
    with pd.ExcelWriter(bucket_table_path, engine='xlsxwriter') as writer:
        # Write original numeric data to excel first
        bucket_table_to_export = bucket_table.copy()
        bucket_table_to_export.to_excel(writer, sheet_name='Sheet1', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # Create scientific notation number format
        sci_format = workbook.add_format({'num_format': '0.00E+00'})
        
        # Apply scientific notation format to data cells (excluding 'shared name' column)
        for col in range(1, len(bucket_table.columns)):  # Start from second column (skip 'shared name')
            worksheet.set_column(col, col, 15, sci_format)  # Width set to 15
        
        # Format 'shared name' column width
        worksheet.set_column(0, 0, len('shared name') + 2)
        
        # Freeze panes
        worksheet.freeze_panes(1, 1)

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
    # Add the data_cols_avgs (without the shared name column) to node_cols_to_keep
    node_cols_to_keep.extend(data_cols_avgs[1:])

    # Get current node table
    node_table = p4c.tables.get_table_columns(table='node', network=suid_main_network)

    # Create a new DataFrame with only the desired columns in the specified order
    node_table_clean = pd.DataFrame()
    for col in node_cols_to_keep:
        if col in node_table.columns:
            node_table_clean[col] = node_table[col]

    # Rename column names G# in node_table_clean to be the corresponding values in job_group_names. Rename these as the GNPS output spectral counts data type
    node_table_clean.rename(columns={group.group_name: group.value + "_spectral_counts" for group in job_group_names}, inplace=True)

    # After each column ending in _exp_avg or _ctrl_avg, create corresponding log10 columns
    node_table_clean = add_log10_columns(node_table_clean)

    # Reorder the columns in the node table so that the log10 columns appear after RTMean and the spectral counts columns appear at the end
    # Get lists of column names by type
    spectral_counts_cols = [col for col in node_table_clean.columns if '_spectral_counts' in col]
    log10_cols = [col for col in node_table_clean.columns if '_log10' in col]
    other_cols = [col for col in node_table_clean.columns if col not in spectral_counts_cols + log10_cols]
    # Find index of 'RTMean' in other_cols
    rtmean_idx = other_cols.index('RTMean')
    # Create new column order
    new_order = (other_cols[:rtmean_idx + 1] + 
                log10_cols +
                other_cols[rtmean_idx + 1:] +
                spectral_counts_cols)
    # Reorder the columns
    node_table_clean = node_table_clean[new_order]

    # Convert RTMean from seconds to minutes (divide by 60)
    node_table_clean['RTMean'] = node_table_clean['RTMean'] / 60

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
    # Keep track of which ctrl groups are used with which exp groups with final_mapping
    final_mapping = create_exp_ctrl_mapping(data_cols_dict)

    for exp_col, mapping in final_mapping.items():
        # only use EXP groups to indicate the _exp_avg and _ctrl_avg columns to use in pie charts
        if not exp_unused or not ctrl_unused:
            print(f'Error in renaming pie chart columns for job {job_name}.')
            break
            
        str_to_replace_exp = exp_unused.pop(0)
        str_to_replace_ctrl = ctrl_unused.pop(0)

        # Replace experimental group name
        filedata = filedata.replace(f'&quot;{str_to_replace_exp}&quot;', f'&quot;{mapping.exp_group}&quot;')
        
        # Only replace control group if it hasn't been used before
        if f'&quot;{mapping.ctrl_group}&quot;' not in filedata:
            filedata = filedata.replace(f'&quot;{str_to_replace_ctrl}&quot;', f'&quot;{mapping.ctrl_group}&quot;')

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

    """""""""""""""""""""""""""""""""""""""""""""
    Create Filtered Networks
    """""""""""""""""""""""""""""""""""""""""""""
    # Re-acquire node table (since modifying columns)
    node_table = p4c.tables.get_table_columns(table='node', network=suid_main_network)
    # For each EXP-CTRL pair in final_mapping, make a list of nodes_to_keep, based on nodes that meet the intensity cutoffs (EXP > EXP_INTENSITY_CUTOFF, CTRL < CTRL_INTENSITY_CUTOFF). The nodes_to_keep will be used in different combinations. Use combinatorics to include all possible combinations of EXP-CTRL pairs.
    # ie: 
    nodes_to_keep_list = []
    for exp_col, mapping in final_mapping.items():
        nodes_to_keep = apply_exp_ctrl_filter(node_table, mapping.exp_group, mapping.ctrl_group, EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_list.append(nodes_to_keep)

    # Create a mapping of filter indices to their corresponding group names
    filter_group_names = {}
    for i, (exp_col, mapping) in enumerate(final_mapping.items()):
        # Extract the group name from the exp_col (removes '_exp_avg')
        group_name = exp_col.rsplit('_', 2)[0]
        filter_group_names[i] = group_name

    # Create combinations with both the filters and their names
    all_combinations = []
    all_combination_names = []
    for r in range(1, len(nodes_to_keep_list) + 1):
        # Get filter combinations
        filter_combinations = list(itertools.combinations(enumerate(nodes_to_keep_list), r))
        
        for combo in filter_combinations:
            # Split indices and filters
            indices, filters = zip(*combo)
            # Create filter name using actual group names
            name = "Filter_" + "_and_".join(filter_group_names[i] for i in indices)
            # Store both filters and name
            all_combinations.append(filters)
            all_combination_names.append(name)

    # For each combination, create a filtered network and reapply style
    for i, filters in enumerate(all_combinations):
        # Combine multiple filters using logical AND (&)
        if len(filters) > 1:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
        else:
            combined_filter = filters[0]
        
        # Create filtered network
        suid_filtered_network = p4c_network_add_filter_columns(
            all_combination_names[i], 
            node_table, 
            combined_filter,
            suid_main_network
        )
        
        # Wait briefly for network creation
        time.sleep(1)
        
        try:
            # Get filtered node table
            filtered_node_table = p4c.tables.get_table_columns(table='node', network=suid_filtered_network)
            if filtered_node_table.empty:
                # Reload node table from main network
                filtered_node_table = node_table[node_table['name'].isin(
                    p4c.get_node_ids(network=suid_filtered_network)
                )]
                
                # If still no nodes after filtering, skip this network
                if len(filtered_node_table) == 0:
                    print(f"Skipping empty network for {all_combination_names[i]}")
                    p4c.delete_network(network=suid_filtered_network)
                    continue
                    
                # Load the filtered data back into network
                p4c.tables.load_table_data(
                    filtered_node_table,
                    data_key_column='name',
                    table_key_column='name',
                    network=suid_filtered_network
                )
            
            # Apply the Cytoscape style
            p4c_import_and_apply_cytoscape_style(
                pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new),
                cytoscape_style_filename_new, 
                suid_filtered_network,
                f"{job_name}_{all_combination_names[i]}"
            )

        except Exception as e:
            print(f"Error processing network {all_combination_names[i]}: {str(e)}")
            # Clean up failed network
            if suid_filtered_network in p4c.get_network_list():
                p4c.delete_network(network=suid_filtered_network)
            continue


    """""""""""""""""""""""""""""""""""""""""""""
    Save Cytoscape Session in Output Folder, Job Name folder
    """""""""""""""""""""""""""""""""""""""""""""
    # If the job_name folder does not exist yet in OUTPUT_FOLDER, create it
    os.makedirs(pjoin(OUTPUT_FOLDER, job_name), exist_ok=True)

    # Save the Cytoscape session
    p4c.session.save_session(filename=pjoin(OUTPUT_FOLDER, job_name, job_name + '_Cytoscape_session.cys'), overwrite_file=True)

    print('Session saved and finished filtered Cytoscape networks for ' + job_name + ', took %.2f seconds' % (time.time() - start))
    start = time.time()

