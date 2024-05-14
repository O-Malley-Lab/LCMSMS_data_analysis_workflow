"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 1: Prepare Inputs for MZmine3

@author: Lazarina Butkovich

Features include:


"""""""""""""""""""""""""""""""""""""""""""""
import pandas as pd
import os
from os.path import join as pjoin
import xml.etree.ElementTree as ET
import subprocess
import shutil
import ftplib
# Install python-dotenv
from dotenv import dotenv_values
import time
start = time.time()

"""""""""""""""""""""""""""""""""""""""""""""
Functions
"""""""""""""""""""""""""""""""""""""""""""""

def change_node_parameters(root, node_str, param_str, tag_str, dir_param):
    """
    Change the parameters of a node in the XML file.
    
    Input
    root : xml.etree.ElementTree.Element
        Root of the XML file.
    node_str : str
        Name of the node to change.
    param_str : str
        Name of the parameter to change within the node.
    tag_str : str
        Tag to use for the parameter (see text in '<...>' in .XML file).
    dir_param : list of str
        List of new values for the parameter (can be a single value).

    Output
    - None
    XML root is modified without returning anything.
    -------
    """
    child = root.find(node_str)
    child_param = child.find(param_str)
    # Remove previous values of the parameter, using tag ('<...>' text)
    for param in child_param.findall(tag_str):
        child_param.remove(param)
    # Add new values of the parameter
    for param in dir_param:
        new_param = ET.Element(tag_str)
        new_param.text = param
        child_param.append(new_param)
    return

def prettify(element, level=0):
    """
    Prettify the XML file for easier reading.
    
    Input
    element : xml.etree.ElementTree.Element
        Element to prettify.
    level : int, optional
        Level of indentation for the element.

    Output
    element : xml.etree.ElementTree.Element
        Prettified element.
    -------
    """
    indent = "    "  # 4 spaces
    if len(element):
        element.text = "\n" + indent * (level + 1)
        element.tail = "\n" + indent * level
        for child in element:
            prettify(child, level + 1)
        child.tail = "\n" + indent * level
    else:
        element.tail = "\n" + indent * level
    return element

def commandline_MZmine3(mzmine_exe_dir, xml_temp_dir_pre_str, job_name, mzmine3_xml_filename_new):
    """
    Run MZmine3 in commandline using the .xml file.

    Input
    mzmine_exe_dir : str
        String directory location of your local MZmine3 executable.
    xml_temp_dir_pre_str : str
        Start of the path for the temp folder.
    job_name : str
        Name of the job.
    mzmine3_xml_filename_new : str
        Name of the new .xml file to run MZmine3.

    Output
    exit_code : int
        Exit code of the MZmine3 process, to keep track of whether the process finished successfully.
    -------
    """
    # Command line arguments for MZmine3 in list format. '-memory' and 'all' enable use of all available memory to decrease processing time.
    command_args = [mzmine_exe_dir, '-batch', pjoin(xml_temp_dir_pre_str, job_name, mzmine3_xml_filename_new), '-memory', 'all']

    # Run MZmine3 in commandline, suppress stdout and stderr. If output is not suppressed, the buffer will fill up and the process will hang.
    process = subprocess.Popen(command_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for the process to finish and get the exit code
    print(f"PID of the process: {process.pid}")
    exit_code = process.wait()

    return exit_code

def create_metaboanalyst_ids(gnps_input_df):
    """
    Create MetaboAnalyst IDs for the MetaboAnalyst input file from the GNPS input file.

    Input
    gnps_input_df : pandas.DataFrame
        Dataframe of the GNPS input file.

    Output
    metaboanalyst_ids : list of str
        List of MetaboAnalyst IDs for the MetaboAnalyst input file.
    """

    # Sort gnps_input_df by row ID
    gnps_input_df = gnps_input_df.sort_values(by = 'row ID')
    metaboanalyst_ids = []
    # Example format of metaboanalyst_id: 1/239.0947mz/0.03min
    for id in gnps_input_df['row ID']:
        mz = round(gnps_input_df[gnps_input_df['row ID'] == id]['row m/z'].values[0], 4)
        rt = round(gnps_input_df[gnps_input_df['row ID'] == id]['row retention time'].values[0], 2)
        metaboanalyst_id = str(id) + '/' + str(mz) + 'mz/' + str(rt) + 'min'
        metaboanalyst_ids.append(metaboanalyst_id)
    return metaboanalyst_ids

def ftp_login(hostname, username, passwd):
    """
    Login to FTP server
    """
    ftp = ftplib.FTP(hostname)
    ftp.login(user=username, passwd=passwd)
    return ftp

def make_folder_if_not_exist(ftp, folder_name):
    """
    Makes a new folder if it doesn't exist
    Does nothing otherwise
    """
    # List existing folders in current directory
    existing_folders = ftp.nlst()
    # create folder if it doesn't already exist
    if folder_name not in existing_folders:
        ftp.mkd(folder_name)

def upload_file(ftp, file_path):
    """
    Upload a file to the FTP server
    """
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as file:
        ftp.storbinary('STOR ' + file_name, file)

def delete_folder(ftp, folder_name):
    """
    Delete a folder on the FTP server
    """
    # Change directory
    ftp.cwd(folder_name)

    # List files in current directory
    items = ftp.nlst()

    # Delete files
    for item in items:
        try:
            ftp.delete(item)
        except ftplib.error_perm:
            # If it fails, assume it's a directory and recurse
            delete_folder(ftp, item)

    # Change directory
    ftp.cwd('..')
    # Delete folder
    ftp.rmd(folder_name)

"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from INPUT_FOLDER to get relevant parameters for job to run. Use the excel tab "Job to Run"
METADATA_OVERALL_FILENAME = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
METADATA_JOB_TAB = 'Job to Run'

# String directory location of your local MZmine3 executable (need to install MZmine3 to enable commandline use)
MZMINE_EXE_DIR = 'D:\MZmine\MZmine.exe'

# Note, for input mzML files, all control file should have 'CTRL' in filename, otherwise script will not know which file is EXP and which is CTRL for comparison. So far, this script only handles two classes in any given job, 'CTRL' and 'EXP'.

# GNPS FTP server: massive.ucsd.edu (check GNPS documentation if this ever changes)
HOSTNAME = 'massive.ucsd.edu'
ALL_UPLOADS_FOLDER_NAME = "GNPS_upload_from_MZmine3_script_1"
# Load .env file
config = dotenv_values(".env")
# Get USERNAME and PASSWD from .env file
USERNAME = config['USERNAME']
PASSWD = config['PASSWD']
RUN_FTP = False

# PRIOR to running script, you need to manually create/generate the batch parameters .xml file for your jobs (filename specified in METADATA_OVERALL_FILENAME column 'MZmine3 batch template'). You should manually look at the parameters settings in the MZmine3 GUI to ensure they are correct for your job. This script will edit the .xml file to input the correct filenames and metadata for the job. Parameters to particularly consider:
# - Instrument-specific parameters (MZmine3 allows you to specify a setup, and you will get some default paramets)
# - Mass detection cutoffs for MS1 and MS2: in the mass detection steps, use the 'Show preview' option under setup to visually see examples of noise levels in your data. You can adjust the mass detection cutoffs to minimize noise peaks.
# - ADAP Chromatogram builder parameters: minimum instensity for consecutive scans, minimum absolute height
# Once you select parameters, you can usually use the same parameters across additional sample groups run with the same instrument and method.

"""""""""""""""""""""""""""""""""""""""""""""
Create GNPS and MetaboAnalyst Metadata .tsv files
"""""""""""""""""""""""""""""""""""""""""""""
# Import metadata table for job
metadata = pd.read_excel(pjoin(INPUT_FOLDER, METADATA_OVERALL_FILENAME), sheet_name = METADATA_JOB_TAB)

# Extract relevant information
job_name = metadata['Job Name'][0]
control_folder_name = metadata['Control Folder'][0]
ionization = metadata['Ionization'][0]
exp_rep_num = metadata['EXP num replicates'][0]
ctrl_rep_num = metadata['CTRL num replicates'][0]


# If it does not already exist, make a folder in temp folder for the job name
if not os.path.exists(pjoin(TEMP_OVERALL_FOLDER, job_name)):
    os.makedirs(pjoin(TEMP_OVERALL_FOLDER, job_name))
temp_job_folder = pjoin(TEMP_OVERALL_FOLDER, job_name)

# Empty the temp_job_folder of any files and folders
for filename in os.listdir(temp_job_folder):
    file_path = pjoin(temp_job_folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


# Format of metadata .tsv: two columns, Filename and Class. List the filenames from folder Job Name, where filenames with 'CTRL' in them are in the 'CTRL' class and filenames without 'CTRL' in them are in the 'EXP' class.
# Create metadata .tsv file in temp folder
metadata_filename = job_name + '_metadata.tsv'
metadata_filepath = pjoin(temp_job_folder, metadata_filename)
# Use pandas to create metadata .tsv file
metadata_df = pd.DataFrame(columns = ['Filename', 'Class'])

# Get EXP and CTRL lists of filenames in job_name folder. Only get the list of files that end in .mzML
# EXP .mzML filenames
job_name_folder_contents = os.listdir(pjoin(INPUT_FOLDER, job_name))
exp_filenames = []
for filename in job_name_folder_contents:
    if filename.endswith('.mzML'):
        exp_filenames.append(filename)
# CTRL .mzML filenames
ctrl_folder_contents = os.listdir(pjoin(INPUT_FOLDER, control_folder_name))
ctrl_filenames = []
for filename in ctrl_folder_contents:
    if filename.endswith('.mzML'):
        ctrl_filenames.append(filename)
# Give an error message if there are no control files
if len(ctrl_filenames) == 0:
    raise ValueError('No ' + job_name + ' control files found in folder ' + control_folder_name)
# Add exp_filenames and ctrl_filenames to mzml_filenames
mzml_filenames = ctrl_filenames + exp_filenames

# Add filenames to metadata_df
metadata_df['Filename'] = mzml_filenames
metadata_df['Class'] = ['CTRL']*len(ctrl_filenames) + ['EXP']*len(exp_filenames)
metadata_df.to_csv(metadata_filepath, sep = '\t', index = False)

# Make a copy of metadata_df for GNPS metadata file, where the headers are changed to 'filename' and 'ATTRIBUTE_GROUP'
metadata_df_gnps = metadata_df.copy()
metadata_df_gnps.columns = ['filename', 'ATTRIBUTE_GROUP']
metadata_filename_gnps = job_name + '_metadata_gnps.tsv'
metadata_filepath_gnps = pjoin(temp_job_folder, metadata_filename_gnps)
metadata_df_gnps.to_csv(metadata_filepath_gnps, sep = '\t', index = False)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
* Edit basic .xml parameters file *
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
Edit basic .xml parameters file: input filenames
"""
# Import basic .xml parameters file using ElementTree https://docs.python.org/3/library/xml.etree.elementtree.html

