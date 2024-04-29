# MetaboAnalystR Script for LCMSMS analysis of Heterologous Expression Samples
# by Lazarina Butkovich

# Sources: 
# Statistical Analysis Module Overview: 
# https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html
# Github for MetaboAnslystR:
# https://github.com/xia-lab/MetaboAnalystR/tree/master


# Workflow:
# Processed metabolomic data ->
# Univariate analysis ->
# Multivariate analysis ->
# Biological interpretation

############################################
# Setting up MetaboAnalystR (only need to do once)
############################################
# Step 1. Install package dependencies

# Specifying "always" fixed an error I was having, where ~4 packages would not update and would freeze the run
options(install.packages.compile.from.source = "always")
metanr_packages <- function(){metr_pkgs <- c("impute", "pcaMethods", "globaltest", "GlobalAncova", "Rgraphviz", "preprocessCore", "genefilter", "sva", "limma", "KEGGgraph", "siggenes","BiocParallel", "MSnbase", "multtest","RBGL","edgeR","fgsea","devtools","crmn","httr","qs")

list_installed <- installed.packages()

new_pkgs <- subset(metr_pkgs, !(metr_pkgs %in% list_installed[, "Package"]))

if(length(new_pkgs)!=0){
  
  if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
  BiocManager::install(new_pkgs)
  print(c(new_pkgs, " packages added..."))
}

if((length(new_pkgs)<1)){
  print("No new packages added...")
}
}

metanr_packages()

# Also installed the following packages: ggplot2, ggrepel, iheatmapr, ellipse

#############################################
# Step 2. Install the package

# Install devtools
install.packages("devtools")

# If above fails, try: Install MetaboAnalystR without documentation
# note: installing with documentation resulted in error, due to incorrect latex interpretation
#devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, build_vignettes = FALSE)

# To view vignettes online: (note, this does not seem to work)
#browseVignettes("MetaboAnalystR")

#############################################


#############################################
# Running MetaboAnalystR (only need to do once)
#############################################
# Statistical Analysis Module Overview: 
# https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html

# If you run into questions about MetaboAnalystR package, use the help link:
# help(package="MetaboAnalystR")



setwd('C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow')



##############
# Values to Change <-- to-do: update this section to use metadata instead
##############
# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from input_folder to get relevant parameters for job to run. Use the excel tab "Job to Run"
metadata_overall_filename = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
metadata_job_sheet = 'Job to Run'
metadata_job_column = 'Job Name'

##############
# Set working directory to input and get overall metadata table info
##############
current_dir = getwd()
# set wd to input folder to get metadata table
setwd('input')
# Import metadata table excel. The excel is in the input folder
metadata_overall = readxl::read_excel(metadata_overall_filename, sheet = metadata_job_sheet)
# Get job_name from metadata_overall first value in metadata_job_column
job_name = metadata_overall[[1,metadata_job_column]]

# Return to original working directory
setwd(current_dir)

##############
# Set working directory to temp and then job folder to get filenames for import data and job-specific metadata for MetaboAnalystR
##############
setwd('temp')
setwd(job_name)
# Job metadata file is job_name + '_metadata.tsv'
metadata_filename = paste(job_name,'_metadata.tsv',sep='')
# MetaboAnalyst input .csv file from MZmine3
# import_data_filename = paste(job_name,'_MetaboAnalyst_input.csv',sep='')
import_data_filename = 'POS_TJGIp11_metaboanalyst_previous_test.csv'

##############
# Load Libraries
##############
library(MetaboAnalystR)
library(devtools)

############################################
# Univariate Methods
############################################
##############
# Prepare Data Table
############## 
mSet<-InitDataObjects("pktable", "stat", FALSE);
# test dataset:
# mSet<-Read.TextData(mSet, "https://www.xialab.ca/api/download/metaboanalyst/human_cachexia.csv", "rowu", "disc");
# Actual dataset:
mSet<-Read.TextData(mSet, input_table_dir, "colu", "disc");
mSet<-SanityCheckData(mSet);


##############
# Replace Missing Values
############## 
# Use ReplaceMin to replace missing values in the metabolomics data with a small volume (default is half of the minimum positive value in the data)
mSet<-ReplaceMin(mSet);

##############
# Normalize Data
############## 
mSet<-PreparePrenormData(mSet);
# Normalize using tutorial's defaults:
mSet<-Normalization(mSet, "SumNorm", "NULL", "MeanCenter")
# Note:
# function form: Normalization(mSetObj, rowNorm, transNorm, scaleNorm, ref=NULL, ratio=FALSE, ratioNum=20)
# ^(Check:) Use SumNorm (for Normalization to constant sum) since I do not have a pooled sample or good reference sample
# ^(Check:)  to not transform the normalized values (otherwise, could log-transform or cubic root-transform)
# ^(Check:) set scaleNorm to NULL

