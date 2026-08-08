## Create an adapted dataset



import re
import pandas as pd

df =  pd.read_csv('C:\\Users\\andre\\UniMelb\\DataAnalysis_DC\\NLR\\Data_PUE_combined\\esif_influx_buildingData_PUE_combined.csv') # Reads only the first row

def clean_ts(s):
    # Remove the "(Mountain Standard Time)" part
    s = re.sub(r'\s*\(.*?\)', '', s).strip()
    return pd.to_datetime(s, utc=True)

df["ts"] = pd.to_datetime(df["ts"].str.replace(r'\s*\(.*?\)', '', regex=True), utc=True)



df.to_parquet("esif_influx_buildingData_PUE_combinedUTC.parquet")
