### All temperatures are in degree Celsius

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

from Dataset_treatment import dataset_input 

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
# ---------------------------------------------------------------------------
# Psychrometric functions
# ---------------------------------------------------------------------------

def P_sat(T):
    # T in C
    return 0.6112 * math.exp(17.67*T/ (T+243.5)) # in kPa

def w_sat(T):
    # T in C
    P_atm = 101.3 # kPa
    return 0.622* P_sat(T)/ (P_atm - P_sat(T))

def h_sat(T):
    # T in degrees C, T_dry bulb
    C_p_water_gaz = 1.864 # kJ/kg·K
    h_fg = 2501 # kJ/kg ref at 0 degree
    return AIR_SPECIFIC_HEAT * T + w_sat(T)* (h_fg + C_p_water_gaz * T) # kJ / kg 

def m_star(T_in, T_out, a_fr, w_fr):
    def C_s():
        num = h_sat(T_in) - h_sat(T_out)    # kJ/ kg
        denom = T_in - T_out
        return num/denom            # kJ / K kg
    C_water = w_fr* RHO_CP_WATER
    num = a_fr * VOLUMIC_MASS_AIR * C_s()          
    denom = C_water
    return num / denom
# ---------------------------------------------------------------------------
# NTU model and usefull functions
# ---------------------------------------------------------------------------

def heat_exchanger(T_hot_in, T_cold_in, Ctot_hot, Ctot_cold, eps) -> tuple:
    '''
    Ctot = heat capacity times flowrate. The idea is to say the heat transfer is maximal and limited by the minimum carrying flow
    '''
    C_min = min(Ctot_hot, Ctot_cold)

    C_r = C_min/(Ctot_hot + Ctot_cold - C_min)

    power_transfered_kW = C_min * eps * (T_hot_in - T_cold_in) 

    T_hot_out = T_hot_in - power_transfered_kW / Ctot_hot
    T_cold_out = T_cold_in + power_transfered_kW / Ctot_cold

    return T_hot_out, T_cold_out, C_min

def compute_UA(epsilon_calibr, C_min, K):
    if K > 1:
        print('in compute UA from epsilon, K > 1. The limiting fluid is not the one expected')
    return C_min * math.log((1 - epsilon_calibr)/(1 - epsilon_calibr*K))/ (K-1)

def epsilon_from_UA(UA, C_min, K):
    "Counter flow"
    NTU = UA / C_min
    num = 1 - math.exp(- NTU* (1 - K))
    denom = 1 - K*math.exp(- NTU* (1 - K))
    return num/denom

def heatsink_capacity(volume, proportion_AL = 0.34):
    t = proportion_AL  #    t_max = 0.34
    

    return  volume*(t* AL_SPECIFIC_HEAT + (1-t)* COPPER_SPECIFIC_HEAT)* (t* AL_RHO + (1-t)* COPPER_RHO)

def find_n_min(boundaries: tuple, target_cool_capa: float):
        a, b = boundaries
        if target_cool_capa < a:
            print('target Cooling capacity too small,for the given range, CRAC or Cool T oversized')
        # Find the minimum n_cracs.
        k = 1
        while target_cool_capa/ k > b:
            k +=1
        return k


# ---------------------------------------------------------------------------
# Data Center immutable values during simulation: 
# ---------------------------------------------------------------------------
DT = 1 / 60 # in hours DEPENDS ON DATASET GRANULARITY 
NDATA = 1
ROOM_INITIAL_TEMP = 25

CRAC_CC_range = (230, 465)
Cool_Tower_CC_range = (53.5, 22300)
fans_cool_t_fr = 3 # m3/s
# SERVER
T_CPU_TJMAX = 95 # C
T_CPU_THERMTRIP = 115 # C

# ---------------------------------------------------------------------------
# ASSUMPTION VALUES FOR RETROENGINEERING DATA CENTER: 
# ---------------------------------------------------------------------------
AVG_TO_MAX_RATIO = 0.8
## SERVERS
CPU_TDP = 95 # W
AIRFLOW_PER_HS =  12.6 * C_CFM_to_m3s # CFM in #m3/s        
DELTA_T_SERVER = 8 # C
R_cs = 0.1 # C/W 
R_jc = 0.2 # C/W (0.1-0.3)
    
