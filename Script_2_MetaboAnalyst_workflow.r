# MetaboAnalystR Script for LCMSMS analysis of Heterologous Expression Samples
# by Lazarina Butkovich

# Sources: 
# Statistical Analysis Module Overview: 
# https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html
# Github for MetaboAnslystR:
# https://github.com/xia-lab/MetaboAnalystR/tree/master


# Workflow:
# Processed metabolomic data -> Univariate analysis -> Multivariate analysis -> Biological interpretation

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
metadata_overall_filename = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
metadata_job_tab = 'Job to Run'
metadata_job_column = 'Job Name'
input_table_post_str = "_MetaboAnalyst_input.csv"

##############
# Set working directory
##############
# Save the original starting directory as wd
wd = getwd()

# Get job_name from overall metadata
input_dir = paste(wd, "input", sep = "\\")
setwd(input_dir)
# Import metadata table excel. The excel is in the input folder
metadata_overall = readxl::read_excel(metadata_overall_filename, sheet = metadata_job_tab)
# Get job_name from metadata_overall first value in metadata_job_column
job_name = metadata_overall[[1,metadata_job_column]]

# Set the working directory to the job_name folder in the temp folder. This is also where output images will go
job_dir = paste(wd, "temp", job_name, sep = "\\")
# If the folder doesn't exist yet in temp, print an error and end the script
if (!dir.exists(job_dir)){
  print("Error: job folder does not exist in temp folder. Please create the temp folder in the working directory (ie: run Script 1 to create job folder and MetaboAnalyst input data table).")
  return()
}
# Create a MetaboAnalystR Output folder in the job folder
output_dir = paste(job_dir, "MetaboAnalystR_Output", sep = "\\")
if (!dir.exists(output_dir)){
  dir.create(output_dir)
}
# Empty the MetaboAnalystR Output folder if it previously existed
file.remove(list.files(output_dir, full.names = TRUE))

setwd(output_dir)


#############################################
# Univariate Methods
#############################################
##############
# Load MetaboAnalystR and Data Table
############## 
# Load MetaboAnalystR
library(MetaboAnalystR)

# For the tutorial dataset, use the following:
# data.type: conc = compound concentration data
# anal.type: stat = statistics; anal.type indicates analysis type to be performed
# paired: FALSE = data is not paired
# mSet<-InitDataObjects("conc", "stat", FALSE);
# ***For my HE LC-MS/MS data, I will want to use the following:
# data.type: pktable = peak intensity table
mSet<-InitDataObjects("pktable", "stat", FALSE);

# May want to address the warning message for font in Windows when previous section is run:
par(family="Arial")

# Import the data table from MZmine3
input_table_dir = paste(job_dir, "\\", job_name, input_table_post_str, sep='')
# Print and error message if there is not a file at the input_table_dir
if (!file.exists(input_table_dir)){
  print("Error: input table file does not exist in the job folder. Please create the input table file in the job folder.")
  return()
}
# Format for MetaboAnalystR tutorial dataset (human_cachexia.csv):
# mSet<-Read.TextData(mSet, input_table_dir, "rowu", "disc");
# ***For my HE LC-MS/MS data, I may want to use the following:
# format: colu = unpaired data, in columns, rather than paired (_p) or in rows (row_)
# lbl.type: disc = discrete data, rather than continuous (cont)
mSet<-Read.TextData(mSet, input_table_dir, "colu", "disc");
mSet<-SanityCheckData(mSet);

##############
# Replace Missing Values
############## 
# Use ReplaceMin to replace missing or 0 values in the metabolomics data with a small volume (default is half of the minimum positive value in the data)
mSet<-ReplaceMin(mSet);

##############
# Normalize Data
############## 
# Prepare data for normalization (function should always be initialized)
mSet<-PreparePrenormData(mSet);

# Tutorial's defaults for normalization:
# mSet<-Normalization(mSet, "NULL", "LogNorm", "MeanCenter", "S10T0", ratio=FALSE, ratioNum=20)

# ***For normalizing my HE LC-MS/MS data, I may want to use the following:
# mSet<-Normalization(mSet, "SumNorm", "NULL", "MeanCenter")
# function form: Normalization(mSetObj, rowNorm, transNorm, scaleNorm, ref=NULL, ratio=FALSE, ratioNum=20)
# ^(Check:) Use SumNorm (for Normalization to constant sum) since I do not have a pooled sample or good reference sample
# ^(Check:)  to not ttransform the normalized values (otherwise, could log-transform or cubic root-transform)
# ^(Check:) set scaleNorm to NULL
# remove ref because default is NULL and I do not have a reference sample
# rowNorm: "SumNorm" = normalization to constant sum
# transNorm: "NULL" = no transformation
# scaleNorm: "MeanCenter" = mean centering
# ref: NULL = no reference sample (default)
mSet<-Normalization(mSet, "SumNorm", "NULL", "MeanCenter")

# Two plot summary plot: Feature View of before and after normalization:
mSet<-PlotNormSummary(mSet, paste("Normalization_feature_", job_name, "_", sep=''), format ="png", dpi=300, width=NA);

