# Utilitaire
import os
import json

path = r"C:\Users\andre\UniMelb\ChatGPT_Thermo_modelling\ep_chiller_cache\chiller_database.json"


with open(path, "r", encoding="utf-8") as file:
    CHILLER_CACHE_JSON =  json.load(file)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# SETTINGS
# ============================================================


# Number of bins for the capacity histogram.
# You can replace this by an integer, e.g. 20 or 30.
HISTOGRAM_BINS = "auto"


# ============================================================
# LOAD JSON
# ============================================================

data = CHILLER_CACHE_JSON

# If the JSON is a dictionary keyed by chiller name
if isinstance(data, dict):
    rows = []

    for key, chiller in data.items():

        # Ignore unexpected entries that are not dictionaries
        if not isinstance(chiller, dict):
            continue

        row = chiller.copy()

        # Keep the JSON dictionary key as a fallback identifier
        row["_json_key"] = key

        rows.append(row)

    df = pd.DataFrame(rows)

elif isinstance(data, list):
    # Also support a JSON containing a list of chillers
    df = pd.DataFrame(data)

else:
    raise ValueError("Unexpected JSON structure.")


print(f"Total number of chillers in file: {len(df)}")


# ============================================================
# SELECT WATER-COOLED CHILLERS
# ============================================================

# Prefer the explicit boolean field "is_water_cooled".
# If it does not exist, fall back to condenser_type.

if "is_water_cooled" in df.columns:

    water_df = df[
        df["is_water_cooled"].fillna(False).astype(bool)
    ].copy()

if "is_air_cooled" in df.columns:

    air_df = df[
        df["is_air_cooled"].fillna(False).astype(bool)
    ].copy()
else:
    raise KeyError(
        "Neither 'is_water_cooled' nor 'condenser_type' "
        "was found in the JSON."
    )


print(f"Number of water-cooled chillers: {len(water_df)}")


# ============================================================
# CLEAN NUMERIC COLUMNS
# ============================================================

# Convert invalid / empty values to NaN
water_df["reference_capacity_kW"] = pd.to_numeric(
    water_df["reference_capacity_kW"],
    errors="coerce"
)

water_df["reference_cop"] = pd.to_numeric(
    water_df["reference_cop"],
    errors="coerce"
)

# Convert invalid / empty values to NaN
air_df["reference_capacity_kW"] = pd.to_numeric(
    air_df["reference_capacity_kW"],
    errors="coerce"
)

air_df["reference_cop"] = pd.to_numeric(
    air_df["reference_cop"],
    errors="coerce"
)


# ============================================================
# 1. COMPRESSOR TYPES
# ============================================================

print("\n" + "=" * 70)
print("COMPRESSOR TYPES — WATER-COOLED CHILLERS")
print("=" * 70)

compressor_counts = (
    water_df["compressor_type"]
    .fillna("Unknown")
    .replace("", "Unknown")
    .value_counts(dropna=False)
)

compressor_percentages = (
    compressor_counts / len(water_df) * 100
)

compressor_summary = pd.DataFrame({
    "number_of_chillers": compressor_counts,
    "percentage": compressor_percentages
})

print(compressor_summary.to_string(float_format=lambda x: f"{x:.1f}"))

print("\n" + "=" * 70)
print("COMPRESSOR TYPES — AIR-COOLED CHILLERS")
print("=" * 70)

compressor_counts = (
    air_df["compressor_type"]
    .fillna("Unknown")
    .replace("", "Unknown")
    .value_counts(dropna=False)
)

compressor_percentages = (
    compressor_counts / len(air_df) * 100
)

compressor_summary = pd.DataFrame({
    "number_of_chillers": compressor_counts,
    "percentage": compressor_percentages
})

print(compressor_summary.to_string(float_format=lambda x: f"{x:.1f}"))


# ============================================================
# FUNCTION FOR RANGE + MAXIMUM ADJACENT GAP
# ============================================================

