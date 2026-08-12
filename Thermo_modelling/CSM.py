### MOST RECENT VERSION

import math
from dataclasses import dataclass, field
from typing import List, Optional
import random as rd
import pandas as pd
import re
import numpy as np
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
C_gallon_to_m3 = 0.003785
C_ton_evap_to_kW = 3.52 
C_F_to_Celisus = 5/9

# ---------------------------------------------------------------------------
# NTU model and usefull functions
# ---------------------------------------------------------------------------

def heat_exchanger(T_hot_in, T_cold_in, Ctot_hot, Ctot_cold, eps, max_capa_kW) -> tuple:
    '''
    Ctot = heat capacity times flowrate. The idea is to say the heat transfer is maximal and limited by the minimum carrying flow
    '''
    C_min = min(Ctot_hot, Ctot_cold)

    C_r = C_min/(Ctot_hot + Ctot_cold - C_min)

    power_transfered_kW = C_min * eps * (T_hot_in - T_cold_in) 
    power_transfered_kW = min(max_capa_kW, power_transfered_kW)
    T_hot_out = T_hot_in - power_transfered_kW / Ctot_hot
    T_cold_out = T_cold_in + power_transfered_kW / Ctot_cold

    return T_hot_out, T_cold_out, C_min



def find_n_min(boundaries: tuple, target_cool_capa: float):
        a, b = boundaries
        if target_cool_capa < a:
            print('target Cooling capacity too small,for the given range, CRAC or Cool T oversized')
        # Find the minimum n_cracs.
        k = 1
        while target_cool_capa/ k > b:
            k +=1
        return k



def psi_ca(airflow_m3s: float) -> float:
    """Case-to-ambient thermal resistance as a function of airflow, K/W."""
    cfm = airflow_m3s / C_CFM_to_m3s
    if cfm <= 0.0:
        raise ValueError("airflow must be strictly positive")
    return 0.1431 + 1.9451 * cfm ** (-1.0719)


def sink_to_air_resistance(airflow_m3s: float, r_cs: float,
                           worst_case: bool = False) -> float:
    """
    FIX: the original computed psi_ca(airflow) and then threw it away, using
    the worst-case constant instead. Now it is an explicit choice.
    """
    psi = PSI_CA_WORST if worst_case else psi_ca(airflow_m3s)
    r_sa = psi - r_cs
    if r_sa <= 0.0:
        raise ValueError(f"R_sa = psi_ca - R_cs = {r_sa:.3f} K/W is non-physical")
    return r_sa



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

OUTSIDE_TEMP = 18   #C
TIME_RESOLUTION = 10


# ---------------------------------------------------------------------------
# INTERVALS FOR MONTE CARLO: 
# ---------------------------------------------------------------------------


# SERVER
T_CPU_TJMAX = 95 # C
T_CPU_THERMTRIP = 115 # C
AIRFLOW_PER_HS =  12.6 * C_CFM_to_m3s # CFM in #m3/s        

## SERVERS

## Room
# EPSILON_RATED = 0.7 # \in [0.65 , 0.90]
# CoolingTower
EPSILON = (95 - 85) / (95 - 78)     # ASHRAE Standard

season_conditions = {
    "summer": (23.8, 0.47),
    "autumn": (19.6, 0.53),
    "winter": (13.7, 0.60),
    "spring": (18.3, 0.51),
}

# ---------------------------------------------------------------------------
# Server defaults (Intel Xeon-class, 1U, air cooled)
# ---------------------------------------------------------------------------
ROOM_INITIAL_TEMP = 20.0       # degC
PSI_CA_WORST = 0.295           # K/W, case-to-ambient at worst-case airflow
# ---------------------------------------------------------------------------
# TIME CONSTANTS: 
# ---------------------------------------------------------------------------




DEFAULT_MODEL = {'reference_capacity_kW' : 150 , 'reference_cop': 6, 'ref_leaving_chw_temp_C':7.2, 'ref_chw_flow_m3s': 2.4 * 150 * C_GPM_to_m3s / C_ton_evap_to_kW , 'ref_cond_flow_m3s' : 3.0 * 150 * C_GPM_to_m3s / C_ton_evap_to_kW , 'min_plr' : 0, 'max_plr': 1.5, 'condenser_type' : 'WaterCooled' , 'capft' : { 'coeffs': [0.25211, 0.013241, - 0.0086373,  0.085811, - 0.0042612, 0.0086619]}, 'eirfplr': {'coeffs': [0.171, 0.588, 0.237]}, 'eirft': {'coeffs': [0.7582035, 0.006896017, -0.001491911, 0.002249459, 0.0003908697, -0.0001735265]}}
# Water loop


# ---------------------------------------------------------------------------
# 1. Outdoor Environment
# ---------------------------------------------------------------------------