# Import and parse .xml file from INPUT_FOLDER. Get mzmine3_xml_filename from the metadata table, string value in column "MZmine3 batch template"
mzmine3_xml_filename = metadata['MZmine3 batch template'][0]
xml_tree = ET.parse(pjoin(INPUT_FOLDER, mzmine3_xml_filename))

# Get root (batch mzmine_version="3.6.0"
xml_root = xml_tree.getroot()
# Can look at children of root (batchstep method="...") and print attrib text for all xml_children
# for child in xml_root:
#     print(child.attrib)

# Set xml_mzml_input_str_start to the start of the path for the mzml files in the input folder, and also sete xml_mzml_temp_str_start to the start of the path for the temp folder
xml_input_dir_pre_str = os.getcwd() + '\\input\\'
xml_temp_dir_pre_str = os.getcwd() + '\\temp\\'

# Update mzml filenames for MZmine3 to use
# Set xml_method_filenames_child to the child of xml_root with the following: batchstep method="io.github.mzmine.modules.io.import_rawdata_all.AllSpectralDataImportModule" parameter_version="1"
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.io.import_rawdata_all.AllSpectralDataImportModule"][@parameter_version="1"]', 'parameter[@name="File names"]', 'file', [xml_input_dir_pre_str + job_name + '\\' + filename for filename in exp_filenames] + [xml_input_dir_pre_str + control_folder_name + '\\' + filename for filename in ctrl_filenames])


