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
import json


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
# Parameters
# ---------------------------------------------------------------------------
path = r"C:\Users\andre\UniMelb\ChatGPT_Thermo_modelling\ep_chiller_cache\chiller_database.json"


with open(path, "r", encoding="utf-8") as file:
    CHILLER_CACHE_JSON =  json.load(file)

L_sorted_chiller_models = []
for model_name in CHILLER_CACHE_JSON:
    data = CHILLER_CACHE_JSON[model_name]
    tuples = (data['reference_capacity_kW'], model_name)
    L_sorted_chiller_models.append(tuples)
L_sorted_chiller_models = sorted(L_sorted_chiller_models, key=lambda x: x[0])

DT = 1 / 60 # in hours DEPENDS ON DATASET GRANULARITY 
OUTSIDE_TEMP = 18   #C

CRAC_CC_range = (214, 455)
Cool_Tower_CC_range = (53.5, 22300) # kW
fans_cool_t_fr = 3 # m3/s
# SERVER
T_CPU_TJMAX = 95 # C
T_CPU_THERMTRIP = 115 # C

season_conditions = {
    "summer": (23.8, 0.47),
    "autumn": (19.6, 0.53),
    "winter": (13.7, 0.60),
    "spring": (18.3, 0.51),
}

# ---------------------------------------------------------------------------
# ASSUMPTION VALUES FOR RETROENGINEERING DATA CENTER: 
# ---------------------------------------------------------------------------
AVG_TO_MAX_RATIO = 0.8
## SERVERS
CPU_TDP = 95 # W
AIRFLOW_PER_HS =  12.6 * C_CFM_to_m3s # CFM in #m3/s        

## Chiller
evap_ratio = 2.4 #GPM / ton
cond_ratio = 3.0 #GPM / ton
DEFAULT_MODEL = {'reference_capacity_kW' : 150 , 'reference_cop': 6, 'ref_leaving_chw_temp_C':7.2, 'ref_chw_flow_m3s': evap_ratio * 150 * C_GPM_to_m3s / C_ton_evap_to_kW , 'ref_cond_flow_m3s' : cond_ratio * 150 * C_GPM_to_m3s / C_ton_evap_to_kW , 'min_plr' : 0, 'max_plr': 1.5, 'condenser_type' : 'WaterCooled' , 'capft' : { 'coeffs': [0.25211, 0.013241, - 0.0086373,  0.085811, - 0.0042612, 0.0086619]}, 'eirfplr': {'coeffs': [0.171, 0.588, 0.237]} }
## CRACs
AIRFLOW_PER_COOL_CAPA = 400 # CFM / ton
EPSILON_RATED = 0.7
SECONDARY_LOOP_DELTA_T = 5  #C
# CoolingTower
EPSILON = (95 - 85) / (95 - 78)
min_approach_temp = 3 # \in [2.5, 4]
# Water loop
vol_ton_ratio = 10 # Gall / ton


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
    # version in ['simplified', 'constant_epsilon']

    def __init__(self, cool_tower_info):
        cooling_capacity_kW, n_coolingT_cells, eps, min_approach_temp, version = cool_tower_info

        self.cooling_capacity_kW = cooling_capacity_kW
        self.n_cells = n_coolingT_cells

        self.waterflow = None
        self.airflow: float = None
        self.leaving_water_temp: float = OUTSIDE_TEMP
        self.entering_water_temp: float = None

        self.version: str = version
        self.wet_bulb_temp: float = 0
        self.min_approach_temp = min_approach_temp
        self.epsilon = eps

        
    def set_leaving_water_temp(self) -> bool:
        T_in, T_wb = self.entering_water_temp, self.wet_bulb_temp
        T_min_control = T_wb + self.min_approach_temp

        if self.version == 'simplified':
            self.leaving_water_temp = T_min_control
            return (self.leaving_water_temp > T_in)

        else:
            T_out = T_in  - self.epsilon* (T_in - T_wb)
            self.leaving_water_temp = max(T_min_control, T_out)

            return (self.leaving_water_temp > T_in)

    def step(self) -> bool:
        return self.set_leaving_water_temp()

# ---------------------------------------------------------------------------
# 3. Chiller
# ---------------------------------------------------------------------------