# Two plot summary plot: Feature View of before and after normalization:
mSet<-PlotNormSummary(mSet, "norm_0_", format ="png", dpi=72, width=NA);

# Two plot summary plot: Sample View of before and after normalization
mSet<-PlotSampleNormSummary(mSet, "snorm_0_", format = "png", dpi=72, width=NA);

##############
# Fold-change Analysis
############## 
# Perform fold-change analysis on uploaded data, unpaired. For tutorial, set fc.thresh to 2.0 fold-change threshold, and cmp.type set to 0 for group 1 minus group 2.
mSet<-FC.Anal(mSet, 2.0, 0, FALSE)

# Plot fold-change analysis. "fc_0_" is the filename, so for custom script, set filename to a changeable variable, followed by "_log2FC_"
mSet<-PlotFC(mSet, "fc_0_", "png", 72, width=NA)

# # To view fold-change 
# mSet$analSet$fc$fc.log

##############
# T-test
############## 
# Perform T-test (parametric)
mSet<-Ttests.Anal(mSet, nonpar=F, threshp=0.05, paired=FALSE, equal.var=TRUE, "fdr", FALSE)

# Plot of the T-test results
mSet<-PlotTT(mSet, imgName = "tt_0_", format = "png", dpi = 72, width=NA)

##############
# Volcano Plot
############## 
# Perform the volcano analysis
mSet<-Volcano.Anal(mSet, FALSE, 2.0, 0, F, 0.1, TRUE, "raw")

# Create the volcano plot. "volcano_0_" is the filename, so for custom script, set filename to a changeable variable, followed by "_volcano_"
mSet<-PlotVolcano(mSet, "volcano_0_", 1, 0, format ="png", dpi=72, width=NA)

##############
# ANOVA (only for multi-group analysis)
############## 
# # Perform ANOVA
# mSet <- ANOVA.Anal(mSet, F, 0.05, "fisher")
# 
# # Plot ANOVA
# mSet <- PlotANOVA(mSet, "aov_0_", "png", 72, width=NA)

##############
# Correlation Analysis (only for multi-group analysis)
############## 
# # OPTION 1 - Heatmap specifying pearson distance and an overview
# mSet<-PlotCorrHeatMap(mSet, "corr_0_", "png", 72, width=NA, "col", "pearson", "bwm", "overview", F, F, 0.0)
# # OPTION 2 - Heatmap specifying pearson correlation and a detailed view
# mSet<-PlotCorrHeatMap(mSet, "corr_1_", format = "png", dpi=72, width=NA, "col", "spearman", "bwm", "detail", F, F, 999)

##############
# Pattern Searching (only for multi-group analysis)
############## 
# # Perform correlation analysis on a pattern (a feature of interest in this case)
# mSet<-FeatureCorrelation(mSet, "pearson", "1,6-Anhydro-beta-D-glucose")
# 
# # Plot the correlation analysis on a pattern
# mSet<-PlotCorr(mSet, "ptn_3_", format="png", dpi=72, width=NA)


############################################
# Principal Component Analysis (PCA)
############################################
# Perform PCA analysis
mSet<-PCA.Anal(mSet)

# Create PCA overview
mSet<-PlotPCAPairSummary(mSet, "pca_pair_0_", format = "png", dpi = 72, width=NA, 5)

# Create PCA scree plot
mSet<-PlotPCAScree(mSet, "pca_scree_0_", "png", dpi = 72, width=NA, 5)

# Create a 2D PCA score plot
mSet<-PlotPCA2DScore(mSet, "pca_score2d_0_", format = "png", dpi=72, width=NA, 1, 2, 0.95, 1, 0)

# Create a 3D PCA score plot
mSet<-PlotPCA3DScoreImg(mSet, "pca_score3d_0_", "png", 72, width=NA, 1,2,3, 40)

# Create a PCA loadings Plots
mSet<-PlotPCALoading(mSet, "pca_loading_0_", "png", 72, width=NA, 1,2);

# Create a PCA Biplot
mSet<-PlotPCABiplot(mSet, "pca_biplot_0_", format = "png", dpi = 72, width=NA, 1, 2)

# View the 3D interactive PLS-DA score plot
# mSet$imgSet$pca.3d
# ^ I was not able to get this 3d viewer to work

setwd(current_dir)
