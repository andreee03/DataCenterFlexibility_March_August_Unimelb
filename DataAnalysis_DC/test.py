import plotly.express as px
import pandas as pd


L = ['NaN', 'NaN', 4, 'NaN']



ts = ['Mon Nov 09 2015 20:00:01 GMT-0700 (Mountain Standard Time)', 'Mon Nov 09 2015 18:00:01 GMT-0700 (Mountain Standard Time)', 'Mon Nov 09 2015 12:00:01 GMT-0700 (Mountain Standard Time)', 'Mon Nov 09 2015 11:00:01 GMT-0700 (Mountain Standard Time)']

df = pd.DataFrame({'ts': ts, 'cooling': L})
# print(df['cooling'].isnull().sum(), df['cooling'].isnull())

import re
import pandas as pd

def clean_ts(s):
    # Remove the "(Mountain Standard Time)" part
    s = re.sub(r'\s*\(.*?\)', '', s).strip()
    return pd.to_datetime(s, utc=True)


df["ts"]= [clean_ts(elt) for elt in df["ts"]]

print(df['ts'])
fig = px.scatter(data_frame= df, x="ts", y='cooling')
fig.show()



print(len(df['cooling']))
