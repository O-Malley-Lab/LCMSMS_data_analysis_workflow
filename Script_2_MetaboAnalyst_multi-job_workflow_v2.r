# MetaboAnalystR Script for LCMSMS analysis of Heterologous Expression Samples
# by Lazarina Butkovich

# Sources:
# Statistical Analysis Module Overview:
# https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html
# Github for MetaboAnalystR:
# https://github.com/xia-lab/MetaboAnalystR/tree/master


# Workflow:
# Processed metabolomic data -> Univariate analysis -> Multivariate analysis -> Biological interpretation # nolint

# Clean global environment
rm(list = ls())

#############################################
# Un-comment steps 1 and 2 below for the first run to install MetaboAnalystR package and dependencies:
#############################################

# #############################################
# # Setting up MetaboAnalystR (only need to do once)
# #############################################
### Install MetaboAnalystR --> Run once, then comment out
# metanr_packages <- function(){
#   
#   metr_pkgs <- c("impute", "pcaMethods", "globaltest", "GlobalAncova", "Rgraphviz", "preprocessCore", "genefilter", "sva", "limma", "KEGGgraph", "siggenes","BiocParallel", "MSnbase", "multtest","RBGL","edgeR","fgsea","devtools","crmn","httr","qs")
#   
#   list_installed <- installed.packages()
#   
#   new_pkgs <- subset(metr_pkgs, !(metr_pkgs %in% list_installed[, "Package"]))
#   
#   if(length(new_pkgs)!=0){
#     
#     if (!requireNamespace("BiocManager", quietly = TRUE))
#       install.packages("BiocManager")
#     BiocManager::install(new_pkgs)
#     print(c(new_pkgs, " packages added..."))
#   }
#   
#   if((length(new_pkgs)<1)){
#     print("No new packages added...")
#   }
# }
# metanr_packages()
# install.packages("devtools")
# library(devtools)
# # Use version with 4.0 volcano plots with correct data point sizes but no p-value legend: 5aee8b4f0d27c27864198a6fd99414575d693836
# devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, ref = "5aee8b4f0d27c27864198a6fd99414575d693836", build_vignettes = TRUE, build_manual =T)
# # devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, build_vignettes = TRUE, build_manual =T)
# library(MetaboAnalystR)


### Other tentatively required packages:
# To view vignettes online: (note, this does not seem to work)
#browseVignettes("MetaboAnalystR")

# # Based off of errors when trying to run, installed the following packages:
# # 1) Install readxl package
# install.packages("readxl")
# library(readxl)

# # 2) Install ggrepel package
# install.packages("ggrepel")
# library(ggrepel)

# # 3) Install ellipse package
# install.packages("ellipse")
# library(ellipse)

# # 4) Install vegan package
# install.packages("vegan")
# library(vegan)

#############################################

#############################################
# Running MetaboAnalystR (only need to do once)
#############################################
# Statistical Analysis Module Overview:
# https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html

# If you run into questions about MetaboAnalystR package, use the help link:
# help(package="MetaboAnalystR")

# #############################################
# Start of Script to Run for MetaboAnalystR
# #############################################

##############
# Values to Change
##############
setwd("C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow")
metadata_overall_filename <- "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx"
metadata_job_tab <- "Multi-jobs"
metadata_job_column <- "Job Name"
input_table_post_str <- "_MetaboAnalyst_input.csv"


##############
# Set working directory
##############
# Save the original starting directory as wd
wd <- getwd()


##############
# Load Metadata_overall
##############
# Get job_name from overall metadata
input_dir <- paste(wd, "input", sep = "\\")
setwd(input_dir)
wd_input <- getwd()
# Import metadata table excel. The excel is in the input folder
metadata_overall <- readxl::read_excel(metadata_overall_filename, sheet = metadata_job_tab)
# job_names is a list of all the values in the metadata_job_column of metadata_overall
job_names <- metadata_overall[[metadata_job_column]]


