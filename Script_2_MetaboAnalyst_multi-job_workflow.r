# Clean global environment
rm(list = ls())

#############################################
# Un-comment steps 1 and 2 below for the first run to install MetaboAnalystR package and dependencies:
#############################################

# #############################################
# # Setting up MetaboAnalystR (only need to do once)
# #############################################
# # Step 1. Install package dependencies
# # Specifying "always" fixed an error I was having, where ~4 packages would not update and would freeze the run
# options(install.packages.compile.from.source = "always")
# ### Install MetaboAnalystR --> Run once, then comment out
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

###
# # Also installed the following packages: ggplot2, ggrepel, iheatmapr, ellipse

# #############################################
# # Step 2. Install the devtools package

# # Install devtools
# install.packages("devtools")
# library(devtools)
# 
# # Use MetaboAnalystR version with 4.0 volcano plots with correct data point sizes but no p-value legend: 5aee8b4f0d27c27864198a6fd99414575d693836
# devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, ref = "5aee8b4f0d27c27864198a6fd99414575d693836", build_vignettes = FALSE, build_manual =F)
# library(MetaboAnalystR)


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

# # 5) Install pls package
# install.packages("pls")
# library(pls)

# # 6) Install 'rjson' package
# install.packages("rjson")
# library(rjson)


##############
# Values to Change
##############
wd <- "C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow"

metadata_overall_filename <- "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx"
metadata_job_tab <- "Multi-jobs"
metadata_job_column <- "Job Name"
input_table_post_str <- "_MetaboAnalyst_input.csv"


##############
# Set working directory
##############
setwd(wd)

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
abmba_features <- metadata_overall[["ABMBA_Feature_Name_from_Script_1"]]