def Psi_CA(CFM):

    return 0.1431 + 1.9451*CFM**(-1.0719) 
Psi_ca_worst = 0.295 # K/ W
Psi_ca = Psi_CA(AIRFLOW_PER_HS / C_CFM_to_m3s) # K / W
R_sa = Psi_ca_worst - R_cs
## Chiller
evap_ratio = 2.4 #GPM / ton
cond_ratio = 3.0 #GPM / ton
EIR = (0.171, 0.588, 0.237)
CAPFT =  (0.25211, 0.013241, - 0.0086373,  0.085811, - 0.0042612, 0.0086619)

SETPOINT = 7.2
## CRACs
AIRFLOW_PER_COOL_CAPA = 400 # CFM / ton
EPSILON_RATED = 0.7
# CoolingTower
EPSILON_CALIBR = (95 - 85) / (95 - 78)
min_approach_temp = 3 # \in [2.5, 4]
# Water loop
vol_ton_ratio = 10 # Gall / ton


   
''' 
Attention, AIRFLOW_PER_CRAC_U is a very important value that will determine whether cpus heat or not. 

        airflow_zero_cpu_heating = self.tdp_kW /( (self.cpu_temp - self.inlet_air_temp) * VOLUMIC_MASS_AIR* AIR_SPECIFIC_HEAT )
'''

# ---------------------------------------------------------------------------
# 1. Outdoor Environment
# ---------------------------------------------------------------------------

class OutdoorEnvironment:
    def __init__(self,
                 ambient_temp,
                 relative_humidity):
        self.ambient_temp = ambient_temp
        self.relative_humidity_pct = relative_humidity

        # Derived
        self.wet_bulb_temp = self.set_wet_bulb_temp()

    def set_wet_bulb_temp(self):
        
        """
        Stull (2011) empirical wet-bulb approximation.
        T_wb ≈ T·atan(0.151977·√(RH%+8.313659)) + atan(T+RH%)
            - atan(RH%-1.676331) + 0.00391838·RH%^1.5·atan(0.023101·RH%)
            - 4.686035
        """

        T = self.ambient_temp
        RH = self.relative_humidity_pct
        Twb = (T * math.atan(0.151977 * math.sqrt(RH + 8.313659))
            + math.atan(T + RH)
            - math.atan(RH - 1.676331)
            + 0.00391838 * RH ** 1.5 * math.atan(0.023101 * RH)
            - 4.686035)
        self.wet_bulb_temp = round(Twb, 2)

    def step(self, ambient_temp: float, relative_humidity: float, ) -> None:

        self.ambient_temp = ambient_temp
        self.relative_humidity_pct = relative_humidity
        self.set_wet_bulb_temp()


# ---------------------------------------------------------------------------
# 2. Cooling Tower
# ---------------------------------------------------------------------------

