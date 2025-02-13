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
Additionally, you must download GNPS job result files (use "Download Clustered Spectra as MGF" option. The .graphml file will be in the sub-folder containing "graphml" in its name. The .mgf file can be uploaded to SIRIUS). Unzip the contents and place them in GNPS_OUTPUT_FOLDER --> {create job folder for POS and NEG}. Folder name template: "Grouping_" + job_name + "_POS" OR "Grouping_" + job_name + "_NEG"
"""""""""""""""""""""""""""""""""""""""""""""


import os
from os.path import join as pjoin
import pandas as pd
import py4cytoscape as p4c
import numpy as np
import matplotlib.pyplot as plt
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
    workbook = writer.book
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

# Filter for metabolites with intensity above this value in experimental sample groups
EXP_INTENSITY_CUTOFF = 0
# Filter for metabolites with intensity below this value in control sample groups
CTRL_INTENSITY_CUTOFF = 1
# Columns of interest
COLUMNS_OF_INTEREST = ['shared name', 'precursor mass', 'RTMean', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'Compound_Name', 'MQScore', 'Smiles', 'INCHI', 'GNPSLibraryURL', 'componentindex', 'DefaultGroups']

GROUP_NAME_COLUMNS = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']

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
    ionization = metadata['Ionization'][job_index]
    grouping_type = metadata['Grouping_Type'][job_index]

    # Determine how many groups are in the job based on if there is a value in the GROUP_NAME_COLUMNS for the job_name or not. Use job_group_names to rename the G1-G6 columns (if able) in the Cytoscape node table.
    job_group_names = []
    for group_column in GROUP_NAME_COLUMNS:
        if metadata[group_column][job_index] != '':
            job_group_names.append(metadata[group_column][job_index])


    """""""""""""""""""""""""""""""""""""""""""""
    Open Cytoscape network from GNPS output .graphml
    """""""""""""""""""""""""""""""""""""""""""""
    # Load the network. The .graphml file is in GNPS output folder --> groupings folder --> job folder --> sub-folder with name including "graphml"
    gnps_output_job_folder = pjoin(GNPS_OUTPUT_FOLDER, GROUPING_INPUT_FOLDER_NAME, job_name)

    # Destroy any networks already in the Cytsocape session
    p4c.networks.delete_all_networks()

    # Find the .graphml file in the sub-folder containing "graphml" in its name.
    for dir in os.listdir(gnps_output_job_folder):
        if 'graphml' in dir:
            graphml_sub_folder = dir
            # look in the sub-folder for the .graphml file
            gnps_graphml_file = os.listdir(pjoin(gnps_output_job_folder, dir))[0]

    # Import the GNPS output into Cytoscape
    p4c.import_network_from_file(pjoin(gnps_output_job_folder, graphml_sub_folder, gnps_graphml_file))

    # Get the SUID of the current network
    suid_main_network = p4c.get_network_suid()


    """""""""""""""""""""""""""""""""""""""""""""
    Adjust Cytoscape Node Table Columns
    """""""""""""""""""""""""""""""""""""""""""""
    # Get current node table
    node_table = p4c.tables.get_table_columns(table='node', network=suid_main_network)

    # Create a new DataFrame with only the desired columns in the specified order
    filtered_node_table = pd.DataFrame()
    for col in COLUMNS_OF_INTEREST:
        if col in node_table.columns:
            filtered_node_table[col] = node_table[col]

    # Clear existing node table data
    cols_immutable = ['name', 'SUID', 'shared name', 'selected']
    for col in node_table.columns:
        if col not in cols_immutable:  # Don't delete required Cytoscape columns
            p4c.delete_table_column(col, table='node', network=suid_main_network)

    # Load the filtered and reordered data back into Cytoscape
    p4c.tables.load_table_data(filtered_node_table, data_key_column='shared name', 
                              table_key_column='name', network=suid_main_network)

    # Rename column names G1-G6 in the Cytoscape node table
    for i, group_name in enumerate(job_group_names):
        old_col_name = f'G{i+1}'
        if old_col_name in filtered_node_table.columns:
            p4c.rename_table_column(old_col_name, group_name, 
                                  table='node', network=suid_main_network)


    """""""""""""""""""""""""""""""""""""""""""""
    Create new style file, using template style file as basis
    """""""""""""""""""""""""""""""""""""""""""""
    # For the style file, adjust the pie chart columns to match the new group names
    # Get the template Cytoscape style file info
    cytoscape_inputs_folder = pjoin(INPUT_FOLDER, 'Cytoscape_inputs')
    cytoscape_style_filename = metadata['Cytoscape_Format_Template_File'][job_index]

    # Adjust string in style file .xml to replace G1 through G6 "[&quot;G1&quot;,&quot;G2&quot;,&quot;G3&quot;,&quot;G4&quot;,&quot;G5&quot;,&quot;G6&quot;]" with the new group names. If any group names are missing, keep the original G#.
    cytoscape_style_filename_new = f'{job_name}_style.xml'
    with open(pjoin(cytoscape_inputs_folder, cytoscape_style_filename), 'r') as file:
        filedata = file.read()
    for i, group_name in enumerate(job_group_names):
        old_col_name = f'G{i+1}'
        filedata = filedata.replace(f'&quot;{old_col_name}&quot;', f'&quot;{group_name}&quot;')

    # Additionally, change "<visualStyle name="{cytoscape_style_filename_root}">, where {cytoscape_style_filename_root} is the string value for cytoscape_style_filename without ".xml", to be "<visualStyle name="{cytoscape_style_filename_new_root}">, where cytoscape_style_filename_new_root is the string value for cytoscape_style_filename_new without ".xml"
    cytoscape_style_filename_root = cytoscape_style_filename.split('.')[0]
    cytoscape_style_filename_new_root = cytoscape_style_filename_new.split('.')[0]
    filedata = filedata.replace(f'name="{cytoscape_style_filename_root}"', f'name="{cytoscape_style_filename_new_root}"')
        
    # Write the new style file
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

    # Based on grouping_type, filtering will be handled differently
    if grouping_type == 1:
        # Filter the network based on the intensity cutoffs. Recall that G1-G4 are mapped to new group names. The G1 vs G2 represent one pair of EXP and CTRL groups and G3 vs G4 another pair.
        # 1 filtered network will be created. If a metabolite passes filters A and B, it will be included in the filtered network.
        # Nodes that pass the filters will have value TRUE in new column 'keep_node.' For each different filtered network, the keep_node column values will be distinct.
        # Use the function p4c_network_add_filter_columns to create the filtered networks.
        # The filtered networks will be named as follows: job_name + 'Metabs_in_' + new G1 name + "_and_" + new G2 name.
        nodes_to_keep_1 = apply_exp_ctrl_filter(node_table, job_group_names[0], job_group_names[1], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_2 = apply_exp_ctrl_filter(node_table, job_group_names[2], job_group_names[3], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_1_2 = nodes_to_keep_1 & nodes_to_keep_2

        # Create the filtered network
        network_filter_suid_1_2 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1], node_table, nodes_to_keep_1_2, suid_main_network)
        # Reapply style to rename network
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_1_2, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1])

    
    elif grouping_type == 2:
        # Filter the network based on the intensity cutoffs. Recall that G1-G6 are mapped to new group names. The G1 vs G2 represent one pair of EXP and CTRL groups (call A), G3 vs G4 another pair (call B), and G5 vs G6 another pair (call C).
        # 4 filtered networks will be created. If a metabolite passes 1) filters A and B, 2) filters A and C, 3) filters B and C, and 4) filters A, B, and C, it will be included in the filtered network.
        # Nodes that pass the filters will have value TRUE in new column 'keep_node.' For each different filtered network, the keep_node column values will be distinct.
        # Use the function p4c_network_add_filter_columns to create the filtered networks.
        # The filtered networks will be named as follows: job_name + 'Metabs_in_' + new G1 name + "_and_" + new G2 name, etc.

        # Filter based on intensity cutoffs using apply_exp_ctrl_filter. Use for each pair of EXP and CTRL groups.
        nodes_to_keep_1 = apply_exp_ctrl_filter(node_table, job_group_names[0], job_group_names[1], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_2 = apply_exp_ctrl_filter(node_table, job_group_names[2], job_group_names[3], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_3 = apply_exp_ctrl_filter(node_table, job_group_names[4], job_group_names[5], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)

        # Determine overlap of nodes that pass filters A and B, A and C, and B and C
        nodes_to_keep_1_2 = nodes_to_keep_1 & nodes_to_keep_2
        nodes_to_keep_1_3 = nodes_to_keep_1 & nodes_to_keep_3
        nodes_to_keep_2_3 = nodes_to_keep_2 & nodes_to_keep_3
        nodes_to_keep_all = nodes_to_keep_1 & nodes_to_keep_2 & nodes_to_keep_3

        # Create the filtered networks and reapply style to rename network
        network_filter_suid_1_2 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1], node_table, nodes_to_keep_1_2, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_1_2, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1])

        network_filter_suid_1_3 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[2], node_table, nodes_to_keep_1_3, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_1_3, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[2])

        network_filter_suid_2_3 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[1] + "_and_" + job_group_names[2], node_table, nodes_to_keep_2_3, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_2_3, 'Metabs_in_' + job_group_names[1] + "_and_" + job_group_names[2])

        # Create the filtered network for the intersection of all 3 pairs of EXP and CTRL groups
        network_filter_suid_all = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1] + "_and_" + job_group_names[2], node_table, nodes_to_keep_all, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_all, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1] + "_and_" + job_group_names[2])

    elif grouping_type == 3:
        # Filter the network based on the intensity cutoffs. Recall that G1-G4 are mapped to new group names. The G1 vs G4 represent one pair of EXP and CTRL groups (call A), G2 vs G4 another pair (call B), and G3 vs G4 another pair (call C).
        # 4 filtered networks will be created. If a metabolite passes 1) filters A, 2) filters B, 3) filters C, and 4) filters A, B, and C, it will be included in the filtered network.

        # Filter based on intensity cutoffs using apply_exp_ctrl_filter. Use for each pair of EXP and CTRL groups.
        nodes_to_keep_1 = apply_exp_ctrl_filter(node_table, job_group_names[0], job_group_names[3], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_2 = apply_exp_ctrl_filter(node_table, job_group_names[1], job_group_names[3], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)
        nodes_to_keep_3 = apply_exp_ctrl_filter(node_table, job_group_names[2], job_group_names[3], EXP_INTENSITY_CUTOFF, CTRL_INTENSITY_CUTOFF)

         # Determine overlap of nodes that pass filters A and B, A and C, and B and C
        nodes_to_keep_1_2 = nodes_to_keep_1 & nodes_to_keep_2
        nodes_to_keep_1_3 = nodes_to_keep_1 & nodes_to_keep_3
        nodes_to_keep_2_3 = nodes_to_keep_2 & nodes_to_keep_3
        nodes_to_keep_all = nodes_to_keep_1 & nodes_to_keep_2 & nodes_to_keep_3

        # Determine overlap of nodes that pass filters A, B, and C
        nodes_to_keep_all = nodes_to_keep_1 & nodes_to_keep_2 & nodes_to_keep_3

        # Create the filtered networks and reapply style to rename network
        network_filter_suid_1_2 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1], node_table, nodes_to_keep_1_2, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_1_2, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1])

        network_filter_suid_1_3 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[2], node_table, nodes_to_keep_1_3, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_1_3, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[2])

        network_filter_suid_2_3 = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[1] + "_and_" + job_group_names[2], node_table, nodes_to_keep_2_3, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_2_3, 'Metabs_in_' + job_group_names[1] + "_and_" + job_group_names[2])
        
        # Create the filtered network for the intersection of all 3 pairs of EXP and CTRL groups
        network_filter_suid_all = p4c_network_add_filter_columns('Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1] + "_and_" + job_group_names[2], node_table, nodes_to_keep_all, suid_main_network)
        p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, cytoscape_style_filename_new), cytoscape_style_filename_new, network_filter_suid_all, 'Metabs_in_' + job_group_names[0] + "_and_" + job_group_names[1] + "_and_" + job_group_names[2])

    else:
        print(f"Error: Invalid grouping_type {grouping_type}. Must be 1, 2, or 3, or adjust script considerations.")
        exit(1)


    """""""""""""""""""""""""""""""""""""""""""""
    Save Cytoscape Session in Output Folder, Job Name folder
    """""""""""""""""""""""""""""""""""""""""""""
    # If the job_name folder does not exist yet in OUTPUT_FOLDER, create it
    job_output_folder = pjoin(OUTPUT_FOLDER, job_name)
    if not os.path.exists(job_output_folder):
        os.makedirs(job_output_folder)

    # Save the Cytoscape session
    p4c.session.save_session(filename=pjoin(OUTPUT_FOLDER, job_name, job_name + '_Cytoscape_session.cys'), overwrite_file=True)

    print('Session saved and finished filtered Cytoscape networks for ' + job_name + ', took %.2f seconds' % (time.time() - start))
    start = time.time()


    # # Plot distributions of the intensity values for the different groups
    # for group_name in job_group_names:
    #     # Get the intensity values for the group
    #     intensity_values = node_table[group_name].tolist()
    #     # Plot the distribution. Set the x-axis from 0 to 20
    #     plt.hist(intensity_values, bins=20)
    #     plt.xlim(0, 20)
    #     plt.title(f'Intensity Distribution for {group_name}')
    #     plt.xlabel('Intensity')
    #     plt.ylabel('Frequency')
    #     # show the plot
    #     plt.show()
    #     plt.close()