class OutdoorEnvironment:
    def __init__(self, outdoor_cond: tuple ):
        
        ambient_temp,relative_humidity = outdoor_cond

        self.ambient_temp = ambient_temp
        self.relative_humidity_pct = relative_humidity * 100

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
        return round(Twb, 2)


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
        self.min_approach_temp = min_approach_temp
        self.epsilon = eps

        
    def set_leaving_water_temp(self, T_wb) -> bool:
        T_in = self.entering_water_temp
        T_min_control = T_wb + self.min_approach_temp

        if self.version == 'simplified':
            self.leaving_water_temp = T_min_control
            return (self.leaving_water_temp > T_in)

        else:
            T_out = T_in  - self.epsilon* (T_in - T_wb)
            self.leaving_water_temp = max(T_min_control, T_out)

            return (self.leaving_water_temp > T_in)

    def step(self, T_wb) -> bool:
        return self.set_leaving_water_temp(T_wb)

# ---------------------------------------------------------------------------
# 3. Chiller
# ---------------------------------------------------------------------------


class Chiller:
    def __init__(self, CHILLER_INFO):
        model = CHILLER_INFO


        self.model = model
        self.setpoint_temp = self.model['ref_leaving_chw_temp_C']
        self.evap_flow_rate =  float(self.model['ref_chw_flow_m3s']) if self.model['ref_chw_flow_m3s'] != "Autosize" else DEFAULT_MODEL['ref_chw_flow_m3s']

        if self.model['condenser_type'] == 'WaterCooled' :
            val = DEFAULT_MODEL['ref_cond_flow_m3s']
            self.cond_w_out_temp = ROOM_INITIAL_TEMP
            self.cond_w_in_temp = ROOM_INITIAL_TEMP
            if self.model['ref_cond_flow_m3s'] != "Autosize" :
                val= float(self.model['ref_cond_flow_m3s'])
        else:
            val = 0
            self.cond_air_temp = OUTSIDE_TEMP
        self.cond_flow_rate = val

        self.evap_w_out_temp = self.setpoint_temp
        self.evap_w_in_temp = ROOM_INITIAL_TEMP

        self.power_kW = 0
        # print("chiller cooling capa:", self.Q_rated)

    def cop(self, PLR, T_e, T_c ):
        denom = self.EIRFPLR(PLR) * self.EIRFT(T_e, T_c )
        cop_ref = self.model['reference_cop']
        return PLR * cop_ref / denom

    def EIRFT(self, T_e, T_c ):
        min_x,max_x = self.model['eirft']['min_x'], self.model['eirft']['max_x']
        min_y,max_y = self.model['eirft']['min_y'], self.model['eirft']['max_y']
        T_e = min(max_x, max(min_x, T_e))
        T_c = min(max_y, max(min_y, T_c))
        EIRFT_params = self.model['eirft']['coeffs']
        a, b, c,d,e,f = EIRFT_params

        val = a + b*T_e + c*T_e**2 + d*T_c + e*T_c**2 + f*T_e*T_c
        return  val
    
    def EIRFPLR(self, PLR):
        val = 0
        EIR_params = self.model['eirfplr']['coeffs']
        for i in range(3):
            val += EIR_params[i]*PLR**i
        return val
    
    def CAPFT(self, T_e, T_c):
        min_x,max_x = self.model['capft']['min_x'], self.model['capft']['max_x']
        min_y,max_y = self.model['capft']['min_y'], self.model['capft']['max_y']
        CAPFT_params = self.model['capft']['coeffs']
        T_e = min(max_x, max(min_x, T_e))
        T_c = min(max_y, max(min_y, T_c))
        a, b, c,d,e,f = CAPFT_params

        val = a + b*T_e + c*T_e**2 + d*T_c + e*T_c**2 + f*T_e*T_c
        return max(0, val)
    
    def update_w_out(self) -> bool:
        C_w_evap = self.evap_flow_rate * RHO_CP_WATER
        watercooled = self.model['condenser_type'] == 'WaterCooled'
        cond_temp = self.cond_w_in_temp if watercooled else self.cond_air_temp

        Q_available = self.CAPFT(self.setpoint_temp, cond_temp) * self.model['reference_capacity_kW']
        Q_demand = C_w_evap * (self.evap_w_in_temp - self.setpoint_temp)

        # Off / no load / no capacity -- well defined, no singularity
        if Q_available <= 0.0 or Q_demand <= 0.0:
            self.power_kW = 0.0
            self.evap_w_out_temp = self.evap_w_in_temp
            if watercooled:
                self.cond_w_out_temp = self.cond_w_in_temp
            return Q_demand < 0.0

        PLR_demand = Q_demand / Q_available
        PLR = min(self.model['max_plr'], max(self.model['min_plr'], PLR_demand))
        PLR = min(PLR, PLR_demand)          # never overshoot below setpoint

        eir = self.EIRFT(self.setpoint_temp, cond_temp) * self.EIRFPLR(PLR)
        self.power_kW = Q_available / self.model['reference_cop'] * eir
        self.evap_w_out_temp = self.evap_w_in_temp - PLR * Q_available / C_w_evap

        if watercooled:
            Q_rejected = PLR * Q_available + self.power_kW      # = Q_evap + W_compressor
            self.cond_w_out_temp = self.cond_w_in_temp + Q_rejected / (self.cond_flow_rate * RHO_CP_WATER)
        return False
    
    
    def step(self) -> bool:
        return self.update_w_out()


