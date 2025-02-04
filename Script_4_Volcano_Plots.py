"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 4: Volcano Plot Generation

@author: Lazarina Butkovich

"""""""""""""""""""""""""""""""""""""""""""""

import os
from os.path import join as pjoin
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from adjustText import adjust_text
import time
start = time.time()


"""""""""""""""""""""""""""""""""""""""""""""
Functions
"""""""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""""""""""
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
GNPS_OUTPUT_FOLDER = r'GNPS_output'
OUTPUT_FOLDER = r'output'

# Use "Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx" from INPUT_FOLDER to get relevant parameters for job to run. Use the excel tab "Job to Run"
METADATA_OVERALL_FILENAME = 'Overall_Running_Metadata_for_All_LCMSMS_Jobs.xlsx'
METADATA_JOB_TAB = 'Multi-jobs'
JOB_COLNAME = 'Job Name'

# Sheet name for Filtered Peaks of Interest excel from output folder's job folders
ALL_FEATURES_SHEETNAME = 'All Peaks Simple'
LFC_COLNAME = 'log2.FC.'
PVAL_COLNAME = 'p.value'
FEATURE_ID_COLNAME = "shared name" # String column

# Cutoffs for significant features for volcano plots
METABOANALYSTR_LOG2FC_CUTOFF = 2
METABOANALYSTR_PVAL_CUTOFF = 0.05
NUM_SIG_DATA_POINTS_TO_LABEL = 10

# Volcano plot visual features
LINE_WIDTH = 2
FONT_SIZE = 24
DATA_POINT_SIZE = 100

# Axes ranges
NEG_LOG10_P_RANGE = [0,9]
LOG2_FC_RANGE = [-15,15]

# Colors for up and down regulated features
UP_COLOR = 'turquoise'
DOWN_COLOR = 'maroon'

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Iterate over each job_name in metadata
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Import metadata table for job
metadata = pd.read_excel(pjoin(INPUT_FOLDER, METADATA_OVERALL_FILENAME), sheet_name = METADATA_JOB_TAB)

# Create volcano plots output folder if it doesn't exist
all_volcano_plots_dir = pjoin(OUTPUT_FOLDER, 'all_volcano_plots')
os.makedirs(all_volcano_plots_dir, exist_ok=True)

# Before the job loop, add:
total_start = time.time()

# # keep track of largest and smallest p-value and log2FC for all jobs
# all_pvals = []
# all_log2FCs = []

for job_index, job in enumerate(metadata[JOB_COLNAME]):
    # Inside the job loop, before processing each job:
    job_start = time.time()

    # Import the .xlsx from the output folder for the job
    # The job folder name is the same as the job name
    output_filename = job + '_Filtered_Peaks_of_Interest.xlsx'
    output_filepath = pjoin(OUTPUT_FOLDER, job, output_filename)
    all_features_df = pd.read_excel(output_filepath, 
                                  sheet_name=ALL_FEATURES_SHEETNAME,
                                  dtype={FEATURE_ID_COLNAME: str})  # Force string type
                                    
    # Keep only the following columns: FEATURE_ID_COLNAME, LFC_COLNAME, PVAL_COLNAME.
    volcano_df = all_features_df.copy()
    volcano_df = volcano_df[[FEATURE_ID_COLNAME, LFC_COLNAME, PVAL_COLNAME, "precursor mass", "RTMean"]]
    volcano_df[FEATURE_ID_COLNAME] = volcano_df[FEATURE_ID_COLNAME].astype(str)  # Ensure string type

    # Build MetaboAnalystID column name (ie: 4867/504.3237mz/7.463min)
    volcano_df['MetaboAnalyst_ID'] = volcano_df[FEATURE_ID_COLNAME] + '/' + volcano_df['precursor mass'].astype(str) + 'mz/' + volcano_df['RTMean'].astype(str) + 'min'

    # Filter only for rows with non-NaN values in LFC_COLNAME and PVAL_COLNAME
    volcano_df = volcano_df.dropna(subset=[LFC_COLNAME, PVAL_COLNAME])

    # Create volcano plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Add dotted lines for cutoffs
    ax.axhline(y=-np.log10(METABOANALYSTR_PVAL_CUTOFF), color='black', linestyle='--', alpha=0.5, linewidth=LINE_WIDTH)
    ax.axvline(x=-METABOANALYSTR_LOG2FC_CUTOFF, color='black', linestyle='--', alpha=0.5, linewidth=LINE_WIDTH)
    ax.axvline(x=METABOANALYSTR_LOG2FC_CUTOFF, color='black', linestyle='--', alpha=0.5, linewidth=LINE_WIDTH)

    # Calculate -log10(p-value)
    volcano_df['-log10(p-value)'] = -np.log10(volcano_df[PVAL_COLNAME])

    # Create masks for different point categories
    sig_mask = volcano_df[PVAL_COLNAME] < METABOANALYSTR_PVAL_CUTOFF
    sig_up_mask = (volcano_df[LFC_COLNAME] > METABOANALYSTR_LOG2FC_CUTOFF) & sig_mask
    sig_down_mask = (volcano_df[LFC_COLNAME] < -METABOANALYSTR_LOG2FC_CUTOFF) & sig_mask
    nonsig_mask = ~(sig_up_mask | sig_down_mask)

    # Plot non-significant points
    ax.scatter(volcano_df[nonsig_mask][LFC_COLNAME], 
              volcano_df[nonsig_mask]['-log10(p-value)'], 
              alpha=0.5, 
              color='grey',
              s=DATA_POINT_SIZE,
              label='Not significant')

    # Plot significant up-regulated points
    ax.scatter(volcano_df[sig_up_mask][LFC_COLNAME], 
              volcano_df[sig_up_mask]['-log10(p-value)'], 
              alpha=0.5,
              color=UP_COLOR,
              edgecolor='black',
              linewidth=1,
              s=DATA_POINT_SIZE,
              label='Significant Up')

    # Plot significant down-regulated points
    ax.scatter(volcano_df[sig_down_mask][LFC_COLNAME], 
              volcano_df[sig_down_mask]['-log10(p-value)'], 
              alpha=0.5,
              color=DOWN_COLOR,
              edgecolor='black', 
              linewidth=1,
              s=DATA_POINT_SIZE,
              label='Significant Down')
    # Set axes limits
    ax.set_xlim(LOG2_FC_RANGE)
    ax.set_ylim(NEG_LOG10_P_RANGE)

    # Set linewidth for axes and ticks and increase tick length
    ax.spines['top'].set_linewidth(LINE_WIDTH)
    ax.spines['right'].set_linewidth(LINE_WIDTH)
    ax.spines['bottom'].set_linewidth(LINE_WIDTH)
    ax.spines['left'].set_linewidth(LINE_WIDTH)
    # Set tick marks at 5-unit intervals
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.yaxis.set_major_locator(plt.MultipleLocator(2))
    ax.tick_params(width=LINE_WIDTH, length=8, labelsize=FONT_SIZE, direction='in')

    # Add labels
    ax.set_xlabel('log2(FC)', fontsize=FONT_SIZE)
    ax.set_ylabel('-log10(p-value)', fontsize=FONT_SIZE)

    # Add plot title, job name
    ax.set_title(f'{job}', fontsize=16)

    # Save plot once and reuse the figure
    volcano_plot_filename = job + '_volcano_plot.png'
    plt.savefig(pjoin(all_volcano_plots_dir, volcano_plot_filename))
    plt.savefig(pjoin(OUTPUT_FOLDER, job, volcano_plot_filename))

    # Add legend and adjust font size
    ax.legend(fontsize=FONT_SIZE)

    # Save plot once and reuse the figure
    volcano_plot_filename = job + '_volcano_plot_legend.png'
    plt.savefig(pjoin(all_volcano_plots_dir, volcano_plot_filename))
    plt.savefig(pjoin(OUTPUT_FOLDER, job, volcano_plot_filename))

    # Add data point labels for most significant features. Use MetaboAnalyst_ID as the label.
    sig_features = volcano_df[sig_mask]
    # Keep only features that pass cutoffs. Keep only upregulated features
    sig_features = sig_features[sig_features[LFC_COLNAME] > METABOANALYSTR_LOG2FC_CUTOFF]
    sig_features = sig_features.sort_values(by=PVAL_COLNAME)
    sig_features = sig_features.head(NUM_SIG_DATA_POINTS_TO_LABEL)
    
    # Create and adjust text labels (only once)
    texts = [plt.text(row[LFC_COLNAME], 
                     row['-log10(p-value)'], 
                     str(row["MetaboAnalyst_ID"]),  # Explicit string conversion
                     fontsize=16) 
             for i, row in sig_features.iterrows()]
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='black', lw=1, alpha=0.5))

    volcano_plot_filename = job + '_volcano_plot_labeled.png'
    plt.savefig(pjoin(all_volcano_plots_dir, volcano_plot_filename))
    plt.savefig(pjoin(OUTPUT_FOLDER, job, volcano_plot_filename))


    plt.close()

    # # Keep track of largest and smallest p-value and log2FC for all jobs
    # all_pvals.extend(volcano_df[PVAL_COLNAME])
    # all_log2FCs.extend(volcano_df[LFC_COLNAME])

    # At the end of the job loop, after plt.close():
    job_end = time.time()
    job_runtime = job_end - job_start
    print(f"Job {job} completed in {job_runtime:.2f} seconds")

# # Print largest and smallest p-value and log2FC for all jobs
# all_pvals = np.array(all_pvals)
# all_log2FCs = np.array(all_log2FCs)
# print(f"Largest p-value: {all_pvals.max()}")
# print(f"Smallest p-value: {all_pvals.min()}")
# print(f"Largest log2FC: {all_log2FCs.max()}")
# print(f"Smallest log2FC: {all_log2FCs.min()}")
