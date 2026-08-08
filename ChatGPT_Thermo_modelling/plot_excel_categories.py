"""
Read an Excel file whose column names start on row 95 and plot columns by category.

Edit COLUMN_CATEGORIES after the first run: the script prints any columns that are
not yet assigned. Accepted categories are "temp", "power", and "other".
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# Changed: Put your Excel column names here as keys, and assign each one to
# "temp", "power", or "other". Unlisted columns are automatically "other".

dict = {  'METEO_GardenWS_AT.PV': 'temp', 'F0N2_FCM1.PV' : 'tempf', 'F0N2_FCM1.SP' : 'tempf',

         'F0N2_FCM1_C5.PV': 'fr', 'F0N2_FCM1_ST1.PV': 'tempf', 'F0N2_FCM1_ST2.PV': 'tempf', 

         'F0N2_FCM2.PV' : 'tempf', 'F0N2_FCM2.SP' : 'tempf',

        'F0N2_FCM2_C6.PV': 'fr', 'F0N2_FCM2_ST1.PV': 'tempf', 'F0N2_FCM2_ST2.PV': 'tempf',

         'HVAC_CP301.PV': 'fr', 'HVAC_ENF1_CVM.W': 'power',

          'HVAC_Enfriadora1.SP': 'temp', 'HVAC_SP301.PV': 'temp', 'HVAC_SP302.PV': 'temp', 

            'HVAC_CP401.PV': 'fr', 'HVAC_ENF2_CVM.W': 'power', 'HVAC_Enfriadora2.SP': 'temp', 'HVAC_SP401.PV': 'temp', 'HVAC_SP402.PV': 'temp'}





def plot_excel_categories(path):
    """Read the Excel file and output 3 Matplotlib figures: temp, power, other."""

    df = pd.read_excel(path, header=94, engine='calamine')

    x_column = 'DateTime'
    x_values = df[x_column]

    grouped_columns = {"temp": [],'tempf': [], "power": [], 'fr': [], 'other': [], }
    for column in dict:
        category = dict[column]
        if category not in grouped_columns:
            category = "other"
        grouped_columns[category].append(column)

    for category, columns in grouped_columns.items():
        fig, ax = plt.subplots(figsize=(12, 6))
        for column in columns:
            numeric_values = pd.to_numeric(df[column], errors="coerce")
            if numeric_values.notna().any():
                ax.plot(x_values[:100], numeric_values[:100], label=str(column))

        ax.set_title(category)
        ax.set_xlabel(x_column)
        ax.set_ylabel(category)
        ax.grid(True, alpha=0.3)
        if ax.lines:
            ax.legend(loc="best", fontsize="small")
        else:
            ax.text(0.5, 0.5, f"No numeric {category} columns", ha="center", va="center")
        fig.tight_layout()

    plt.show()

if __name__ == "__main__":
    path = r"C:\Users\andre\Downloads\cooling_july_october.xlsx"

    plot_excel_categories(path)
