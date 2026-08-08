
import math
from dataclasses import dataclass, field
from typing import List, Optional
import random
import pandas as pd
import re
import plotly.express as px
from scipy.linalg import expm, inv, eig
import numpy as np

# ---------------------------------------------------------------------------
# DATASET
# ---------------------------------------------------------------------------

from Dataset_treatment import dataset_input 

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

C_CFM_to_m3s = 0.472/ 1000
C_GPM_to_m3s = 6.31* 10 **(-5)
C_ton_evap_to_W = 3.52 *10**3
# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
DT = 1 / 60 # in hours DEPENDS ON DATASET GRANULARITY 
NDATA = 1
OUTSIDE_INITIAL_TEMP: float = 35
RHO_CP_WATER = 4186   # kJ/(m3·K)
VOLUMIC_MASS_AIR = 1.2        # kg/m³
AIR_SPECIFIC_HEAT = 1.005      #C_p at constant pressure, kJ/(kg·K)
COPPER_SPECIFIC_HEAT= 0.384 # J/(g·K) Copper 
AL_SPECIFIC_HEAT = 0.897 # J/(g·K)    
AL_RHO = 2.7* 10**(-3) # g/mm3    
COPPER_RHO = 8.96* 10**(-3) # g/mm3    
# ---------------------------------------------------------------------------
# Data Center immutable values during simulation: 
# ---------------------------------------------------------------------------

# Data Center
N_SERVERS: int = 8
N_CRAC_UNITS: int = 1
# N_CHILLERS

EVAP_FLOW_RATE = 230* 10**3 * 2.4 * C_GPM_to_m3s / C_ton_evap_to_W # m3/s

# CRAC
D_AIR_RATED: float = 16.5 # m3/s 
CHILLED_WATER_TEMP = 7.2
EPSILON_RATED = 0.7
C_r = D_AIR_RATED * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR/ (RHO_CP_WATER* EVAP_FLOW_RATE)
# INTERFACE CRAC SERVER 

T_INLET = 24 #C

## Dynamic behaviour


def Psi_CA(CFM):

    return 0.1431 + 1.9451*CFM**(-1.0719) 

def heatsink_capacity(volume, proportion_AL = 0.34):
    t = proportion_AL  #    t_max = 0.34
    

    return  volume*(t* AL_SPECIFIC_HEAT + (1-t)* COPPER_SPECIFIC_HEAT)* (t* AL_RHO + (1-t)* COPPER_RHO)

def heat_exchanger(T_hot_in, T_cold_in, Ctot_hot, Ctot_cold, efficiency) -> tuple:
    '''
    Ctot = heat capacity times flowrate. The idea is to say the heat transfer is maximal and limited by the minimum carrying flow
    '''
    C_r = min(Ctot_hot, Ctot_cold)

    power_transfered_W = C_r * efficiency * (T_hot_in - T_cold_in) 

    T_hot_out = T_hot_in - power_transfered_W / Ctot_hot

    T_cold_out = T_cold_in + power_transfered_W / Ctot_cold
    return T_hot_out, T_cold_out

def compute_UA(epsilon_calibr, C_min, K):
    return C_min * math.log((1 - epsilon_calibr)/(1 - epsilon_calibr*K))/ (K-1)

def epsilon_from_UA(UA, C_min, K):
    "Counter flow"
    NTU = UA / C_min
    num = 1 - math.exp(- NTU* (1 - K))
    denom = 1 - K*math.exp(- NTU* (1 - K))
    return num/denom


# SERVER
volume_IHS = 1200*6
R_cs = 0.1 # C/W 
T_CPU_TJMAX = 95 # C
T_CPU_THERMTRIP = 115 # C
R_jc = 0.2 # C/W (0.1-0.3)
CPU_MASS = 50 #g
SI_SPECIFIC_HEAT  = 0.710 # J/(g·K) Silicon 

CPU_HEAT_CAPACITY = SI_SPECIFIC_HEAT * CPU_MASS + COPPER_SPECIFIC_HEAT *COPPER_RHO* volume_IHS  # J/K
# Intel Sheet :https://www.intel.la/content/dam/www/public/us/en/documents/design-guides/xeon-7500-xeon-e7-8800-4800-2800-families-guide.pdf

