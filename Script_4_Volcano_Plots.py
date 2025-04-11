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
def build_metaboanalystid_col(volcano_df, feature_id_colname, mz_col_name = 'precursor mass', rt_col_name = 'RTMean', metaboanalystid_col_name = 'MetaboAnalyst_ID'):
    """
    Build the MetaboAnalystID column, using the format of #/#mz/#min (ie: 4867/504.3237mz/7.463min) and the existing Feature ID #, RT and m/z columns.

    Inputs
    volcano_df: pandas DataFrame containing the data
    feature_id_colname: str, name of the column containing the Feature ID
    mz_col_name: str, name of the column containing the m/z values (default: 'precursor mass')
    rt_col_name: str, name of the column containing the RT values (default: 'RTMean')
    metaboanalystid_col_name: str, name of the column to be created for MetaboAnalyst ID (default: 'MetaboAnalyst_ID')
    
    Outputs
    return: None
    """
    new_col = volcano_df[feature_id_colname] + '/' + volcano_df[mz_col_name].astype(str) + 'mz/' + volcano_df[rt_col_name].astype(str) + 'min'
    volcano_df[metaboanalystid_col_name] = new_col
    return

def plot_cutoff_lines(ax, pval_cutoff, log2fc_cutoff, line_width, line_color='black'):
    """
    Plot significance cutoff lines on a volcano plot.
    
    Inputs
    ax: matplotlib Axes object to plot on
    pval_cutoff: float, p-value cutoff for significance
    log2fc_cutoff: float, log2 fold change cutoff for significance
    line_width: float, width of the cutoff lines
    pval_colname: str, name of the p-value column (default: 'p-value')
    log2fc_colname: str, name of the log2 fold change column (default: 'log2FC')

    Outputs
    return: None
    """
    ax.axhline(y=-np.log10(pval_cutoff), color=line_color, linestyle='--', alpha=0.5, linewidth=line_width)
    ax.axvline(x=-log2fc_cutoff, color=line_color, linestyle='--', alpha=0.5, linewidth=line_width)
    ax.axvline(x=log2fc_cutoff, color=line_color, linestyle='--', alpha=0.5, linewidth=line_width)
    return

def format_volcano_plot(ax, lfc_range, neg_log10_p_range, line_width=2, font_size=12):
    """
    Format the volcano plot using specific parameters.
    
    Inputs
    ax: matplotlib Axes object to format
    lfc_range: tuple, range for the x-axis (log2 fold change)
    neg_log10_p_range: tuple, range for the y-axis (-log10 p-value)
    line_width: float, width of the axes lines and ticks
    font_size: int, size of the tick labels

    Outputs
    return: None
    """
    # Set axes limits
    ax.set_xlim(lfc_range)
    ax.set_ylim(neg_log10_p_range)
    # Set linewidth for axes and ticks and increase tick length
    ax.spines['top'].set_linewidth(line_width)
    ax.spines['right'].set_linewidth(line_width)
    ax.spines['bottom'].set_linewidth(line_width)
    ax.spines['left'].set_linewidth(line_width)
    # Set tick marks at 5-unit intervals
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.yaxis.set_major_locator(plt.MultipleLocator(2))
    ax.tick_params(width=line_width, length=8, labelsize=font_size, direction='in')
    ax.legend(fontsize=font_size)
    return
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

# Start the overall timer
total_start = time.time()

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
    build_metaboanalystid_col(volcano_df, FEATURE_ID_COLNAME)

    # Filter only for rows with non-NaN values in LFC_COLNAME and PVAL_COLNAME
    volcano_df = volcano_df.dropna(subset=[LFC_COLNAME, PVAL_COLNAME])

    # Create volcano plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Add dotted lines for cutoffs
    plot_cutoff_lines(ax, METABOANALYSTR_PVAL_CUTOFF, METABOANALYSTR_LOG2FC_CUTOFF, line_width=LINE_WIDTH)

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
    
    # Set axes limits, add legend, linewidths for axes and ticks, and tick intervals
    format_volcano_plot(ax, LOG2_FC_RANGE, NEG_LOG10_P_RANGE, line_width=LINE_WIDTH, font_size=FONT_SIZE)

    # Add labels
    ax.set_xlabel('log2(FC)', fontsize=FONT_SIZE)
    ax.set_ylabel('-log10(p-value)', fontsize=FONT_SIZE)

    # Add plot title, job name. Remove the portion of the job string after the last "_"
    job_title = job.rsplit('_', 1)[0]
    ax.set_title(f'{job_title}', fontsize=FONT_SIZE)

    # Save plot once and reuse the figure
    volcano_plot_filename = job + '_volcano_plot.png'
    plt.savefig(pjoin(all_volcano_plots_dir, volcano_plot_filename))
    plt.savefig(pjoin(OUTPUT_FOLDER, job, volcano_plot_filename))

    # Add legend and adjust font size
    ax.legend(fontsize=FONT_SIZE)

    # Save plot once and reuse the figure for additional formats of the figure
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

    # Print job time completion message
    job_end = time.time()
    job_runtime = job_end - job_start
    print(f"Job {job} completed in {job_runtime:.2f} seconds")