# ---------------------------------------------------------------------------
# 4. Water loop evaporator side
# ---------------------------------------------------------------------------

class Evaporator_loop:
    # Model a water loop with buffer tank and can transform into 
    def __init__(self, EVAP_LOOP_INFO):
        cc_chiller, gall_per_ton = EVAP_LOOP_INFO

        self.volume_water = cc_chiller  * gall_per_ton * C_gallon_to_m3 / C_ton_evap_to_kW   # m3
        self.n_slices = None
        self.water = None

        self.flow_rate = None

        self.chiller_index = None 

        
    def calibration(self, evap_fr, set_p):
        self.flow_rate = evap_fr
        time_per_loop = self.volume_water / evap_fr
        self.n_slices = max(2, math.floor(self.volume_water/(self.flow_rate*TIME_RESOLUTION)))
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
        return w_crac_temp, w_chiller_temp



# ---------------------------------------------------------------------------
# 5. CRAC / CRAH Unit  (Computer Room Air Conditioning / Handling)
# ---------------------------------------------------------------------------

class CRACUnit:

    # CRAC

    def __init__(self, crac_info, name:str
                  = 'CRAC_unit'):
        cc_crac, m3_fr, eps, sl_delta_t = crac_info


        self.name = name
        self.cool_capa_kW = cc_crac

        self.airflow = m3_fr # m3/s
        self.waterflow = None       # m3/s
        self.epsilon = eps
        self.secondary_loop_delta_T = sl_delta_t

        self.a_out_temp = ROOM_INITIAL_TEMP
        self.a_in_temp = ROOM_INITIAL_TEMP
        self.w_out_temp = ROOM_INITIAL_TEMP
        self.w_in_temp = ROOM_INITIAL_TEMP

    def calibration(self, w_fr):
        self.waterflow = w_fr
        print('WaterflowPer Cra si:', w_fr)
        C_air, C_w = self.airflow* AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR, self.waterflow * RHO_CP_WATER
        print(f'CRAC: C_AIR {C_air}, C_W : {C_w}')

    def update_out_temps(self) -> bool:
        C_air, C_w = self.airflow* AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR, self.waterflow * RHO_CP_WATER
        T_a_in, T_w_in = self.a_in_temp, self.w_in_temp
        max_capa_kW = self.cool_capa_kW
        self.a_out_temp, w_out_temp_sec_loop, C_min = heat_exchanger(T_a_in, T_w_in + self.secondary_loop_delta_T, C_air, C_w , self.epsilon, max_capa_kW)

        self.w_out_temp = w_out_temp_sec_loop - self.secondary_loop_delta_T
        return (C_min != C_air)    # Assumption C air is the min.

    def step(self) -> bool:
        return self.update_out_temps()

# ---------------------------------------------------------------------------
# 6. Server
# ---------------------------------------------------------------------------


