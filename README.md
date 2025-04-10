# Heterologous Expression of Anaerobic Gut Fungal Polyketides and Nonribosomal Peptides in Model Fungal Hosts

## Background
*In silico* genome mining tools predict many biosynthetic gene clusters for secondary metabolites from anaerobic gut fungi (phylum Neocallimastigomycota). In this research project, we sought to learn more about the products of these gene clusters via the technique of heterologous expression, wherein we did the following:
1. We inserted predicted biosynthetic genes into vectors
2. We transformed the vectors into model host microbes - in this project, *Saccharomyces cerevisiae* and *Aspergillus nidulans*
3. We cultured the transformed host microbes under expression conditions
4. We harvested culture samples (cell pellets) for data analysis and screening.

For this project, we implemented an untargeted metabolomics screen with LC-MS/MS (liquid chromatography with tandem mass spectrometry) to determine which expression groups possessed standout metabolites (by abundance and t-test statistics) relative to the negative control: the model host microbe expressing the corresponding empty vector - the transformed vector with no inserted gene to express. 

We used two approaches to analyze the untargeted LC-MS/MS datasets: (1) Feature-based molecular networking (FBMN) (Scripts 1 - 4) and (2) Classical Molecular Networking (CMN) (Script 5). Please refer to documentation on the GNPS ([Global Natural Product Social Molecular Networking](https://gnps.ucsd.edu/)) web platform for a description of the FBMN vs. CMN approaches. Broadly, FBMN and CMN use different methods to distinguish metabolite signals in the data, with FBMN determining distinct peaks (features) for metabolites and CMN only considering MS/MS spectra. For this project and set of scripts, the CMN approach is more lenient for determining if a metabolite signal is real. For the FBMN approach, we implemented multiple existing tools to perform data processing and analysis: MZmine3, MetaboAnalyst, GNPS, and SIRIUS. For the CMN approach, we used GNPS and SIRIUS.

While screening heterologous expression is a main use case for this workflow, other untargeted LC-MS/MS data sources with 2 sample groups (Experimental vs. Control) can be similarly processed and analyzed. Overall, datasets run through this workflow include the following experimental-control pairings:

| Experimental Group                                    | Control for Comparison                               |
| ------------------------------------------------- | ----------------------------------------- |
| Heterologous Expression | Empty Vector Negative Control |
| Cultured Anaerobic Gut Fungi | Media Negative Control |
| Cultured Anaerobic Gut Fungi Spiked with Epigenetic Elicitors | Cultured Anaerobic Gut Fungi Spiked with Blank Solvent |


## Associated Publication
[to be filled in after publication]


## Data Availability
Raw .mzML data files will be made publicly available on the MASSIVE data repository once the corresponding publication is published. (to-do: update after publication)


## Script Summaries: Feature-based Molecular Networking
### Script_1_MZmine3_multi-job_workflow.py
Script 1 is a Python script that automates MZmine3 preprocessing of LC-MS/MS data. It creates metadata files, modifies XML parameters (based on your manually curated parameters template file), executes MZmine3 via command line, and prepares inputs to MetaboAnalyst, GNPS, and SIRIUS analysis. The script also handles FTP upload of processed data to GNPS servers.

### Script_2_MetaboAnalyst_multi-job_workflow.r 
Script 2 is an R script that performs statistical analysis of metabolomics data using MetaboAnalystR. Features include data normalization, fold-change analysis, t-tests, and principal component analysis (PCA). The script generates visualizations and statistical outputs for metabolite abundance comparisons.

### Script_3_Cytoscape_networking_multi-job_workflow.py
Script 3 is a Python script that formats and filters molecular networks in Cytoscape. It processes GNPS networking results, incorporates MetaboAnalyst statistical data, and applies custom visual styles. The script includes filtering options to highlight metabolites of interest and generates detailed node attribute tables.

### Script_4_Volcano_Plots.py
Script 4 is a Python script that generates stylized volcano plots using MetaboAnalyst data (from Script 2). 

## Script Summary: Classical Molecular Networking
### Script_5_Groupings_GNPS_Analysis.py
to-do: fill in


## Script Details: Feature-based Molecular Networking Workflow

**************Part 1:**************
Before running Script 1:

Organize data files
- (1) Manual: convert data files to .mzML format
- (2) Manual (optional): if necessary, consider writing custom code to rename filenames from long original names to shorter, descriptive names
- (3) Manual (one-time): create "data" folder and population with .mzML data files
Example: "C:\Users\lazab\Desktop\python_scripts\workspace\LCMSMS_analysis_pipeline\data\{data files folder}\{data files}"
NEED: .mzML files
Note: create a separate {data files folder} sub-folder for EXP with base job name and CTRL samples
Note: to run the workflow with the data from the heterologous expression of gut fungal secondary metabolites, see the MASSIVE data repository once the data is public (to-do: update once published)

Setup GNPS and WinSCP accounts to run jobs on GNPS
- (4) Manual (one-time): create GNPS account and WinSCP connect to massive.ucsd.edu FTP (see GNPS documentation, use same username and password as GNPS account). Condier creating a .env file in the working directory to hold the email, username, and password information (see Script 1 code for context)

Setup metadata excel sheet with job information
- (5) Manual: fill out a main metadata excel sheet with running account of job information for all jobs, as well as info for all changeable values (see format of "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" in the input folder)
Excel Columns: Job Name, Control Folder, Ionization, RT minimum cutoff, ABMBA_Feature_Name_from_Script_1, MZmine3 batch template
Note: determine the RT minimum cutoff by viewing the chromatograms in MZmine and qualitatively approximate the metabolites that quickly come off the column. Remove these poorly separated metabolites to improve downstream data handling and statistical analysis.

Determine MZmine3 parameters
- (6) Manual: determine parameters for MZmine3 tool to run jobs and prepare a .xml parameters file template. If necessary, manually create an MZmine3 job for the data files to determine pre-processing parameters. Alternatively, use previously determined parameters.

Script 1 features:
- Creates GNPS and MetaboAnalyst Metadata .tsv files
- Edits the template .xml parameters file for MZmine3, using information in the overall metadata excel
- Runs MZmine3 in commandline using the edited .xml parameters file
- Organizes MZmine3 output files for GNPS input
- Uploads GNPS_input_for_job_name folder to GNPS via FTP
- Uses the MZmine3 output for GNPS input to generate the MetaboAnalyst input


**************Part 2:**************
Suggested: use RStudio to run Script 2.

Script 2 features:
- Runs the MetaboAnalyst tool to generate statistics, including log2 fold-change and raw p-values. See the [MetaboAnalyst GitHub repository](https://github.com/xia-lab/MetaboAnalystR) and [tutorial](https://www.metaboanalyst.ca/resources/vignettes/Introductions.html) for more information.
- Creates empty GNPS_output job sub-folders for you to later manually populate with GNPS output files (see next Part).

After running Script 2:
- (1) Manual: check correctness of statistical treatments. For example, ensure appropriate feature and sample normalization (Gaussian curve) by going to temp folder --> job folder --> MetaboAnalystR Output --> normalization .png outputs.


**************Part 3:**************
Before running Script 3:
- (1) Manual: run the [FBMN GNPS job](https://ccms-ucsd.github.io/GNPSDocumentation/featurebasedmolecularnetworking/). Once the job is complete, use the "Download Cytoscape Data" link to download GNPS outputs (zipped). Organize these outputs in job_name sub-folders (created in Script 2) in a folder "GNPS_output". Manually unzip folders contents for GNPS outputs.
- (2) Manual (one-time): determine style .xml settings for Cytoscape networks
- (3) Manual: have the Cytoscape program open in order to run Script 3

Script 3 features:
- Adjusts GNPS-generated molecular networks in Cytoscape using Python (py4cytoscape)
- Imports node table with additional data, create pie charts, adjust style, label compound names
- Aligns data analysis results from MZmine3, MetaboAnalyst, and GNPS
- Filters metabolite features in the Cytoscape network based on possible metabolites of interest (ie: highly detected in EXP samples and not in CTRL samples)
- If desired, searches data for specific compounds based on m/z and RT (with set +/- cutoffs), such as the standard ABMBA and the possible anaerobic gut fungal metabolite baumin (Swift et al. 2021).
- Outputs filtered results in Cytoscape networks and formatted excels of features.
Output Excel Tabs: 
"All Peaks Simple": unfiltered list of all peaks, with column selection simplified
"All Peaks": unfiltered list of all peaks
"Filtered Peaks of Interest": filtered peaks, using MetaboAnalyst statistics
"Upreg Likely Host Metabolites": filtered peaks for metabolites likely present in the control samples but detected more in the experimental samples
"All Cmpd Matches": all detected metabolites with MS/MS match to GNPS reference databases
"Cmpd Matches No Sus": all detected metabolites with MS/MS match to GNPS reference databases, with "Suspect related to..." compound annotations removed.
"ABMBA Standard": specifies which feature likely corresponds with the ABMBA standard added to samples
"Putative Baumin": specifies which feature likely corresponds to the possible anaerobic gut fungal metabolite baumin (Swift et al. 2021).
"Filter Parameters": a record of the specific filtering parameters used in Script 3 to generate the output excel


**************Part 4:**************

Manual: (optional) separately run SIRIUS tool using MZmine3 output for SIRIUS

Script 4 features:
to-do: fill in

## Script Details: Classical Molecular Networking Workflow

**************Part 1:**************
Script 5 features:
to-do: fill in


## Installation
### Dependencies

#### Script 1: MZmine3 Multi-job Workflow
- Python 3.8+
- Required Python modules/packages:
    - pandas
    - xml.etree.ElementTree
    - subprocess
    - shutil
    - ftplib
    - python-dotenv
- MZmine3 installation (https://github.com/mzmine/mzmine3)
- GNPS account with FTP access

#### Script 2: MetaboAnalyst Multi-job Workflow  
- R 4.0+
- Required R modules/packages:
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
- Required Python modules/packages:
    - pandas
    - py4cytoscape
    - numpy
- Cytoscape 3.9+ installation
- Running Cytoscape instance required during script execution

#### Script 4 (to-do: add)

#### Script 5 (to-do: add)


## Tutorial
For initial testing and troubleshooting of the scripts and installed dependencies:
- Consider using the "data_tutorial" folder and "Tutorial" tabs in the metadata Excel files
- Tutorial sample comparisons:
    - For FBMN, *S. cerevisiae* with p9 plasmid vs. empty vector control
    - For FBMN, *A. nidulans* with TJGIp11 plasmid vs. empty vector control
    - For CMN (Script 5), comparison of yeast with p9 vs yeast empty vector vs. *A. nidulans* with TJGIp11 vs *A. nidulans* empty vector. p9 and TJGIp11 are vectors containing a predicted non-ribosomal peptide synthetase gene from the anaerobic gut fungal strain *Anaeromyces robustus* S4.
Note: The metadata Excel files support multi-job analysis, with each row representing a separate experimental-control pairing to process.


## Support
For support with using these scripts, please contact butkovichlaza@gmail.com.


## Authors and Acknowledgements
Primary author: Lazarina Butkovich (University of California, Santa Barbara)

Thank you to Fred Krauss for feedback and assistance in writing and formatting these scripts. 

## References
Swift, C. L.; Louie, K. B.; Bowen, B. P.; Olson, H. M.; Purvine, S. O.; Salamov, A.; Mondo, S. J.; Solomon, K. V.; Wright, A. T.; Northen, T. R.; Grigoriev, I. V.; Keller, N. P.; O’Malley, M. A. Anaerobic Gut Fungi Are an Untapped Reservoir of Natural Products. PNAS 2021, 118 (18), 1–10. https://doi.org/10.1073/pnas.2019855118.