##############
# Create For Loop over entire remaining script, to run for each Job Name
##############
for (job_index in seq_along(job_names)) {
  # Get job_name from metadata_overall first value in metadata_job_column
  job_name = job_names[job_index]

  # Print the job_name
  print("") # add empty line
  print(paste("Starting job for ", job_name, ".", sep = ""))

  # For copy-pasting GNPS downloaded output for Cytoscape script, first create the GNPS_output folder in the working directory, if it does not exist already
  output_dir_gnps <- paste(wd, "GNPS_output", sep = "\\")
  if (!dir.exists(output_dir_gnps)){
    dir.create(output_dir_gnps)
  }
  # Create a job_name folder in the GNPS_output folder
  job_dir_gnps <- paste(output_dir_gnps, job_name, sep = "\\")
  # First delete the job_name folder if it already exists
  if (dir.exists(job_dir_gnps)) {
    print("The GNPS_output folder already exists, so it was not created")
    # If folder already exists, do nothing
  } else {
    # If the job_name folder does not exist, create it
    dir.create(job_dir_gnps)
    print("The GNPS_output folder did not previously exist, so it was created")
  }
  # ^ note: by the end of the code, this folder will be empty; you will manually place the GNPS downloaded results (Run GNPS job manually, Go to finished GNPS job, select "View All Library Hits", download all, copy-paste that into this folder, then unzip the folder)

  # Set the working directory to the job_name folder in the temp folder. This is also where output images will go
  job_dir <- paste(wd, "temp", job_name, sep = "\\")
  # If the folder doesn't exist yet in temp, print an error and end the script
  if (!dir.exists(job_dir)) {
    print("Error: job folder does not exist in temp folder. Please create the temp folder in the working directory (ie: run Script 1 to create job folder and MetaboAnalyst input data table).")
    return()
  }
  # Create a MetaboAnalystR Output folder in the job folder
  output_dir <- paste(job_dir, "MetaboAnalystR_Output", sep = "\\")
  if (!dir.exists(output_dir)){
    dir.create(output_dir)
  }
  # Empty the MetaboAnalystR Output folder if it previously existed
  file.remove(list.files(output_dir, full.names = TRUE))

  setwd(output_dir)
  wd_output <- getwd()


  #############################################
  # Univariate Methods
  #############################################
  ##############
  # Load MetaboAnalystR and Data Table
  ##############
  # Load MetaboAnalystR
  library(MetaboAnalystR)

  # Initialize data object init for MetaboAnalystR
  # data.type: pktable = peak intensity table
  init <- InitDataObjects("pktable", "stat", FALSE);

  # Import the peak intensity data table from MZmine3 (Script 1)
  input_table_dir <- paste(job_dir, "\\", job_name, input_table_post_str, sep="")
  # Print an error message if there is not a file at the input_table_dir
  if (!file.exists(input_table_dir)) {
    print("Error: input table file does not exist in the job folder. Please create the input table file in the job folder.")
    return()
  }

  # Read the peak intensity data table into raw_data
  # format: colu = unpaired data, in columns, rather than paired (_p) or in rows (row_)
  # lbl.type: disc = discrete data, rather than continuous (cont)
  raw_data <- Read.TextData(init, input_table_dir, "colu", "disc")
  raw_data <- SanityCheckData(raw_data)


  ##############
  # Replace Missing Values
  ##############
  # Replace missing or 0 values in the metabolomics data with a small volume (default is half of the minimum positive value in the data)
  processed_data <- ReplaceMin(raw_data);

  
  ##############
  # Normalize Data to TIC
  ##############
  # Prepare data for normalization (function should always be initialized)
  processed_data <- PreparePrenormData(processed_data);

  # Normalize data to total ion chromatogram (TIC)
  # rowNorm: "SumNorm" = normalization to constant sum
  # transNorm: "NULL" = no transformation
  # scaleNorm: "None" for no scaling; or change to "MeanCenter" = mean centering
  # ref: NULL = no reference sample (default)
  processed_data <- Normalization(processed_data, "NULL", "SumNorm", "NULL", "None");
  
  # Write the normalized data to a pandas dataframe
  norm_df <- data.frame(t(processed_data$dataSet$norm))
  # Write the row.names to a new column (shift all other columns over so that row.names are in the first column)
  norm_df$MetaboAnalyst_ID <- rownames(norm_df)
  norm_df <- norm_df[, c(ncol(norm_df), 1:(ncol(norm_df)-1))]

  # Create a shared_name column
  norm_df$shared_name <- sapply(strsplit(as.character(norm_df$MetaboAnalyst_ID), "/"), "[", 1)

  # Remove the row.names column
  rownames(norm_df) <- NULL

  # Write norm_df to csv
  write.csv(norm_df, paste(job_name,"_normalized_data_transposed.csv", sep=""), row.names = FALSE)

  # Two plot summary plot: Feature View of before and after normalization:
  PlotNormSummary(processed_data, paste("Normalization_feature_", job_name, "_", sep = ""), format ="png", dpi=300, width = NA);

  # Two plot summary plot: Sample View of before and after normalization
  PlotSampleNormSummary(processed_data, paste("Normalization_sample_", job_name, "_", sep = ""), format = "png", dpi=300, width = NA);

  
  ##############
  # Fold-change Analysis
  ##############
  # Perform fold-change analysis on uploaded data, unpaired.
  # Set fc.thresh to 2.0 fold-change threshold, and cmp.type set to 1 for group 2 (CTRL) vs group 1 (EXP).
  fold_change_anal <- FC.Anal(processed_data, 2.0, cmp.type = 1, FALSE)

  # Plot fold-change analysis
  PlotFC(fold_change_anal, paste("Fold-change_", job_name, "_", sep = ""), "png", 72, width = NA)


  ##############
  # T-test
  ##############
  # Perform T-test (parametric)
  # nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
  # threshp: 0.05 = threshold p-value
  # paired: FALSE = data is not paired
  # equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use
  # pvalType = p-value adjustment method, "raw" = raw p-value, fdr = FDR-adjusted p-value
  # all_results = TRUE = report p-values for all features, not just significant values
  tt_anal <- Ttests.Anal(fold_change_anal, nonpar = F, threshp = 0.05, paired = FALSE, equal.var = TRUE, "fdr", FALSE)

  # Plot of the T-test results
  # if the following line causes an error, skip and continue the rest of the script
  plot_tt_error_occurred <- FALSE
  tryCatch({
    plot_obj_tt = PlotTT(tt_anal, paste("T_test_", job_name, "_", sep = ""), "png", 72, width = NA)
  }, error = function(e) {
    plot_tt_error_occurred = TRUE
    print("Error occurred in PlotTT function, likely due to low number of significant features. Skipping this step.")
  })


  ##############
  # Volcano Plot
  ##############
  # Perform the volcano analysis
  # paired: FALSE = data is not paired
  # fc.thresh: 2.0 = fold-change threshold
  # cmp.type: 0 = group 1 (CTRL) vs group 2 (EXP)
  # nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
  # threshp: 0.05 = threshold p-value
  # equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use
  # pval.type: "fdr" = use fdr p-values, "raw" = use raw p-values
  # cmp.type=1 for group 2 (EXP) vs group 1 (CTRL)
  volcano_anal <- Volcano.Anal(tt_anal, FALSE, 2.0, 1, F, 0.05, TRUE, "fdr")

  # Positive log2 fold-change values indicate upregulation in group 2 (EXP).
  # Negative log2 fold-change values indicate downregulation in group 2 (EXP).

  # Create the volcano plot
  # plotLbl: 1 = show labels for significant features
  # plotTheme: 0 = use default theme, or use 2 for less borders
  plot_volcano_error_occurred <- FALSE
  tryCatch({
    plot_obj_volc = PlotVolcano(volcano_anal, paste("Volcano_", job_name, "_", sep = ""), 1, 0, format = "png", dpi = 300, width = NA)
    }, error = function(e) {
      plot_volcano_error_occurred = TRUE
      print("Error occurred in PlotVolcano function, likely due to low number of significant features. Skipping this step.")
    })


  ##############
  # Principal Component Analysis (PCA)
  ##############
  # Perform PCA analysis
  pca_anal <- PCA.Anal(tt_anal)

  # Create PCA overview
  # pc.num: 5 = the number of principal components to display in the pairwise score plot
  PlotPCAPairSummary(pca_anal, paste("PCA_Pair_", job_name, "_", sep = ""), format = "png", dpi = 300, width = NA, 5)

  # Create PCA scree plot
  # A Scree Plot is a simple line segment plot that shows the eigenvalues for each individual PC. The scree plot is used to determine the number of components to retain in PCA, because at a high enough number of considered components, the variance explained by higher components is not meaningful.
  # To visually assess the screen plot, look for the "elbow" in the plot, which is the point where the slope of the line changes the most. This is the point where the marginal gain in variance explained by adding another component is minimal.
  # scree.num: 5 = the number of principal components to display in the scree plot
  PlotPCAScree(pca_anal, paste("PCA_Scree_", job_name, "_", sep = ""), "png", dpi = 300, width = NA, 5)

  # Create a 2D PCA score plot, using principal components 1 and 2
  PlotPCA2DScore(pca_anal, paste("PCA_score_2D_1_2_", job_name, "_", sep = ""), format = "png", dpi = 300, width = NA, 1, 2, 0.95, 1, 0)

  # Create a PCA loadings Plots, using principal components 1 and 2
  PlotPCALoading(pca_anal, paste("PCA_Loading_1_2_", job_name, "_", sep = ""), "png", 72, width = NA, 1, 2)

  # Create a PCA Biplot, using principal components 1 and 2
  PlotPCABiplot(pca_anal, paste("PCA_BiPlot_1_2_", job_name, "_", sep = ""), format = "png", dpi = 300, width = NA, 1, 2)


  ##############
  # Rename Output Files and Add Appropriate Headers for Downstream Use
  ##############
  # Change "fold_change.csv" filename
  file.rename("fold_change.csv", paste(job_name, "_fold_change.csv", sep = ""))

  # import the fold_change.csv file as a pandas dataframe
  log2fc_data <- read.csv(paste(job_name, "_fold_change.csv", sep = ""))

  # Name the first column header 'MetaboAnalyst ID'
  colnames(log2fc_data)[1] <- "MetaboAnalyst_ID"

  # Add a column with header 'shared name', where the values are the string prior to the '/' in the first column of log2fc_data
  log2fc_data$shared_name <- sapply(strsplit(as.character(log2fc_data$MetaboAnalyst_ID), "/"), "[", 1)

  # Save dataframe
  write.csv(log2fc_data, paste(job_name, "_fold_change.csv", sep = ""), row.names = FALSE)


  # Change "t_test.csv" filename
  file.rename("t_test.csv", paste(job_name, "_t_test.csv", sep = ""))

  # import the fold_change.csv file as a pandas dataframe
  t_test_data <- read.csv(paste(job_name, "_t_test.csv", sep = ""))

  # Name the first column header 'MetaboAnalyst ID'
  colnames(t_test_data)[1] <- "MetaboAnalyst_ID"

  # Add a column with header 'shared name', where the values are the string prior to the '/' in the first column of log2fc_data
  t_test_data$shared_name <- sapply(strsplit(as.character(t_test_data$MetaboAnalyst_ID), "/"), "[", 1)

  # Save dataframe
  write.csv(t_test_data, paste(job_name, "_t_test.csv", sep = ""), row.names = FALSE)

  # Reset wd to starting wd
  setwd(wd)


  ##############
  # Notes for Future Additions to Script
  ##############
  # For future analysis:
  # Example for generating violin plot for specific feature of interest (adjust feature name):
  # mset<-UpdateLoadingCmpd(mset, "760/497.192mz/4.16min")
  # mset<-SetCmpdSummaryType(mset, "violin")
  # mset<-PlotCmpdSummary(mset, "760/497.192mz/4.16min","NA","NA", 1, "png", 72)

  # Can generate heatmap:
  # mset<-PlotHeatMap(mset, paste("heatmap_1_", job_name, "_", sep=''), "png", 72, width=NA, "norm", "row", "euclidean", "ward.D","bwm", 8,8, 10.0,0.02,10, 10, T, T, NULL, T, F, T, T, T,T)

}

# If .Rhistory was created in the working directory, delete it
if (file.exists(".Rhistory")) {
  file.remove(".Rhistory")
}
