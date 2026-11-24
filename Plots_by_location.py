import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import shutil
import numpy as np
from plot_config import label_list as config_label_list, colors


# Set the path to the directory containing the CSV files
current_dir = os.getcwd()
parent_dir = "E:\\Python\\SEPI_Scripts\\Annual_SEPI_Results"
dir_path = parent_dir
missing_dir_path = "E:\\Python\\SEPI_Scripts\\Results_Missing_Data"

# Create output folder
folder_name = current_dir
os.makedirs(folder_name, exist_ok=True)
output_path1 = os.path.join(folder_name, "storms_per_station_ave.png")
output_path2 = os.path.join(folder_name, "SEPI_per_year_ave.png")
output_path3 = os.path.join(folder_name, "storms_per_Station_BW.png")
output_path4 = os.path.join(folder_name, "SEPI_per_year_BW.png")
output_path5 = os.path.join(folder_name, "Ave_SEPI_per_year.png")



# Convert millimeters to inches
mm_to_inch = 0.0393701
fig_width_mm = 85
fig_height_mm = 50

fig_width_inch = fig_width_mm * mm_to_inch
fig_height_inch = fig_height_mm * mm_to_inch

# Create the figure with the specified size in millimeters
plt.figure(figsize=(fig_width_inch, fig_height_inch))

# Get a list of all Annual SEPI CSV files and their matching missing-data files
file_names = sorted([f for f in os.listdir(dir_path) if f.endswith('Annual SEPI.csv')])
missing_file_names = sorted([f for f in os.listdir(missing_dir_path) if f.endswith('-missing.csv')])

# Sort files by numeric prefix to maintain correct order
def extract_numeric_prefix(filename):
    """Extract the numeric prefix from the filename."""
    for i, char in enumerate(filename):
        if not char.isdigit():
            return int(filename[:i]) if i > 0 else 0
    return 0

file_names = sorted(file_names, key=extract_numeric_prefix)
missing_file_names = sorted(missing_file_names, key=extract_numeric_prefix)

# Map source file names to display labels using config label list
def get_label_for_file(file_name):
    """Get the label from config_label_list based on file position."""
    idx = file_names.index(file_name)
    if idx < len(config_label_list):
        return config_label_list[idx]
    # Fallback to filename-based label if needed
    label = file_name.replace('Annual SEPI.csv', '').strip()
    label = ''.join(c for c in label if not c.isdigit()).strip()
    return label

matched_files = []
for file_name in file_names:
    # Extract numeric prefix from annual file
    prefix = extract_numeric_prefix(file_name)
    # Find matching missing file with same prefix
    matching_missing = None
    for m_file in missing_file_names:
        m_prefix = extract_numeric_prefix(m_file)
        if m_prefix == prefix:
            matching_missing = m_file
            break
    
    if matching_missing:
        matched_files.append((file_name, matching_missing))
    else:
        print(f"Skipping unmatched annual file: {file_name}")

if not matched_files:
    raise RuntimeError('No matching Annual SEPI files found in the specified directories.')

file_names, missing_file_names = map(list, zip(*matched_files))

# Use the config label list
label_list = config_label_list[:len(file_names)]

# Data from Number of Storms"
ave_vals = []
st_devs = []

# Data from "Total SEPI"
SEPI_ave_vals = []
SEPI_st_devs = []

# Copy the data into a list to calculate further stats for Box and Whiskers Plot
number_data = []
SEPI_data = []

# Ave SEPI per year data
Ave_Annual_SEPI_ave_vals = []
Ave_Annual_SEPI_st_devs = []

# Track which labels will actually be used
used_labels = []

for file_name, m_file_name, station_label in zip(file_names, missing_file_names, label_list):
    print(station_label)
    
    # Load the CSV file into a pandas dataframe
    df = pd.read_csv(os.path.join(dir_path, file_name))
    mdf = pd.read_csv(os.path.join(missing_dir_path, m_file_name))

    # Clean the column names
    df.columns = df.columns.str.strip().copy()
    mdf.columns = mdf.columns.str.strip().copy()

    required_df_cols = ['Year', 'Number of Storms', 'Total SEPI']
    missing_df_cols = [col for col in required_df_cols if col not in df.columns]
    required_mdf_cols = ['Year', '# of Missing points']
    missing_mdf_cols = [col for col in required_mdf_cols if col not in mdf.columns]

    if missing_df_cols or missing_mdf_cols:
        print(f"Skipping {file_name}: missing required columns {missing_df_cols + missing_mdf_cols}")
        continue
    
    # Add label to used_labels only if file is valid
    used_labels.append(station_label)

    total_num_points = 8760
    thr = .1 * 8760        # Only keep if 90% of the data is present
    mdf.loc[:, 'Threshold'] = mdf['# of Missing points'].apply(lambda x: True if x < thr else False).copy()

    # Create an empty list to store the years that satisfy the condition
    years_to_skip = []

    # Iterate through the DataFrame and check the condition
    for index, row in mdf.iterrows():
        if row['Threshold'] is False:
            years_to_skip.append(row['Year'])
            
    #print("Number of Years to Skip = ", len(years_to_skip))
    print("Incomplete data for years: ", years_to_skip)
    
    # Filter the rows of df using the list of years to skip
    df_filtered = df.loc[~df['Year'].isin(years_to_skip)]
    
    ave_storms = df_filtered['Number of Storms'].mean()
    ave_vals.append(ave_storms)
    
    stdev = df_filtered['Number of Storms'].std()
    st_devs.append(stdev)
    
    SEPI_ave = df_filtered['Total SEPI'].mean()
    SEPI_ave_vals.append(SEPI_ave)
    
    SEPI_stdev = df_filtered['Total SEPI'].std()
    SEPI_st_devs.append(SEPI_stdev)
    
    number_data.append(df_filtered['Number of Storms'])
    SEPI_data.append(df_filtered['Total SEPI'])

    # Calculate average value of SEPI per year = total value of annual SEPI / total annual number of storms
    Ave_Annual_SEPI_data = df_filtered['Total SEPI'] / df_filtered['Number of Storms']
    Ave_Annual_SEPI_ave = Ave_Annual_SEPI_data.mean()
    Ave_Annual_SEPI_ave_vals.append(Ave_Annual_SEPI_ave)
    Ave_Annual_SEPI_std = Ave_Annual_SEPI_data.std()
    Ave_Annual_SEPI_st_devs.append(Ave_Annual_SEPI_std)