class CoolingTower:
    # version in ['simplified', 'constant_epsilon', 'variable_airflow']

    def __init__(self, cool_tower_info):
        cooling_capacity_kW, n_coolingT_cells, eps, min_approach_temp, version = cool_tower_info

        self.cooling_capacity_kW = cooling_capacity_kW
        self.n_cells = n_coolingT_cells

        self.waterflow = None
        self.airflow: float = None
        self.leaving_water_temp: float = ROOM_INITIAL_TEMP -10 
        self.entering_water_temp: float = ROOM_INITIAL_TEMP

        self.version: str = version
        self.wet_bulb_temp: float = 0
        self.min_approach_temp = min_approach_temp
        self.epsilon = eps
        self.UA_calibr = None

    def calibration(self, air_fr, w_fr):
        if self.version == 'variable_airflow':
            self.airflow = air_fr
            C_air = self.airflow * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
            self.waterflow = w_fr
            m_star_calibr = m_star((95-32)*C_F_to_Celisus, (85-32)*C_F_to_Celisus, self.airflow, self.waterflow)
            print('calibration Cool T: ', self.epsilon, m_star_calibr)
            self.UA_calibr = compute_UA(self.epsilon, C_air, m_star_calibr)
        
    def set_leaving_water_temp(self) -> bool:
        T_in, T_wb = self.entering_water_temp, self.wet_bulb_temp
        T_min_control = T_wb + self.min_approach_temp

        if self.version == 'simplified':
            self.leaving_water_temp = T_min_control
            return (self.leaving_water_temp > T_in)

        elif self.version == 'constant_epsilon':
            T_out = T_in  - epsilon* (T_in - T_wb)
            self.leaving_water_temp = max(T_min_control, T_out)

            return (self.leaving_water_temp > T_in)
        else:
            # Loop to find T leaving water
            k = 0
            tolerance= 0.1
            delta = 1
            T_out = self.leaving_water_temp
            while k < 10 and delta > tolerance:
                if T_in == T_out:
                    m_sta = m_star(T_in, T_in - 1, self.airflow, self.waterflow)
                else:
                    m_sta = m_star(T_in, T_out, self.airflow, self.waterflow)

                epsilon = epsilon_from_UA(self.UA_calibr, self.airflow, m_sta) 

                T_out_new = T_in  - epsilon* (T_in - T_wb)
                delta = max(T_out_new - T_out, - T_out_new + T_out)
                T_out = T_out_new
                k +=1

            self.leaving_water_temp = max(T_min_control, T_out)
            self.epsilon = epsilon
            # print('epsilon cooling tower:', self.epsilon)
            return (self.leaving_water_temp > T_in)

    def step(self) -> bool:
        return self.set_leaving_water_temp()

# ---------------------------------------------------------------------------
# 3. Chiller
# ---------------------------------------------------------------------------


class Chiller_water_cooled:
    def __init__(self, CHILLER_INFO):
        Q_rated_kW, cop_ref, EIR, CAPFT, set_p, evap_cc_ratio, cond_cc_ratio = CHILLER_INFO


        self.Q_rated = Q_rated_kW
        self.cop_ref = cop_ref # initial value, varies with plr
        self.EIR_params = EIR
        self.CAPFT_params = CAPFT
        self.setpoint_nom_temp = set_p
        self.setpoint_flexibility_temp = set_p

        self.evap_flow_rate =  self.Q_rated   * evap_cc_ratio *C_GPM_to_m3s / C_ton_evap_to_kW # m3/s
        self.cond_flow_rate =  self.Q_rated * C_GPM_to_m3s / C_ton_evap_to_kW *cond_cc_ratio    # m3/s

        self.evap_w_out_temp = ROOM_INITIAL_TEMP
        self.evap_w_in_temp = ROOM_INITIAL_TEMP
        self.cond_w_out_temp = ROOM_INITIAL_TEMP
        self.cond_w_in_temp = ROOM_INITIAL_TEMP

        self.power_saved = 0
        self.power_kW = 0
        # print("chiller cooling capa:", self.Q_rated)

    def cop(self, PLR):
        denom = 0
        for i in range(3):
            denom += self.EIR_params[i]*PLR**i
        return self.cop_ref / denom

    def CAPFT(self):
        'Sort du chapeau'
        T_e, T_c = self.evap_w_in_temp, self.cond_w_in_temp
        a, b, c,d,e,f = self.CAPFT_params

        val = a + b*T_e + c*T_e**2 + d*T_c + e*T_c**2 + f*T_e*T_c
        return max(0, val)
    
    def update_w_out(self) -> bool:

        C_water_evap = self.evap_flow_rate*RHO_CP_WATER
        C_water_cond = self.cond_flow_rate*RHO_CP_WATER

        # if self.power_kW ==0:

        #     self.evap_w_out_temp, self.cond_w_out_temp, k = heat_exchanger(self.evap_w_in_temp, self.cond_w_in_temp, self.evap_flow_rate*RHO_CP_WATER, self.cond_flow_rate* RHO_CP_WATER, 0.7)

        #     return False

        Q_max = self.CAPFT()* self.Q_rated
        print('Q max allowed by the CAPFT', Q_max)


        # self.evap_w_out_temp = self.setpoint_flexibility_temp


        Q_demand_flex = min(C_water_evap * ( self.evap_w_in_temp - self.setpoint_flexibility_temp), Q_max)
        # Q_demand = min(C_water_evap * ( self.evap_w_in_temp - self.setpoint_nom_temp), Q_max)


        Q_demand = C_water_evap * ( self.evap_w_in_temp - self.setpoint_nom_temp)
        print('evap in , cond in:', self.evap_w_in_temp, self.cond_w_in_temp)

        PLR = Q_demand / self.Q_rated # can be higher than 1
        PLR_flex = Q_demand_flex / self.Q_rated # can be higher than 1
        COP = self.cop(PLR)
        COP_flex = self.cop(PLR_flex)
        print(f'PLR:{PLR}, COP Operational: {COP}')
        self.power_kW = Q_demand / COP
        self.evap_w_out_temp = self.evap_w_in_temp - Q_demand_flex /C_water_evap
        self.cond_w_out_temp = self.cond_w_in_temp + (1 + 1/COP) * C_water_evap/C_water_cond *( self.evap_w_in_temp - self.evap_w_out_temp)

        self.power_saved = self.power_kW - Q_demand_flex / COP_flex
        # print("power chiller:", self.power_kW)
        if Q_demand < 0:
            print('entropy pb for chiller')
        print('evap out , cond out:', self.evap_w_out_temp, self.cond_w_out_temp)

        return (Q_demand < 0)
    
    def step(self) -> bool:
        return self.update_w_out()