class Chiller:
    def __init__(self, CHILLER_INFO):
        model = CHILLER_INFO


        self.model = model
        self.setpoint_nom_temp = self.model['ref_leaving_chw_temp_C']
        self.setpoint_flexibility_temp = None
        self.time = 0
        self.evap_flow_rate =  self.model['ref_chw_flow_m3s'] if isinstance(self.model['ref_chw_flow_m3s'] , float) else DEFAULT_MODEL['ref_chw_flow_m3s']
        self.cond_flow_rate = self.model['ref_cond_flow_m3s']if isinstance(self.model['ref_cond_flow_m3s'] , float) else DEFAULT_MODEL['ref_cond_flow_m3s']

        self.evap_w_out_temp = self.setpoint_nom_temp
        self.evap_w_in_temp = ROOM_INITIAL_TEMP
        self.cond_w_out_temp = ROOM_INITIAL_TEMP
        self.cond_w_in_temp = ROOM_INITIAL_TEMP

        self.power_saved = 0
        self.power_kW_nom = 0
        # print("chiller cooling capa:", self.Q_rated)

    def cop(self, PLR):
        min_PLR, max_PLR = self.model['min_plr'], self.model['max_plr']
        PLR = min(max_PLR, max(min_PLR, PLR) )
        denom = 0
        cop_ref = self.model['reference_cop']
        EIR_params = self.model['eirfplr']['coeffs']
        for i in range(3):
            denom += EIR_params[i]*PLR**i
        return cop_ref / denom

    def CAPFT(self):
        CAPFT_params = self.model['capft']['coeffs']
        T_e, T_c = self.evap_w_in_temp, self.cond_w_in_temp
        a, b, c,d,e,f = CAPFT_params

        val = a + b*T_e + c*T_e**2 + d*T_c + e*T_c**2 + f*T_e*T_c
        return max(0, val)
    
    def update_w_out(self) -> bool:

        C_w_evap, C_w_cond = self.evap_flow_rate*RHO_CP_WATER, self.cond_flow_rate*RHO_CP_WATER
        Q_rated = self.model['reference_capacity_kW']
        Q_max = self.CAPFT()* Q_rated

        Q_demand_flex = min(C_w_evap * ( self.evap_w_in_temp - self.setpoint_flexibility_temp), Q_max)
        # Q_demand = min(C_w_evap * ( self.evap_w_in_temp - self.setpoint_nom_temp), Q_max)


        Q_demand = min(C_w_evap * ( self.evap_w_in_temp - self.setpoint_nom_temp), Q_max)

        PLR = Q_demand / Q_rated # can be higher than 1
        PLR_flex = Q_demand_flex / Q_rated # can be higher than 1
        COP = self.cop(PLR)
        COP_flex = self.cop(PLR_flex)
        self.power_kW_nom = Q_demand / COP
        self.evap_w_out_temp = self.evap_w_in_temp - Q_demand_flex /C_w_evap
        self.cond_w_out_temp = self.cond_w_in_temp + (1 + 1/COP) * C_w_evap/C_w_cond *( self.evap_w_in_temp - self.evap_w_out_temp)

        self.power_saved = self.power_kW_nom - Q_demand_flex / COP_flex
        # print("power chiller:", self.power_kW_nom)
        if Q_demand < 0:
            print('entropy pb for chiller')

        return (Q_demand < 0)
    
    def step(self, time_resol) -> bool:
        self.time += time_resol
        return self.update_w_out()


# ---------------------------------------------------------------------------
# 4. Water loop evaporator side
# ---------------------------------------------------------------------------

class Evaporator_loop:
    # Model a water loop with buffer tank and can transform into 
    def __init__(self, EVAP_LOOP_INFO):
        cc_chiller, gall_per_ton, sl_delta_t, time_resolution = EVAP_LOOP_INFO

        self.volume = cc_chiller  * gall_per_ton * C_gallon_to_m3 / C_ton_evap_to_kW   # m3
        self.n_slices = None
        self.water = None
        self.secondary_loop_delta_T = sl_delta_t

        self.dt = time_resolution
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

    def step(self):
        w_crac_temp = self.water[-1]
        w_chiller_temp = self.water[self.chiller_index]

        # Move the water slice by slice        
        last_slice = self.water[-1]
        for k in range(1,self.n_slices):
            self.water[self.n_slices - k] = self.water[self.n_slices -k-1]
        self.water[0] = last_slice
        return w_crac_temp + self.secondary_loop_delta_T, w_chiller_temp



# ---------------------------------------------------------------------------
# 5. CRAC / CRAH Unit  (Computer Room Air Conditioning / Handling)
# ---------------------------------------------------------------------------