"""
Edit basic .xml parameters file: metadata
"""
# Update current_file for metadata section
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.visualization.projectmetadata.io.ProjectMetadataImportModule"][@parameter_version="1"]', 'parameter[@name="File names"]', 'current_file', [xml_temp_dir_pre_str + job_name + '\\' + metadata_filename])
# Update last_file for metadata section
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.visualization.projectmetadata.io.ProjectMetadataImportModule"][@parameter_version="1"]', 'parameter[@name="File names"]', 'last_file', [xml_temp_dir_pre_str + job_name + '\\' + metadata_filename])


"""
Edit basic .xml parameters file: MZmine3 export for GNPS input
"""
# Update export step for GNPS input, current_file parameter
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule"][@parameter_version="2"]', 'parameter[@name="Filename"]', 'current_file', [xml_temp_dir_pre_str + job_name + '\\' + job_name + '_gnps.mgf'])

# Update export step for GNPS input, last_file parameter
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule"][@parameter_version="2"]', 'parameter[@name="Filename"]', 'last_file', [xml_temp_dir_pre_str + job_name + '\\' + job_name + '_gnps.mgf'])


"""
Edit GNPS auto-run parameters
"""
# Within the xml_method_gnps_child, the node <parameter name="Submit to GNPS" selected="false">, there are nodes to edit: Meta data file, Job title, Email, Username, Password
# If you are another user, you will want to change the Email, Username, and Password

