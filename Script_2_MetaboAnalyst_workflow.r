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
# Functions
##############
# format_output_csv_data <- function(csv_filename, job_name){
#   new_filename = paste(job_name, "_", csv_filename, sep='')
#   
#   # Rename file as 
#   file.rename(csv_filename, new_filename)
#   
#   # Import the csv file as a pandas dataframe
#   data = read.csv(new_filename)
#   
#   # Name the first column header 'MetaboAnalyst ID'
#   colnames(data)[1] = "MetaboAnalyst_ID"
#   
#   # Add a column with header 'shared name', where the values are the string prior to the '/' in the first column of data
#   data$shared_name = sapply(strsplit(as.character(data$MetaboAnalyst_ID), "/"), "[", 1)
#   
#   # Save dataframe
#   write.csv(data, new_filename, row.names = FALSE)
# }

##############
# Values to Change
##############
setwd("C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow")
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
wd_input = getwd()
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
wd_output = getwd()


#############################################
# Univariate Methods
#############################################
##############
# Load MetaboAnalystR and Data Table
############## 
# Load MetaboAnalystR
library(MetaboAnalystR)

# Initialize data object mSet for MetaboAnalystR
# data.type: pktable = peak intensity table
mSet<-InitDataObjects("pktable", "stat", FALSE);

# Import the peak intensity data table from MZmine3 (Script 1)
input_table_dir = paste(job_dir, "\\", job_name, input_table_post_str, sep='')
# Print an error message if there is not a file at the input_table_dir
if (!file.exists(input_table_dir)){
  print("Error: input table file does not exist in the job folder. Please create the input table file in the job folder.")
  return()
}

# Read the peak intensity data table into mSet
# format: colu = unpaired data, in columns, rather than paired (_p) or in rows (row_)
# lbl.type: disc = discrete data, rather than continuous (cont)
mSet<-Read.TextData(mSet, input_table_dir, "colu", "disc");
mSet<-SanityCheckData(mSet);


##############
# Replace Missing Values
############## 
# Replace missing or 0 values in the metabolomics data with a small volume (default is half of the minimum positive value in the data)
mSet<-ReplaceMin(mSet);

##############
# Data Filtering (Currently not implemented)
############## 
# The following info on Data Filtering is from the web version of MetaboAnalyst one-factor statistical analysis workflow
# The purpose of the data filtering is to identify and remove variables that are unlikely to be of use when modeling the data
# These non-informative variables include those with (1) low repeatability, as characterized by those with high percent RSD (relative standard deviation), (2) near-constant variables, and (3) very small values.

# FilterVariable function in MetaboAnalystR states that final dataset should have no more than 5000 variables for effective computing

# Plot the features before filtering < to-do

# Reliability filter
# default off, requires QC samples

# Variance filter
# Use RSD, with 40% filtered out for LC-MS with number of features over 1000
# mSet<-FilterVariable(mSet, qc.filter=FALSE, filter="rsd", filter.cutoff=40)

# Abundance filter
# default mean intensity value

# Plot the features after filtering < to-do


##############
# Normalize Data to TIC
############## 
# Prepare data for normalization (function should always be initialized)
mSet<-PreparePrenormData(mSet);

# Normalize data to total ion chromatogram (TIC)
# rowNorm: "SumNorm" = normalization to constant sum
# transNorm: "NULL" = no transformation
# scaleNorm: "None" for no scaling; or change to "MeanCenter" = mean centering
# ref: NULL = no reference sample (default)

mSet<-Normalization(mSet, "SumNorm", "NULL", "None")

# Write the normalized data to a pandas dataframe
norm_df = data.frame(t(mSet$dataSet$norm))
# Write the row.names to a new column (shift all other columns over so that row.names are in the first column)
norm_df$MetaboAnalyst_ID = rownames(norm_df)
norm_df = norm_df[, c(ncol(norm_df), 1:(ncol(norm_df)-1))]

# Create a shared_name column
norm_df$shared_name = sapply(strsplit(as.character(norm_df$MetaboAnalyst_ID), "/"), "[", 1)

# Remove the row.names column
rownames(norm_df) = NULL

# Write norm_df to csv
write.csv(norm_df, paste(job_name,"_normalized_data_transposed.csv", sep=''), row.names = FALSE)

# Two plot summary plot: Feature View of before and after normalization:
mSet<-PlotNormSummary(mSet, paste("Normalization_feature_", job_name, "_", sep=''), format ="png", dpi=300, width=NA);

# Two plot summary plot: Sample View of before and after normalization
mSet<-PlotSampleNormSummary(mSet, paste("Normalization_sample_", job_name, "_", sep=''), format = "png", dpi=300, width=NA);