class CRACUnit:

    # CRAC

    def __init__(self, crac_info, name:str
                  = 'CRAC_unit'):
        cc_crac, CFM_per_cool_capa, eps = crac_info


        self.name = name
        self.cool_capa_kW = cc_crac

        self.airflow = self.cool_capa_kW * CFM_per_cool_capa * C_CFM_to_m3s  / C_ton_evap_to_kW  # m3/s
        self.waterflow = None       # m3/s
        self.epsilon = eps

        self.a_out_temp = ROOM_INITIAL_TEMP
        self.a_in_temp = ROOM_INITIAL_TEMP
        self.w_out_temp = ROOM_INITIAL_TEMP
        self.w_in_temp = ROOM_INITIAL_TEMP

    def calibration(self, w_fr):
        self.waterflow = w_fr
        C_air, C_w = self.airflow* AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR, self.waterflow * RHO_CP_WATER
        print(f'CRAC: C_AIR {C_air}, C_W : {C_w}')

    def update_out_temps(self) -> bool:
        C_air, C_w = self.airflow* AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR, self.waterflow * RHO_CP_WATER
        T_a_in, T_w_in = self.a_in_temp, self.w_in_temp,
        self.a_out_temp, self.w_out_temp, C_min = heat_exchanger(T_a_in, T_w_in , C_air, C_w , self.epsilon)
        return (C_min != C_air)    # Assumption C air is the min.

    def step(self) -> bool:
        return self.update_out_temps()

# ---------------------------------------------------------------------------
# 6. Server
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 8. IT Room
# ---------------------------------------------------------------------------
class ITRoom:
  
    def __init__(self,
                 CRAC_INFO):
        n_crac_units, crac_info = CRAC_INFO

        self.cold_aisle_temp: float = ROOM_INITIAL_TEMP
        self.hot_aisle_temp: float = ROOM_INITIAL_TEMP

        self.CRACUnit: List[CRACUnit] = [
            CRACUnit(crac_info, name=f"CRAC-{i+1}")
            for i in range(n_crac_units)
        ]
        self.cracs_w_out_temp: float = ROOM_INITIAL_TEMP

        self.tot_airflow_IT_room = sum([cracU.airflow for cracU in self.CRACUnit])


    # --- Equations -----------------------------------------------------------
    def calibration(self, evap_fr):
        for cracU in self.CRACUnit:
            cracU.calibration(evap_fr / len(self.CRACUnit)) 

    def step(self) -> bool:
        return self.power_flow()



# ---------------------------------------------------------------------------
# 9. Data Center Facility  (Top-level orchestrator)
# ---------------------------------------------------------------------------