# Make edits
xml_gnps_child = xml_root.find('batchstep[@method="io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule"][@parameter_version="2"]')

xml_gnps_autorun_node = xml_gnps_child.find('parameter[@name="Submit to GNPS"]')
# xml_method_gnps_autorun_node.set('selected', 'true')

# Adjust metadata file for GNPS job auto-run
xml_gnps_autorun_metadata_subnode = xml_gnps_autorun_node.find('parameter[@name="Meta data file"]')
# Within this node, adjust current_file and last_file to be the metadata file (GNPS specific format)
current_file = ET.Element('current_file')
for filename in xml_gnps_autorun_metadata_subnode.findall('current_file'):
    xml_gnps_autorun_metadata_subnode.remove(filename)
current_file.text = xml_temp_dir_pre_str + job_name + '\\' + metadata_filename_gnps
xml_gnps_autorun_metadata_subnode.append(current_file)

last_file = ET.Element('last_file')
for filename in xml_gnps_autorun_metadata_subnode.findall('last_file'):
    xml_gnps_autorun_metadata_subnode.remove(filename)
last_file.text = xml_temp_dir_pre_str + job_name + '\\' + metadata_filename_gnps
xml_gnps_autorun_metadata_subnode.append(last_file)

# Adjust job title for GNPS job auto-run
xml_method_gnps_autorun_job_title_node = xml_gnps_autorun_node.find('parameter[@name="Job title"]')
xml_method_gnps_autorun_job_title_node.text = job_name + '_MZmine3_autorun_GNPS'

# Adjust email for GNPS job auto-run
xml_method_gnps_autorun_email_node = xml_gnps_autorun_node.find('parameter[@name="Email"]')
xml_method_gnps_autorun_email_node.text = 'lbutkovich@ucsb.edu'

# Adjust username for GNPS job auto-run
xml_method_gnps_autorun_username_node = xml_gnps_autorun_node.find('parameter[@name="Username"]')
# Get username from .env file
xml_method_gnps_autorun_username_node.text = os.getenv('USERNAME')

# Adjust password for GNPS job auto-run
xml_method_gnps_autorun_password_node = xml_gnps_autorun_node.find('parameter[@name="Password"]')
# Get password from .env file
xml_method_gnps_autorun_password_node.text = os.getenv('PASSWD')


"""
Edit basic .xml parameters file: MZmine3 export for SIRIUS input
"""
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.io.export_features_sirius.SiriusExportModule"][@parameter_version="1"]', 'parameter[@name="Filename"]', 'current_file', [xml_temp_dir_pre_str + job_name + '\\' + job_name + '_sirius.mgf'])
change_node_parameters(xml_root, 'batchstep[@method="io.github.mzmine.modules.io.export_features_sirius.SiriusExportModule"][@parameter_version="1"]', 'parameter[@name="Filename"]', 'last_file', [xml_temp_dir_pre_str + job_name + '\\' + job_name + '_sirius.mgf'])


"""
Save new xml file
"""
# Use prettify function to make the xml file more readable
xml_root_prettified = prettify(xml_root)
xml_tree = ET.ElementTree(xml_root_prettified)
# Save new xml file as a new file in temp folder
mzmine3_xml_filename_new = job_name + '_mzmine3.xml'
xml_tree.write(pjoin(temp_job_folder, mzmine3_xml_filename_new))


"""""""""""""""""""""""""""""""""""""""""""""
Use XML file to run MZmine3 in Commandline <-- to-do
"""""""""""""""""""""""""""""""""""""""""""""
# Later, implement GNPS job auto-run <-- to-do
# Print time taken to prepare files for MZmine3
print('Finished preparing files for MZmine3, took %.2f seconds' % (time.time() - start))
start = time.time()

