# Heterologous Expression of Anaerobic Gut Fungal Polyketides and Nonribosomal Peptides in Model Fungal Hosts

## Background
*In silico* genome mining tools predict many biosynthetic gene clusters for secondary metabolites from anaerobic gut fungi (phylum Neocallimastigomycota). In this research project, we sought to learn more about the products of these gene clusters via the technique of heterologous expression, wherein you insert predicted biosynthetic genes into vectors, transform the vectors into model host microbes, culture the transformed host microbes under expression conditions, and harvest samples for data analysis and screening.

For this project, we mainly used an untargeted metabolomics screen with LC-MS/MS (liquid chromatography with tandem mass spectrometry) to determine which expression groups possessed standout metabolites (by abundance and t-test statistics) relative to the negative control: the model host microbe expressing the corresponding empty vector (transformed vector with no inserted gene to express). We implemented multiple existing tools to perform data processing and analysis: MZmine3, MetaboAnalyst, GNPS, and SIRIUS.

While screening heterologous expression is a main use case for this workflow, other untargeted LC-MS/MS data sources with 2 sample groups (Experimental vs. Control) can be similarly processed and analyzed. Overall, datasets run through this workflow include the following experimental-control pairings:
| Experimental Group                                    | Control for Comparison                               |
| ------------------------------------------------- | ----------------------------------------- |
| Heterologous Expression | Empty Vector Negative Control |
| Cultured Anaerobic Gut Fungi | Media Negative Control |
| Cultured Anaerobic Gut Fungi Spiked with Epigenetic Elicitors | Cultured Anaerobic Gut Fungi Spiked with Blank Solvent |

## Associated Publication
[to be filled in]

## Installation
### Dependencies

#### Script 1: MZmine3 Multi-job Workflow
- Python 3.8+
- Required Python packages:
    - pandas
    - os
    - xml.etree.ElementTree
    - subprocess
    - shutil
    - ftplib
    - python-dotenv
- MZmine3 installation (https://github.com/mzmine/mzmine3)
- GNPS account with FTP access

#### Script 2: MetaboAnalyst Multi-job Workflow  
- R 4.0+
- Required R packages:
    - MetaboAnalystR
    - impute
    - pcaMethods
    - globaltest 
    - GlobalAncova
    - Rgraphviz
    - preprocessCore
    - genefilter
    - sva
    - limma
    - KEGGgraph
    - siggenes
    - BiocParallel
    - MSnbase
    - multtest
    - RBGL
    - edgeR
    - fgsea
    - devtools
    - crmn
    - httr
    - qs
    - readxl (for reading Excel metadata)
    - ggrepel (for plot labeling)
    - ellipse (for PCA plots)
    - vegan (for statistical analysis)

#### Script 3: Cytoscape Networking Multi-job Workflow
- Python 3.8+
- Required Python packages:
    - pandas
    - py4cytoscape
    - numpy
- Cytoscape 3.9+ installation
- Running Cytoscape instance required during script execution

## Script Summaries
### Script_1_MZmine3_multi-job_workflow.py
Script 1 is a Python script that automates MZmine3 preprocessing of LC-MS/MS data. It creates metadata files, modifies XML parameters (based on your manually curated parameters template file), executes MZmine3 via command line, and prepares inputs to MetaboAnalyst, GNPS, and SIRIUS analysis. The script also handles FTP upload of processed data to GNPS servers.

### Script_2_MetaboAnalyst_multi-job_workflow.r 
Script 2 is an R script that performs statistical analysis of metabolomics data using MetaboAnalystR. Features include data normalization, fold-change analysis, t-tests, volcano plots, and principal component analysis (PCA). The script generates visualizations and statistical outputs for metabolite abundance comparisons.

### Script_3_Cytoscape_networking_multi-job_workflow.py
Script 3 is a Python script for creating and formatting molecular networks in Cytoscape. It processes GNPS networking results, integrates MetaboAnalyst statistical data, and applies custom visual styles. The script includes filtering options to highlight metabolites of interest and generates detailed node attribute tables.


## Script Details

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
Excel Columns: base job name, CTRL sample name, ionization mode, EXP replicate number, CTRL replicate number, MZmine3 batch template, RT minimum cutoff
Note: the RT minimum cutoff can be determine by viewing the TIC for the .mzML files in MZmine and qualitatively approximating the metabolites that quickly come off the column. Removing these difficult-to- improves downstream data handling and statistical analysis.

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

After runnning:
Manually check correctness of statistical treatments. For example, ensure appropriate feature and sample normalization (Gaussian curve) by going to temp folder --> job folder --> MetaboAnalystR Output --> normalization .png outputs.

**************Part 3:**************

Manual: determine style .xml settings for Cytoscape networks

Manual: Download GNPS job results: (1) 

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
Manual: (optional) separately run SIRIUS tool using MZmine3 output for SIRIUS

## Support
For support with using these scripts, please contact lbutkovich@ucsb.edu.

## Authors and Acknowledgements
Primary author: Lazarina Butkovich (University of California, Santa Barbara)

Thank you to Fred Krauss for feedback and assistance in writing and formatting these scripts. 