class DataCenterFacility:

    

    def __init__(self , CRAC_INFO: tuple, CHILLER_INFO: tuple, EVAP_LOOP_INFO: tuple, COOLING_TOWER_INFO,  dt):
        # Important to have exact correspondance between the attribute and the class represented
        self.time: float = 0.0
        self.time_resolution = dt
        # Instantiate subsystems
        self.OutdoorEnvironment = OutdoorEnvironment(ambient_temp=OUTSIDE_TEMP, relative_humidity=0.55)

        self.Chiller = Chiller(CHILLER_INFO) 
        if COOLING_TOWER_INFO:
            self.CoolingTower = CoolingTower(COOLING_TOWER_INFO) 

        self.Evaporator_loop = Evaporator_loop(EVAP_LOOP_INFO)
        self.Evaporator_loop.calibration(self.Chiller.evap_flow_rate, self.Chiller.setpoint_nom_temp)

        self.entropy_violated: bool = True

        self.ITRoom = ITRoom(CRAC_INFO)
        self.ITRoom.calibration(self.Chiller.evap_flow_rate)
    # --- Equations -----------------------------------------------------------

    # def initial_condition(self, cooltower_leaving_temp: float, setp) -> None:
    #     self.CoolingTower.leaving_water_temp = cooltower_leaving_temp
    #     self.Chiller.evap_w_out_temp = setp

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
        self.Chiller.evap_w_in_temp = w_slice_to_chiller
        self.Chiller.setpoint_flexibility_temp = self.setpoint('base', self.time, 20, 50, self.Chiller.setpoint_nom_temp, 13, 5, 10)

        if self.Chiller.model['condenser_type'] == 'WaterCooled':
            # --------------------------------------------------------------------
            # COOLING TOWER contribution
            # --------------------------------------------------------------------
            self.Chiller.cond_w_in_temp = self.CoolingTower.leaving_water_temp
            entropy_viol += self.Chiller.step(self.time_resolution)
            # self.Chiller.setpoint_nom_temp = 
            self.CoolingTower.entering_water_temp = self.Chiller.cond_w_out_temp
            self.CoolingTower.wet_bulb_temp = self.OutdoorEnvironment.wet_bulb_temp
            entropy_viol += self.CoolingTower.step()
        else:
            self.Chiller.cond_w_in_temp = self.OutdoorEnvironment.ambient_temp
            entropy_viol += self.Chiller.step(self.time_resolution)

        w_slice_chiller_to_loop = self.Chiller.evap_w_out_temp
        self.Evaporator_loop.update(w_slice_crac_to_loop, w_slice_chiller_to_loop)
        return entropy_viol

    def update_dict(self, dict):
        for key in dict:
            if dynamic_correspondance_attributes_class[key] == 'DataCenterFacility':
                dict[key].append(getattr(self, key))
            elif dynamic_correspondance_attributes_class[key] in ['CRACUnit', 'Server_air_cooled']:
                dict[key].append(round(getattr(getattr(dc.ITRoom, dynamic_correspondance_attributes_class[key])[0], key),  2))
            else:
                dict[key].append(round(getattr(getattr(dc, dynamic_correspondance_attributes_class[key]), key), 2))

        
    def setpoint(self, situation, t, start_time, stop_time, T_setp_nom, T_setp_hot = None, T_setp_cold = None, precool_time = None):
        '''
        situation variable can take values in ['precooling', 'rise_setp', 'base']
        
        start time : reduction of Chiller power, corresponds to an increase in setpoint, stop time: time where setpoint comes back to normal, precool_time, time where the precool setpoint is set, before start_time
        
        We need : precool_time < start_time < stop_time '''

        if situation == 'precooling':
            boole = 0
            boole2 = 0
            if t >= precool_time and t < start_time:
                boole2 = 1
            elif t >= start_time and t <= stop_time:
                boole = 1
            
            return T_setp_nom + (T_setp_hot - T_setp_nom) * boole + (T_setp_cold - T_setp_nom)* boole2
        elif situation == 'rise_setp':
            boole = 0
            if t >= start_time and t <= stop_time:
                boole = 1
            return T_setp_nom + (T_setp_hot - T_setp_nom) * boole
        
        elif situation == 'base':
            return T_setp_nom

        
    def step(self, n_step: int, T_hot_out: float, outdoor_cond: tuple,values_for_plot: dict) -> None:
        relative_humidity, ambient_temp  = outdoor_cond
        self.time = self.time_resolution * n_step

        self.entropy_violated = False
        # path indoors / power

        self.ITRoom.hot_aisle_temp = T_hot_out

        # path outdoors
        self.OutdoorEnvironment.step(ambient_temp, relative_humidity)      


        self.entropy_violated +=self.heat_flow()
        
        if self.entropy_violated:
            print("Entropy broken, wrong heat transfer at:", self.time)
        # update values_for_plot:

        self.update_dict(values_for_plot)



def retroEngineering_data_center(PUE: float, size_in_kW: float,  CC_CRAC_boundaries_kW: tuple, CC_Cool_Tower_boundaries_kW: tuple, time_resolution,  Oversizing = 1, Tier = None)-> DataCenterFacility:
    '''
    Gives adapted cooling system and server relying on the Chiller as the central piece of the cooling system. Power consummed to size the IT hardware 
    For a given Cooling Capacity of Chiller, the function always give the same Cooling tower and CRAC capacities. No randomness in them.'''
    # corr_Tier_Redundancy = {1:None, 2: None, 3: N+1, 4: 2 *N}
    # -----------------------------
    # Server Power
    # -----------------------------
    power_IT = size_in_kW /PUE 
    max_power_IT = power_IT / AVG_TO_MAX_RATIO
    

    CC_Chiller_nom =  max_power_IT  # CC = Cooling Capacity
    model = chose_model(CC_Chiller_nom, 10)
    # model = DEFAULT_MODEL
    COP_ref = model['reference_cop']
    CHILLER_INFO = (model)
    # -----------------------------
    # CRACS
    # -----------------------------

    Q_evap = CC_Chiller_nom
    n_cracs = find_n_min(CC_CRAC_boundaries_kW, Q_evap)
    CRAC_INFO = (n_cracs, (Q_evap/n_cracs , AIRFLOW_PER_COOL_CAPA, EPSILON_RATED))


    # -----------------------------
    # Cooling Tower
    # -----------------------------
    if model['condenser_type'] =='WaterAirCooled':
        # COP_avg = 1/(1 - PUE)
        Q_cond = Q_evap* (1 + 1 / COP_ref)

        n_coolingT_cells = find_n_min(CC_Cool_Tower_boundaries_kW, Q_cond)

        COOLING_TOWER_INFO = (Q_cond, n_coolingT_cells, EPSILON, min_approach_temp, 'simplified')
    else: COOLING_TOWER_INFO = None

    # -----------------------------
    # Evap loop
    # -----------------------------
    EVAP_LOOP_INFO = (CC_Chiller_nom, vol_ton_ratio, SECONDARY_LOOP_DELTA_T, time_resolution)
    print(f"cooling system power:{Q_evap/COP_ref} out of {size_in_kW} kW")
        # Server end


    return DataCenterFacility(CRAC_INFO, CHILLER_INFO, EVAP_LOOP_INFO, COOLING_TOWER_INFO, time_resolution)