# ---------------------------------------------------------------------------
# 4. Water loop evaporator side
# ---------------------------------------------------------------------------

class Evaporator_loop:
    # Model a water loop with buffer tank and can transform into 
    def __init__(self, EVAP_LOOP_INFO):
        cc_chiller, gall_per_ton, dt, bool = EVAP_LOOP_INFO

        self.volume = cc_chiller  * gall_per_ton * C_gallon_to_m3 / C_ton_evap_to_kW   # m3
        self.n_slices = None
        self.water = None

        self.dt = dt
        self.flow_rate = None
        self.chiller_index = None 

        
    def calibration(self, evap_fr, set_p):
        self.flow_rate = evap_fr
        time_per_loop = self.volume / evap_fr
        self.n_slices = math.floor(self.volume/(self.flow_rate*self.dt))
        self.water = [set_p for i in range(self.n_slices)]
        self.chiller_index = self.n_slices // 2 -1

        print('Water loop, time_per_loop is:', time_per_loop)

    def update(self,  IT_CRAC_w_out, Chiller_w_out):
        self.water[0] = IT_CRAC_w_out
        self.water[self.chiller_index + 1] = Chiller_w_out
        # print(self.water)

    def step(self):
        w_crac_temp = self.water[-1]
        w_chiller_temp = self.water[self.chiller_index]

        # Move the water slice by slice        
        last_slice = self.water[-1]
        for k in range(1,self.n_slices):
            self.water[self.n_slices - k] = self.water[self.n_slices -k-1]
        self.water[0] = last_slice
        return w_crac_temp, w_chiller_temp



# ---------------------------------------------------------------------------
# 5. CRAC / CRAH Unit  (Computer Room Air Conditioning / Handling)
# ---------------------------------------------------------------------------

class CRACUnit:

    # CRAC

    def __init__(self, crac_info, name:str = 'CRAC_unit'):
        cc_crac, CFM_per_cool_capa, eps = crac_info


        self.name = name
        self.cool_capa_kW = cc_crac

        self.airflow = self.cool_capa_kW * CFM_per_cool_capa * C_CFM_to_m3s  / C_ton_evap_to_kW  # m3/s
        self.waterflow = None       # m3/s

        self.epsilon = eps
        self.UA_rated = None

        self.a_out_temp = ROOM_INITIAL_TEMP
        self.a_in_temp = ROOM_INITIAL_TEMP
        self.w_out_temp = ROOM_INITIAL_TEMP
        self.w_in_temp = ROOM_INITIAL_TEMP

        self.power_transfered_W: float = 0.0

    def calibration(self, w_fr):
        C_air = self.airflow* AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
        self.waterflow = w_fr
        C_r = C_air / (self.waterflow * RHO_CP_WATER)
        self.UA_rated = compute_UA(self.epsilon, C_air ,C_r)

    def update_out_temps(self) -> bool:
        if self.waterflow == 0 or self.airflow ==0:
            print('cooling system does not work ! Flow rates= 0')
            return False
        
        C_water = self.waterflow*RHO_CP_WATER   # kW/K
        C_air = self.airflow * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR # kW / K

        # print(f'C air {C_air} C water: {C_water}')
        self.epsilon = epsilon_from_UA(self.UA_rated, C_air, C_air / C_water)
        # print('epsilon: ', self.epsilon)
        self.a_out_temp, self.w_out_temp, C_min = heat_exchanger(self.a_in_temp, self.w_in_temp, C_air, C_water , self.epsilon)

        # print(f'air CRAC in{self.a_in_temp}, water CRAC in {self.w_in_temp}')
        # print(f'air CRAC exit {self.a_out_temp}, water CRAC exit {self.w_out_temp}')
        return (C_min != C_air)    # Assumption C air is the min.

    
    def step(self) -> bool:
        return self.update_out_temps()

