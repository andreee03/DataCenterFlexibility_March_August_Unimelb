
import pandas as pd
import numpy as np
import random as rd

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def tools():    

    path =  "C:\\Users\\andre\\UniMelb\\DataAnalysis_DC\\Thailand_DC\\energydata-master-v2\\energydata-master\\csv\\ulcs\\ulc1.txt"
    df = pd.read_csv(path)

    df["timeval"] = pd.to_datetime(df["timeval"])
    # Example: one central Melbourne outdoor sensor near Federation Square / Flinders St

    start = "2020-07-09 00:00:00"
    end = "2020-07-16 00:00:00"

    mask = (df["timeval"] >= start) & (df["timeval"] < end)
    df_week = df.loc[mask, [
                "timeval",
                "ActiveThreePhasePower_W",
            ]]

    df_week.to_csv("Thailand_DCenergydata-master-v2.csv", index=False)

    print(df_week.head())
    print(f"Number of rows: {len(df_week)}")
# tools()

# Artificial temperature:
import numpy as np
import pandas as pd

def synthetic_temp_humidity(timestamps):
    """
    Generate rough synthetic outdoor temperature (°C) and relative humidity (%)
    from a list/array of timestamps, using daily + seasonal cycles + noise.
    """
    ts = pd.to_datetime(pd.Series(timestamps))

    # --- time features ---
    day_of_year = ts.dt.dayofyear.values          # 1-365
    hour_of_day = ts.dt.hour.values + ts.dt.minute.values / 60.0  # 0-24

    # ================= TEMPERATURE =================
    mean_temp = 15                                  # yearly average °C
    seasonal_amp = 10                                # summer/winter swing
    daily_amp = 5                                    # day/night swing

    # seasonal cycle, peak around day 200 (mid-summer, adjust for hemisphere)
    seasonal_temp = seasonal_amp * np.sin(2 * np.pi * (day_of_year - 80) / 365)

    # daily cycle, peak around 15:00
    daily_temp = daily_amp * np.sin(2 * np.pi * (hour_of_day - 9) / 24)

    noise_temp = np.random.normal(0, 1.5, size=len(ts))  # random variability

    outside_temp = mean_temp + seasonal_temp + daily_temp + noise_temp

    # ================= HUMIDITY =================
    mean_rh = 60                                     # baseline %
    seasonal_rh_amp = 15
    daily_rh_amp = 10

    # humidity often out of phase with temp (higher when cooler)
    seasonal_humidity = seasonal_rh_amp * np.sin(2 * np.pi * (day_of_year - 260) / 365)
    daily_humidity = -daily_rh_amp * np.sin(2 * np.pi * (hour_of_day - 9) / 24)  # inverse of temp

    humidity_from_temperature_noise = -0.5 * noise_temp   # hotter noise -> drier
    humidity_independent_noise = np.random.normal(0, 3, size=len(ts))

    outside_relative_humidity = (
        mean_rh
        + seasonal_humidity
        + daily_humidity
        + humidity_from_temperature_noise
        + humidity_independent_noise
    )

    # clip RH to physical bounds
    outside_relative_humidity = np.clip(outside_relative_humidity, 0.1,99.5)

    return pd.DataFrame({
        "timeval": ts,
        "outside_temp_C": outside_temp,
        "outside_relative_humidity_pct": outside_relative_humidity
    })


    
power_path = "C:\\Users\\andre\\UniMelb\\Thermo_modelling\\Thailand_DCenergydata-master-v2.csv"


df_power = pd.read_csv(power_path) 

df = synthetic_temp_humidity(df_power['timeval'])


# print(len(df['received_at']))
# print(7*24*4, 'est ce au il y a des trous ?')
# print(df['received_at'][0], df['received_at'][len(df['received_at'])-1])

# df = generate_melbourne_weather(df_power['timeval'])


# df.to_csv("Temperatures.csv", index=False)
n_data = 50
def create_dataset() -> dict[list]:
    dataset = {'time_utc': [i for i in range(n_data)], 
            'input_power_IT_room_kW' : [100 * rd.gauss(1, 0.1) for i in range(n_data)], 
            'ambient_temp' : [20* rd.gauss(1, 0.1) for i in range(n_data)], 
            'relative_humidity' : [55* rd.gauss(1, 0.1) for i in range(n_data)]
    }
    return dataset 

# def create_dataset() -> dict[list]:
#     dataset = {'time_utc': df_power['timeval'], 
#             'input_power_IT_room_kW' : df_power['ActiveThreePhasePower_W'] / 1000, 
#             'ambient_temp' : df['outside_temp_C'], 
#             'relative_humidity' : df['outside_relative_humidity_pct']
#     }
#     return dataset 

dataset_input = create_dataset()

for key in dataset_input:
    print(dataset_input[key])