def analyze_numeric_variable(df, column, label, unit=""):
    """
    Calculate:
      - number of valid values
      - minimum
      - maximum
      - overall range
      - maximum gap between consecutive sorted observations

    Also identifies the chillers on each side of the largest gap.
    """

    temp = df.copy()

    # Keep only rows having a valid value
    temp = temp.dropna(subset=[column])

    # Sort from smallest to largest
    temp = temp.sort_values(column).reset_index(drop=True)

    values = temp[column].to_numpy()

    if len(values) == 0:
        print(f"\nNo valid data for {label}.")
        return None

    minimum = values[0]
    maximum = values[-1]
    total_range = maximum - minimum

    print("\n" + "=" * 70)
    print(label.upper())
    print("=" * 70)

    print(f"Number of valid observations : {len(values)}")
    print(f"Minimum                      : {minimum:.4f} {unit}")
    print(f"Maximum                      : {maximum:.4f} {unit}")
    print(f"Range (max - min)            : {total_range:.4f} {unit}")

    # At least 2 observations are needed to calculate adjacent gaps
    if len(values) >= 2:

        # np.diff calculates:
        #
        # sorted_value[i+1] - sorted_value[i]
        #
        gaps = np.diff(values)

        max_gap_index = np.argmax(gaps)
        max_gap = gaps[max_gap_index]

        lower_value = values[max_gap_index]
        upper_value = values[max_gap_index + 1]

        lower_row = temp.iloc[max_gap_index]
        upper_row = temp.iloc[max_gap_index + 1]

        lower_name = lower_row.get(
            "name",
            lower_row.get("_json_key", "Unknown")
        )

        upper_name = upper_row.get(
            "name",
            upper_row.get("_json_key", "Unknown")
        )

        print()
        print("Largest gap between consecutive sorted values")
        print(f"Gap                          : {max_gap:.4f} {unit}")
        print(f"Lower value                  : {lower_value:.4f} {unit}")
        print(f"Upper value                  : {upper_value:.4f} {unit}")
        print(f"Lower-value chiller          : {lower_name}")
        print(f"Upper-value chiller          : {upper_name}")

        result = {
            "minimum": minimum,
            "maximum": maximum,
            "range": total_range,
            "maximum_adjacent_gap": max_gap,
            "gap_lower_value": lower_value,
            "gap_upper_value": upper_value,
            "gap_lower_chiller": lower_name,
            "gap_upper_chiller": upper_name,
        }

    else:
        result = {
            "minimum": minimum,
            "maximum": maximum,
            "range": total_range,
            "maximum_adjacent_gap": np.nan,
        }

    return result


# ============================================================
# 2. COOLING CAPACITY STATISTICS
# ============================================================
print('#water')
capacity_results = analyze_numeric_variable(
    water_df,
    column="reference_capacity_kW",
    label="Reference cooling capacity",
    unit="kW"
)
print('#air')
capacity_results = analyze_numeric_variable(
    air_df,
    column="reference_capacity_kW",
    label="Reference cooling capacity",
    unit="kW"
)


# ============================================================
# 3. COP STATISTICS
# ============================================================

cop_results = analyze_numeric_variable(
    water_df,
    column="reference_cop",
    label="Reference COP",
    unit=""
)
print('#air')

cop_results = analyze_numeric_variable(
    air_df,
    column="reference_cop",
    label="Reference COP",
    unit=""
)
# ============================================================
# 4. HISTOGRAM OF COOLING CAPACITY
# ============================================================
def histo(dataset, value, dataset2):
    val1 = (
        dataset[value]
        .dropna()
        .to_numpy()
    )

    val2 = (
        dataset2[value]
        .dropna()
        .to_numpy()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(
        val1,
        bins=HISTOGRAM_BINS,
        edgecolor="black",
        label = 'water_cooled'

    )

    ax.set_xlabel('water_cooled')
    ax.hist(
        val2,
        bins=HISTOGRAM_BINS,
        edgecolor="black",
        label = 'air_cooled'
    )


    ax.set_xlabel(value)
    ax.set_ylabel("Number of chillers")
    ax.set_title(f"Water and Air-cooled chillers — {value} distribution")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="best", fontsize="small")

    fig.tight_layout()


    plt.show()

histo(water_df, 'reference_capacity_kW' , air_df)



# ============================================================
# 6. OPTIONAL: EXPORT RESULTS
# ============================================================

# compressor_summary.to_csv(
#     "water_cooled_compressor_types.csv"
# )

# capacity_frequency.to_csv(
#     "water_cooled_capacity_frequencies.csv",
#     index=False
# )

# water_df.to_csv(
#     "water_cooled_chillers.csv",
#     index=False
# )