## Analyze of Data


import matplotlib.pyplot as plt
import pandas as pd

import plotly.express as px

df = pd.read_parquet(r"C:\Users\andre\UniMelb\DataAnalysis_DC\NLR\esif_influx_buildingData_PUE_combinedUTC.parquet")
# df =  pd.read_csv('C:\\Users\\andre\\UniMelb\\DataAnalysis_DC\\NLR\\Data_PUE_combined\\esif_influx_buildingData_PUE_combined.csv') # Reads only the first row

### Display 
keys  = list(df.keys()[2:-1])     # Dont use tags + time manually + day
print(keys)

keys_interst = keys[3:-2]
keys_interst.append(keys[0])
keys_interst.append(keys[-1])

print(keys_interst)
keys_without_it = [elt for elt in keys_interst if elt != 'it_power_kw']

print(keys_without_it)
def mask(abs, ord):
    keys
    x = list()
    y = list()
    for i in range(len(abs)):
        if str(abs[i]) > "2019-08-01" and str(abs[i]) < "2020-01-02":
            x.append(abs[i])
            y.append(ord[i])
    return x, y

def accurate_values():
    print("Trouver le pic cooling", df['ts'][1660000], df['ts'][1760000])
    print( "Bornes", df['ts'][1], df['ts'][len(df['ts'])-2], len(df['ts'])-2)

# tags,ts,cooling_kw,energy_reuse,ere,hvac_kw,it_power_kw,plug_and_light_kw,pue,pump_kw,day



#Pbs : -UTC avec () - NaN -
Granularity = 100
df = df[::Granularity]
def main():
    for key in keys:
        fig = px.scatter(data_frame= df, x="ts", y=key)
        fig.show()
        fig.write_html(f"Plot of {key} for{(len(df[key])- df[key].isnull().sum())//100}values.html")

# main()
def plot_all(list_k):
   
    fig, ax = plt.subplots(figsize=(12, 6))
    for key in list_k:

        ax.plot(df["ts"], df[key], label=str( key))

    ax.set_title('power_in_kW')
    ax.set_xlabel("time_utc")
    ax.set_ylabel('power_in_kW')
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    fig.tight_layout()

    plt.show()

plot_all(keys_interst)
plot_all(keys_without_it)