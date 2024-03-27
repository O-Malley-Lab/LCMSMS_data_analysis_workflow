# LCMSMS_data_analysis_workflow
 
LC-MS/MS Data Analysis Workflow Outline

**************Part 1:**************

ORGANIZE INPUT DATA FILES
- Manual (one-time): convert data files to .mzML format

- Manual: organize .mzML data files into job input folders
Example: "C:\Users\lazab\Desktop\python_scripts\workspace\LCMSMS_analysis_pipeline\{job input folder}\{data files folder}\{data files}"
NEED: .mzML files
Notes: create separate data file folder for EXP with base job name and CTRL samples

- Manual: if necessary for GNPS job, upload data files with WinSCP for GNPS access

- Script (one-time): run script to rename filenames from long original names to short, descriptive names

- Manual: fill out a main metadata excel sheet with running account of job information for all jobs, as well as info for all changeable values
Excel Columns: base job name, CTRL sample name, ionization mode, EXP replicate number, CTRL replicate number

Manual (one-time): if necessary, manually create a MZmine3 job for the data files to determine pre-processing parameters

- Script: prepare MZmine3 inputs in Python 
*Use main metadata excel sheet to fetch relevant changeable values
*Changeable values: base job name, CTRL sample name, ionization mode, EXP replicate number, CTRL replicate number, MZmine parameters, MetaboAnalyst parameters, GNPS parameters
*Create metadata file for GNPS, MetaboAnalyst
*NEED: base job name, CTRL sample name, ionization mode

- Script: run MZmine3 in commandline (try GitHub CLI?) to pre-process data
Outputs: Export for MetaboAnalyst, Export/submit to GNPS-FBMN, Export for SIRIUS 

- Script: run MetaboAnalyst in R


**************Part 2:**************

- Manual: download GNPS job output

- Script: Python filter script; align data analysis results from MZmine, MetaboAnalyst, and GNPS.
Info to align:
shared name
mz (precursor mass)
RT (RTMean)
ionization
Average Peak Area EXP
Average Peak Area CTRL
Area ratio
log10 Average Peak Area EXP
log10 Average Peak Area CTRL
Compound match (from GNPS)
GNPSLibraryURL
MQScore (from GNPS)
SharedPeaks
MetaboAnalyst p-value 

Output Excel Tabs: 
"All Peaks": unfiltered list of all peaks
"Cytoscape Import Table": include peak area data
"filtered hits": filter metabolites for those high in EXP and low in CTRL
"Upreg Likely Host Metab": metabolites present in CTRL but upregulated in EXP (only applicable for heterologous expression jobs)
"compound matches": all detected metabolites from samples with GNPS compound match
"ABMBA Standard": specify which feature is likely the ABMBA standard
"Filter parameters": record what parameters were used for the job


- Script: Adjust GNPS cytoscape network file in Python (py4cytoscape) or R (RCy3) or manually
Import node table with additional data, create pie charts, adjust style, label compound names

Questions:
- Is it fine to first use the same MZmine3 parameters for all jobs?
- Is there a way to automatet running GNPS jobs?
- Is there a way to automate running SIRIUS jobs?
- For 2018 LCMSMS data and 2023 demo samples, I do not have data for cell pellet weights, so I cannot compare amounts of metabolites across samples. How should I report differences in metabolites? For example, should I not use the MetaboAnalyst p-value for how different the metabolite amounts are between 2 sample types?
- Is shared name conserved across MZmine, MetaboAnalyst, and GNPS?