# First plot - Ave per year
plt.figure(figsize=(fig_width_inch, fig_height_inch))
x = np.arange(len(used_labels))
fig, ax = plt.subplots(figsize=(12, 4))  # bigger width
ax.errorbar(
    x, ave_vals,
    yerr=st_devs,
    marker='o',
    markersize=2.0,
    capsize=2.0,
    linestyle="None",
    ecolor='red',
    markerfacecolor='none',
    markeredgecolor='red',
    linewidth=1.0
)
ax.set_xticks(x)
ax.set_xticklabels(used_labels, rotation=90, fontsize=10, ha='center')
ax.set_ylabel("Num. of Storms", fontsize=12)
ax.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
ax.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.tight_layout()
plt.savefig(output_path1, dpi=1000, bbox_inches='tight')
plt.close()


# Second Plot - Total SEPI per year
plt.figure(figsize=(fig_width_inch, fig_height_inch))
plt.ylabel("Total SEPI per Year ($m^2 h$)", fontsize = 22)
plt.errorbar(x, SEPI_ave_vals, yerr=SEPI_st_devs, marker='o', markersize = 2.0, capsize=2.0, linestyle="None", ecolor='blue', markerfacecolor='none', markeredgecolor='blue', linewidth=1.0)
plt.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(20))
plt.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(100))
plt.xticks(x, used_labels, rotation='vertical', fontsize=10)
plt.ylabel("SEPI per Year ($m^2 h$)", fontsize = 12)
plt.yticks(fontsize=10)
plt.savefig(output_path2, dpi=1000, bbox_inches='tight')
plt.tick_params(axis='both', labelsize=10)
plt.close()

# Third Plot - Box and Whiskers Plot for Storms per Station
plt.figure(figsize=(fig_width_inch, fig_height_inch))
plt.boxplot(number_data, labels = used_labels, flierprops={'markersize': 2})
x_ticks = np.arange(1, len(used_labels) + 1)
plt.xticks(x_ticks, used_labels, rotation='vertical', fontsize=10)
plt.ylabel("Num. of Storms", fontsize = 12)
# Customize the gridlines and labels
plt.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(2))
plt.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(10))
plt.yticks(fontsize=10)
plt.savefig(output_path3, dpi=1000, bbox_inches='tight')
plt.close()

# Forth Plot - Box and Whiskers Plot for Storms per Station
plt.figure(figsize=(fig_width_inch, fig_height_inch))
plt.boxplot(SEPI_data, labels = used_labels, flierprops={'markersize': 2})
x_ticks = np.arange(1, len(used_labels) + 1)
plt.xticks(x_ticks, used_labels, rotation='vertical', fontsize=10)
plt.ylabel("SEPI per Year", fontsize = 12)
plt.yticks(fontsize=10)
# Customize the gridlines and labels
plt.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(20))
plt.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(100))
plt.savefig(output_path4, dpi=1000, bbox_inches='tight')
plt.close()

# 5th Plot - Ave SEPI per year
plt.figure(figsize=(fig_width_inch, fig_height_inch))
plt.ylabel("Ave SEPI per Year ($m^2 h$)", fontsize = 22)
plt.errorbar(x, Ave_Annual_SEPI_ave_vals, yerr=Ave_Annual_SEPI_st_devs, marker='o', markersize = 2.0, capsize=2.0, linestyle="None", ecolor='blue', markerfacecolor='none', markeredgecolor='blue', linewidth=1.0)
plt.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(2))
plt.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(10))
plt.xticks(x, used_labels, rotation='vertical', fontsize=10)
plt.ylabel("Ave SEPI per Year ($m^2 h$)", fontsize = 12)
plt.yticks(fontsize=10)
plt.savefig(output_path5, dpi=1000, bbox_inches='tight')
plt.tick_params(axis='both', labelsize=10)
plt.close()