# Run MZmine3 in commandline using the .xml file. Use the function commandline_MZmine3
exit_code = commandline_MZmine3(MZMINE_EXE_DIR, xml_temp_dir_pre_str, job_name, mzmine3_xml_filename_new)
print(f"Process finished with exit code {exit_code}")
print("MZmine3 job started for " + job_name)

# Print time taken to run MZmine3
print('Finished running MZmine3, took %.2f seconds' % (time.time() - start))
start = time.time() 

"""""""""""""""""""""""""""""""""""""""""""""
Rearrange MZmine3 output files for easy GNPS input
"""""""""""""""""""""""""""""""""""""""""""""
# Update: .mzML files are large, so instead of transferring them to a specific folder, we will leave them in their input files and only access them from there. Additionally, all other files for GNPS input will also not be moved or copied and will only be accessed and used from their original locations.

# # Create a new folder in temp, job_name folder "GNPS_input_for_" + job_name
# gnps_input_folder = pjoin(temp_job_folder, "GNPS_input_for_" + job_name)
# os.makedirs(gnps_input_folder)

# """
# .mzML files
# """

# # # Copy .mzML files from input folder to GNPS_input_for_job_name folder
# # for filename in exp_filenames:
# #     shutil.copy(pjoin(INPUT_FOLDER, job_name, filename), pjoin(gnps_input_folder, filename))

# # for filename in ctrl_filenames:
# #     shutil.copy(pjoin(INPUT_FOLDER, control_folder_name, filename), pjoin(gnps_input_folder, filename))

# """
# Quant Peak Area .csv
# """
# # Cut the quant peak area .csv file from temp folder, job_name folder to the GNPS_input_for_job_name folder
# shutil.move(pjoin(temp_job_folder, job_name + '_gnps_quant.csv'), pjoin(gnps_input_folder, job_name + '_gnps_quant.csv'))

# """
# .mgf MS2 file
# """
# # MZmine3 produces a .mgf file in the temp folder, job_name folder. Cut and paste the .mgf file to the GNPS_input_for_job_name folder
# shutil.move(pjoin(temp_job_folder, job_name + '_gnps.mgf'), pjoin(gnps_input_folder, job_name + '_gnps.mgf'))

# """
# Metadata .tsv file
# """
# # Copy the GNPS metadata .tsv from temp folder, job_name folder to the GNPS_input_for_job_name folder
# shutil.copy(metadata_filepath_gnps, pjoin(gnps_input_folder, metadata_filename_gnps))
# ""

"""""""""""""""""""""""""""""""""""""""""""""
Use FTP () to upload GNPS_input_for_job_name folder to GNPS
"""""""""""""""""""""""""""""""""""""""""""""
# Only run this section if RUN_FTP is True
if RUN_FTP:
    # Using , login to FTP server
    ftp = ftp_login(HOSTNAME, USERNAME, PASSWD)
    # If desired, uncomment below to list files in current directory
    # ftp.retrlines('LIST')
    # print('---')

    # Make a new folder named ALL_UPLOADS_FOLDER_NAME value to hold all job upload folders, if it does not already exist in the FTP server
    make_folder_if_not_exist(ftp, ALL_UPLOADS_FOLDER_NAME)

    # Change directory
    ftp.cwd(ALL_UPLOADS_FOLDER_NAME)

    # If the job_name folder already exists in the ALL_UPLOADS_FOLDER_NAME folder, delete it (we want all new files each time we run the script)
    if job_name in ftp.nlst():
        delete_folder(ftp, job_name)

    # Make a new folder named job_name to hold the GNPS input files for this job, if it does not already exist in the ALL_UPLOADS_FOLDER_NAME folder in the FTP server
    make_folder_if_not_exist(ftp, job_name)

    # Change directory
    ftp.cwd(job_name)

    # For each .mzML filename (EXP and CTRL), upload the file to the FTP server (in the job_name folder)
    for filename in exp_filenames:
        upload_file(ftp, pjoin(INPUT_FOLDER, job_name, filename))
    for filename in ctrl_filenames:
        upload_file(ftp, pjoin(INPUT_FOLDER, control_folder_name, filename))

    # Upload the quant peak area .csv file to the FTP server (in temp_job_folder)
    upload_file(ftp, pjoin(temp_job_folder, job_name + '_gnps_quant.csv'))

    # Upload the .mgf file to the FTP server (in temp_job_folder)
    upload_file(ftp, pjoin(temp_job_folder, job_name + '_gnps.mgf'))

    # Upload the metadata .tsv file to the FTP server (in temp_job_folder)
    upload_file(ftp, metadata_filepath_gnps)

    # List files in current directory
    print("Files uploaded for GNPS access: ")
    ftp.retrlines('LIST')
    print('---')

    # Logout of FTP
    ftp.quit()

    # Print time taken to prepare files for GNPS
    print('Finished FTP file transfer for GNPS, took %.2f seconds' % (time.time() - start))
    start = time.time()
