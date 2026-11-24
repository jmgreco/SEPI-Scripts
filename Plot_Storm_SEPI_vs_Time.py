import sys
import os
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import shutil
import numpy as np
from scipy.stats import linregress
from plot_config import colors, font_family,  label_list
from dateutil import parser
import csv
import matplotlib.ticker as ticker
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

font_size = 14 
label_size = 13


plt.rcParams["font.family"] = "Arial"

# Convert millimeters to inches
mm_to_inch = 0.0393701
fig_width_mm = 300
fig_height_mm = 210
fig_width_inch = fig_width_mm * mm_to_inch
fig_height_inch = fig_height_mm * mm_to_inch
plt.figure(figsize=(fig_width_inch, fig_height_inch))
plt.subplots_adjust(right=0.8)

# Set the path to the directory containing the CSV files
current_dir = os.getcwd()
parent_dir = 'e:\Python\SEPI_Scritps\Final_Storm_Results'
folder_path = "E:\Python\SEPI_Scripts\Final_Storm_Results"

# Create the path to the folder within the current directory
filenames = os.listdir(folder_path)
file_paths = [os.path.join(folder_path, f) for f in filenames]

# Get a list of all CSV files in the directory
file_names = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
file_names = sorted(file_names)

now = datetime.now()
date_string = now.strftime("%Y-%m-%d")
output_path = "SEPI_vs_Time.png"

# Set the vertical offset
vertical_offset = 3600.0 


# Create a list to store the dataframes
dfs = []
i = 0
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
            values1 = []
            values2 = []
            for row in reader:
                date = parser.parse(row[0]).date()
                #date = datetime.strptime(row[0], '%Y-%m-%d %H:%M')
                value1 = float(row[1])
                value2 = float(row[2])
                dates.append(date)
                values1.append(value1)
                values2.append(value2)
        
        result = []
        decimal_dates = []
        for num in values1:
            result.append(num + vertical_offset)
            
        for val in dates:
            decimal_year = val.year + (val.timetuple().tm_yday - 1) / 365.25
            decimal_dates.append(decimal_year)
        plt.plot(dates, result, marker='o', markersize = 1.0, color=colors[i % len(colors)], linewidth = .5, label=label_list[i], linestyle = "None")
        #vertical_offset -= 200.0    #goes with a initial veritcal offset (above) of 2200.0)

        
        # Add linear trendline and equation using matplotlib date numbers
        x_nums = mdates.date2num(dates)
        y = result
        z = np.polyfit(x_nums, y, 1)
        p = np.poly1d(z)
        
        # Calculate linear regression and p-value using scipy.stats.linregress
        slope, intercept, r_value, p_value, std_err = linregress(x_nums, y)
        summary = []
        slope_per_year = slope * 365.25
        r2_value = r_value**2

        summary.append({
            "station": label_list[i],
            "slope_per_year": slope_per_year,
            "r2": r2_value,
            "p_value": p_value,
            "stderr_per_year" : std_err*365.25,
            "intercept": intercept
        })
        
        adf_result = adfuller(y)

        # Print equation and p-value
        print(f"Trendline: y = {slope_per_year:.4f} per year + {intercept:.2f}")
        print("P-value for slope coefficient:", p_value)
        print('ADF Statistic:', adf_result[0])
        print('p-value for adf test:', adf_result[1])

        #Interpreting the results
        if adf_result[1] < 0.05 : 
            print("The data is stationary (p-value < 0.05).")
        else:
            print("The data is not stationary (p-value >= 0.05).")
        # Uncomment to plot trendlines
            
        #for val in dates:
            #decimal_year = val.year + (val.timetuple().tm_yday - 1) / 365.25
            #decimal_dates.append(decimal_year)
        #plt.plot(dates, result, marker='o', markersize = 1.0, color=colors[i % len(colors)], linewidth = .5, label=label_list[i], linestyle = "None")
        #vertical_offset -= 200.0    #goes with a initial veritcal offset (above) of 2200.0)
        #plt.plot(x, p, "k--", linewidth=2, color = 'black', label = "Trendline: y = {:.2f}x + {:.2f}".format(slope, intercept))
       # label_text = "m = {:.4f}, p = {:.4f}, $R^2$ = {:.4f}, st err = {:.4f}".format(slope, p_value, r2_value, std_err)
        #print("y={:.2f}x+{:.2f}".format(z[0], z[1]))
        #plt.plot(x, p, "k--", linewidth=2, color = 'black', label = "Trendline: y = {:.2f}x + {:.2f}".format(slope, intercept))
        # Print labels next to the data points
        x_label = 4070
        y_label = vertical_offset + 80
        #plt.text(x_label, y_label, label_text, color=colors[i % len(colors)], fontsize=8)
        
        
        vertical_offset -= 300.0
        plt.plot(dates, p(x_nums), color=colors[i % len(colors)], label=f'Trend Line: y={slope_per_year:.4f} + {intercept:.2f}')
        i += 1
summary_df = pd.DataFrame(summary)
print(summary_df.sort_values("slope_per_year", ascending = False))
print(summary_df[["slope_per_year", "r2", "p_value"]].describe())
plt.grid(True, which='major', axis='x', alpha=0.5, linestyle='-')
#plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(25))
#plt.grid(True, which='minor', axis='x', alpha=0.5, linestyle='-')
plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(365 * 5))  # 365 days per year
plt.grid(True, which='minor', axis='x', alpha=0.5, linestyle='-')

# Set the major grid lines for y ax
plt.grid(True, which='major', axis='y', alpha=0.5, linestyle='-')
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(300))

# Set the minor grid lines for the y-axis
plt.grid(True, which='minor', axis='y', alpha=0.5, linestyle='--')
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(100))

plt.ylim(-100, 3700)
#plt.xlim(1910,2055)

#xticks = [1920, 1940, 1960, 1980, 2000, 2020]
#plt.xticks(xticks)

plt.xlabel("Date", fontsize=font_size)
plt.ylabel("SEPI ($m^2 \cdot h$)", fontsize=font_size)
#plt.text(0.5, -0.1, "(a)", transform=plt.gca().transAxes, fontsize=label_size, ha='center')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize = font_size)

#plt.savefig(output_path, dpi=300, bbox_inches='tight')
# Create the legend and store it in a variable
leg = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=font_size)

# Save, explicitly including the legend in the tight bounding box calculation
plt.savefig(output_path, dpi=300, bbox_inches='tight', bbox_extra_artists=(leg,))

plt.show()
plt.clf

print("Slope ranking:")
print(summary_df[["station","slope_per_year"]].sort_values("slope_per_year", ascending=False))

print("Positive slopes:", (summary_df["slope_per_year"] > 0).sum())
print("Negative slopes:", (summary_df["slope_per_year"] < 0).sum())



