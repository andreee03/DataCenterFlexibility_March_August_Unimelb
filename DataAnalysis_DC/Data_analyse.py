## Analyze of Data


import matplotlib.pyplot as plt
import pandas as pd

import plotly.express as px

df = pd.read_parquet("a_0.parquet")
# df =  pd.read_csv('C:\\Users\\andre\\UniMelb\\DataAnalysis_DC\\NLR\\Data_PUE_combined\\esif_influx_buildingData_PUE_combined.csv') # Reads only the first row

### Display 
cles  = list(df.keys())     # Dont use tags + time manually + day
# print(cles)

def mask(abs, ord):
    x = list()
    y = list()
    for i in range(len(abs)):
        if str(abs[i]) > "2019-08-01" and str(abs[i]) < "2020-01-02":
            x.append(abs[i])
            y.append(ord[i])
    return x, y

def accurate_values():
    print(df.head())
    print(len(df['timestamp']))
    print(df['timestamp'][0], df['timestamp'][len(df['timestamp'])-1])


# accurate_values()
# tags,ts,cooling_kw,energy_reuse,ere,hvac_kw,it_power_kw,plug_and_light_kw,pue,pump_kw,day

cles_selec = ['p0_power_avg','ps0_input_power_avg',  'ps0_input_voltag_avg', 'gpu0_core_temp_avg']

# df['ps0and1_input_power_avg'] = df['ps1_input_power_avg']+ df['ps0_input_power_avg'] - ( df['ps0_output_curre_avg']*df['ps0_output_volta_avg']+ df['ps1_output_curre_avg']*df['ps1_output_volta_avg'])
#Pbs : -UTC avec () - NaN -
Granularity = 100
df = df[::Granularity]
def main():
    # for cle in cles_selec:
    fig = px.scatter(data_frame= df, x="timestamp", y='value')
    print('Pb dans data pour: value ', df['value'].isnull().sum())
    fig.show()
        # fig.write_html(f"Plot of {cle} for{(len(df[cle])- df[cle].isnull().sum())//100}values.html")

# main()
def tout_plot():
    
    dfs = []
    for cle in cles_clean:
        DDff = pd.DataFrame({
            "ts": df["ts"],
            'power_kW': df[cle],
            "color": cle
        })
    # print(df.dtypes)
        if cle != 'it_power_kw':
            dfs.append(DDff)

    df_all = pd.concat(dfs, ignore_index=True)
    fig = px.scatter(data_frame= df_all, x="ts", y="power_kW", color='color')
    fig.write_html("Superposition_power_curves_kW_Without_IT.html")
    # fig.show()