def MONTE_CARLO(n_simulations, ):
    PUE_boundaries = (1.2, 1.6)
    sizes_boundaries_kW = (15, 5000)
    random_PUE = rd.uniform(1.2, 1.6)
    random_size = rd.uniform(50, 100000)

    List_data_centers = [retroEngineering_data_center(random_PUE[k], random_size[k], CRAC_CC_range, Cool_Tower_CC_range) for k in range(n_simulations) ]
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

def chose_model(reference_capacity_kW,range_tol_kW):
    # Limited at 1 chiller. No available if cooling capacity demanded too big (> 5.5 MW)
    L_choice = []
    if reference_capacity_kW  > L_sorted_chiller_models[-1][0]:
        print('Limited at 1 chiller. No available if cooling capacity demanded too big (> 5.5 MW)')
        return None
    elif reference_capacity_kW < L_sorted_chiller_models[0][0]:
        return CHILLER_CACHE_JSON[L_sorted_chiller_models[0][1]]
    index = 0
    while reference_capacity_kW > L_sorted_chiller_models[index][0] :
        index +=1
    j = index       
    while L_sorted_chiller_models[j][0] <= L_sorted_chiller_models[index][0] + range_tol_kW and j < len(L_sorted_chiller_models):
        L_choice.append(L_sorted_chiller_models[j])
        j+=1
    n_choice = rd.randint(0, len(L_choice)-1)
    return CHILLER_CACHE_JSON[L_choice[n_choice][1]]

def plotting(dict: dict[List]) -> None:
    '''
    Requirements, the keys of dict should be real attributes of the classes !!
    '''
    dico_dfs = { 'temp' : [], 'power' : []}

    pat = r"(temp|power)"
    for key in dict:
        if key != 'time':
                            
            match = re.search(pat, key)

            if match: 
                df = pd.DataFrame({
                    "time": dict['time'],
                    match.group(1): dict[key],
                    "Description": key 
                })
                dico_dfs[match.group(1)].append(df)
            else:
                if 'other' not in dico_dfs.keys():
                    dico_dfs['other'] = []
                df = pd.DataFrame({
                                    "time": dict['time'],
                                    'other': dict[key],
                                    "Description": key 
                                })
                dico_dfs['other'].append(df)


    for category, values in dico_dfs.items():
        if not values:
            continue

        fig, ax = plt.subplots(figsize=(12, 6))
        for value in values:
            label = value["Description"].iloc[0]
            ax.plot(value["time"], value[category], label=str(label))

        ax.set_title(category)
        ax.set_xlabel("time")
        ax.set_ylabel(category)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize="small")
        fig.tight_layout()

    plt.show()



    print("Number of points plotted", len(dict['time']))

if __name__ == "__main__":
    # rd.seed(42)          # reproducible run
    ROOM_INITIAL_TEMP = 25

    dynamic_correspondance_attributes_class = create_correspondance_dico()


    Liste = [
        'ambient_temp',
        'cond_w_in_temp',
        'cond_w_out_temp',
        'evap_w_in_temp',
        'evap_w_out_temp',
        'power_kW_nom',
        'power_saved',
        'setpoint_flexibility_temp',
        'setpoint_nom_temp',
        'a_in_temp',
        'a_out_temp',
        'cracs_w_out_temp',
        'time'] 
    dict_for_plot = initialise_dict_for_plot(Liste)


    dc = retroEngineering_data_center(1.6, 160, CRAC_CC_range, Cool_Tower_CC_range, 10)
    print(dc.Chiller.model)

    path = r"C:\Users\andre\UniMelb\Validation_data\cooling_system_synthetic_inputs_5_scenarios\01_steady_state_constant.csv"
    dataset_input = pd.read_csv(path)

    N_DATA_INPUT = len(dataset_input['time_utc'])
    print(dict_for_plot)
    for j in range(N_DATA_INPUT):

        dc.step(n_step= j, 
                T_hot_out=dataset_input['input_power_IT_room_kW'][j], 
                outdoor_cond=season_conditions['summer'], 
                values_for_plot= dict_for_plot)
    plotting(dict_for_plot)