# Two plot summary plot: Sample View of before and after normalization
mSet<-PlotSampleNormSummary(mSet, paste("Normalization_sample_", job_name, "_", sep=''), format = "png", dpi=300, width=NA);

##############
# Fold-change Analysis
############## 
# Perform fold-change analysis on uploaded data, unpaired. For tutorial, set fc.thresh to 2.0 fold-change threshold, and cmp.type set to 0 for group 1 minus group 2.
mSet<-FC.Anal(mSet, 2.0, 0, FALSE)

# Plot fold-change analysis. "fc_0_" is the filename, so for custom script, set filename to a changeable variable, followed by "_log2FC_"
mSet<-PlotFC(mSet, paste("Fold-change_",job_name, "_", sep=''), "png", 72, width=NA)

# # To view fold-change 
# mSet$analSet$fc$fc.log

##############
# T-test
############## 
# Perform T-test (parametric)
# nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
# threshp: 0.05 = threshold p-value
# paired: FALSE = data is not paired
# equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use
# pvalType = "fdr" = p-value adjustment method, "fdr" = false discovery rate
# all_results = FALSE = only show significant results (do not return T-test analysis results for all compounds, only significant?)
mSet<-Ttests.Anal(mSet, nonpar=F, threshp=0.05, paired=FALSE, equal.var=TRUE, "fdr", FALSE)
# Plot of the T-test results
mSet<-PlotTT(mSet, imgName = paste("T-test_features_",job_name, "_", sep=''), format = "png", dpi=300, width=NA)

##############
# Volcano Plot
############## 
# Perform the volcano analysis
# paired: FALSE = data is not paired
# fc.thresh: 2.0 = fold-change threshold
# cmp.type: 0 = group 1 (CTRL?) vs group 2 (EXP?)
# nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
# threshp: 0.05 = threshold p-value
# equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use
# pval.type: "raw" = use raw p-values, instead of FDR-adjusted p-values (Q: why?)
mSet<-Volcano.Anal(mSet, FALSE, 2.0, 0, F, 0.05, TRUE, "raw")

# Create the volcano plot
# plotLbl: 1 = show labels for significant features
# plotTheme: 0 = use default theme, or use 2 for less borders
mSet<-PlotVolcano(mSet, paste("Volcano_", job_name, "_", sep=''), 1, 0, format ="png", dpi=300, width=NA)

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
# mSet<-PlotCorrHeatMap(mSet, "corr_1_", format = "png", dpi=300, width=NA, "col", "spearman", "bwm", "detail", F, F, 999)

##############
# Pattern Searching (only for multi-group analysis)
############## 
# # Perform correlation analysis on a pattern (a feature of interest in this case)
# mSet<-FeatureCorrelation(mSet, "pearson", "1,6-Anhydro-beta-D-glucose")
# 
# # Plot the correlation analysis on a pattern
# mSet<-PlotCorr(mSet, "ptn_3_", format="png", dpi=300, width=NA)


##############
# Principal Component Analysis (PCA)
############## 
# Perform PCA analysis
mSet<-PCA.Anal(mSet)

# Create PCA overview
# pc.num: 5 = the number of principal components to display in the pairwise score plot
mSet<-PlotPCAPairSummary(mSet, paste("PCA_Pair_", job_name, "_", sep=''), format = "png", dpi=300, width=NA, 5)

# Create PCA scree plot
# A Scree Plot is a simple line segment plot that shows the eigenvalues for each individual PC. The scree plot is used to determine the number of components to retain in PCA, because at a high enough number of considered components, the variance explained by higher components is not meaningful.
# To visually assess the screen plot, look for the "elbow" in the plot, which is the point where the slope of the line changes the most. This is the point where the marginal gain in variance explained by adding another component is minimal.
# scree.num: 5 = the number of principal components to display in the scree plot
mSet<-PlotPCAScree(mSet, paste("PCA_Scree_", job_name, "_", sep=''), "png", dpi=300, width=NA, 5)

# Create a 2D PCA score plot, using principal components 1 and 2
mSet<-PlotPCA2DScore(mSet, paste("PCA_score_2D_1_2_", job_name, "_", sep=''), format = "png", dpi=300, width=NA, 1, 2, 0.95, 1, 0)

# Create a 3D PCA score plot, using principal components 1, 2, and 3
mSet<-PlotPCA3DScoreImg(mSet, paste("PCA_score_3D_", job_name, "_", sep=''), "png", 72, width=NA, 1,2,3, 40)

# Create a PCA loadings Plots, using principal components 1 and 2
mSet<-PlotPCALoading(mSet, paste("PCA_Loading_1_2_", job_name, "_", sep=''), "png", 72, width=NA, 1,2);

# Create a PCA Biplot, using principal components 1 and 2
mSet<-PlotPCABiplot(mSet, paste("PCA_BiPlot_1_2_", job_name, "_", sep=''), format = "png", dpi=300, width=NA, 1, 2)

# # View the 3D interactive PLS-DA score plot
# mSet$imgSet$pca.3d
# # ^ I was not able to get this 3d viewer to work

# Reset wd to starting wd
setwd(wd)