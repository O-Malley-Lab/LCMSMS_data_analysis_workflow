import os
from os.path import join as pjoin
import zipfile
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
GNPS_OUTPUT_FOLDER = r'GNPS_output'
OUTPUT_FOLDER = r'output'

# for each folder in GNPS_OUTPUT_FOLDER, if the folder contains a zipped folder, unzip the contents within the folder
if os.path.exists(GNPS_OUTPUT_FOLDER):
    for folder in os.listdir(GNPS_OUTPUT_FOLDER):
        folder_path = pjoin(GNPS_OUTPUT_FOLDER, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                file_path = pjoin(folder_path, file)
                if file.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(folder_path)
                    os.remove(file_path)