class ServerAirCooled:
    """
    Node network:

        junction --R_jc-- case --R_cs-- heatsink --R_sa-- inlet air

    Steady state:
        T_sink     = T_in + P*R_sa
        T_case     = T_sink + P*R_cs
        T_junction = T_case + P*R_jc
        T_air,hs   = T_in + P / C_air,hs

    Transient: two capacitances (die+IHS, heatsink) with R_jc+R_cs between
    them and R_sa to ambient. Steady state of the ODE reproduces the algebra
    above exactly.
    """

    def __init__(
        self, server_info ):

        thermal_resistances, airflow_per_heatsink,tdp_W,n_cpu,cpu_power_fraction, airflow_tot_room= server_info
        self.R_jc, self.R_cs, self.R_sa = thermal_resistances      # K/W
        self.airflow_per_heatsink = airflow_per_heatsink           # m3/s
        self.tdp_W = tdp_W
        self.n_cpu = n_cpu

        # Air stream through one heatsink, W/K
        
        self.nominal_server_power_W = tdp_W * n_cpu / cpu_power_fraction

        self.airflow_tot_room = airflow_tot_room

        if self.airflow_tot_room < self.airflow_per_heatsink  * n_cpu:
            raise ValueError(
                "Total server air capacity rate is smaller than the sum of the "
                "heatsink streams -- check delta_T_server / airflow / TDP."
            )
        self.cpu_power_fraction = cpu_power_fraction

        # State
        self.server_power_consumed_W = 0.0
        self.heat_power_generated_W = 0.0
        self.inlet_air_temp = ROOM_INITIAL_TEMP
        self.heatsink_temp = ROOM_INITIAL_TEMP
        self.case_temp = ROOM_INITIAL_TEMP
        self.junction_temp = ROOM_INITIAL_TEMP
        self.exit_air_heatsink_temp = ROOM_INITIAL_TEMP
        self.exit_air_tot_temp = ROOM_INITIAL_TEMP
        self.entropy_violations = 0

    # --- diagnostics --------------------------------------------------------


    def _update_temperatures(self, dt: Optional[float]) -> None:
        C_hs = 1000*self.airflow_per_heatsink * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
        power_W = self.heat_power_generated_W

        self.heatsink_temp = self.inlet_air_temp + power_W * self.R_sa
        self.case_temp = self.heatsink_temp + power_W * self.R_cs
        self.junction_temp = self.case_temp + power_W * self.R_jc


        q_conv = (self.heatsink_temp - self.inlet_air_temp) / self.R_sa
        self.exit_air_heatsink_temp = self.inlet_air_temp + q_conv / C_hs

    def _update_exhaust(self) -> None:
        """
        FIX: the original was
            exit_air_tot = exit_air_heatsink + delta_T_server + inlet_air
        which double-counts the inlet temperature (exit_air_heatsink already
        contains it) and so overstated the exhaust by ~T_inlet.

        The whole-server exhaust is an energy balance on the total airflow:
            T_exhaust = T_in + P_server_total / C_air_server
        which reduces to T_in + delta_T_server at nominal load.
        """
        C_tot = 1000*self.airflow_tot_room*AIR_SPECIFIC_HEAT*VOLUMIC_MASS_AIR
        total_room_power = self.heat_power_generated_W *self.n_cpu/ self.cpu_power_fraction
        self.exit_air_tot_temp = self.inlet_air_temp + total_room_power / C_tot

    def _check_second_law(self, tol: float = 1e-9) -> bool:
        """
        Air leaving the fins cannot be hotter than the fins themselves.
        FIX: returns a real bool, counts violations instead of printing every
        timestep, and no longer relies on `False += bool` int coercion.
        """
        violated = self.exit_air_heatsink_temp > self.heatsink_temp + tol
        if violated:
            self.entropy_violations += 1
        return violated

    def power_flow(self, cpu_power_W: float,
                   dt: Optional[float] = None) -> bool:
        """Advance one timestep. Returns True if the second-law check failed."""
        if cpu_power_W < 0.0:
            raise ValueError("power must be non-negative")
        # FIX: tdp_W was stored but never used -- clamp and warn instead.
        if cpu_power_W > self.tdp_W:
            cpu_power_W = self.tdp_W

        self.server_power_consumed_W = cpu_power_W
        self.heat_power_generated_W = cpu_power_W   # all electrical power -> heat

        self._update_temperatures(dt)
        self._update_exhaust()
        return self._check_second_law()


#
# ---------------------------------------------------------------------------
# 7. IT Room
# ---------------------------------------------------------------------------
class ITRoom:
  
    def __init__(self,
                 ITROOM_INFO):
        n_crac_units, volume, cabinets_capacitance, crac_info, server_info = ITROOM_INFO
        self.server_index = None
        self.air = None

        self.CRACUnit: List[CRACUnit] = [
            CRACUnit(crac_info, name=f"CRAC-{i+1}")
            for i in range(n_crac_units)
        ]
        self.tot_airflow_IT_room = sum([cracU.airflow for cracU in self.CRACUnit])
        self.ServerAirCooled = ServerAirCooled(server_info)

        self.cabinets_capacitance = cabinets_capacitance    # kJ / K
        self.volume_air: float = volume
        self.n_slices = None

    # --- Equations -----------------------------------------------------------
    def calibration(self, evap_fr):
        self.n_slices = max(2, math.floor(self.volume_air/(self.tot_airflow_IT_room*TIME_RESOLUTION)))
        self.server_index = self.n_slices // 2 -1
        self.air = [ROOM_INITIAL_TEMP for i in range(self.n_slices)]
        print('len Crac U is:',len(self.CRACUnit) )
        for cracU in self.CRACUnit:
            cracU.calibration(evap_fr / len(self.CRACUnit)) 
        print('Air loop, time_per_loop is:', self.n_slices *TIME_RESOLUTION)

    def update(self,  air_slice_crac_to_ITRoom, Server_a_out):
        self.air[0] = air_slice_crac_to_ITRoom
        self.air[self.server_index + 1] = Server_a_out

    
    def step(self) -> bool:
        air_crac_temp = self.air[-1]
        air_slice_to_servers = self.air[self.server_index]

        # Move the air slice by slice        
        last_slice = self.air[-1]
        for k in range(1,self.n_slices):
            self.air[self.n_slices - k] = self.air[self.n_slices -k-1]
        self.air[0] = last_slice
        # self.power_flow()
        return air_crac_temp , air_slice_to_servers


# ---------------------------------------------------------------------------
# 8. Cooling Systen Facility  (Top-level orchestrator)
# ---------------------------------------------------------------------------