# ---------------------------------------------------------------------------
# 6. Server
# ---------------------------------------------------------------------------

class Server_air_cooled:

    def __init__(self, server_info, name: str ="Server_air_cooled", 
                 ):

        thermal_resistances, thermal_capacitances, airflow, tdp_W = server_info
        self.name = name
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

        self.exit_air_heatsink_temp: float = ROOM_INITIAL_TEMP

    # --- Equations -----------------------------------------------------------


    def time_scale(self)-> str:
        R1, R2, C1, C2 = self.R_jc + self.R_cs, self.R_sa ,self. c_die_IHS, self.c_heatsink 

        A = np.array([
            [-1.0 / (R1 * C1),  1.0 / (R1 * C1)],
        [ 1.0 / (R1 * C2), -(1.0/R1 + 1.0/R2) / C2]
        ])


        eigenvalues = eig(A)[0]
        return f'time1:{-1/float(eigenvalues[0])},\n time2 {-1/float(eigenvalues[1])}'

    
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
        

# ---------------------------------------------------------------------------
# 8. IT Room
# ---------------------------------------------------------------------------
class ITRoom:
  
    def __init__(self,
                 SERVER_INFO,
                 CRAC_INFO):
        n_servers, delta_T_server, server_info = SERVER_INFO
        n_crac_units, crac_info = CRAC_INFO

        self.cold_aisle_temp: float = ROOM_INITIAL_TEMP
        self.hot_aisle_temp: float = ROOM_INITIAL_TEMP

        self.Server_air_cooled: List[Server_air_cooled] = [
            Server_air_cooled(server_info, name=f"Server-{i+1:03d}")
            for i in range(n_servers)
        ]
        self.CRACUnit: List[CRACUnit] = [
            CRACUnit(crac_info, name=f"CRAC-{i+1}")
            for i in range(n_crac_units)
        ]
        self.total_IT_power_kW: float = 0.0
        self.cracs_w_out_temp: float = ROOM_INITIAL_TEMP

        self.tot_airflow_IT_room = sum([cracU.airflow for cracU in self.CRACUnit])
        self.tot_airflow_heatsink=  sum([serv.airflow_per_heatsink for serv in self.Server_air_cooled])
        self.delta_T_server = delta_T_server    # difference of temperature, between inlet air and air around the heatsink

        print("density of the server, should be less than 1, and quite similar to the ratio inside a blade : air through HS, air inlet tot", round(self.tot_airflow_heatsink/ self.tot_airflow_IT_room, 4) )

    # --- Equations -----------------------------------------------------------
    def calibration(self, evap_fr):
        for cracU in self.CRACUnit:
            cracU.calibration(evap_fr / len(self.CRACUnit))
        for serv in self.Server_air_cooled:
            serv.time_scale()

    def calc_hot_aisle_temp(self) -> float:
        T_bypass = self.cold_aisle_temp + self.delta_T_server    

        air_bypass_heatsink = T_bypass*(self.tot_airflow_IT_room - self.tot_airflow_heatsink)

        air_through_heatsink = 0
        for serv in self.Server_air_cooled:
            air_through_heatsink += serv.exit_air_heatsink_temp * serv.airflow_per_heatsink

        self.hot_aisle_temp = (air_through_heatsink + air_bypass_heatsink) / self.tot_airflow_IT_room


    def calc_cold_aisle_temp(self) -> float:
        self.cold_aisle_temp =  sum([cracU.a_out_temp for cracU in self.CRACUnit]) / len(self.CRACUnit)
    

    def power_distribution_unit(self,input_power_IT_room_kW: float ) -> List[float]:
        List_power_per_server = []

        power_per_server_W = input_power_IT_room_kW * 1000 / len(self.Server_air_cooled)
        # print('power per server', power_per_server_W)
        # assumption all servers are identical and identical workloads
        List_power_per_server_W = [power_per_server_W for j in range(len(self.Server_air_cooled)) ]

        return List_power_per_server_W

    

    def power_flow(self) -> bool:

        violated_entropy = False
        list_power_per_server_W= self.power_distribution_unit(self.total_IT_power_kW)

        for k, serv in enumerate(self.Server_air_cooled):
            serv.inlet_air_temp = self.cold_aisle_temp
            serv.server_power_consumed_W =list_power_per_server_W[k]
            violated_entropy += serv.step()
        
        return violated_entropy
    

    def step(self) -> bool:
        return self.power_flow()



