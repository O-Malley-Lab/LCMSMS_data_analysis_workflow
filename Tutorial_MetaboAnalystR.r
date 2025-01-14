# MetaboAnalystR tutorial link:
# https://www.metaboanalyst.ca/resources/vignettes/Statistical_Analysis_Module.html

# Clean global environment
rm(list = ls())

# # Set font
# par(family = "Roboto")

###

### Install MetaboAnalystR --> Run once, then comment out
metanr_packages <- function(){

  metr_pkgs <- c("impute", "pcaMethods", "globaltest", "GlobalAncova", "Rgraphviz", "preprocessCore", "genefilter", "sva", "limma", "KEGGgraph", "siggenes","BiocParallel", "MSnbase", "multtest","RBGL","edgeR","fgsea","devtools","crmn","httr","qs")

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
install.packages("devtools")
library(devtools)
# Use version with 4.0 volcano plots with correct data point sizes but no p-value legend: 5aee8b4f0d27c27864198a6fd99414575d693836
devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, ref = "5aee8b4f0d27c27864198a6fd99414575d693836", build_vignettes = TRUE, build_manual =T)
# devtools::install_github("xia-lab/MetaboAnalystR", build = TRUE, build_vignettes = TRUE, build_manual =T)
library(MetaboAnalystR)

###


### Load MetaboAnalystR
library(MetaboAnalystR)
init<-InitDataObjects("conc", "stat", FALSE);


### Import data
setwd("C:\\Users\\lazab\\Documents\\github\\LCMSMS_data_analysis_workflow\\input\\MetaboAnalystR_tutorial")
wd <- getwd();

data_table_filename = "human_cachexia_MetaboAnalyst_R_tutorial_data.csv"
# Import data table .csv
input_table_dir <- paste(wd, "\\", data_table_filename, sep="");
raw_data <- Read.TextData(init, input_table_dir, "rowu", "disc");
raw_data <- SanityCheckData(raw_data);


### Process data
# Normalize data
processed_data <- ReplaceMin(raw_data);
processed_data <- PreparePrenormData(processed_data);
processed_data <- Normalization(processed_data, "NULL", "LogNorm", "MeanCenter", "S10T0", ratio=FALSE, ratioNum=20);

# Plot sample behavior
PlotNormSummary(processed_data, "norm_0_", format ="png", dpi=72, width=NA)
PlotSampleNormSummary(processed_data, "snorm_0_", format = "png", dpi=72, width=NA)

# Generate log2 fold-change data before normalization (tutorial says to do before normalization but proceeds to run after normalization?)
# Perform fold-change analysis on uploaded data, unpaired
fold_change_anal <-FC.Anal(processed_data, 2.0, 0, FALSE)

# Plot fold-change analysis
plot_obj_fold_change <- PlotFC(fold_change_anal, "fc_0_", "png", 72, width=NA)

# # To view fold-change: 
# plot_obj_fold_change$analSet$fc$fc.log

# Perform T-test
# Perform T-test (parametric)
tt_anal <- Ttests.Anal(fold_change_anal, nonpar=F, threshp=0.05, paired=FALSE, equal.var=TRUE, "fdr", FALSE)

# Plot of the T-test results
plot_obj_tt <-PlotTT(tt_anal, imgName = "tt_0_", format = "png", dpi = 72, width=NA)


### Generate volcano plot. Change raw to fdr to test for my LC-MS/MS analysis script
volcano_anal <- Volcano.Anal(tt_anal, FALSE, 2.0, 0, F, 0.1, TRUE, "fdr")

plot_obj_volcano <- PlotVolcano(volcano_anal, "volcano_0_", 1, 0, format ="png", dpi=72, width=NA)


### Perform PCA analysis
pca_anal <- PCA.Anal(tt_anal)

# Create PCA overview
plot_obj_pca <- PlotPCAPairSummary(pca_anal, "pca_pair_0_", format = "png", dpi = 72, width=NA, 5)

# Create PCA scree plot
plot_obj_pca_scree <- PlotPCAScree(pca_anal, "pca_scree_0_", "png", dpi = 72, width=NA, 5)

# Create a 2D PCA score plot (this is the main PCA plot I am interested in)
plot_obj_pca_2d <- PlotPCA2DScore(pca_anal, "pca_score2d_0_", format = "png", dpi=72, width=NA, 1, 2, 0.95, 1, 0)

# Create a PCA loadings Plots
plot_obj_pca_loading <- PlotPCALoading(pca_anal, "pca_loading_0_", "png", 72, width=NA, 1,2)

# Create a PCA Biplot
plot_obj_pca_biplot <- PlotPCABiplot(pca_anal, "pca_biplot_0_", format = "png", dpi = 72, width=NA, 1, 2)
