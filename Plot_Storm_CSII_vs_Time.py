import sys
import os
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import shutil
import numpy as np
from scipy.stats import linregress
from plot_config import colors, font_family,  label_list
from dateutil import parser
import csv
import matplotlib.lines as mlines
import matplotlib.ticker as ticker  # Import the ticker module
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import matplotlib.dates as mdates

font_size = 14 
label_size = 13

plt.rcParams["font.family"] = "Arial"

# Make plots for all stations with a single delta value
delta = 0.3
delta_str = str(delta).replace('.', '-')

# Convert millimeters to inches
mm_to_inch = 0.0393701
fig_width_mm = 250
fig_height_mm = 210

fig_width_inch = fig_width_mm * mm_to_inch
fig_height_inch = fig_height_mm * mm_to_inch

# Create the figure with the specified size in millimeters
plt.figure(figsize=(fig_width_inch, fig_height_inch))
plt.subplots_adjust(right=0.8)

# Set the path to the directory containing the CSV files
current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)
folder_path = "E:\Python\SEPI_Scripts\Final_Storm_Results"

# Create the path to the folder within the current directory
filenames = os.listdir(folder_path)
file_paths = [os.path.join(folder_path, f) for f in filenames]

# Get a list of all CSV files in the directory
file_names = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
file_names = sorted(file_names)
print(file_names)
now = datetime.now()
date_string = now.strftime("%Y-%m-%d")
output_path = f"CSII_Plot_delta_{delta_str}.png"

# Set the vertical offset
vertical_offset = 4200.0

# Create a list to store the dataframes
dfs = []

i = 0
summary = []
all_results_min = float('inf')
all_results_max = float('-inf')
#fig, ax = plt.subplots()
#fig, ax = plt.subplots(figsize=(10, 7))

#for filename in os.listdir(directory):
for i, file_name in enumerate(file_names):
    print(file_name)
    print("Color = ", colors[i % len(colors)])
    print(label_list[i % len(label_list)])

    if file_name.endswith(".csv"):
        filepath = os.path.join(folder_path, file_name)
        with open(filepath) as f:
            reader = csv.reader(f)
            next(reader)  # skip the header row
            dates = []
            sepi = []
            tp = []
            result = []

            for row in reader:
                try:
                    date = parser.parse(row[0]).date()
                    # Filter out dates outside the expected range (2002-2025)
                    if date.year < 2000 or date.year > 2030:
                        print(f"  Warning: Skipping outlier date {date} in {file_name}")
                        continue
                    sepi_val = float(row[1])
                    tp_val = float(row[2])
                    dates.append(date)
                    sepi.append(sepi_val)
                    tp.append(tp_val)
                except Exception as e:
                    print(f"  Error parsing row {row}: {e}")
                
        tau_p = [t / 365 for t in tp]
        csii = [sepi[0]]
        for j in range(1, len(sepi)):
            csii_val = sepi[j] + csii[j-1] * delta ** tau_p[j]
            csii.append(csii_val)
        
        for num in csii:
            result.append(num + vertical_offset)
        plt.plot(dates, result, marker='o', markersize = 1.0, color=colors[i % len(colors)], linewidth = .5, label=label_list[i], linestyle = "None")
        vertical_offset -= 400.0

        all_results_min = min(all_results_min, min(result))
        all_results_max = max(all_results_max, max(result))

        decimal_dates = []

        # Convert `dates` to decimal years before doing any regression or fitting
        for val in dates:
            decimal_year = val.year + (val.timetuple().tm_yday - 1) / 365.25
            decimal_dates.append(decimal_year)

        # Add linear trendline and equation only if we have enough data
        x = np.array(decimal_dates)
        y = np.array(result)
        x_nums = mdates.date2num(dates)
        if x.size >= 2 and y.size >= 2:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)

            # Calculate linear regression and p-value using scipy.stats.linregress
            slope, intercept, r_value, p_value, std_err = linregress(x, y)
            r2_value = r_value * r_value
            slope_per_year = slope * 365.25

            # Attempt ADF test, guard against errors for very small series
            try:
                adf_result = adfuller(y)
                adf_stat, adf_p = adf_result[0], adf_result[1]
            except Exception:
                adf_stat, adf_p = (None, None)
            summary.append({
                        "station": label_list[i],
                        "slope_per_year": slope_per_year,
                        "r2": r2_value,
                        "p_value": p_value,
                        "adf_p_value": adf_result[1],
                        "stderr_per_year" : std_err*365.25,
                        "intercept": intercept
                    })
            # Print equation and p-value
            print("Trendline: y = {:.2f}x + {:.2f}".format(slope, intercept))
            print("P-value for slope coefficient:", p_value)
            if adf_p is not None:
                print('ADF Statistic:', adf_stat)
                print('p-value for adf', adf_p)
                if adf_p < 0.05:
                    print("The data is stationary (p-value < 0.05).")
                else:
                    print("The data is not stationary (p-value >= 0.05).")

            label_text = "m = {:.4f}, p = {:.4f}, $R^2$ = {:.4f}, st err = {:.4f}".format(slope, p_value, r2_value, std_err)
            print("y={:.2f}x+{:.2f}".format(z[0], z[1]))
            # Optionally plot trendline using the same x-values as the fit
            plt.plot(dates, p(x), color=colors[i % len(colors)], label=f'Trend Line: y={slope:.4f} + {intercept:.2f}')
        #plt.plot(dates, result, marker='o', markersize = 1.0, color='k', linewidth = .5, label=label_list[i], linestyle = "None")
            i += 1
print("Summary of trends:",summary)
summary_df = pd.DataFrame(summary)

plt.grid(True, which='major', axis='x', alpha=0.5, linestyle='-')
#plt.gca().yaxis.set_major_locator(plt.MultipleLocator(200))
plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(365 * 5))  # 365 days per year
plt.grid(True, which='minor', axis='x', alpha=0.5, linestyle='-')

# Set the major grid lines for y ax
plt.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(300))

# Set the minor grid lines for the y-axis
plt.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(100))

# Use dynamic y-limits based on the plotted offsets so all station series are visible.
plt.ylim(all_results_min - 100, all_results_max + 100)
#plt.xlim(1910,2055)

#xticks = [1920, 1940, 1960, 1980, 2000, 2020]
#plt.xticks(xticks)


plt.xlabel("Date", fontsize=font_size)
plt.ylabel("CSII ($m^2 \cdot h$)", fontsize=font_size)
#plt.text(0.5, -0.1, "(b)", transform=plt.gca().transAxes, fontsize=label_size, ha='center')
# Create the legend and store it in a variable
leg = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=font_size)

# Save, explicitly including the legend in the tight bounding box calculation
plt.savefig(output_path, dpi=300, bbox_inches='tight', bbox_extra_artists=(leg,))
plt.show()
plt.clf