# ---------------------------------------------------------------------------
# 9. Data Center Facility  (Top-level orchestrator)
# ---------------------------------------------------------------------------

class DataCenterFacility:

    def __init__(self ,SERVER_INFO: tuple, CRAC_INFO: tuple, CHILLER_INFO: tuple, EVAP_LOOP_INFO: tuple, COOLING_TOWER_INFO, dt):
        # Important to have exact correspondance between the attribute and the class represented
        self.time_utc: float = 0.0
        self.dt = dt
        # Instantiate subsystems
        self.OutdoorEnvironment = OutdoorEnvironment(ambient_temp=28.0, relative_humidity=0.55)

        self.Chiller_water_cooled = Chiller_water_cooled(CHILLER_INFO) 

        self.CoolingTower = CoolingTower(COOLING_TOWER_INFO) 
        self.CoolingTower.calibration(fans_cool_t_fr, self.Chiller_water_cooled.cond_flow_rate)

        self.Evaporator_loop = Evaporator_loop(EVAP_LOOP_INFO)
        self.Evaporator_loop.calibration(self.Chiller_water_cooled.evap_flow_rate, self.Chiller_water_cooled.setpoint_nom_temp)

        self.entropy_violated: bool = True

        self.ITRoom = ITRoom(SERVER_INFO, CRAC_INFO)
        self.ITRoom.calibration(self.Chiller_water_cooled.evap_flow_rate)

    # --- Equations -----------------------------------------------------------


    def heat_flow(self)-> bool:
        entropy_viol = False 
        # --------------------------------------------------------------------
        # CRACS contribution
        # --------------------------------------------------------------------
        for cracU in self.ITRoom.CRACUnit:

            w_slice_to_CRAC, w_slice_to_chiller = self.Evaporator_loop.step()

            cracU.w_in_temp = w_slice_to_CRAC

            cracU.a_in_temp = self.ITRoom.hot_aisle_temp
            entropy_viol += cracU.step()

        w_slice_crac_to_loop = sum([cracU.w_out_temp*cracU.waterflow for cracU in self.ITRoom.CRACUnit ]) / sum([cracU.waterflow for cracU in self.ITRoom.CRACUnit ])
        # --------------------------------------------------------------------
        # CHILLER contribution
        # --------------------------------------------------------------------
        self.Chiller_water_cooled.evap_w_in_temp = w_slice_to_chiller
        self.Chiller_water_cooled.cond_w_in_temp = self.CoolingTower.leaving_water_temp
        # self.Chiller_water_cooled.setpoint_nom_temp = 
        entropy_viol += self.Chiller_water_cooled.step()
        w_slice_chiller_to_loop = self.Chiller_water_cooled.evap_w_out_temp

        self.Evaporator_loop.update(w_slice_crac_to_loop, w_slice_chiller_to_loop)
        # --------------------------------------------------------------------
        # COOLING TOWER contribution
        # --------------------------------------------------------------------
        self.CoolingTower.entering_water_temp = self.Chiller_water_cooled.cond_w_out_temp
        self.CoolingTower.wet_bulb_temp = self.OutdoorEnvironment.wet_bulb_temp
        entropy_viol += self.CoolingTower.step()

        return entropy_viol

    def update_dict(self, dict):
        for key in dict:
            if dynamic_correspondance_attributes_class[key] == 'DataCenterFacility':
                dict[key].append(getattr(self, key))
            elif dynamic_correspondance_attributes_class[key] in ['CRACUnit', 'Server_air_cooled']:
                dict[key].append(round(getattr(getattr(dc.ITRoom, dynamic_correspondance_attributes_class[key])[0], key),  2))
            else:
                dict[key].append(round(getattr(getattr(dc, dynamic_correspondance_attributes_class[key]), key), 2))

    def step(self, time_utc: float, input_power_IT_room_kW: float, ambient_temp: float, relative_humidity: float, values_for_plot: dict) -> None:

        self.time_utc = time_utc

        self.entropy_violated = False
        # path indoors / power
        self.ITRoom.calc_cold_aisle_temp()
        self.ITRoom.total_IT_power_kW = input_power_IT_room_kW
        self.ITRoom.step()  # power_flow, thermodynamic model
        self.ITRoom.calc_hot_aisle_temp()

        # path outdoors
        self.OutdoorEnvironment.step(ambient_temp, relative_humidity)      


        self.entropy_violated +=self.heat_flow()
        
        if self.entropy_violated:
            print("Entropy broken, wrong heat transfer at:", time_utc)
        # update values_for_plot:

        self.update_dict(values_for_plot)



