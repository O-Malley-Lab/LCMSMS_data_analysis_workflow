"""""""""""""""""""""""""""""""""""""""""""""
LCMSMS Data Analysis Workflow, Script 5: A. nidulans vs. Yeast Heterologous Expression GNPS Analysis
@author: Lazarina Butkovich

This script has the following features for analyzing GNPS output for comparing A. nidulans and Yeast heterologous expression of the same gut fungal proteinID:
- Create 

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
Values
"""""""""""""""""""""""""""""""""""""""""""""
INPUT_FOLDER = r'input' 
TEMP_OVERALL_FOLDER = r'temp'
GNPS_OUTPUT_FOLDER = r'GNPS_output'
OUTPUT_FOLDER = r'output'

METADATA_FILENAME = 'Anid_vs_Yeast_HE_Groupings_Metadata.xlsx'
