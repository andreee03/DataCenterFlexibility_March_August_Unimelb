## Analyze of Data


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json

import pickle

path = r"C:\Users\andre\UniMelb\DataAnalysis_DC\UK\ukpn-data-centre-demand-profiles-perDC.pkl"
with open(path, "rb") as f:
    DataSet = pickle.load(f)

### Utilitaires:

def mask(abs, ord):
    x = list()
    y = list()
    for i in range(len(abs)):
        if abs[i] > "2024-01-01" and abs[i] < "2024-02-02":
            x.append(abs[i])
            y.append(ord[i])
    return x, y
for values in DataSet:
    # values = DataSet[elt]
    values["utc_timestamp"] = pd.to_datetime(values["utc_timestamp"])

    order = values["utc_timestamp"].argsort()

    values["utc_timestamp"] = values["utc_timestamp"][order]
    values["hh_utilisation_ratio"] = np.asarray(
        values["hh_utilisation_ratio"]
    )[order]

### Display 
dico_dfs = {f'group {i}' : [] for i in range(10)}
for i, dc in enumerate(DataSet):
    df = pd.DataFrame({
        "utc_timestamp":pd.to_datetime(dc["utc_timestamp"][::10]),
        "hh_utilisation_ratio": dc["hh_utilisation_ratio"][::10],
        "dc": f"DC_{i+1}: {dc['dc_type']} "
    })
    dico_dfs[f'group {i// 10}'].append(df)


for category, values in dico_dfs.items():
    if not values:
        continue

    fig, ax = plt.subplots(figsize=(12, 6))
    for value in values:
        label = value["dc"].iloc[0]
        ax.plot(value["utc_timestamp"], value['hh_utilisation_ratio'], label=str(label))

    ax.set_title('hh_utilisation_ratio per data center')
    ax.set_xlabel("utc_timestamp")
    ax.set_ylabel('hh_utilisation_ratio')
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    fig.tight_layout()

plt.show()



print("Number of points plotted", len(DataSet[0]["utc_timestamp"]))


















































def display_summary(data):
    """Show a readable summary of the data."""
    if isinstance(data, list):
        print(f"→ List of {len(data)} items")
        print("\nFirst item:")
        print(json.dumps(data[0], indent=2))
        print(json.dumps(data[1], indent=2))


        # If items are dicts, show all keys
        if isinstance(data[0], dict):
            print(f"\nKeys: {list(data[0].keys())}")

    elif isinstance(data, dict):
        print(f"→ Object with keys: {list(data.keys())}")
        print(json.dumps(data, indent=2))

    else:
        print(f"→ Single value: {data}")


def manip(data):
    i=0
    for item in data:
        print(item["anonymised_data_centre_name"])
        i+=1
    print(f"Total items: {i}")
    print(type(data[0]))
    print(type(data[0]))

