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

# # Clean global environment
# rm(list = ls())

#############################################
# Un-comment steps 1 and 2 below for the first run to install MetaboAnalystR package and dependencies:
#############################################

# #############################################
# # Setting up MetaboAnalystR (only need to do once)
# #############################################
# # Step 1. Install package dependencies
# # Specifying "always" fixed an error I was having, where ~4 packages would not update and would freeze the run
# options(install.packages.compile.from.source = "always")
# metanr_packages <- function(){metr_pkgs <- c("impute", "pcaMethods", "globaltest", "GlobalAncova", "Rgraphviz", "preprocessCore", "genefilter", "sva", "limma", "KEGGgraph", "siggenes","BiocParallel", "MSnbase", "multtest","RBGL","edgeR","fgsea","devtools","crmn","httr","qs")
  
#   list_installed <- installed.packages()
  
#   new_pkgs <- subset(metr_pkgs, !(metr_pkgs %in% list_installed[, "Package"]))
  
#   if(length(new_pkgs)!=0){
    
#     if (!requireNamespace("BiocManager", quietly = TRUE))
#       install.packages("BiocManager")
#     BiocManager::install(new_pkgs)
#     print(c(new_pkgs, " packages added..."))
#   }
  
#   if((length(new_pkgs)<1)){
#     print("No new packages added...")
#   }
# }

# metanr_packages()

# # Also installed the following packages: ggplot2, ggrepel, iheatmapr, ellipse

# #############################################
# # Step 2. Install the package

# # Install devtools
# install.packages("devtools")
# library(devtools)

# # If above fails, try: Install MetaboAnalystR without documentation
# # note: installing with documentation resulted in error, due to incorrect latex interpretation
# devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, build_vignettes = FALSE)

# # To view vignettes online: (note, this does not seem to work)
# #browseVignettes("MetaboAnalystR")

# #############################################

# #############################################
# # Running MetaboAnalystR (only need to do once)
# #############################################
# # Statistical Analysis Module Overview: 
# # https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html

# # If you run into questions about MetaboAnalystR package, use the help link:
# # help(package="MetaboAnalystR")

# #############################################
# Start of Script to Run for MetaboAnalystR
# #############################################
##############
# Values to Change
##############
# Get job_name (to-do)
job_name = 'tutorial'
input_table_filename = "human_cachexia.csv"

##############
# Set working directory
##############
# Set the working directory to the job_name folder in the temp folder. This is also where output images will go
wd = getwd()
job_dir = paste(wd, "temp", job_name, sep = "\\")
# If the folder doesn't exist yet in temp, print an error and end the script
if (!dir.exists(job_dir)){
  print("Error: job folder does not exist in temp folder. Please create the temp folder in the working directory (ie: run Script 1 to create job folder and MetaboAnalyst input data table).")
  return()
}
setwd(job_dir)


#############################################
# Univariate Methods
#############################################
##############
# Load MetaboAnalystR and Data Table
############## 
# Load MetaboAnalystR
library(MetaboAnalystR)

mSet<-InitDataObjects("conc", "stat", FALSE);
# ***For my HE LC-MS/MS data, I may want to use the following:
# mSet<-InitDataObjects("pktable", "stat", FALSE);

# May want to address the warning message for font in Windows when previous section is run:
par(family="Arial")

# Import the data table from MZmine3
input_table_dir = paste(job_dir,input_table_filename,sep='\\')
mSet<-Read.TextData(mSet, input_table_dir, "rowu", "disc");
# ***For my HE LC-MS/MS data, I may want to use the following:
# mSet<-Read.TextData(mSet, "*write out file path...*", "colu", "disc");
mSet<-SanityCheckData(mSet);

##############
# Replace Missing Values
############## 
# Use ReplaceMin to replace missing values in the metabolomics data with a small volume (default is half of the minimum positive value in the data)
mSet<-ReplaceMin(mSet);
# ***Use same for my HE LC-MS/MS data

##############
# Normalize Data
############## 
mSet<-PreparePrenormData(mSet);
# Normalize using tutorial's defaults:
mSet<-Normalization(mSet, "NULL", "LogNorm", "MeanCenter", "S10T0", ratio=FALSE, ratioNum=20)
# ***For normalizing my HE LC-MS/MS data, I may want to use the following:
# mSet<-Normalization(mSet, "SumNorm", "NULL", "MeanCenter")
# function form: Normalization(mSetObj, rowNorm, transNorm, scaleNorm, ref=NULL, ratio=FALSE, ratioNum=20)
# ^(Check:) Use SumNorm (for Normalization to constant sum) since I do not have a pooled sample or good reference sample
# ^(Check:)  to not ttransform the normalized values (otherwise, could log-transform or cubic root-transform)
# ^(Check:) set scaleNorm to NULL
# remove ref because default is NULL and I do not have a reference sample

# Two plot summary plot: Feature View of before and after normalization:
mSet<-PlotNormSummary(mSet, "norm_0_", format ="png", dpi=72, width=NA);
# ***Use same for my HE LC-MS/MS data

# Two plot summary plot: Sample View of before and after normalization
mSet<-PlotSampleNormSummary(mSet, "snorm_0_", format = "png", dpi=72, width=NA);
# ***Use same for my HE LC-MS/MS data

##############
# Fold-change Analysis
############## 
# Perform fold-change analysis on uploaded data, unpaired. For tutorial, set fc.thresh to 2.0 fold-change threshold, and cmp.type set to 0 for group 1 minus group 2.
mSet<-FC.Anal(mSet, 2.0, 0, FALSE)

# Plot fold-change analysis. "fc_0_" is the filename, so for custom script, set filename to a changeable variable, followed by "_log2FC_"
mSet<-PlotFC(mSet, "fc_0_", "png", 72, width=NA)

# To view fold-change 
mSet$analSet$fc$fc.log

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


##############
# Principal Component Analysis (PCA)
############## 
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
mSet$imgSet$pca.3d
# ^ I was not able to get this 3d viewer to work