class DataCenterFacility:

    

    def __init__(self , outdoor_conditions, ITROOM_INFO: tuple, CHILLER_INFO: tuple, EVAP_LOOP_INFO: tuple, COOLING_TOWER_INFO,  dt, time_scales, setp_info):
        # Important to have exact correspondance between the attribute and the class represented
        self.time: float = 0.0
        self.time_resolution = dt
        self.setp_info = setp_info
        # Instantiate subsystems
        self.OutdoorEnvironment = OutdoorEnvironment(outdoor_conditions)

        self.Chiller = Chiller(CHILLER_INFO) 
        if COOLING_TOWER_INFO:
            self.CoolingTower = CoolingTower(COOLING_TOWER_INFO) 
        self.L_power_chiller = []
        self.Evaporator_loop = Evaporator_loop(EVAP_LOOP_INFO)
        self.Evaporator_loop.calibration(self.Chiller.evap_flow_rate, self.Chiller.setpoint_temp)

        self.entropy_violated: bool = True

        self.ITRoom = ITRoom(ITROOM_INFO)
        print('self.Chiller.evap_flow_rate is :', self.Chiller.evap_flow_rate)
        self.ITRoom.calibration(self.Chiller.evap_flow_rate)
        self.time_scales = time_scales
    # --- Equations -----------------------------------------------------------

    # def initial_condition(self, cooltower_leaving_temp: float, setp) -> None:
    #     self.CoolingTower.leaving_water_temp = cooltower_leaving_temp
    #     self.Chiller.evap_w_out_temp = setp

    def heat_flow(self, Server_a_out)-> bool:
        entropy_viol = False 
        # --------------------------------------------------------------------
        # CRACS contribution
        # --------------------------------------------------------------------
        w_slice_to_CRAC, w_slice_to_chiller = self.Evaporator_loop.step()
        air_slice_to_CRAC, air_slice_to_servers = self.ITRoom.step()
        for cracU in self.ITRoom.CRACUnit:
            cracU.w_in_temp = w_slice_to_CRAC

            cracU.a_in_temp = air_slice_to_CRAC
            entropy_viol += cracU.step()
            # cracU.a_out_temp = air_slice_to_servers
        air_slice_crac_to_ITRoom = sum([cracU.a_out_temp*cracU.airflow for cracU in self.ITRoom.CRACUnit ]) / sum([cracU.airflow for cracU in self.ITRoom.CRACUnit ])

        self.ITRoom.update(air_slice_crac_to_ITRoom, Server_a_out )
        w_slice_crac_to_loop = sum([cracU.w_out_temp*cracU.waterflow for cracU in self.ITRoom.CRACUnit ]) / sum([cracU.waterflow for cracU in self.ITRoom.CRACUnit ])
        # --------------------------------------------------------------------
        # CHILLER contribution
        # --------------------------------------------------------------------
        self.Chiller.evap_w_in_temp = w_slice_to_chiller
        self.Chiller.setpoint_temp = self.setpoint(self.time)

        if self.Chiller.model['condenser_type'] == 'WaterCooled':
            # --------------------------------------------------------------------
            # COOLING TOWER contribution
            # --------------------------------------------------------------------
            self.Chiller.cond_w_in_temp = self.CoolingTower.leaving_water_temp
  
            entropy_viol += self.Chiller.step()
            self.CoolingTower.entering_water_temp = self.Chiller.cond_w_out_temp
            self.CoolingTower.wet_bulb_temp = self.OutdoorEnvironment.wet_bulb_temp
            entropy_viol += self.CoolingTower.step(self.OutdoorEnvironment.wet_bulb_temp)
        else:
            self.Chiller.cond_air_temp = self.OutdoorEnvironment.ambient_temp
            entropy_viol += self.Chiller.step()
        w_slice_chiller_to_loop = self.Chiller.evap_w_out_temp
        self.Evaporator_loop.update(w_slice_crac_to_loop, w_slice_chiller_to_loop)
        return air_slice_to_servers, entropy_viol

    def update_dict(self, trace: dict):
        for key in trace:
            owner = ATTR_OWNER[key]
            if owner == 'DataCenterFacility':
                val = getattr(self, key)
            elif owner == 'CRACUnit':
                val = getattr(self.ITRoom.CRACUnit[0], key)
            elif owner == 'ServerAirCooled':
                val = getattr(self.ITRoom.ServerAirCooled, key)
            else:
                val = getattr(getattr(self, owner), key)
            trace[key].append(round(val, 3) if isinstance(val, float) else val)
            
    def setpoint(self, t)-> float:
        '''
        situation variable can take values in ['precooling', 'rise_setp', 'base']
        
        start time : reduction of Chiller power, corresponds to an increase in setpoint, stop time: time where setpoint comes back to normal, precool_time, time where the precool setpoint is set, before start_time
        
        We need : precool_time < start_time < stop_time '''
        boole = 0
        T_setp_nom = self.Chiller.model['ref_leaving_chw_temp_C']
        setp_mode = self.setp_info['mode']
        T_setp_hot = self.setp_info['T_setp_hot']
        T_setp_cold = self.setp_info['T_setp_cold']

        if setp_mode == 'precooling':
            boole2 = 0
            if t >= self.setp_info['precool_time'] and t < self.setp_info['start_time']:
                boole2 = 1
            elif t >= self.setp_info['start_time'] and t <= self.setp_info['stop_time']:
                boole = 1
            
            return T_setp_nom + (T_setp_hot - T_setp_nom) * boole + (T_setp_cold - T_setp_nom)* boole2

        elif setp_mode == 'base':
            return T_setp_nom
        
        elif setp_mode == 'rise_setp':
            if t >= self.setp_info['start_time'] and t <= self.setp_info['stop_time']:
                boole = 1
            return T_setp_nom + (T_setp_hot - T_setp_nom) * boole
        else:
            return T_setp_nom

    def reset(self):
        self.time = 0.0
        self.L_power_chiller = []
        self.Evaporator_loop.calibration(self.Chiller.evap_flow_rate,
                                        self.Chiller.model['ref_leaving_chw_temp_C'])
        self.ITRoom.calibration(self.Chiller.evap_flow_rate)
        self.Chiller.setpoint_temp = self.Chiller.model['ref_leaving_chw_temp_C']
        self.Chiller.evap_w_in_temp = ROOM_INITIAL_TEMP
        self.Chiller.evap_w_out_temp = self.Chiller.setpoint_temp
        if self.Chiller.model['condenser_type'] == 'WaterCooled':
            self.Chiller.cond_w_in_temp = self.Chiller.cond_w_out_temp = ROOM_INITIAL_TEMP
            self.CoolingTower.leaving_water_temp = OUTSIDE_TEMP
        srv = self.ITRoom.ServerAirCooled
        for a in ('inlet_air_temp','heatsink_temp','case_temp','junction_temp',
                'exit_air_heatsink_temp','exit_air_tot_temp'):
            setattr(srv, a, ROOM_INITIAL_TEMP)
        srv.entropy_violations = 0
        for c in self.ITRoom.CRACUnit:
            c.a_in_temp = c.a_out_temp = c.w_in_temp = c.w_out_temp = ROOM_INITIAL_TEMP
            
    def step(self, n_step: int, P_cpu_W: float, values_for_plot: dict) -> None:
        self.time = self.time_resolution * n_step
        self.entropy_violated = False
        # path indoors / power
        self.ITRoom.ServerAirCooled.power_flow(P_cpu_W)

        air_to_servers, entropy =self.heat_flow(self.ITRoom.ServerAirCooled.exit_air_tot_temp)
        self.entropy_violated += entropy
        self.ITRoom.ServerAirCooled.inlet_air_temp = air_to_servers
        self.L_power_chiller.append(self.Chiller.power_kW)
        if self.entropy_violated:
            print("Entropy broken, wrong heat transfer at:", self.time)
        # update values_for_plot:

        self.update_dict(values_for_plot)
        
    def time_transcient(self) -> float:
        L_time = self.time_scales

        V_w, fr_w = self.Evaporator_loop.volume_water, self.Evaporator_loop.flow_rate
        V_a, fr_a = self.ITRoom.volume_air, self.ITRoom.tot_airflow_IT_room
        n_cpu_per_cabinet = 70
        t_w = V_w/ fr_w 
        t_a = V_a/ fr_a 
        t_heating_cabinet = self.ITRoom.ServerAirCooled.n_cpu / n_cpu_per_cabinet * self.ITRoom.cabinets_capacitance  / (self.ITRoom.tot_airflow_IT_room * AIR_SPECIFIC_HEAT* VOLUMIC_MASS_AIR)
        L_time.append(t_w/2)
        L_time.append(t_a/2)
        L_time.append(t_heating_cabinet)

        return 2*sum(L_time)

