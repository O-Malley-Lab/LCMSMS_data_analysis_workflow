# LCMSMS_data_analysis_workflow
 
LC-MS/MS Data Analysis Workflow Outline

**************Part 1:**************

Before running Script 1:

ORGANIZE INPUT DATA FILES
- Manual (one-time): convert data files to .mzML format

- Manual: organize .mzML data files into job input folders
Example: "C:\Users\lazab\Desktop\python_scripts\workspace\LCMSMS_analysis_pipeline\{job input folder}\{data files folder}\{data files}"
NEED: .mzML files
Notes: create separate data file folder for EXP with base job name and CTRL samples

- Manual: (one-time) create GNPS account and WinSCP connect to massive.ucsd.edu FTP (see GNPS documentation, use same username and password as GNPS account)

- Manual (one-time): write custom code to rename filenames from long original names to shorter, descriptive names

FILL OUT METADATA EXCEL FOR JOBS TO RUN
- Manual: fill out a main metadata excel sheet with running account of job information for all jobs, as well as info for all changeable values
Excel Columns: base job name, CTRL sample name, ionization mode, EXP replicate number, CTRL replicate number, MZmine3 batch template

DETERMINE PARAMETERS FOR MZMINE3 TOOL TO RUN JOBS
- Manual (one-time): if necessary, manually create a MZmine3 job for the data files to determine pre-processing parameters. Alternatively, use previously determined parameters

Script 1 features:
- Create GNPS and MetaboAnalyst Metadata .tsv files
- Edit basic .xml parameters file for MZmine3
- Run MZmine3 in commandline using the .xml file
- Rearrange MZmine3 output files for easy GNPS input
- Use FTP to upload GNPS_input_for_job_name folder to GNPS
- Use the MZmine3 output for GNPS input to generate the MetaboAnalyst input

- Manual: run GNPS job and download GNPS output when complete

**************Part 2:**************

Script 2 features:
- Run MetaboAnalyst tool

**************Part 3:**************

Manual: determine style .xml settings for Cytoscape networks

Script 3 features:
- Python filter script
- Align data analysis results from MZmine3, MetaboAnalyst, and GNPS.


Output Excel Tabs: 
"All Peaks": unfiltered list of all peaks
"Cytoscape Import Table": include peak area data
"filtered hits": filter metabolites for those high in EXP and low in CTRL
"Upreg Likely Host Metab": metabolites present in CTRL but upregulated in EXP (only applicable for heterologous expression jobs)
"compound matches": all detected metabolites from samples with GNPS compound match
"ABMBA Standard": specify which feature is likely the ABMBA standard
"Filter parameters": record what parameters were used for the job


- Script: Adjust GNPS cytoscape network file in Python (py4cytoscape)

Import node table with additional data, create pie charts, adjust style, label compound names


**************Part 4:**************
Manual: (optional) run SIRIUS tool using MZmine3 output for SIRIUS