##############
# Normalize Data to Sample-specific Factor (Currently not implemented)
############## 
# Note: If instead you want to do normalization to cell pellet weights, uncomment below code, comment out the above section to normalize to TIC, and define cell_pellet_weights_post_str with the correct filename by adding it in the Values to Change section
# cell_pellet_weights_filename = paste(job_name, cell_pellets_weights_post_str, sep='')
# setwd(wd_input)
# setwd(job_name)
# if (!file.exists(cell_pellet_weights_filename)){
#   mSet<-Normalization(mSet, "SumNorm", "NULL", "None")
# } else {
#   cell_pellet_weights_dir = paste(wd_input, "\\", job_name, "\\", cell_pellet_weights_filename, sep='')
#     cell_pellet_data = readxl::read_excel(cell_pellet_weights_dir)
#     # Double check that the cell_pellet_data rows are in the same order as ,Set$dataSet$url.smp.nms
#     sample_cols <-mSet$dataSet$url.smp.nms
#     cell_pellet_data_new = cell_pellet_data[match(sample_cols, cell_pellet_data$"Sample"),]

#   # for value in cell_pellet_data_new$"Weight (mg)"
#   norm.vec <- as.numeric(cell_pellet_data_new$"Weight (mg)")

#   # Call function using rowNorm="SpecNorm"
#   setwd(wd_output)
#   # When using SpecNorm, norm.vec is used with no way to specify in the function
#   mSet<-Normalization(mSet, "SpecNorm", "NULL", "None")
# }
# setwd(wd_output)

# # Write the normalized data to a csv file
# write.csv(t(mSet$dataSet$norm), paste(job_name,"_normalized_data_transposed.csv", sep=''), row.names = TRUE)

# # Two plot summary plot: Feature View of before and after normalization:
# mSet<-PlotNormSummary(mSet, paste("Normalization_feature_", job_name, "_", sep=''), format ="png", dpi=300, width=NA);

# # Two plot summary plot: Sample View of before and after normalization
# mSet<-PlotSampleNormSummary(mSet, paste("Normalization_sample_", job_name, "_", sep=''), format = "png", dpi=300, width=NA);


##############
# Fold-change Analysis
############## 
# Perform fold-change analysis on uploaded data, unpaired. 
# Set fc.thresh to 2.0 fold-change threshold, and cmp.type set to 1 for group 2 (CTRL) vs group 1 (EXP).
mSet<-FC.Anal(mSet, 2.0, cmp.type=1, FALSE)

# Plot fold-change analysis
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
# cmp.type=1 for group 2 (EXP) vs group 1 (CTRL)
mSet<-Volcano.Anal(mSet, FALSE, 2.0, 1, F, 0.05, TRUE, "raw")

# Create the volcano plot
# plotLbl: 1 = show labels for significant features
# plotTheme: 0 = use default theme, or use 2 for less borders
mSet<-PlotVolcano(mSet, paste("Volcano_", job_name, "_", sep=''), 1, 0, format ="png", dpi=300, width=NA)


##############
# ANOVA, Correlation Analysis, and Pattern Searching are additional MetaboAnalyst tools but are only for multi-group analysis
############## 


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


##############
# Rename Output Files and Add Appropriate Headers for Downstream Use
############## 
# Change "fold_change.csv" filename
file.rename("fold_change.csv", paste(job_name, "_fold_change.csv", sep=''))

# import the fold_change.csv file as a pandas dataframe
log2fc_data = read.csv(paste(job_name, "_fold_change.csv", sep=''))

# Name the first column header 'MetaboAnalyst ID'
colnames(log2fc_data)[1] = "MetaboAnalyst_ID"

# Add a column with header 'shared name', where the values are the string prior to the '/' in the first column of log2fc_data
log2fc_data$shared_name = sapply(strsplit(as.character(log2fc_data$MetaboAnalyst_ID), "/"), "[", 1)

# Save dataframe
write.csv(log2fc_data, paste(job_name, "_fold_change.csv", sep=''), row.names = FALSE)


# Change "t_test.csv" filename
file.rename("t_test.csv", paste(job_name, "_t_test.csv", sep=''))

# import the fold_change.csv file as a pandas dataframe
t_test_data = read.csv(paste(job_name, "_t_test.csv", sep=''))

# Name the first column header 'MetaboAnalyst ID'
colnames(t_test_data)[1] = "MetaboAnalyst_ID"

# Add a column with header 'shared name', where the values are the string prior to the '/' in the first column of log2fc_data
t_test_data$shared_name = sapply(strsplit(as.character(t_test_data$MetaboAnalyst_ID), "/"), "[", 1)

# Save dataframe
write.csv(t_test_data, paste(job_name, "_t_test.csv", sep=''), row.names = FALSE)

# Reset wd to starting wd
setwd(wd)


##############
# Notes for Future Additions to Script
############## 
# For future analysis:
# Example for generating violin plot for specific feature of interest (adjust feature name):
# mSet<-UpdateLoadingCmpd(mSet, "760/497.192mz/4.16min")
# mSet<-SetCmpdSummaryType(mSet, "violin")
# mSet<-PlotCmpdSummary(mSet, "760/497.192mz/4.16min","NA","NA", 1, "png", 72)

# Can generate heatmap:
# mSet<-PlotHeatMap(mSet, paste("heatmap_1_", job_name, "_", sep=''), "png", 72, width=NA, "norm", "row", "euclidean", "ward.D","bwm", 8,8, 10.0,0.02,10, 10, T, T, NULL, T, F, T, T, T,T)