Intel_T_INLET = 42 #C 
CPU_TDP = 95 # W
volume_1U = 90 *90 * 26.5 # mm3
heatsink_CAPA = heatsink_capacity(volume_1U/2, 0)       # J/ K
D_FAN =  12.6 * C_CFM_to_m3s # CFM in #m3/s 
Psi_ca_worst = 0.295 # K/ W

Psi_ca = Psi_CA(D_FAN / C_CFM_to_m3s) # K / W
R_sa = Psi_ca_worst - R_cs

class Server:
    def __init__(self,name: str ="Server"):
        self.name = name
        self.inlet_air_temp: float = OUTSIDE_INITIAL_TEMP
        self.server_power_consumed_kW: float = 0
        self.heat_power_generated_W: float = 0.0

        self.heatsink_temp: float = OUTSIDE_INITIAL_TEMP
        self.airflow_per_server: float = 0.0
        self.case_temp: float = OUTSIDE_INITIAL_TEMP
        self.exhaust_air_temp: float = OUTSIDE_INITIAL_TEMP
        self.junction_temp: float = OUTSIDE_INITIAL_TEMP
    # --- Equations -----------------------------------------------------------

    def set_values(self, power_server_W):
        self.heat_power_generated_W = power_server_W

    def time_scale(self)-> str:
        R1, R2, C1, C2 = R_jc + R_cs, R_sa , CPU_HEAT_CAPACITY, heatsink_CAPA

        A = np.array([
            [-1.0 / (R1 * C1),  1.0 / (R1 * C1)],
        [ 1.0 / (R1 * C2), -(1.0/R1 + 1.0/R2) / C2]
        ])

        self.inv_matrix_system_CPU_HS = inv(A)

        eigenvalues = eig(A)[0]
        return f'time1:{-1/float(eigenvalues[0])},\n time2 {-1/float(eigenvalues[1])}'
    
    def epsilon(self, R_sa):
        print('epsilon equivalent is:', 1/(self.airflow_per_server * R_sa))

    def update_temp(self, power_W: float) -> bool:
        '''thermodynamical exchanges
        The core of the modelling:

        T_{HS} = T_{CPU} - P_{IT} R_{js}\\
        
        T_{CPU} = T_{inlet} + P_{IT} ( R_{js} + R_{sa} )  \\

        T_{out} = T_{inlet} + (1 - \exp(- \frac{1}{R_{sa} * \rho_{air} D_{air} c_p,air})) P_{IT} R_{sa}   \cite{arxiv_CPU_eq} (page 20, Eq. 20)
        '''
        C_air = AIR_SPECIFIC_HEAT*VOLUMIC_MASS_AIR * self.airflow_per_server
        
        self.exhaust_air_temp = self.inlet_air_temp + power_W/ C_air

        self.heatsink_temp = self.inlet_air_temp + power_W * R_sa 

        self.case_temp = self.heatsink_temp + power_W *  R_cs

        self.junction_temp = self.case_temp + power_W * R_jc 



        NTU = 1/((Psi_ca - R_cs ) * VOLUMIC_MASS_AIR * AIR_SPECIFIC_HEAT * self.airflow_per_server)
        self.exhaust_air_temp = self.inlet_air_temp + (1 - math.exp(-NTU) ) * power_W * (Psi_ca - R_cs )
        # print('NTU Server = ', NTU)
        return (self.exhaust_air_temp > self.heatsink_temp)

    def step(self, power_server_W: float) -> bool:
        self.set_values( power_server_W)
        return self.update_temp(power_server_W)  # update exhaust_air_temp and cpu_temp



