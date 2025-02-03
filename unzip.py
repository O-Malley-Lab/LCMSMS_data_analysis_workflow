import os
import shutil
from os.path import join as pjoin
import zipfile
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
GNPS_OUTPUT_FOLDER = r'GNPS_output'
OUTPUT_FOLDER = r'output'

"""
Unzip files in INPUT_FOLDER
"""
# # for each folder in GNPS_OUTPUT_FOLDER, if the folder contains a zipped folder, unzip the contents within the folder
# if os.path.exists(GNPS_OUTPUT_FOLDER):
#     for folder in os.listdir(GNPS_OUTPUT_FOLDER):
#         folder_path = pjoin(GNPS_OUTPUT_FOLDER, folder)
#         if os.path.isdir(folder_path):
#             for file in os.listdir(folder_path):
#                 file_path = pjoin(folder_path, file)
#                 if file.endswith('.zip'):
#                     with zipfile.ZipFile(file_path, 'r') as zip_ref:
#                         zip_ref.extractall(folder_path)
#                     os.remove(file_path)


"""
Move volcano plots to a single folder
"""
# # For each job folder in TEMP_OVERALL_FOLDER, go into the folder named "MetaboAnalystR_Output" and copy the file with "Volcano_" at the start of its filename. Paste the file into the folder in OUTPUT_FOLDER named "all_volcano_plots"
# if os.path.exists(OUTPUT_FOLDER):
#     # Ensure destination folder exists
#     volcano_plots_dir = pjoin(OUTPUT_FOLDER, 'all_volcano_plots')
#     os.makedirs(volcano_plots_dir, exist_ok=True)


# if os.path.exists(TEMP_OVERALL_FOLDER):
#     for folder in os.listdir(TEMP_OVERALL_FOLDER):
#         folder_path = pjoin(TEMP_OVERALL_FOLDER, folder)
#         if os.path.isdir(folder_path):
#             metabo_dir = pjoin(folder_path, 'MetaboAnalystR_Output')
#             if os.path.exists(metabo_dir):
#                 for subfile in os.listdir(metabo_dir):
#                     if subfile.startswith('Volcano_'):
#                         src_path = pjoin(metabo_dir, subfile)
#                         dst_path = pjoin(volcano_plots_dir, subfile)
#                         try:
#                             shutil.copy2(src_path, dst_path)  # copy2 preserves metadata
#                         except (IOError, OSError) as e:
#                             print(f"Error copying {src_path}: {e}")