def output_values(L_global, L_nom, L_flex, L_precool, t_flex):
    L_saved = L_nom - L_flex
    L_saved_precool = L_nom - L_precool
    L_global.append({'power_profile_flex': L_saved, 'power_profile_precool': L_saved_precool, 't_flex':t_flex})


def retroEngineering_data_center(outdoor_conditions, PUE, AVG_TO_MAX_RATIO, CPU_POWER_FRACTION, CHILLER_DESIGN_MARGIN, CRAH_AIRFLOW_MARGIN, MAX_DELTA_T_SERVER_K, vol_ratio, vol_ton_ratio, size_in_kW,SECONDARY_LOOP_DELTA_T , min_approach_temp, R_jc, R_cs, time_modulation_compressor, CPU_TDP_W,cabinet_capacitance, EPSILON_RATED, 
                                 CC_CRAC_boundaries_kW, CC_Cool_Tower_boundaries_kW,
                                 time_resolution, Oversizing=1, Tier=None) -> DataCenterFacility:

    

    # ----------------- IT load -----------------
    power_IT     = size_in_kW / PUE
    max_power_IT = power_IT / AVG_TO_MAX_RATIO
    max_power_CPU = CPU_POWER_FRACTION * max_power_IT      # servers/heatsinks ONLY

    # ----------------- Chiller -----------------
    mechanical_load = max_power_IT 
    CC_Chiller_nom  = mechanical_load * CHILLER_DESIGN_MARGIN 

    model     = chose_model(CC_Chiller_nom, 10)
    COP_ref   = model['reference_cop']
    CHILLER_INFO = (model)

    # ----------------- Air side (derived, not assumed) -----------------
    Q_evap = CC_Chiller_nom
    airflow_IT   = max_power_IT / (AIR_SPECIFIC_HEAT* VOLUMIC_MASS_AIR* MAX_DELTA_T_SERVER_K)     # m3/s
    airflow_CRAH = airflow_IT * CRAH_AIRFLOW_MARGIN

    n_cracs = find_n_min(CC_CRAC_boundaries_kW, Q_evap)

 # ----------------- Server -----------------
    n_cpu = math.floor(max_power_CPU * 1000/ CPU_TDP_W)
    R_sa = sink_to_air_resistance(AIRFLOW_PER_HS, R_cs)

    
    SERVER_INFO = ((R_jc, R_cs, R_sa), AIRFLOW_PER_HS, CPU_TDP_W, n_cpu, CPU_POWER_FRACTION, airflow_CRAH)

    ITROOM_INFO = (n_cracs, vol_ratio * max_power_IT, cabinet_capacitance,
                   (Q_evap / n_cracs, airflow_CRAH / n_cracs,
                    EPSILON_RATED, SECONDARY_LOOP_DELTA_T), SERVER_INFO)
    

    # ----------------- Cooling tower -----------------
    if model['condenser_type'] == 'WaterCooled':
        Q_cond = Q_evap * (1 + 1 / COP_ref) 
        n_coolingT_cells = find_n_min(CC_Cool_Tower_boundaries_kW, Q_cond)
        COOLING_TOWER_INFO = (Q_cond, n_coolingT_cells, EPSILON,
                              min_approach_temp, 'constant_epsilon')
    else:
        COOLING_TOWER_INFO = None

    EVAP_LOOP_INFO = (CC_Chiller_nom, vol_ton_ratio)
   
    list_times = [time_modulation_compressor]
    return DataCenterFacility(outdoor_conditions, ITROOM_INFO, CHILLER_INFO, EVAP_LOOP_INFO, COOLING_TOWER_INFO, time_resolution, list_times, 'base')