def retroEngineering_data_center(PUE: float, size_in_kW: float, COP_ref: float,  CC_CRAC_boundaries_kW: tuple, CC_Cool_Tower_boundaries_kW: tuple, dt,  Oversizing = 1, Tier = None)-> DataCenterFacility:
    '''
    Gives adapted cooling system and server relying on the Chiller as the central piece of the cooling system. Power consummed to size the IT hardware 
    For a given Cooling Capacity of Chiller, the function always give the same Cooling tower and CRAC capacities. No randomness in them.'''
    # corr_Tier_Redundancy = {1:None, 2: None, 3: N+1, 4: 2 *N}
    # -----------------------------
    # Server Power
    # -----------------------------
    power_IT = size_in_kW /PUE 
    max_power_IT = power_IT / AVG_TO_MAX_RATIO
    
    def set_server_intel_info():
        # Highly dependent on the type of Data Center: HPC, CPUs, Hybrid.
        # For the moment, full CPUs of type Xeon Intel.
        n_servers = math.floor(max_power_IT * 1000 / CPU_TDP) // 2

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
        
        return (n_servers, DELTA_T_SERVER, ( set_thermal_resistances(), set_thermal_capacitances(), AIRFLOW_PER_HS, CPU_TDP))
    
    SERVER_INFO = set_server_intel_info()
    # -----------------------------
    # CHILLER
    # -----------------------------

    CC_Chiller_nom =  max_power_IT  # CC = Cooling Capacity
    CHILLER_INFO = (CC_Chiller_nom, COP_ref, EIR, CAPFT,  SETPOINT, evap_ratio, cond_ratio)
    # -----------------------------
    # CRACS
    # -----------------------------

    Q_evap = CC_Chiller_nom
    n_cracs = find_n_min(CC_CRAC_boundaries_kW, Q_evap)
    CRAC_INFO = (n_cracs, (Q_evap/n_cracs , AIRFLOW_PER_COOL_CAPA, EPSILON_RATED))

    # -----------------------------
    # Cooling Tower
    # -----------------------------
    
    # COP_avg = 1/(1 - PUE)
    Q_cond = Q_evap* (1 + 1 / COP_ref)

    n_coolingT_cells = find_n_min(CC_Cool_Tower_boundaries_kW, Q_cond)

    COOLING_TOWER_INFO = (Q_cond, n_coolingT_cells, EPSILON_CALIBR, min_approach_temp)
    EVAP_LOOP_INFO = (CC_Chiller_nom, vol_ton_ratio, dt, False)
    print(f"cooling system power:{Q_evap/COP_ref} out of {size_in_kW} kW")
    # Server end


    return DataCenterFacility(SERVER_INFO, CRAC_INFO, CHILLER_INFO, EVAP_LOOP_INFO, COOLING_TOWER_INFO, dt)

