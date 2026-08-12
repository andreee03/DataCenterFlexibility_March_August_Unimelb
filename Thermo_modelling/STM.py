### MOST RECENT VERSION
import math
from dataclasses import dataclass, field
from typing import List, Optional
import random as rd
import pandas as pd
import re
import plotly.express as px
import matplotlib.pyplot as plt
from scipy.linalg import expm, inv, eig
import numpy as np

# ---------------------------------------------------------------------------
# DATASET
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
RHO_CP_WATER = 4186   # kJ/(m3·K)
VOLUMIC_MASS_AIR = 1.2        # kg/m³
AIR_SPECIFIC_HEAT = 1.005      #C_p at constant pressure, kJ/(kg·K)
COPPER_SPECIFIC_HEAT= 0.384 # J/(g·K) Copper 
AL_SPECIFIC_HEAT = 0.897 # J/(g·K)    
AL_RHO = 2.7* 10**(-3) # g/mm3    
COPPER_RHO = 8.96* 10**(-3) # g/mm3    
SI_SPECIFIC_HEAT  = 0.710 # J/(g·K) Silicon 

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------
C_CFM_to_m3s = 0.472/ 1000
C_GPM_to_m3s = 6.31* 10 **(-5)
C_gallon_to_m3 = 0.00454609
C_ton_evap_to_kW = 3.52 
C_F_to_Celisus = 5/9


## SERVERS
ROOM_INITIAL_TEMP = 20
CPU_TDP = 95 # W
AIRFLOW_PER_HS =  12.6 * C_CFM_to_m3s # CFM in #m3/s        
DELTA_T_SERVER = 8 # C
R_cs = 0.1 # C/W 
R_jc = 0.2 # C/W (0.1-0.3)


def heatsink_capacity(volume, proportion_AL = 0.34):
    t = proportion_AL  #    t_max = 0.34
    

    return  volume*(t* AL_SPECIFIC_HEAT + (1-t)* COPPER_SPECIFIC_HEAT)* (t* AL_RHO + (1-t)* COPPER_RHO)

def Psi_CA(fr):
    # K / W
    CFM = fr / C_CFM_to_m3s
    return 0.1431 + 1.9451*CFM**(-1.0719) 

Psi_ca_worst = 0.295 # K/ W
Psi_ca = Psi_CA(AIRFLOW_PER_HS) # K / W

R_sa = Psi_ca_worst - R_cs


path = r"C:\Users\andre\UniMelb\Validation_data\files"

# ---------------------------------------------------------------------------
# 6. Server
# ---------------------------------------------------------------------------

class Server_air_cooled:

    def __init__(self, server_info 
                 ):

        delta_T_server, thermal_resistances, thermal_capacitances, airflow, tdp_W = server_info
        self.server_power_consumed_W: float = 0
        self.heat_power_generated_W: float = 0.0
        self.tdp_W = tdp_W      # maximum amount of heat CPU is expected to generate

        R_jc, R_cs, R_sa = thermal_resistances
        C_die_IHS, C_hs = thermal_capacitances

        self.R_jc = R_jc # should be in K/W
        self.R_sa = R_sa  # should be in K/W
        self.R_cs = R_cs  # should be in K/W
        self.c_die_IHS = C_die_IHS  # J/K
        self.c_heatsink = C_hs # J/K

        self.airflow_per_heatsink: float = airflow      # m3/s

        self.inlet_air_temp: float = ROOM_INITIAL_TEMP
        self.heatsink_temp: float = ROOM_INITIAL_TEMP
        self.case_temp: float = ROOM_INITIAL_TEMP
        self.junction_temp: float = ROOM_INITIAL_TEMP
        self.delta_T_server = delta_T_server
        self.exit_air_heatsink_temp: float = ROOM_INITIAL_TEMP
        self.exit_air_tot_temp: float = ROOM_INITIAL_TEMP

    # --- Equations -----------------------------------------------------------

  
    def debug(self, R_sa):
        print('server epsilon equivalent is:', 1/(self.airflow_per_heatsink * R_sa))
    

    def update_temp(self) -> bool:
        '''thermodynamical exchanges
        The core of the modelling:

        T_{junction} - T_{case} = P_{IT} R_{jc}\\
        T_{case} - T_{sink} = P_{IT} R_{cs}\\

        T_{sink} - T_{air, inlet} = P_{IT} R_{sa}\\
        
        P_{IT} = C_{air}* (T_{air, HS exhaust} - T_{air, inlet}) 

        '''
        C_air = AIR_SPECIFIC_HEAT*VOLUMIC_MASS_AIR * self.airflow_per_heatsink * 1000  # W/K

        self.heat_power_generated_W = self.server_power_consumed_W
        power_W = self.heat_power_generated_W       # W

        self.exit_air_heatsink_temp = self.inlet_air_temp + power_W/ C_air

        self.heatsink_temp = self.inlet_air_temp + power_W * self.R_sa 
    
        self.case_temp = self.heatsink_temp + power_W *  self.R_cs

        self.junction_temp = self.case_temp + power_W * self.R_jc 
        # j = rd.uniform(0,1)
        # if j < 0.01:
        #     print( f'HS:{self.heatsink_temp}, case {self.case_temp}, juncti:{self.junction_temp}, air HS exit :{self.exit_air_heatsink_temp}')
        return (self.exit_air_heatsink_temp > self.heatsink_temp)

    def step(self) -> bool:
        return self.update_temp() 

    
    def update_dict(self, dict):
        for key in dict:
            if key != 'time_utc':
                dict[key].append(round(getattr(Server_test, key),  2))
           
    def update_tot_air_exit(self):

        self.exit_air_tot_temp = (self.exit_air_heatsink_temp + self.delta_T_server + self.inlet_air_temp) 

    def power_flow(self, T_inlet, power_server, values_for_plot, time_utc) -> bool:

        violated_entropy = False

        self.inlet_air_temp = T_inlet
        self.server_power_consumed_W = power_server
        violated_entropy += self.step()
        self.update_tot_air_exit()
        self.update_dict(values_for_plot)

        if violated_entropy:
            print("Entropy broken, wrong heat transfer at:", time_utc)
        # update values_for_plot:
        