def MONTE_CARLO(n_simulations, outdoor_conditions, seed=0):
    
    CRAC_CC_range = (214, 455)
    Cool_Tower_CC_range = (53.5, 22300) # kW
    
    PARAM_BOUNDS = {
    'PUE':                  (1.2, 1.6),
    'AVG_TO_MAX_RATIO':     (0.6, 0.9),
    'CPU_POWER_FRACTION':   (0.20, 0.45),
    'CHILLER_DESIGN_MARGIN':(1.0, 1.2),
    'CRAH_AIRFLOW_MARGIN':  (1.0, 1.30),
    'time_modulation_compressor': (30, 120), #s
    'EPSILON_RATED' : (0.65 , 0.90),
    'MAX_DELTA_T_SERVER_K': (5.0, 12.0),
    'vol_ratio':            (1.35, 8.6),   # m³/kW
    'cabinet_capacitance':  (50, 80),      # kJ/K
    'vol_ton_ratio':        (6, 20),       # gal/ton
    'SECONDARY_LOOP_DELTA_T':(5.5, 10),
    'min_approach_temp':    (2.8, 5.6),
    'R_jc':                 (0.1, 0.2),
    'R_cs':                 (0.05, 0.12),
    'CPU_TDP_W':              (95, 105),
}
    fixed = dict(CC_CRAC_boundaries_kW=CRAC_CC_range,
             CC_Cool_Tower_boundaries_kW=Cool_Tower_CC_range,
             time_resolution=TIME_RESOLUTION)
    rng = rd.Random(seed)
    rows = []

    def draw_params(rng=rd):
        p =  {k: rng.uniform(*b) for k, b in PARAM_BOUNDS.items()}
        p['size_in_kW']=  math.exp(rng.uniform(math.log(15), math.log(3200)))
        return p
    
    for i in range(n_simulations):
        p = draw_params(rng)
        dc = retroEngineering_data_center(outdoor_conditions, **p, **fixed)
        model = dc.Chiller.model
        T_nom = model['ref_leaving_chw_temp_C']
        P_cpu_W = (1000.0 * p['size_in_kW'] / p['PUE']
                * p['CPU_POWER_FRACTION'] / dc.ITRoom.ServerAirCooled.n_cpu)
        t_flex = dc.time_transcient()          # facility-level, computed once

        for j in range(1, 5):
            for mode in ['base', 'precooling', 'rise_setp']:
                dc.setp_info = {'mode': mode, 'start_time': 2000, 'stop_time': 3000,
                                'precool_time': 1000,
                                'T_setp_hot':  T_nom + j * (15 - T_nom) / 4,
                                'T_setp_cold': T_nom + j * (4 - T_nom) / 4}
                run_simulation(dc, P_cpu_W)

                P = np.asarray(dc.L_power_chiller, dtype=np.float32)
                rows.append({'facility_id': i, 'situation': j, 'mode': mode, **p,
                            't_flex_s': t_flex,
                            'E_chiller_kWh': P.sum() * dc.time_resolution / 3600,
                            'P_peak_kW': float(P.max()) if P.size else 0.0,
                            'L_power': P,
                            'violations': dc.ITRoom.ServerAirCooled.entropy_violations})
        return pd.DataFrame(rows)