else:
    print("FTP for GNPS access was not run. To run FTP, set RUN_FTP to True.")


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

# Import GNPS input file
gnps_input_filename = job_name + '_gnps_quant.csv'
gnps_input_filepath = pjoin(temp_job_folder, gnps_input_filename)
gnps_input_df = pd.read_csv(gnps_input_filepath)
# Sort by row ID
gnps_input_df = gnps_input_df.sort_values(by = 'row ID')

# Create a pandas dataframe for the metaboanalyst input file, no header
metaboanalyst_input_df = pd.DataFrame()

# First row is the 'Filename' row. Row 1 column 1 is 'Filename'. Row 1 column 2 is the first filename in the mzml_filenames list. Row 1 column 2 is the second filename in the mzml_filenames list. Continue until all filenames are listed.
# Create row 1 as a list of strings
filename_row = ['Filename'] + mzml_filenames
# Make row 1 of metaboanalyst_input_df the filename_row
metaboanalyst_input_df = pd.DataFrame(columns = filename_row)

# The second row of metaboanalyt_input_df is the 'Class' row. The values in the subsequent columns of the second row are CTRL and EXP, corresponding to the class of the samples in the mzml_filenames list.
# Create row 2 as a list of strings
class_row = ['Class']
for filename in mzml_filenames:
    if 'CTRL' in filename:
        class_row.append('CTRL')
    else:
        class_row.append('EXP')
# Make row 2 of metaboanalyst_input_df the class_row
metaboanalyst_input_df.loc[0] = class_row

# Go through each row ID in gnps_input_df and add the feature identifier string and intensity values to metaboanalyst_input_df
# example format: 1/239.0947mz/0.03min
metaboanalyst_ids = create_metaboanalyst_ids(gnps_input_df)

# Iterate through each id in metaboanalyst_ids and add the string as the value for the first column, starting at row 3 (recall, row 1 and row 2 are already filled with a different format)
i=2
for id in metaboanalyst_ids:
    # Fill in only first column of row i
    metaboanalyst_input_df.loc[i, 'Filename'] = id
    i += 1

# Now, add peak intensity values for each metaboanalyst_ids id and each filename in mzml_filenames.
# Iterate through each id in metaboanalyst_ids
for filename_gnps in mzml_filenames:
    for id in metaboanalyst_ids:
        # Get the row in gnps_input_df corresponding to the id
        gnps_row = gnps_input_df[gnps_input_df['row ID'] == int(id.split('/')[0])]
        # Get the peak intensity value for the id and the filename
        peak_intensity = gnps_row[filename_gnps + ' Peak area'].values[0]
        # Get the row number in metaboanalyst_input_df corresponding to the id
        metaboanalyst_row = metaboanalyst_input_df[metaboanalyst_input_df['Filename'] == id]
        # Fill in the peak intensity value for the filename
        metaboanalyst_input_df.loc[metaboanalyst_row.index[0], filename_gnps] = peak_intensity
        # If there is no peak intensity value for the filename, leave the cell blank
        if pd.isnull(metaboanalyst_input_df.loc[metaboanalyst_row.index[0], filename_gnps]):
            metaboanalyst_input_df.loc[metaboanalyst_row.index[0], filename_gnps] = ''

# Export the MetaboAnalyst input file to temp folder
metaboanalyst_input_filename = job_name + '_MetaboAnalyst_input.csv'
metaboanalyst_input_filepath = pjoin(temp_job_folder, metaboanalyst_input_filename)
metaboanalyst_input_df.to_csv(metaboanalyst_input_filepath, index = False)

# Print time taken to prepare files for MetaboAnalyst
print('Finished preparing files for MetaboAnalyst, took %.2f seconds' % (time.time() - start))
start = time.time()