#############################################
# Setting up MetaboAnalystR (only need to do once)
#############################################
for (job_index in seq_along(job_names)) {
  ##############
  # Get Job Information
  ##############
  # Get job_name from metadata_overall first value in metadata_job_column
  job_name <- job_names[job_index]
  job_abmba_feature_name <- abmba_features[job_index]
    
  # Print the job_name
  print("") # add empty line
  print(paste("Starting job for ", job_name, ".", sep = ""))
  
  
  ##############
  # Create Folders for Organizing Outputs
  ##############
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
  
  # Initialize data object mset for MetaboAnalystR
  # data.type: pktable = peak intensity table
  mset <- InitDataObjects("pktable", "stat", FALSE);
  
  # Import the peak intensity data table from MZmine3 (Script 1)
  input_table_dir <- paste(job_dir, "\\", job_name, input_table_post_str, sep="")
  # Print an error message if there is not a file at the input_table_dir
  if (!file.exists(input_table_dir)) {
    print("Error: input table file does not exist in the job folder. Please create the input table file in the job folder.")
    return()
  }
  
  # Read the peak intensity data table into mset
  # format: colu = unpaired data, in columns, rather than paired (_p) or in rows (row_)
  # lbl.type: disc = discrete data, rather than continuous (cont)
  mset <- Read.TextData(mset, input_table_dir, "colu", "disc")
  mset <- SanityCheckData(mset)


  ##############
  # Replace Missing Values
  ##############
  # Replace missing or 0 values in the metabolomics data with a small volume (default is half of the minimum positive value in the data)
  mset <- ReplaceMin(mset)
  
  
  ##############
  # Apply Abundance Filter (Median) and Normalize Data to Reference Feature (ABMBA)
  ##############
  # Variance filter
  # No QC sample to use for filter
  # var.filter = "rsd"
  # var.cutoff = 0
  # int.filter = "median", "mean" (Abundance filter)
  # int.cutoff = 40
  mset<-FilterVariable(mset, "F", 0, var.filter="rsd", 0, "median", 40)
  
  # Prepare data for normalization (function should always be initialized)
  mset <- PreparePrenormData(mset)

  # Normalize data to reference feature (ABMBA)
  # rowNorm: "CompNorm" = normalization to reference feature
  # transNorm: "LogNorm" = log10 normalization, NULL" = no transformation
  # ref: job_abmba_feature_name = feature name for internal standard, ABMBA, determined from Script 1
  # scaleNorm: "NULL" for no scaling
  mset <- Normalization(mset, "CompNorm", transNorm="LogNorm", scaleNorm="NULL", ref=job_abmba_feature_name, ratio=FALSE, ratioNum=20)


  # ##############
  # # Alternative Normalization Method: Filter Data then Normalize Data to TIC (commented out)
  # ##############
  # # Variance filter
  # # Use RSD, with 40% filtered out for LC-MS with number of features over 1000
  # # Abundance filter
  # # Mean Filter
  # mset <- FilterVariable(mset, "F", 0, var.filter="rsd", var.cutoff=40, "mean", 25)
  # 
  # # Prepare data for normalization (function should always be initialized)
  # mset <- PreparePrenormData(mset)
  # 
  # # Normalize data to total ion chromatogram (TIC)
  # # rowNorm: "SumNorm" = normalization to constant sum
  # # transNorm: "NULL" = no transformation
  # # scaleNorm: "None" for no scaling; or change to "MeanCenter" = mean centering, "AutoNorm" for autoscaling, etc.
  # # ref: NULL = no reference sample (default)
  # 
  # mset <- Normalization(mset, "SumNorm", transNorm="NULL", scaleNorm="AutoNorm", ratio=FALSE, ratioNum=20)


  ##############
  # Alternative Normalization Method: Normalize to Sample-specific Factor (commented out)
  ##############
  # Note: If instead you want to do normalization to cell pellet weights, uncomment below code, comment out the above section to normalize to TIC, and define cell_pellet_weights_post_str with the correct filename by adding it in the Values to Change section
  # cell_pellet_weights_filename = paste(job_name, cell_pellets_weights_post_str, sep='')
  # setwd(wd_input)
  # setwd(job_name)
  # if (!file.exists(cell_pellet_weights_filename)){
  #   mset<-Normalization(mset, "SumNorm", "NULL", "None")
  # } else {
  #   cell_pellet_weights_dir = paste(wd_input, "\\", job_name, "\\", cell_pellet_weights_filename, sep='')
  #     cell_pellet_data = readxl::read_excel(cell_pellet_weights_dir)
  #     # Double check that the cell_pellet_data rows are in the same order as ,Set$dataSet$url.smp.nms
  #     sample_cols <-mset$dataSet$url.smp.nms
  #     cell_pellet_data_new = cell_pellet_data[match(sample_cols, cell_pellet_data$"Sample"),]
  
  #   # for value in cell_pellet_data_new$"Weight (mg)"
  #   norm.vec <- as.numeric(cell_pellet_data_new$"Weight (mg)")
  
  #   # Call function using rowNorm="SpecNorm"
  #   setwd(wd_output)
  #   # When using SpecNorm, norm.vec is used with no way to specify in the function
  #   mset<-Normalization(mset, "SpecNorm", "NULL", "None")
  # }
  # setwd(wd_output)
  
  # # Write the normalized data to a csv file
  # write.csv(t(mset$dataSet$norm), paste(job_name,"_normalized_data_transposed.csv", sep=''), row.names = TRUE)
  
  # # Two plot summary plot: Feature View of before and after normalization:
  # mset<-PlotNormSummary(mset, paste("Normalization_feature_", job_name, "_", sep=''), format ="png", dpi=300, width=NA);
  
  # # Two plot summary plot: Sample View of before and after normalization
  # mset<-PlotSampleNormSummary(mset, paste("Normalization_sample_", job_name, "_", sep=''), format = "png", dpi=300, width=NA);
  

  ##############
  # Export Normalized Data
  ##############
  # Write the normalized data to a pandas dataframe
  norm_df <- data.frame(t(mset$dataSet$norm))
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
  mset <- PlotNormSummary(mset, paste("Normalization_feature_", job_name, "_", sep = ""), format ="png", dpi=300, width = NA);
  
  # Two plot summary plot: Sample View of before and after normalization
  mset <- PlotSampleNormSummary(mset, paste("Normalization_sample_", job_name, "_", sep = ""), format = "png", dpi=300, width = NA);
  

  ##############
  # Fold-change Analysis
  ##############
  # Perform fold-change analysis on uploaded data, unpaired.
  # Set fc.thresh to 2.0 fold-change threshold, and cmp.type set to 1 for EXP/CTRL comparison
  mset <- FC.Anal(mset, 2.0, cmp.type = 1, FALSE)

  # Plot fold-change analysis
  mset <- PlotFC(mset, paste("Fold-change_", job_name, "_", sep = ""), "png", 72, width = NA)

  # # To view fold-change
  # mset$analSet$fc$fc.log


  ##############
  # T-test
  ##############
  # Perform T-test (parametric)
  # From web version: "For large data set (> 1000 variables), both the paired information and the group variance will be ignored, and the default parameters will be used for t-tests to save computational time."
  # "If you choose non-parametric tests (Wilcoxon rank-sum test), the group variance will be ignored."
  # nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
  # threshp: 0.05 = threshold p-value
  # paired: FALSE = data is not paired
  # equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use.
  # pvalType = "fdr" = p-value adjustment method, "fdr" = false discovery rate
  # all_results = TRUE = show all results, not only  significant results
  mset <- Ttests.Anal(mset, nonpar = F, threshp = 0.05, paired = FALSE, equal.var = TRUE, "fdr", TRUE)

  # # Plot of the T-test results
  # # if the following line causes an error, skip and continue the rest of the script
  # setwd(output_dir)
  # plot_tt_error_occurred <- FALSE
  # tryCatch({
  #   mset = PlotTT(mset, paste("T_test_", job_name, "_", sep = ""), "png", 72, width = NA)
  # }, error = function(e) {
  #   plot_tt_error_occurred = TRUE
  #   print("Error occurred in PlotTT function, likely due to low number of significant features. Skipping this step.")
  # })


  ##############
  # Volcano Plot: raw p-values
  ##############
  # Perform the volcano analysis
  # paired: FALSE = data is not paired
  # fc.thresh: 2.0 = fold-change threshold
  # cmp.type: 1 = (EXP/CTRL), such that:
  #   Positive log2 fold-change values indicate upregulation in group 2 (EXP).
  #   Negative log2 fold-change values indicate downregulation in group 2 (EXP).
  # nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
  # threshp: 0.05 = threshold p-value
  # equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use
  # pval.type: "raw" = use raw p-values, instead of FDR-adjusted p-values
  mset <- Volcano.Anal(mset, FALSE, 2.0, 1, F, 0.05, TRUE, "raw")
  
  
  # Positive log2 fold-change values indicate upregulation in group 2 (EXP).
  # Negative log2 fold-change values indicate downregulation in group 2 (EXP).
  

  # Positive log2 fold-change values indicate upregulation in group 2 (EXP).
  # Negative log2 fold-change values indicate downregulation in group 2 (EXP).
  
  # Create the volcano plot
  # plotLbl: 1 = show labels for significant features
  # plotTheme: 0 = use default theme, or use 2 for less borders
  mset <- PlotVolcano(mset, paste("Volcano_raw_p_", job_name, "_", sep = ""), 1, 0, format = "png", dpi = 300, width = NA)

  # ##############
  # # Volcano Plot: FDR-adjusted p-values (commented out to avoid errors due to no significant hits)
  # ##############
  # # Perform the volcano analysis
  # # paired: FALSE = data is not paired
  # # fc.thresh: 2.0 = fold-change threshold
  # # cmp.type: 1 = (EXP/CTRL), such that:
  # #   Positive log2 fold-change values indicate upregulation in group 2 (EXP).
  # #   Negative log2 fold-change values indicate downregulation in group 2 (EXP).
  # # nonpar: F = false, for using a non-parametric test, which is a distribution-free test with fewer assumptions. T-tests are parametric.
  # # threshp: 0.05 = threshold p-value
  # # equal.var: TRUE = evaluates if the group variance is equal, to inform which t-test to use
  # # pval.type: "fdr" = use FDR-adjusted p-values
  # mset <- Volcano.Anal(mset, FALSE, 2.0, 1, F, 0.05, TRUE, "fdr")
  # 
  # # Create the volcano plot
  # # plotLbl: 1 = show labels for significant features
  # # plotTheme: 0 = use default theme, or use 2 for less borders
  # mset <- PlotVolcano(mset, paste("Volcano_FDR-adj_p_", job_name, "_", sep = ""), 1, 0, format = "png", dpi = 300, width = NA)
  # 

  ##############
  # Principal Component Analysis (PCA)
  ##############
  # Perform PCA analysis
  mset <- PCA.Anal(mset)

  # Create PCA overview
  # pc.num: 5 = the number of principal components to display in the pairwise score plot
  mset <- PlotPCAPairSummary(mset, paste("PCA_Pair_", job_name, "_", sep = ""), format = "png", dpi = 300, width = NA, 5)

  # Create PCA scree plot
  # A Scree Plot is a simple line segment plot that shows the eigenvalues for each individual PC. The scree plot is used to determine the number of components to retain in PCA, because at a high enough number of considered components, the variance explained by higher components is not meaningful.
  # To visually assess the screen plot, look for the "elbow" in the plot, which is the point where the slope of the line changes the most. This is the point where the marginal gain in variance explained by adding another component is minimal.
  # scree.num: 5 = the number of principal components to display in the scree plot
  mset <- PlotPCAScree(mset, paste("PCA_Scree_", job_name, "_", sep = ""), "png", dpi = 300, width = NA, 5)

  # Create a 2D PCA score plot, using principal components 1 and 2
  mset <- PlotPCA2DScore(mset, paste("PCA_score_2D_1_2_", job_name, "_", sep = ""), format = "png", dpi = 300, width = NA, 1, 2, 0.95, 1, 0)

  # "Error in PlotPCA3DScoreImg(mset, paste("PCA_score_3D_", job_name, "_", : object 'cols' not found""
  # # Create a 3D PCA score plot, using principal components 1, 2, and 3
  # mset<-PlotPCA3DScoreImg(mset, paste("PCA_score_3D_", job_name, "_", sep=''), "png", 72, width=NA, 1,2,3, 40)

  # Create a PCA loadings Plots, using principal components 1 and 2
  mset <- PlotPCALoading(mset, paste("PCA_Loading_1_2_", job_name, "_", sep = ""), "png", 72, width = NA, 1, 2)

  # Create a PCA Biplot, using principal components 1 and 2
  mset <- PlotPCABiplot(mset, paste("PCA_BiPlot_1_2_", job_name, "_", sep = ""), format = "png", dpi = 300, width = NA, 1, 2)
  
  
  # # View the 3D interactive PLS-DA score plot
  # mset$imgSet$pca.3d
  # # ^ I was not able to get this 3d viewer to work
  

  # # View the 3D interactive PLS-DA score plot
  # mset$imgSet$pca.3d
  # # ^ I was not able to get this 3d viewer to work
  
  
  # ##############
  # # Partial Least Squares - Discriminant Analysis (PLS-DA) -- (commented out to perform sPLS-DA instead)
  # ##############
  # # Dimensionality reduction that takes into account sample groupings, to emphasize metabolite features that contribute most to group differences
  # mset<-PLSR.Anal(mset, reg=TRUE)
  # mset<-PlotPLSPairSummary(mset, paste("pls_pair_0_", job_name, "_", sep=""), "png", 72, width=NA, 5)
  # mset<-PlotPLS2DScore(mset, paste("pls_score2d_0_", job_name, "_", sep=""), "png", 72, width=NA, 1,2,0.95,0,0, "na")
  # mset<-PlotPLS3DScoreImg(mset, paste("pls_score3d_0_", job_name, "_", sep=""), "png", 72, width=NA, 1,2,3, 40)
  # mset<-PlotPLSLoading(mset, paste("pls_loading_0_", job_name, "_", sep=""), "png", 72, width=NA, 1, 2);
  # # mset<-PlotPLS3DLoading(mset, paste("pls_loading3d_0_", job_name, "_", sep=""), "json", 1,2,3)
  # mset<-PlotPLS.Imp(mset, paste("pls_imp_0_", job_name, "_", sep=""), "png", 72, width=NA, "vip", "Comp. 1", 15,FALSE)
  
  
  ##############
  # Sparse Partial Least Squares - Discriminant Analysis (sPLS-DA)
  ##############
  mset<-SPLSR.Anal(mset, 5, 10, "same", "Mfold", 5, F)
  mset<-PlotSPLSPairSummary(mset, paste("spls_pair_0_", job_name, "_", sep=""), "png", 72, width=NA, 5)
  mset<-PlotSPLS2DScore(mset, paste("spls_score2d_0_", job_name, "_", sep=""), "png", 72, width=NA, 1,2,0.95,0,0,"na")
  mset<-PlotSPLS3DScoreImg(mset, paste("spls_score3d_0_", job_name, "_", sep=""), "png", 72, width=NA, 1,2,3, 40)
  mset<-PlotSPLSLoading(mset, paste("spls_loading_0_", job_name, "_", sep=""), "png", 72, width=NA, 1,"overview");

  
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
