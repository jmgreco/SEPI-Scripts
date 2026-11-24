import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import re
import numpy as np
from plot_config import colors, font_family, font_size, label_size

plt.rcParams["font.family"] = font_family

def parse_duration_to_days(duration_str):
    duration_str = str(duration_str).strip()
    if not duration_str:
        return 0.0
    days = hours = minutes = 0.0
    for match in re.finditer(r"(\d+\.?\d*)\s*([dhm])", duration_str):
        value = float(match.group(1))
        unit = match.group(2)
        if unit == 'd':
            days += value
        elif unit == 'h':
            hours += value
        elif unit == 'm':
            minutes += value
    return days + hours / 24 + minutes / 1440


def station_name_from_filename(filename):
    name = filename.replace('TEMPStorm.csv', '')
    return name.strip()


def compute_csii(series_sepi, series_duration_days, delta=0.3):
    csii = []
    if len(series_sepi) == 0:
        return csii
    csii.append(series_sepi.iloc[0])
    for idx in range(1, len(series_sepi)):
        tau_p = series_duration_days.iloc[idx] / 365.0
        csii_val = series_sepi.iloc[idx] + csii[idx - 1] * delta ** tau_p
        csii.append(csii_val)
    return pd.Series(csii, index=series_sepi.index)


def main():
    root_dir = Path(__file__).resolve().parent
    input_dir = root_dir / 'TEMP_Storm_Results'
    output_dir = root_dir / 'CSII_SEPI_Comparison_Results'
    output_dir.mkdir(exist_ok=True)

    station_rows = []
    annual_rows = []
    all_station_dfs = []
    delta = 0.3

    csv_files = sorted([p for p in input_dir.glob('*TEMPStorm.csv') if p.is_file()])
    if not csv_files:
        raise FileNotFoundError(f'No TEMPStorm.csv files found in {input_dir}')

    for file_idx, csv_path in enumerate(csv_files):
        station_name = station_name_from_filename(csv_path.name)
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()

        if 'Start Date' not in df.columns or 'SEPI' not in df.columns or 'Duration' not in df.columns:
            raise ValueError(f'Missing expected columns in {csv_path.name}. Expected Start Date, SEPI, Duration.')

        df = df.copy()
        df['Station'] = station_name
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        df = df.dropna(subset=['Start Date', 'SEPI'])
        df['SEPI'] = pd.to_numeric(df['SEPI'], errors='coerce')
        df['Duration Days'] = df['Duration'].apply(parse_duration_to_days)
        df = df.sort_values('Start Date').reset_index(drop=True)
        df['CSII'] = compute_csii(df['SEPI'], df['Duration Days'], delta=delta)
        df['Year'] = df['Start Date'].dt.year

        all_station_dfs.append(df)

        # Save per-station time series rows for combined CSV
        station_rows.append(df[['Station', 'Start Date', 'SEPI', 'Duration', 'Duration Days', 'CSII']])

        # Annual average values for each station
        annual = (
            df.groupby('Year')
            .agg(
                Annual_Average_CSII=('CSII', 'mean'),
                Annual_Average_SEPI=('SEPI', 'mean'),
                Event_Count=('SEPI', 'count')
            )
            .reset_index()
        )
        annual['Station'] = station_name
        annual_rows.append(annual)

    combined_df = pd.concat(station_rows, ignore_index=True)
    combined_df = combined_df.sort_values(['Station', 'Start Date'])
    combined_csv_path = output_dir / 'csii_timeseries_all_stations.csv'
    combined_df.to_csv(combined_csv_path, index=False)

    annual_df = pd.concat(annual_rows, ignore_index=True)
    annual_df = annual_df[(annual_df['Year'] >= 2022) & (annual_df['Year'] <= 2026)]
    annual_csv_path = output_dir / 'csii_annual_average_by_station_2022_2026.csv'
    annual_df.to_csv(annual_csv_path, index=False)

    print(f'Saved CSII time series CSV: {combined_csv_path}')
    print(f'Saved annual average CSV: {annual_csv_path}')

    # Plot 1: CSII over time for all stations
    plt.figure(figsize=(12, 6))
    for idx, df in enumerate(all_station_dfs):
        station_name = df['Station'].iloc[0]
        plt.plot(df['Start Date'], df['CSII'], label=station_name, color=colors[idx % len(colors)], linewidth=1)
    plt.title('CSII Time Series for All Stations', fontsize=font_size)
    plt.xlabel('Date', fontsize=label_size)
    plt.ylabel('CSII ($m^2 \\cdot h$)', fontsize=label_size)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(output_dir / 'csii_time_series_all_stations.png', dpi=300)
    plt.close()

    # Plot 2: Grouped bar chart of mean CSII and mean SEPI per station (2022-2026)
    station_means = (
        annual_df.groupby('Station')
        .agg(Mean_CSII=('Annual_Average_CSII', 'mean'), Mean_SEPI=('Annual_Average_SEPI', 'mean'))
        .reset_index()
        .sort_values('Station')
    )

    stations = station_means['Station'].tolist()
    csii_vals = station_means['Mean_CSII'].fillna(0).values
    sepi_vals = station_means['Mean_SEPI'].fillna(0).values

    x = np.arange(len(stations))
    width = 0.35

    plt.figure(figsize=(14, 7))
    # Use two consistent colors: one for CSII, one for SEPI
    csii_color = colors[1 % len(colors)]
    sepi_color = colors[3 % len(colors)]

    bars1 = plt.bar(x - width/2, csii_vals, width, label='Mean CSII', color=csii_color)
    bars2 = plt.bar(x + width/2, sepi_vals, width, label='Mean SEPI', color=sepi_color, alpha=0.85)

    # Add numeric labels on top of bars
    def autolabel(bars, fmt='{:.0f}'):
        for bar in bars:
            h = bar.get_height()
            plt.annotate(fmt.format(h),
                         xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 3),
                         textcoords='offset points',
                         ha='center', va='bottom', fontsize=8)

    autolabel(bars1, fmt='{:.0f}')
    autolabel(bars2, fmt='{:.0f}')

    plt.title('Mean CSII and Mean SEPI per Station (2022-2026)', fontsize=font_size)
    plt.xlabel('Station', fontsize=label_size)
    plt.ylabel('Mean Annual Value ($m^2 \\cdot h$)', fontsize=label_size)
    plt.xticks(x, stations, rotation=45, ha='right')

    # Format y-axis with thousands separator
    import matplotlib.ticker as mtick
    plt.gca().yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: format(int(x), ',')))

    # Adjust y-limits for padding
    ymax = max(csii_vals.max() if len(csii_vals) else 0, sepi_vals.max() if len(sepi_vals) else 0)
    plt.ylim(0, ymax * 1.15 if ymax > 0 else 1)

    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(output_dir / 'annual_average_csii_sepi_comparison_2022_2026_bar.png', dpi=300)
    plt.close()

    print('Saved plot: csii_time_series_all_stations.png')
    print('Saved plot: annual_average_csii_sepi_comparison_2022_2026_bar.png')


if __name__ == '__main__':
    main()
