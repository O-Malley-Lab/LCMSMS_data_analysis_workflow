"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 3: Cytoscape Networking, Multi-job Workflow

@author: Lazarina Butkovich

"""""""""""""""""""""""""""""""""""""""""""""

import os
from os.path import join as pjoin
import pandas as pd
import py4cytoscape as p4c
import numpy as np
import time
start = time.time()
"""""""""""""""""""""""""""""""""""""""""""""
!!! Prior to running, you need to manually open Cytoscape !!!
"""""""""""""""""""""""""""""""""""""""""""""

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


"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
GNPS_OUTPUT_FOLDER = r'GNPS_output'
OUTPUT_FOLDER = r'output'

# Overall Metadata
# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from INPUT_FOLDER to get relevant parameters for job to run. Use the excel tab "Job to Run"
METADATA_OVERALL_FILENAME = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
METADATA_JOB_TAB = 'Multi-jobs'

# Cytoscape Style
CYTOSCAPE_INPUTS_FOLDER_NAME = 'Cytoscape_inputs'
# Cytoscape style .xml filenames (located in cytoscape_inputs_folder).
# Note, you need to manually edit the 'visualStyle name' in the .xml file to match the filename (without the .xml)
# CYTOSCAPE_STYLE_FILENAME = 'styles_7.xml'
CYTOSCAPE_STYLE_FILENAME = 'styles_7_label_shared_name.xml'
# CYTOSCAPE_STYLE_FILTERED_FILENAME = 'styles_7_filter_node_emphasis.xml'
CYTOSCAPE_STYLE_FILTERED_FILENAME = 'styles_7_label_shared_name_filter_node_emphasis.xml'

# MetaboAnalyst Outputs of Interest  
METABOANALYST_OUTPUT_FOLDER_NAME = 'MetaboAnalystR_Output'
# METABOANALYST_LOG2FC_FILENAME_POST_STR = "_fold_change.csv"
# METABOANALYST_TTEST_FILENAME_POST_STR = "_t_test.csv"
METABOANALYST_LOG2FC_FILENAME_POST_STR = "_fc_all.csv"
METABOANALYST_TTEST_ALL_RESULTS_FILENAME = "t_test_all.csv"
METABOANALYST_NORM_PEAK_AREA_FILENAME_POST_STR = "_normalized_data_transposed.csv"

# Columns from MetaboAnalyst Outputs to add to Cytoscape node table
LOG2FC_COLS_TO_KEEP = ['shared_name', 'log2.FC.']
T_TEST_COLS_TO_KEEP = ['shared_name', 'p.value']

# Filtering Parameters
CTRL_LOG10_CUTOFF = 5 # Log10 of CTRL must be less than this value
EXP_LOG10_CUTOFF = 6 # Log10 of EXP must be greater than this value
# MetaboAnalystR filters
METABOANALYSTR_LOG2FC_CUTOFF = 2
METABOANALYSTR_PVAL_CUTOFF = 0.05
# Filters for upregulated likely host metabolites
HOST_CTRL_LOG10_CUTOFF = 5 # Log10 of CTRL must be greater than this value
HOST_RATIO_CUTOFF = 10 # Ratio of EXP to CTRL must be greater than this value

# Standard Peaks
# ABMBA standard peak
ABMBA_MZ_POS  = 229.9811 #m/z 229.9811
ABMBA_RT_POS = 4.685 #4.685 minutes
ABMBA_MZ_NEG = 227.9655 #m/z 227.9655
ABMBA_RT_NEG = 4.8 #4.8 min
# Set deviation amounts for RT and m/z (for identifying specific peaks, such as standards)
MZ_DEV = 0.1
RT_DEV = 0.5

# Compounds of Interest
# Baumin
BAUMIN_MZ_POS = 523.1249
BAUMIN_RT_POS = 4.67

# Columns of interest
COLUMNS_OF_INTEREST = ['shared name', 'precursor mass', 'RTMean', 'log2.FC.', 'p.value', 'Compound_Name', 'Suspect_Compound_Match','Analog:MQScore', 'GNPSGROUP:EXP','GNPSGROUP:CTRL', 'GNPSGROUP:EXP_log10','GNPSGROUP:CTRL_log10', 'EXP:CTRL_ratio', 'GNPSLinkout_Cluster']


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Iterate over each job_name in metadata
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
start = time.time()
# Import metadata table for job
metadata = pd.read_excel(pjoin(INPUT_FOLDER, METADATA_OVERALL_FILENAME), sheet_name = METADATA_JOB_TAB)

for job_index, job in enumerate(metadata['Job Name']):
    # Cytoscape column names to keep (and their order) in the exported node table (input for filtering script), with columns added through for-loop
    cytoscape_cols_to_keep = [
    'shared name', 'precursor mass', 'RTMean', 'GNPSGROUP:EXP', 'GNPSGROUP:CTRL', 'componentindex', 'sum(precursor intensity)', 'NODE_TYPE','number of spectra',  'MassDiff', 'GNPSLinkout_Network', 'GNPSLinkout_Cluster', 'Instrument', 'PI', 'GNPSLibraryURL', 'Analog:MQScore', 'SpectrumID', 'Analog:SharedPeaks','Compound_Name','log2.FC.', 'p.value',
    ]

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Main Part 1: Prepare Cytoscape Network and Format Node Table
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""
    Get Job Info
    """""""""""""""""""""""""""""""""""""""""""""
    # Extract relevant information
    job_name = metadata['Job Name'][job_index]
    control_folder_name = metadata['Control Folder'][job_index]
    ionization = metadata['Ionization'][job_index]

    if ionization == 'POS':
        abmba_mz = ABMBA_MZ_POS
        abmba_rt = ABMBA_RT_POS
    elif ionization == 'NEG':
        abmba_mz = ABMBA_MZ_NEG
        abmba_rt = ABMBA_RT_NEG
    else:
        raise ValueError(f'Invalid ionization mode for job {job_name}. Must be either "POS" or "NEG".')

    # Define cytoscape inputs folder 
    cytoscape_inputs_folder = pjoin(INPUT_FOLDER, CYTOSCAPE_INPUTS_FOLDER_NAME)


    """""""""""""""""""""""""""""""""""""""""""""
    Open Cytoscape network from GNPS output .graphml and sete visual style
    """""""""""""""""""""""""""""""""""""""""""""
    # GNPS Output folder (later, change this to be just the job_name in TEMP_OVERALL_FOLDER, rather than a testing folder)
    gnps_output_job_folder = pjoin(GNPS_OUTPUT_FOLDER, job_name)

    # Destroy any networks already in the Cytsocape session
    p4c.networks.delete_all_networks()

    # GNPS Outputs are located in temp_folder
    # Find the .graphml file in the GNPS output folder. Upload into Cytoscape
    gnps_graphml_file = [f for f in os.listdir(gnps_output_job_folder) if f.endswith('.graphml')][0]

    # Import the GNPS output into Cytoscape
    p4c.import_network_from_file(pjoin(gnps_output_job_folder, gnps_graphml_file))

    # Get the SUID of the current network
    suid_main_network = p4c.get_network_suid()

    # Set the visual style based on CYTOSCAPE_STYLE_FILENAME
    p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, CYTOSCAPE_STYLE_FILENAME), CYTOSCAPE_STYLE_FILENAME, suid_main_network, job_name)


    """""""""""""""""""""""""""""""""""""""""""""
    Import GNPS Quant Data (Raw Peak Area Values)
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

    # Load peak area data into the node table
    node_table_add_columns(gnps_quant_data, peak_area_cols_to_keep, suid_main_network, 'row ID')


    """""""""""""""""""""""""""""""""""""""""""""
    Import MetaboAnalyst Data
    """""""""""""""""""""""""""""""""""""""""""""
    # Import and load log2fc data. Values >0 are upregulated in EXP.
    log2fc_filename = job_name + METABOANALYST_LOG2FC_FILENAME_POST_STR
    log2fc_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, METABOANALYST_OUTPUT_FOLDER_NAME, log2fc_filename))

    # Convert MetaboAnalyst_ID name to a column "shared name", where the value in the column prior to the first '/' is the shared name value
    log2fc_data['shared_name'] = log2fc_data['MetaboAnalyst_ID'].apply(lambda x: x.split('/')[0])

    # Rename "Log2_FoldChange" column to "log2.FC."
    log2fc_data = log2fc_data.rename(columns={'Log2_FoldChange': 'log2.FC.'})
    node_table_add_columns(log2fc_data, LOG2FC_COLS_TO_KEEP, suid_main_network, 'shared_name')

    # Import and load t-test data.
    t_test_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, METABOANALYST_OUTPUT_FOLDER_NAME, METABOANALYST_TTEST_ALL_RESULTS_FILENAME))

    # Rename the first column (unnamed) to 'MetaboAnalyst_ID'
    t_test_data = t_test_data.rename(columns={t_test_data.columns[0]: 'MetaboAnalyst_ID'})

    # Convert MetaboAnalyst_ID name to a column "shared name", where the value in the column prior to the first '/' is the shared name value
    t_test_data['shared_name'] = t_test_data['MetaboAnalyst_ID'].apply(lambda x: x.split('/')[0])
    node_table_add_columns(t_test_data, T_TEST_COLS_TO_KEEP, suid_main_network, 'shared_name')

    # Import normalized peak area data
    norm_peak_area_filename = job_name + METABOANALYST_NORM_PEAK_AREA_FILENAME_POST_STR
    norm_peak_area_data = pd.read_csv(pjoin(TEMP_OVERALL_FOLDER, job_name, METABOANALYST_OUTPUT_FOLDER_NAME, norm_peak_area_filename))

    # Keep all normalized peak area columns except for MetaboAnalyst_ID
    norm_peak_area_data = norm_peak_area_data.drop(columns=['MetaboAnalyst_ID'])

    # Rename normalized data columns (not shared_name) to end with '_normalized'
    norm_peak_area_data.columns = [col + '_normalized' if col != 'shared_name' else col for col in norm_peak_area_data.columns]
    norm_data_cols_to_keep = norm_peak_area_data.columns

    # Load normalized peak area data into the node table
    node_table_add_columns(norm_peak_area_data, norm_data_cols_to_keep, suid_main_network, 'shared_name')


    """""""""""""""""""""""""""""""""""""""""""""
    Generate log10 values of Peak Area and Average Peak Area Columns
    """""""""""""""""""""""""""""""""""""""""""""
    # Generate log10 values of the peak area columns (peak_area_cols_raw_data). Label as the original column name with '_log10'
    log10_peak_area_cols = [col + '_log10' for col in peak_area_cols_raw_data]
    # Add data for log10 values
    for col in peak_area_cols_raw_data:
        gnps_quant_data[col + '_log10'] = gnps_quant_data[col].apply(lambda x: None if x == 0 else np.log10(x))

    # Add the key column (row ID) to the log10 peak area columns
    log10_peak_area_cols.insert(0, 'row ID')

    # Load log10 peak area data into the node table
    node_table_add_columns(gnps_quant_data, log10_peak_area_cols, suid_main_network, 'row ID')

    # Average peak area columns: GNPSGROUP:CTRL and GNPSGROUP:EXP
    # Generate log10 values for average peak area columns (GNPSGROUP:CTRL and GNPSGROUP:EXP). Label as the original column name with '_log10'
    avg_peak_area_cols = ['GNPSGROUP:CTRL', 'GNPSGROUP:EXP']

    # Get the node table as a dataframe
    node_table_temp = p4c.tables.get_table_columns(network=suid_main_network, table='node')

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
    node_table_add_columns(node_table_temp, avg_peak_area_cols_log10, suid_main_network, 'name')

    # Generate an EXP:CTRL_ratio column
    node_table_temp['EXP:CTRL_ratio'] = node_table_temp['GNPSGROUP:EXP'] / node_table_temp['GNPSGROUP:CTRL']
    # Replace inf values with a large number [np.inf, -np.inf], 10000000000 (E10) and -10000000000 (-E10), respectively
    node_table_temp['EXP:CTRL_ratio'] = node_table_temp['EXP:CTRL_ratio'].replace([np.inf, -np.inf], [10000000000, -10000000000])
    # Round to 2 decimal places. Skip if value is None.
    node_table_temp['EXP:CTRL_ratio'] = node_table_temp['EXP:CTRL_ratio'].apply(lambda x: round(x, 2) if x is not None else None)
    # Add EXP:CTRL_ratio to cytoscape_cols_to_keep
    cytoscape_cols_to_keep.append('EXP:CTRL_ratio')
    # Load EXP:CTRL_ratio data into the node table
    node_table_add_columns(node_table_temp, ['name', 'EXP:CTRL_ratio'], suid_main_network, 'name')
    # Reset index
    node_table_temp = node_table_temp.reset_index(drop=True)


    """""""""""""""""""""""""""""""""""""""""""""
    In Compound_Name column, cut-paste values with "Suspect" to a new column "Suspect_Compound_Match"
    """""""""""""""""""""""""""""""""""""""""""""
    # Get Compound_Name column values in a dataframe with 'name' as the key column
    compound_name_df = node_table_temp.copy()
    compound_name_df = compound_name_df[['name', 'Compound_Name']]
    suspect_compound_match_col_values = []
    for index, row in compound_name_df.iterrows():
        # First, determine if the value is none. This would cause a TypeError if trying to search for 'Suspect' in the value
        if pd.isnull(row['Compound_Name']):
            suspect_compound_match_col_values.append(None)
        elif 'Suspect' in row['Compound_Name']:
            suspect_compound_match_col_values.append(row['Compound_Name'])
            # Replace the value in 'Compound_Name' with None
            compound_name_df.at[index, 'Compound_Name'] = None
        else:
            suspect_compound_match_col_values.append(None)
            
    # Add the new values suspect_compound_match_col_values to column 'Suspect_Compound_Match' in the compound_name_df dataframe. Use .loc to avoid SettingWithCopyWarning
    for index, value in enumerate(suspect_compound_match_col_values):
        compound_name_df.loc[index, 'Suspect_Compound_Match'] = value
    # Add 'Suspect_Compound_Match' to cytoscape_cols_to_keep
    cytoscape_cols_to_keep.append('Suspect_Compound_Match')
    # Load 'Suspect_Compound_Match' data into the node table
    node_table_add_columns(compound_name_df, ['name', 'Suspect_Compound_Match'], suid_main_network, 'name')
    # Delete the previous 'Compound_Name' column from the node table
    p4c.tables.delete_table_column('Compound_Name', table='node', network=suid_main_network)
    # Load 'Compound_Name' data from edited compound_name_df into the node table, replacing the previous 'Compound_Name' column.
    node_table_add_columns(compound_name_df, ['name', 'Compound_Name'], suid_main_network, 'name')


    """""""""""""""""""""""""""""""""""""""""""""
    Export Entire Node Table
    """""""""""""""""""""""""""""""""""""""""""""
    # Export the entire node table to an excel file
    node_table = p4c.tables.get_table_columns(network=suid_main_network, table='node')
    # Specify columns and their order to keep in the exported node table
    node_table_simplified = node_table.copy()
    node_table_simplified = node_table_simplified[cytoscape_cols_to_keep]
    # Export the node table to an excel file
    node_table_simplified.to_excel(pjoin(TEMP_OVERALL_FOLDER, job_name, job_name + '_Cytoscape_node_table.xlsx'), index=False)


    """""""""""""""""""""""""""""""""""""""""""""
    Reload the Simplified Node Table into Cytoscape to Replace the Current Node Table
    """""""""""""""""""""""""""""""""""""""""""""
    # Delete all columns of the current node table except for 'name', 'SUID', 'shared name', 'selected', which are immutable
    node_table_cols_complex = p4c.tables.get_table_column_names(network=suid_main_network, table='node')
    node_table_cols_complex.remove('name')
    node_table_cols_complex.remove('SUID')
    node_table_cols_complex.remove('shared name')
    node_table_cols_complex.remove('selected')

    for col in node_table_cols_complex:
        p4c.tables.delete_table_column(col, table='node', network=suid_main_network)

    # Load the simplified node table into Cytoscape
    p4c.tables.load_table_data(node_table_simplified, data_key_column='name', table_key_column='name', network=suid_main_network)

    print('Finished main Cytoscape network for ' + job_name + ', took %.2f seconds' % (time.time() - start))
    start = time.time()

    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Main Part 2: Filtering Script for Output Excel
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""
    Create new dataframe of node_table to filter for peaks of interest, using MetaobanalystR stats
    """""""""""""""""""""""""""""""""""""""""""""
    table_filtered = node_table.copy()

    # First, filter for peaks that have a log2.FC. value greater than LOG2FC_CUTOFF
    table_filtered = table_filtered[table_filtered['log2.FC.'] > METABOANALYSTR_LOG2FC_CUTOFF]

    # Second, filter for peaks that have a p.value less than PVAL_CUTOFF
    table_filtered = table_filtered[table_filtered['p.value'] < METABOANALYSTR_PVAL_CUTOFF]

    # Third, filter for peaks that have a GNPSGROUP:CTRL_log10 less than the cutoff. Set table_filtered['GNPSGROUP:CTRL_log10'] to float type (not str) to avoid error in filtering. You should include rows that have a value of 'None' in the column, as these are peaks that were not detected in the control samples. Note that NaN is float type. Ensure that the column is float type. Then filter.
    table_filtered['GNPSGROUP:CTRL_log10'] = table_filtered['GNPSGROUP:CTRL_log10'].astype(float)
    table_filtered = table_filtered[(table_filtered['GNPSGROUP:CTRL_log10'] < CTRL_LOG10_CUTOFF) | (table_filtered['GNPSGROUP:CTRL_log10'].isnull())]

    # Fourth, filter for peaks that have a GNPSGROUP:EXP_log10 greater than the cutoff. Set table_filtered['GNPSGROUP:EXP_log10'] to float type (not str) to avoid error in filtering
    table_filtered['GNPSGROUP:EXP_log10'] = table_filtered['GNPSGROUP:EXP_log10'].astype(float)
    table_filtered = table_filtered[table_filtered['GNPSGROUP:EXP_log10'] > EXP_LOG10_CUTOFF]

    # Sort table_filtered in descending order by GNPSGROUP:EXP_log10
    table_filtered = table_filtered.sort_values(by = 'GNPSGROUP:EXP_log10', ascending = False)
    
    # Reset index
    table_filtered = table_filtered.reset_index(drop = True)


    """""""""""""""""""""""""""""""""""""""""""""
    Create new dataframe of upregulated likely host metabolites
    """""""""""""""""""""""""""""""""""""""""""""
    table_host_upreg = node_table.copy()

    # First, filter for peaks that have a GNPSGROUP:CTRL_log10 greater than the cutoff. Set table_host_upreg['GNPSGROUP:CTRL_log10'] to float type (not str) to avoid error in filtering
    table_host_upreg['GNPSGROUP:CTRL_log10'] = table_host_upreg['GNPSGROUP:CTRL_log10'].astype(float)
    table_host_upreg = table_host_upreg[table_host_upreg['GNPSGROUP:CTRL_log10'] > HOST_CTRL_LOG10_CUTOFF]

    # Second, filter for peaks that have a EXP:CTRL_ratio greater than the HOST_RATIO_CUTOFF
    table_host_upreg = table_host_upreg[table_host_upreg['EXP:CTRL_ratio'] > HOST_RATIO_CUTOFF]

    # Sort table_host_upreg in descending order by GNPSGROUP:EXP_log10
    table_host_upreg = table_host_upreg.sort_values(by = 'GNPSGROUP:EXP_log10', ascending = False)
    # Reset index
    table_host_upreg = table_host_upreg.reset_index(drop = True)


    """""""""""""""""""""""""""""""""""""""""""""
    Write a table listing potential ABMBA standard peaks
    """""""""""""""""""""""""""""""""""""""""""""
    table_ABMBA = node_table.copy()

    # First, filter for peaks that have a m/z ('precursor mass') within the deviation of the ABMBA standard m/z
    table_ABMBA = table_ABMBA[(table_ABMBA['precursor mass'] > abmba_mz - MZ_DEV) & (table_ABMBA['precursor mass'] < abmba_mz + MZ_DEV)]

    # Second, filter for peaks that have a RT ('RTMean') within the deviation of the ABMBA standard RT
    table_ABMBA = table_ABMBA[(table_ABMBA['RTMean'] > abmba_rt - RT_DEV) & (table_ABMBA['RTMean'] < abmba_rt + RT_DEV)]

    # Sort table_ABMBA in ascending order by name
    table_ABMBA = table_ABMBA.sort_values(by = 'name', ascending = True)
    # Reset index
    table_ABMBA = table_ABMBA.reset_index(drop = True)

    """""""""""""""""""""""""""""""""""""""""""""
    Write a table listing potential baumin peaks
    """""""""""""""""""""""""""""""""""""""""""""
    # if positive ionization mode, use BAUMIN_MZ_POS and BAUMIN_RT_POS. Otherwise, skip searching for baumin.
    if ionization == 'POS':
        table_baumin = node_table.copy()

        # First, filter for peaks that have a m/z ('precursor mass') within the deviation of the baumin standard m/z
        table_baumin = table_baumin[(table_baumin['precursor mass'] > BAUMIN_MZ_POS - MZ_DEV) & (table_baumin['precursor mass'] < BAUMIN_MZ_POS + MZ_DEV)]

        # Second, filter for peaks that have a RT ('RTMean') within the deviation of the baumin standard RT
        table_baumin = table_baumin[(table_baumin['RTMean'] > BAUMIN_RT_POS - RT_DEV) & (table_baumin['RTMean'] < BAUMIN_RT_POS + RT_DEV)]

        # Sort table_baumin in ascending order by name
        table_baumin = table_baumin.sort_values(by = 'name', ascending = True)

        # Reset index
        table_baumin = table_baumin.reset_index(drop = True)


    """""""""""""""""""""""""""""""""""""""""""""
    Write a table with all peaks with compound matches to databases. This includes potential primary metabolites. Have a version without suspect compounds and a version with suspect compounds.
    """""""""""""""""""""""""""""""""""""""""""""
    table_all_matched_cmpds= node_table.copy()

    # First, filter for peaks that have a 'Compound_Name' that is not NaN
    table_all_matched_cmpds = table_all_matched_cmpds[table_all_matched_cmpds['Compound_Name'].notna()]

    # table_matched_cmpds_no_suspect is table_all_matched_cmpds with any 'Compound_Name' that contains string 'Suspect' removed
    table_matched_cmpds_no_suspect = table_all_matched_cmpds.copy()
    table_matched_cmpds_no_suspect = table_all_matched_cmpds[~table_all_matched_cmpds['Compound_Name'].str.contains('Suspect', na = False)]


    """""""""""""""""""""""""""""""""""""""""""""
    Formatted Simplest Table
    """""""""""""""""""""""""""""""""""""""""""""
    table_formatted = node_table[COLUMNS_OF_INTEREST].copy()

    # Make the values in "GNPSGROUP:EXP","GNPSGROUP:CTRL", "GNPSGROUP:EXP_log10","GNPSGROUP:CTRL_log10", 'EXP:CTRL_ratio' be in scientific notation and rounded to 2 decimal places
    columns_sci_notation = ['GNPSGROUP:EXP','GNPSGROUP:CTRL', 'p.value']
    # Make in scientific notation and round to 2 decimal places
    table_formatted[columns_sci_notation] = table_formatted[columns_sci_notation].applymap(lambda x: '{:.2e}'.format(x))

    columns_to_round = ['log2.FC.','GNPSGROUP:EXP_log10','GNPSGROUP:CTRL_log10']
    # Round to 2 decimal places. Skip if value is None.
    for col in columns_to_round:
        table_formatted[col] = pd.to_numeric(table_formatted[col], errors='coerce')
        table_formatted[col] = table_formatted[col].round(2)


    """""""""""""""""""""""""""""""""""""""""""""
    Make a table of the parameters used in this script
    """""""""""""""""""""""""""""""""""""""""""""
    parameters = pd.DataFrame({'Parameter': ['METABOANALYSTR_LOG2FC_CUTOFF', 'METABOANALYSTR_PVAL_CUTOFF', 'CTRL_LOG10_CUTOFF', 'EXP_LOG10_CUTOFF', 'HOST_CTRL_LOG10_CUTOFF', 'HOST_RATIO_CUTOFF', 'MZ_DEV', 'RT_DEV','ABMBA_mz','ABMBA_RT'], 'Value': [METABOANALYSTR_LOG2FC_CUTOFF, METABOANALYSTR_PVAL_CUTOFF, CTRL_LOG10_CUTOFF, EXP_LOG10_CUTOFF, HOST_CTRL_LOG10_CUTOFF, HOST_RATIO_CUTOFF, MZ_DEV, RT_DEV, abmba_mz, abmba_rt]})


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Main Part 3: Create Filtered Cytoscape Networks for Peaks of Interest
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""
    Create filtered network for MetaboAnalystR filters
    """""""""""""""""""""""""""""""""""""""""""""
    nodes_to_keep_metaboanalystr = node_table_temp['log2.FC.'] > METABOANALYSTR_LOG2FC_CUTOFF
    nodes_to_keep_metaboanalystr = nodes_to_keep_metaboanalystr & (node_table_temp['p.value'] < METABOANALYSTR_PVAL_CUTOFF)

    # Include rows that have a value of 'None' in the column, as these are peaks that were not detected in the control samples
    nodes_to_keep_metaboanalystr = nodes_to_keep_metaboanalystr & ((node_table_temp['GNPSGROUP:CTRL_log10'] < CTRL_LOG10_CUTOFF) | (node_table_temp['GNPSGROUP:CTRL_log10'].isnull()))
    nodes_to_keep_metaboanalystr = nodes_to_keep_metaboanalystr & (node_table_temp['GNPSGROUP:EXP_log10'] > EXP_LOG10_CUTOFF)

    suid_target = p4c_network_add_filter_columns("MetaboAnalystR_Filter", node_table_temp, nodes_to_keep_metaboanalystr, suid_main_network, key_col='shared name', componentindex_colname='componentindex')
    p4c_import_and_apply_cytoscape_style(pjoin(cytoscape_inputs_folder, CYTOSCAPE_STYLE_FILTERED_FILENAME), CYTOSCAPE_STYLE_FILTERED_FILENAME, suid_target, job_name + '_MetaboAnalystR_Filter')


    """""""""""""""""""""""""""""""""""""""""""""
    Save Cytoscape Session in Output Folder, Job Name folder
    """""""""""""""""""""""""""""""""""""""""""""
    # If the job_name folder does not exist yet in OUTPUT_FOLDER, create it
    if not os.path.exists(pjoin(OUTPUT_FOLDER, job_name)):
        os.makedirs(pjoin(OUTPUT_FOLDER, job_name))
    
    # Save the Cytoscape session
    p4c.session.save_session(filename=pjoin(OUTPUT_FOLDER, job_name, job_name + '_Cytoscape_session.cys'), overwrite_file=True)

    print('Session saved and finished filtered Cytoscape networks for ' + job_name + ', took %.2f seconds' % (time.time() - start))
    start = time.time()


    """""""""""""""""""""""""""""""""""""""""""""
    Format Column Order in Dataframes for Excel Sheets
    """""""""""""""""""""""""""""""""""""""""""""
    # For each dataframe written to a sheet, have the first columns be COLUMNS_OF_INTEREST ('shared name', 'precursor mass', 'RTMean', 'log2.FC.', 'p.value', 'GNPSGROUP:EXP','GNPSGROUP:CTRL', 'GNPSGROUP:EXP_log10','GNPSGROUP:CTRL_log10', 'EXP:CTRL_ratio',  'GNPSLinkout_Cluster','Compound_Name','Analog:MQScore') and then the rest of the columns in the dataframe
    # For each dataframe, reorder columns to have COLUMNS_OF_INTEREST first
    dataframes = {
        'table_formatted': table_formatted,
        'node_table': node_table,
        'table_filtered': table_filtered, 
        'table_host_upreg': table_host_upreg,
        'table_all_matched_cmpds': table_all_matched_cmpds,
        'table_matched_cmpds_no_suspect': table_matched_cmpds_no_suspect,
        'table_ABMBA': table_ABMBA
    }

    if ionization == 'POS':
        dataframes['table_baumin'] = table_baumin

    for name, df in dataframes.items():
        # Get columns that are in both COLUMNS_OF_INTEREST and df.columns
        valid_cols = [col for col in COLUMNS_OF_INTEREST if col in df.columns]
        # Get remaining columns that are not in COLUMNS_OF_INTEREST
        other_cols = [col for col in df.columns if col not in COLUMNS_OF_INTEREST]
        # Reorder columns with valid COLUMNS_OF_INTEREST first, then other columns
        dataframes[name] = df.reindex(columns=valid_cols + other_cols)

    # Update original variables with reordered dataframes
    table_formatted = dataframes['table_formatted']
    node_table = dataframes['node_table']
    table_filtered = dataframes['table_filtered']
    table_host_upreg = dataframes['table_host_upreg']
    table_all_matched_cmpds = dataframes['table_all_matched_cmpds']
    table_matched_cmpds_no_suspect = dataframes['table_matched_cmpds_no_suspect']
    table_ABMBA = dataframes['table_ABMBA']

    if ionization == 'POS':
        table_baumin = dataframes['table_baumin']
    

    """""""""""""""""""""""""""""""""""""""""""""
    Write each dataframe to a different sheet in output excel
    """""""""""""""""""""""""""""""""""""""""""""
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
    if ionization == 'POS':
        table_baumin.to_excel(writer, sheet_name = 'Putative Baumin', index = False)
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
    # Print time taken to write the excel file

print("All jobs complete.")