class CRACUnit:

    def __init__(self, name:str = 'CRAC_unit'):
        self.name = name
        self.a_out_temp = OUTSIDE_INITIAL_TEMP
        self.a_in_temp = OUTSIDE_INITIAL_TEMP
        self.w_out_temp = OUTSIDE_INITIAL_TEMP
        self.w_in_temp = OUTSIDE_INITIAL_TEMP

        self.UA_rated = 0

        self.power_transfered_W: float = 0.0
        self.airflow = 0.0
        

    def update_out_temps(self) -> bool:
        '''
        C_i = \rho_i c_{p, i} D_i

        C_{min} = min(C_{w}, C_{air} ) = C_{air}

        C_r = \frac{C_{air}}{C_{water}}

        PowerTransfered = C_{min} epsilon ( T_{hot, in} - T_{cold, in} ) \cite{arxiv_eq} [2]

        \epsilon = \frac{1 - exp(-NTU(1 - C_r))}{1 - C_r exp(-NTU(1 - C_r))}

        NTU = \frac{UA}{C_{min}}    \cite{Science_direct_NTU}

        Idem that for the Cooling Tower, we estimate NTU_{calibr} thanks to \epsilon_{calibr} using one operating point.

        \epsilon_{rated} = \frac{Q_{designed}}{C_{air,rated}(T_{air, in, rated} - T_{w, in, rated}) }

        NTU_{calibr} = \frac{ln(\frac{1−\epsilon_{calibr}}{1−C_r\epsilon_{calibr}}​)​}{C_r−1}.

        UA_{calibr} = C_{air, rated} * NTU_{calibr} 

        C_{air,rated} = D_{air, rated} c_{p, air} \rho_{air}

        '''
        C_air = AIR_SPECIFIC_HEAT*VOLUMIC_MASS_AIR* self.airflow 

        self.power_transfered_W = C_air * epsilon_from_UA(self.UA_rated, C_air, C_r) * (self.a_in_temp - self.w_in_temp)

        self.a_out_temp = self.a_in_temp - self.power_transfered_W  /C_air


        return False  # possible if Epsilon_rated (1 + Cair/Cwater) > 1
   
       
    def step(self) -> bool:
        return self.update_out_temps()

def start_cooling_system(crac: CRACUnit, server: Server):

    crac.airflow = D_AIR_RATED
    crac.w_in_temp = CHILLED_WATER_TEMP
    crac.UA_rated = compute_UA(EPSILON_RATED, D_AIR_RATED*AIR_SPECIFIC_HEAT*VOLUMIC_MASS_AIR, C_r)
    server.airflow_per_server = D_FAN
    server.inlet_air_temp = Intel_T_INLET




def plotting(dict: dict[List]) -> None:
    '''
    Requirements, the keys of dict should be real attributes of the classes !!
    '''
    dico_dfs = { 'temp' : [], 'W' : []}

    pat = r"_(temp|W)"
    for i, key in enumerate(dict):
        if key != 'time_utc':
                            
            match = re.search(pat, key)

            df = pd.DataFrame({
                "time_utc": [i for i in range(NDATA)],
                match.group(1): dict[key],
                "Description": key 
            })
            dico_dfs[match.group(1)].append(df)


    for key in dico_dfs:
        df_all = pd.concat(dico_dfs[key], ignore_index=True)
        fig = px.scatter(data_frame= df_all, x="time_utc", y=key, color='Description')
        fig.show()



dict_for_plot = {'heat_power_generated_W':[],
                 'heatsink_temp': [], 
                 'junction_temp': [],
                 'case_temp': [],
                 'exhaust_air_temp': [],
                 'a_in_temp': [],
                 'a_out_temp': [],
                 'power_transfered_W': []}


Server_test = Server()
CRACUnit_test  = CRACUnit()
start_cooling_system(CRACUnit_test, Server_test)
N_SERVERS_MAX = math.floor(D_AIR_RATED/ D_FAN)
N_SERVERS = 2000
for j in range(NDATA):
    entropy_violated = 0

    entropy_violated+= Server_test.step( CPU_TDP)

    D_hot_air= N_SERVERS * D_FAN 

    T_room = (D_hot_air * Server_test.exhaust_air_temp + ( D_AIR_RATED - D_hot_air ) * Server_test.inlet_air_temp ) / D_AIR_RATED
    CRACUnit_test.a_in_temp = T_room

    entropy_violated+= CRACUnit_test.step()
    Server_test.inlet_air_temp = Intel_T_INLET

    if entropy_violated:
        print('entropy_violated')
    for key in dict_for_plot:
        try1 = getattr(Server_test, key, None)
        try2 = getattr(CRACUnit_test, key, None)
        if try1:
            dict_for_plot[key].append(try1)
        else:
            dict_for_plot[key].append(try2)
print(f'N_servers = {CRACUnit_test.power_transfered_W /  Server_test.heat_power_generated_W}')

print('time scales:', Server_test.time_scale())
plotting(dict_for_plot)
