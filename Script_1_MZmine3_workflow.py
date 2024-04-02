"""
LCMSMS Data Analysis Workflow, Script 1: Prepare Inputs for MZmine3

@author: Lazarina Butkovich

Features include:
    Create metadata .tsv file in temp folder
"""
import pandas as pd
import os
from os.path import join as pjoin
import xml.etree.ElementTree as ET

"""
Values
""" 
input_folder = r'input' 
temp_overall_folder = r'temp'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from input_folder to get relevant parameters for job to run. Use the excel tab "Job to Run"
metadata_filename = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
metadata_job_tab = 'Job to Run'

"""
Create GNPS and MetaboAnalyst Metadata .tsv files
"""
# Import metadata table for job
metadata = pd.read_excel(pjoin(input_folder, metadata_filename), sheet_name = metadata_job_tab)

# Extract relevant information
job_name = metadata['Job Name'][0]
ionization = metadata['Ionization'][0]
exp_rep_num = metadata['EXP num replicates'][0]
ctrl_rep_num = metadata['CTRL num replicates'][0]

# If it does not already exist, make a folder in temp folder for the job name
if not os.path.exists(pjoin(temp_overall_folder, job_name)):
    os.makedirs(pjoin(temp_overall_folder, job_name))
temp_folder = pjoin(temp_overall_folder, job_name)

# Format of metadata .tsv: two columns, Filename and Class. List the filenames from folder Job Name, where filenames with 'CTRL' in them are in the 'CTRL' class and filenames without 'CTRL' in them are in the 'EXP' class.
# Create metadata .tsv file in temp folder
metadata_filename = job_name + '_metadata.tsv'
metadata_filepath = pjoin(temp_folder, metadata_filename)
# Use pandas to create metadata .tsv file
metadata_df = pd.DataFrame(columns = ['Filename', 'Class'])



# Get EXP and CTRL lists of filenames in job_name folder
mzml_filenames = os.listdir(pjoin(input_folder, job_name))
# If control filenames have 'Control' instead of "CTRL', edit filenames
for filename in mzml_filenames:
    if 'Control' in filename:
        os.rename(pjoin(input_folder, job_name, filename), pjoin(input_folder, job_name, filename.replace('Control', 'CTRL')))
# reset mzml_filenames
mzml_filenames = os.listdir(pjoin(input_folder, job_name))
# Make list of filenames in ctrl_folder_name
ctrl_filenames = [filename for filename in mzml_filenames if filename.endswith('.mzML') and 'CTRL' in filename]
# Make list of filenames in exp_folder_name
exp_filenames = [filename for filename in mzml_filenames if filename.endswith('.mzML') and 'CTRL' not in filename]

# Add filenames to metadata_df
metadata_df['Filename'] = ctrl_filenames + exp_filenames
metadata_df['Class'] = ['CTRL']*len(ctrl_filenames) + ['EXP']*len(exp_filenames)
metadata_df.to_csv(metadata_filepath, sep = '\t', index = False)

"""
Edit basic .xml parameters file
"""
# Import basic .xml parameters file using ElementTree https://docs.python.org/3/library/xml.etree.elementtree.html

# Import and parse .xml file from input_folder
mzmine3_xml_filename = 'MZmine3_batch_params_LCMSMS_HE_for_Commandline_2024_8_test_for_Python_workflow.xml'
xml_tree = ET.parse(pjoin(input_folder, mzmine3_xml_filename))

# Get root (batch mzmine_version="3.6.0"
xml_root = xml_tree.getroot()
# Look at children of root (batchstep method="...") and print attrib text for all xml_children
for child in xml_root:
    print(child.attrib)

# Update mzml filenames for MZmine3 to use
# Set xml_method_filenames_child to the child of xml_root with the following: batchstep method="io.github.mzmine.modules.io.import_rawdata_all.AllSpectralDataImportModule" parameter_version="1"
xml_method_filenames_child_str = 'batchstep[@method="io.github.mzmine.modules.io.import_rawdata_all.AllSpectralDataImportModule"][@parameter_version="1"]'
xml_method_filenames_child = xml_root.find(xml_method_filenames_child_str)


# Update metadata file to use (MS mode under CorrelateGroupingModule)

# Update GNPS export filename to be placed in temp folder
mzmine3_gnps_export_filename_root = job_name + '_gnps'
# example: Anid_HE_TJGIp11_pos_2018_gnps

# Update SIRIUS export filename to be placed in temp folder
mzmine3_sirius_export_filename = job_name + '_sirius.mgf'



"""
Use the MZmine3 output for GNPS input to generate the MetaboAnalyst input
"""
# Note, the GNPS export file has less rows than the corresponding MetaboAnalyst export file from MZmine3. For this work, I want to compare features directly between MetaboAnalyst, GNPS, etc., so having the same features input into those tools is helpful. I was unable to find a way to export the MetaboAnalyst import file from MZmine3 commandline. To get the MetaboAnalyst import file from the MZmine3 gui, you need to manually import the metadata info before being able to indicate the variable to sort groups by (ie: 'Class').

# Headers for MetaboAnalyst import file
# Note: the format for this file is 
# row 1: "Filename" in column 1, then list .mzML filenames in columns
# row 2: "Class" in column 1, then list 'CTRL' or 'EXP' in columns
# For subsequent rows, the first column is the feature identifier string, and the subsequent columns are the intensity (ie: peak area) values for each .mzML file.
# Format of feature_id = row_ID + '/' + row_mz rounded to 4 places + 'mz/' + row_rt rounded to 2 places + 'min'
# row_ID is the 'row ID' column value in the GNPS input file
# row_mz is the 'row m/z' column value in the GNPS input file
# row_rt is the 'row retention time' column value in the GNPS input file
# Sort gnps file by row ID to get the order of rows in the MetaboAnalyst import file
