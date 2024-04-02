"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 1: Prepare Inputs for MZmine3

@author: Lazarina Butkovich

Features include:
    Create metadata .tsv file in temp folder
"""""""""""""""""""""""""""""""""""""""""""""
import pandas as pd
import os
from os.path import join as pjoin
import xml.etree.ElementTree as ET

"""""""""""""""""""""""""""""""""""""""""""""
Values
""" """"""""""""""""""""""""""""""""""""""""""
input_folder = r'input' 
temp_overall_folder = r'temp'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from input_folder to get relevant parameters for job to run. Use the excel tab "Job to Run"
metadata_overall_filename = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
metadata_job_tab = 'Job to Run'


"""""""""""""""""""""""""""""""""""""""""""""
Create GNPS and MetaboAnalyst Metadata .tsv files
"""""""""""""""""""""""""""""""""""""""""""""
# Import metadata table for job
metadata = pd.read_excel(pjoin(input_folder, metadata_overall_filename), sheet_name = metadata_job_tab)

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


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
* Edit basic .xml parameters file *
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
Edit basic .xml parameters file: input filenames
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
# print nodes of xml_method_filenames_child
# for node in xml_method_filenames_child:
#     print(node.tag, node.attrib)
# Go to the 'File names' parameter node of xml_method_filenames_child. Remove all these file names and add the filenames from the job_name folder
# Print the nodes of the 'File names' parameter node in xml_method_filenames_child
xml_method_filenames_child_filenames = xml_method_filenames_child.find('parameter[@name="File names"]')
xml_mzml_input_str_start = 'C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow\\input\\'
# Remove all the filenames (<file>) in xml_method_filenames_child_filenames
for filename in xml_method_filenames_child_filenames.findall('file'):
    xml_method_filenames_child_filenames.remove(filename)
# Add filenames as nodes (<file>) of xml_method_filenames_child_filenames. Each filename will start with xml_mzml_filename_str_start, followed by the job_name, followed by \\, followed by the filename. Each node should be on a different line in the xml file
for filename in mzml_filenames:
    new_file = ET.Element('file')
    new_file.text = xml_mzml_input_str_start + job_name + '\\' + filename
    xml_method_filenames_child_filenames.append(new_file)


"""
Edit basic .xml parameters file: metadata
"""
# Update metadata file to use (<batchstep method="io.github.mzmine.modules.visualization.projectmetadata.io.ProjectMetadataImportModule" parameter_version="1">). 
xml_method_metadata_child_str = 'batchstep[@method="io.github.mzmine.modules.visualization.projectmetadata.io.ProjectMetadataImportModule"][@parameter_version="1"]'
xml_method_metadata_child = xml_root.find(xml_method_metadata_child_str)
# The node of the child to use is <parameter name="File names">
xml_method_metadata_child_filenames = xml_method_metadata_child.find('parameter[@name="File names"]')
xml_mzml_temp_str_start = 'C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow\\input\\'

# Add current_file and last_file nodes to xml_method_metadata_child. For the path, use xml_mzml_temp_str_start + job_name + '\\' + metadata_filename
current_file = ET.Element('current_file')
current_file.text = xml_mzml_temp_str_start + job_name + '\\' + metadata_filename
# Remove previous current_file
for filename in xml_method_metadata_child_filenames.findall('current_file'):
    xml_method_metadata_child_filenames.remove(filename)
xml_method_metadata_child_filenames.append(current_file)

last_file = ET.Element('last_file')
last_file.text = xml_mzml_temp_str_start + job_name + '\\' + metadata_filename
# Remove previous last_file
for filename in xml_method_metadata_child_filenames.findall('last_file'):
    xml_method_metadata_child_filenames.remove(filename)
xml_method_metadata_child_filenames.append(last_file)


"""
Edit basic .xml parameters file: MZmine3 export for GNPS input
"""
# Update export step for GNPS input (<batchstep method="io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule" parameter_version="2">). 
xml_method_gnps_child_str = 'batchstep[@method="io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule"][@parameter_version="2"]'
xml_method_gnps_child = xml_root.find(xml_method_gnps_child_str)
# The node of the child to use is <parameter name="Filename">
xml_method_gnps_child_filenames = xml_method_gnps_child.find('parameter[@name="Filename"]')
xml_mzml_temp_str_start = 'C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow\\input\\'
mzmine3_gnps_export_filename = job_name + '_gnps.mgf'

# Add current_file and last_file nodes to xml_method_gnps_child. For the path, use xml_mzml_temp_str_start + job_name + '\\' + mzmine3_gnps_export_filename
current_file = ET.Element('current_file')
current_file.text = xml_mzml_temp_str_start + job_name + '\\' + mzmine3_gnps_export_filename
# Remove previous current_file
for filename in xml_method_gnps_child_filenames.findall('current_file'):
    xml_method_gnps_child_filenames.remove(filename)
xml_method_gnps_child_filenames.append(current_file)

last_file = ET.Element('last_file')
last_file.text = xml_mzml_temp_str_start + job_name + '\\' + mzmine3_gnps_export_filename
# Remove previous last_file
for filename in xml_method_gnps_child_filenames.findall('last_file'):
    xml_method_gnps_child_filenames.remove(filename)
xml_method_gnps_child_filenames.append(last_file)


"""
Edit GNPS auto-run parameters < to-do
"""
# Within the xml_method_gnps_child, the node <parameter name="Submit to GNPS" selected="false"> (to-do: change false to true when you want to auto-run GNPS), there are nodes to edit:
# <parameter name="Meta data file" selected="true"> -- Change the value of the node to the path of the metadata file
# <parameter name="Job title"> -- change the value of the node to the job name + '_MZmine3_autorun_GNPS'
# If you are another user, you will want to change the Email, Username, and Password

# Make edits
xml_method_gnps_autorun_node = xml_method_gnps_child.find('parameter[@name="Submit to GNPS"]')
# xml_method_gnps_autorun_node.set('selected', 'true')

# Adjust metadata file for GNPS job auto-run
xml_method_gnps_autorun_metadata_node = xml_method_gnps_autorun_node.find('parameter[@name="Meta data file"]')
xml_method_gnps_autorun_metadata_node.text = xml_mzml_temp_str_start + job_name + '\\' + metadata_filename

# Adjust job title for GNPS job auto-run
xml_method_gnps_autorun_job_title_node = xml_method_gnps_autorun_node.find('parameter[@name="Job title"]')
xml_method_gnps_autorun_job_title_node.text = job_name + '_MZmine3_autorun_GNPS'

# Adjust email for GNPS job auto-run
xml_method_gnps_autorun_email_node = xml_method_gnps_autorun_node.find('parameter[@name="Email"]')
xml_method_gnps_autorun_email_node.text = 'lbutkovich@ucsb.edu'

# Adjust username for GNPS job auto-run
xml_method_gnps_autorun_username_node = xml_method_gnps_autorun_node.find('parameter[@name="Username"]')
xml_method_gnps_autorun_username_node.text = 'lbutkovich'

# Adjust password for GNPS job auto-run
xml_method_gnps_autorun_password_node = xml_method_gnps_autorun_node.find('parameter[@name="Password"]')
xml_method_gnps_autorun_password_node.text = 'password123'


"""
Edit basic .xml parameters file: MZmine3 export for SIRIUS input
"""
# Update export step for SIRIUS input (<batchstep method="io.github.mzmine.modules.io.export_features_sirius.SiriusExportModule" parameter_version="1">). 
xml_method_sirius_child_str = 'batchstep[@method="io.github.mzmine.modules.io.export_features_sirius.SiriusExportModule"][@parameter_version="1"]'
xml_method_sirius_child = xml_root.find(xml_method_sirius_child_str)
# The node of the child to use is <parameter name="Filename">
xml_method_sirius_child_filenames = xml_method_sirius_child.find('parameter[@name="Filename"]')
xml_mzml_temp_str_start = 'C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow\\input\\'
mzmine3_sirius_export_filename = job_name + '_sirius.mgf'

# Add current_file and last_file nodes to xml_method_sirius_child. For the path, use xml_mzml_temp_str_start + job_name + '\\' + mzmine3_sirius_export_filename
current_file = ET.Element('current_file')
current_file.text = xml_mzml_temp_str_start + job_name + '\\' + mzmine3_sirius_export_filename
# Remove previous current_file
for filename in xml_method_sirius_child_filenames.findall('current_file'):
    xml_method_sirius_child_filenames.remove(filename)
xml_method_sirius_child_filenames.append(current_file)

last_file = ET.Element('last_file')
last_file.text = xml_mzml_temp_str_start + job_name + '\\' + mzmine3_sirius_export_filename
# Remove previous last_file
for filename in xml_method_sirius_child_filenames.findall('last_file'):
    xml_method_sirius_child_filenames.remove(filename)
xml_method_sirius_child_filenames.append(last_file)


"""
Save new xml file
"""
# Save new xml file as a new file in temp folder
mzmine3_xml_filename_new = job_name + '_mzmine3.xml'
xml_tree.write(pjoin(temp_folder, mzmine3_xml_filename_new))


"""""""""""""""""""""""""""""""""""""""""""""
Use the MZmine3 output for GNPS input to generate the MetaboAnalyst input
"""""""""""""""""""""""""""""""""""""""""""""
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