def MONTE_CARLO(n_simulations, ):
    COP_ref_boundaries = (5.5, 6.5) 
    PUE_boundaries = (1.2, 1.6)
    sizes_boundaries_kW = (50, 100000)
    random_PUE = rd.uniform(1.2, 1.6)
    random_size = rd.uniform(50, 100000)
    random_COP_ref = rd.uniform(5.5, 6.5)

    List_data_centers = [retroEngineering_data_center(random_PUE[k], random_size[k], random_COP_ref[k], CRAC_CC_range, Cool_Tower_CC_range) for k in range(n_simulations) ]
    return List_data_centers
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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

def initial_condition(DataCenter: DataCenterFacility, cooltower_leaving_temp: float) -> None:
    DataCenter.CoolingTower.leaving_water_temp = cooltower_leaving_temp


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

    List_all_keys = ['ambient_temp', 'relative_humidity_pct', 'wet_bulb_temp',

                      'UA_calibr', 'airflow', 'cooling_capacity_kW', 'entering_water_temp', 'epsilon', 'leaving_water_temp', 'n_cells', 'waterflow',

                        'EIR_params', 'Q_rated', 'cond_flow_rate', 'cond_w_in_temp', 'cond_w_out_temp', 'cop_ref', 'evap_flow_rate', 'evap_w_in_temp', 'evap_w_out_temp', 'power_kW', 'power_saved', 'setpoint_flexibility_temp', 'setpoint_nom_temp', 

                        'TES_tank', 'chiller_index', 'dt', 'flow_rate', 'n_slices', 'volume', 'water', 

                        'UA_rated', 'a_in_temp', 'a_out_temp', 'cool_capa_kW', 'name', 'power_transfered_W', 'w_in_temp', 'w_out_temp', 

                        'R_cs', 'R_jc', 'R_sa', 'airflow_per_heatsink', 'c_die_IHS', 'c_heatsink', 'case_temp', 'delta_T_server', 'exit_air_heatsink_temp', 'heat_power_generated_W', 'heatsink_temp', 'inlet_air_temp', 'junction_temp', 'server_power_consumed_W', 'tdp_W', 

                        'CRACUnit', 'Server_air_cooled', 'cold_aisle_temp', 'cracs_w_out_temp', 'hot_aisle_temp', 'tot_airflow_IT_room', 'tot_airflow_heatsink', 'total_IT_power_kW', 'Chiller_water_cooled', 'CoolingTower', 'ITRoom', 'OutdoorEnvironment', 'Evaporator_loop', 'entropy_violated', 'time_utc']
    List_keys = ['time_utc',

    'total_IT_power_kW', 'setpoint_flexibility_temp',


    'junction_temp', 'cold_aisle_temp',
      'hot_aisle_temp', 'heatsink_temp', 'exit_air_heatsink_temp', 'junction_temp', 'case_temp',


        'power_saved', 'power_kW']

    List_keys_Chiller_coolT = ['ambient_temp', 'wet_bulb_temp',  'leaving_water_temp', 'waterflow', 'cond_w_in_temp', 'cond_w_out_temp', 'cold_aisle_temp', 'evap_w_in_temp', 'evap_w_out_temp',

    'power_kW', 'power_saved', 'total_IT_power_kW', 'time_utc'
    ]
    dict_for_plot = initialise_dict_for_plot(List_keys_Chiller_coolT)

    dc = retroEngineering_data_center(1.6, 160, 6, CRAC_CC_range, Cool_Tower_CC_range, 60)
    print(f'N SERVER = {len(dc.ITRoom.Server_air_cooled)}')
    print(f'N CRACs = {len(dc.ITRoom.CRACUnit)}')
    N_DATA_INPUT = len(dataset_input['time_utc'])

    for j in range(N_DATA_INPUT):

        dc.step(time_utc= dataset_input['time_utc'][j], 
                input_power_IT_room_kW=dataset_input['input_power_IT_room_kW'][j], 
                ambient_temp=dataset_input['ambient_temp'][j], 
                relative_humidity=dataset_input['relative_humidity'][j],  
                values_for_plot= dict_for_plot)
    plotting(dict_for_plot)