def create_correspondance_dico():
    var = {}
    all_classes: list[type] = [
        obj for obj in globals().values() 
        if isinstance(obj, type)]

    for classe in all_classes:
        for attribute in classe.__static_attributes__ :
            var[attribute] = classe.__name__
    return var

def initialise_dict_for_plot(keys: list[str]) -> dict:
    all_attribs = create_correspondance_dico().keys()
    for elt in keys:
        if elt not in all_attribs:
            print('Wrong_initialisation_for:', elt)
    return {key : [] for key in keys }

def plotting(dict: dict[List]) -> None:
    '''
    Requirements, the keys of dict should be real attributes of the classes !!
    '''
    dico_dfs = { 'temp' : [], 'power' : []}

    pat = r"(temp|power)"
    for key in dict:
        if key != 'time_utc':
                            
            match = re.search(pat, key)

            if match: 
                df = pd.DataFrame({
                    "time_utc": dict['time_utc'],
                    match.group(1): dict[key],
                    "Description": key 
                })
                dico_dfs[match.group(1)].append(df)
            else:
                if 'other' not in dico_dfs.keys():
                    dico_dfs['other'] = []
                df = pd.DataFrame({
                                    "time_utc": dict['time_utc'],
                                    'other': dict[key],
                                    "Description": key 
                                })
                dico_dfs['other'].append(df)


    for key in dico_dfs:
        df_all = pd.concat(dico_dfs[key], ignore_index=True)
        fig = px.line(data_frame= df_all, x="time_utc", y=key, color='Description')
        fig.show()


    print("Number of points plotted", len(dict['time_utc']))

if __name__ == "__main__":
    rd.seed(42)          # reproducible run

    dynamic_correspondance_attributes_class = create_correspondance_dico()
    for key in dynamic_correspondance_attributes_class:
        print(key)

    l= [ 'time_utc', 'airflow_per_heatsink',
'exit_air_heatsink_temp',
'exit_air_tot_temp',
'inlet_air_temp',
'junction_temp',
'server_power_consumed_W',]

    def set_server_intel_info():
        # Highly dependent on the type of Data Center: HPC, CPUs, Hybrid.
        # For the moment, full CPUs of type Xeon Intel.

        def set_thermal_resistances():
            '''     (R_jc, R_cs, R_sa) C/W '''
            
            return (R_jc, R_cs, R_sa)
        def set_thermal_capacitances():
            CPU_MASS = 50 #g
            volume_IHS = 1200*6 # mm3
            CPU_HEAT_CAPACITY = SI_SPECIFIC_HEAT * CPU_MASS + COPPER_SPECIFIC_HEAT *COPPER_RHO* volume_IHS  # J/K

            # test_server_intel():
            Intel_T_INLET = 42 #C 
            volume_1U = 90 *90 * 26.5 # mm3
            heatsink_CAPA = heatsink_capacity(volume_1U/2, 0)       # J/ K

            return (CPU_HEAT_CAPACITY, heatsink_CAPA)
        
        return (DELTA_T_SERVER,  set_thermal_resistances(), set_thermal_capacitances(), AIRFLOW_PER_HS, CPU_TDP)
    
    server_info = set_server_intel_info()

    Server_test = Server_air_cooled(server_info)

    dict_for_plot = initialise_dict_for_plot(l)

    path = r"C:\Users\andre\UniMelb\Validation_data\cooling_system_synthetic_inputs_5_scenarios\05.csv"
    dataset_input = pd.read_csv(path)
    N_DATA_INPUT = len(dataset_input['time_utc'])

    for j in range(N_DATA_INPUT):

        Server_test.power_flow(time_utc= j, 
                power_server=95* 0.7, 
                T_inlet=dataset_input['input_power_IT_room_kW'][j],  
                values_for_plot= dict_for_plot)
        
    plotting(dict_for_plot)
    