def MONTE_CARLO(n_simulations, outdoor_conditions):

    CRAC_CC_range = (214, 455)
    Cool_Tower_CC_range = (53.5, 22300) # kW
    
    PARAM_BOUNDS = {
    'PUE':                  (1.2, 1.6),
    'AVG_TO_MAX_RATIO':     (0.6, 0.9),
    'CPU_POWER_FRACTION':   (0.20, 0.45),
    'CHILLER_DESIGN_MARGIN':(1.0, 1.2),
    'CRAH_AIRFLOW_MARGIN':  (1.0, 1.30),
    'time_modulation_compressor': (30, 120), #s
    'EPSILON_RATED' : (0.65 , 0.90),
    'MAX_DELTA_T_SERVER_K': (5.0, 12.0),
    'vol_ratio':            (1.35, 8.6),   # m³/kW
    'cabinet_capacitance':  (50, 80),      # kJ/K
    'vol_ton_ratio':        (6, 20),       # gal/ton
    'SECONDARY_LOOP_DELTA_T':(5.5, 10),
    'min_approach_temp':    (2.8, 5.6),
    'R_jc':                 (0.1, 0.2),
    'R_cs':                 (0.05, 0.12),
    'CPU_TDP_W':              (95, 105),
}
    def draw_params(rng=rd):
        p =  {k: rng.uniform(*b) for k, b in PARAM_BOUNDS.items()}
        p['size_in_kW']=  math.exp(rd.uniform(math.log(15), math.log(3200)))
        return p
    
    L_global = {'precooling':{'Sit1': [],'Sit2': [],'Sit3': [],'Sit4': []}, 'rise_setp':{'Sit1': [],'Sit2': [],'Sit3': [],'Sit4': []}, 'time_flex': 0}
    

    List_data_centers = [retroEngineering_data_center(outdoor_conditions, ** draw_params(), CC_CRAC_boundaries_kW=CRAC_CC_range, CC_Cool_Tower_boundaries_kW=Cool_Tower_CC_range, time_resolution=TIME_RESOLUTION) for k in range(n_simulations) ]
    for data_center in List_data_centers:
        P_cpu_W = 1000*  p['size_in_kW']/p['PUE'] * p['CPU_POWER_FRACTION'] / data_center.ITRoom.ServerAirCooled.n_cpu
        T_setp_hot_max = 15
        T_setp_cold_max = 4
        T_setp_nom = data_center.Chiller.model['ref_leaving_chw_temp_C']
        step_hot = (T_setp_hot_max - T_setp_nom) /4
        step_cold = (T_setp_cold_max - T_setp_nom) /4
        for j in range(1, 5):
            setp_info = {'start_time':2000, 'stop_time':3000, 'T_setp_hot': T_setp_nom + j*step_hot, 'T_setp_cold': T_setp_nom + j*step_cold, 'precool_time':1000}
            for setp_mode in ['base', 'precooling', 'rise_setp']:
                setp_info['mode'] = setp_mode
                data_center.setp_info = setp_info

                L_global[setp_mode][f'Sit{j}'] = run_simulation(data_center, P_cpu_W)

        L_global['time_flex']+= data_center.time_transcient()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

ATTR_OWNER = {
    'ambient_temp': 'OutdoorEnvironment', 'wet_bulb_temp': 'OutdoorEnvironment',
    'evap_w_in_temp': 'Chiller', 'evap_w_out_temp': 'Chiller',
    'cond_w_in_temp': 'Chiller', 'cond_w_out_temp': 'Chiller',
    'power_kW': 'Chiller', 'setpoint_temp': 'Chiller',
    'a_in_temp': 'CRACUnit', 'a_out_temp': 'CRACUnit',
    'w_in_temp': 'CRACUnit', 'w_out_temp': 'CRACUnit',
    'junction_temp': 'ServerAirCooled', 'inlet_air_temp': 'ServerAirCooled',
    'exit_air_tot_temp': 'ServerAirCooled', 'heatsink_temp': 'ServerAirCooled',
    'leaving_water_temp': 'CoolingTower', 'entering_water_temp': 'CoolingTower',
    'time': 'DataCenterFacility',
}

def initialise_dict_for_plot(keys: list[str]) -> dict:
    all_attribs = ATTR_OWNER.keys()
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
    while j < len(L_sorted_chiller_models) and L_sorted_chiller_models[j][0] <= L_sorted_chiller_models[index][0] + range_tol_kW :
        L_choice.append(L_sorted_chiller_models[j])
        j+=1
    n_choice = rd.randint(0, len(L_choice)-1)
    return CHILLER_CACHE_JSON[L_choice[n_choice][1]]

def run_simulation(dc: DataCenterFacility, P_cpu_W, time_seconds = 36000):
    n_steps = time_seconds // dc.time_resolution
    for j in range(n_steps):   
        dc.step(n_step= j, 
                P_cpu_W=P_cpu_W, 
                values_for_plot={})
    return (dc.L_power_chiller)

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
    rd.seed(0)
    ROOM_INITIAL_TEMP = 25



    Liste = [] 
    dict_for_plot = initialise_dict_for_plot(Liste)


    MONTE_CARLO(100, season_conditions['autumn'])