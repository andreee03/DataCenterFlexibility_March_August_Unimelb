"""
datacenter_thermal_model.py
============================
Thermal modelling of a Data Center Facility.

Subsystems modelled:
  - OutdoorEnvironment   : ambient weather conditions
  - Chiller              : refrigeration plant (compressor + condenser + evaporator)
  - CoolingTower         : heat rejection to ambient
  - CRAC / CRAH unit     : Computer-Room Air Conditioner / Handler
  - ITRoom               : server hall with IT load, hot/cold aisles
  - Server               : individual compute node
  - DataCenterFacility   : top-level orchestrator + PUE calculation
"""

### All temperatures are in degree Celsius

import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))



# ---------------------------------------------------------------------------
# 1. Outdoor Environment
# ---------------------------------------------------------------------------

class OutdoorEnvironment:
    """
    Represents ambient weather conditions outside the data center.

    Key attributes
    --------------
    ambient_temp      : dry-bulb air temperature  [°C]
    wet_bulb_temp     : wet-bulb temperature       [°C]
    relative_humidity   : 0 – 1 fraction
    """

    def __init__(self,
                 ambient_temp: float = 25.0,
                 relative_humidity: float = 0.50):
        self.ambient_temp = ambient_temp
        self.relative_humidity = _clamp(relative_humidity, 0.0, 1.0)

        # Derived
        self.wet_bulb_temp = self._calc_wet_bulb()
        self.dew_point = self._calc_dew_point()

    # --- Equations -----------------------------------------------------------

    def _calc_wet_bulb(self) -> float:
        """
        Stull (2011) empirical wet-bulb approximation.
        T_wb ≈ T·atan(0.151977·√(RH%+8.313659)) + atan(T+RH%)
               - atan(RH%-1.676331) + 0.00391838·RH%^1.5·atan(0.023101·RH%)
               - 4.686035
        """
        T = self.ambient_temp
        RH = self.relative_humidity * 100.0
        Twb = (T * math.atan(0.151977 * math.sqrt(RH + 8.313659))
               + math.atan(T + RH)
               - math.atan(RH - 1.676331)
               + 0.00391838 * RH ** 1.5 * math.atan(0.023101 * RH)
               - 4.686035)
        return round(Twb, 2)

    def _calc_dew_point(self) -> float:
        """Magnus formula for dew point."""
        a, b = 17.27, 237.7
        alpha = (a * self.ambient_temp) / (b + self.ambient_temp) + math.log(
            max(self.relative_humidity, 1e-6))
        return round((b * alpha) / (a - alpha), 2)

    def step(self, ambient_temp: float, relative_humidity: float, ) -> None:
        """
        Advance environment by dt_hours using a simple sinusoidal diurnal cycle
        plus random perturbations.
        """
        self.ambient_temp = ambient_temp
        self.relative_humidity = _clamp(relative_humidity , 0.1, 0.95)
        self.wet_bulb_temp = self._calc_wet_bulb()
        self.dew_point = self._calc_dew_point()

    def __repr__(self) -> str:
        return (f"OutdoorEnvironment(T={self.ambient_temp:.1f}°C, "
                f"RH={self.relative_humidity*100:.0f}%, "
                f"Twb={self.wet_bulb_temp:.1f}°C)")


# ---------------------------------------------------------------------------
# 2. Cooling Tower
# ---------------------------------------------------------------------------

class CoolingTower:
    """
    Evaporative cooling tower that rejects heat from the chiller condenser loop
    to the ambient air.

    Key attributes
    --------------
    approach_temp      : Twb + approach = leaving water temp [°C]
    flow_rate_kgs        : condenser water flow rate            [kg/s]
    fan_power_kW         : tower fan electrical consumption     [kW]
    heat_rejected_kW     : total heat rejected to atmosphere    [kW]
    leaving_water_temp : water temperature leaving tower      [°C]
    """

    SPECIFIC_HEAT_WATER = 4.186   # kJ/(kg·K)

    def __init__(self,
                 design_capacity_kW: float = 500.0,
                 approach_temp: float = 4.0,
                 flow_rate_kgs: float = 20.0):
        
        self.design_capacity_kW = design_capacity_kW
        self.approach_temp = approach_temp      # name for the performance of a cooling tower.
        self.flow_rate_kgs = flow_rate_kgs

        self.heat_rejected_kW: float = 0.0
        self.leaving_water_temp: float = 30.0
        self.entering_water_temp: float = 35.0
        self.power_consummed_kW: float = 0.0

    # --- Equations -----------------------------------------------------------

    def calc_leaving_water_temp(self, wet_bulb: float) -> float:
        """
        Leaving water temp = wet-bulb + approach (simplified NTU model).
        A real tower model would use NTU-effectiveness, but this is a
        tractable first-order approximation.
        """
        return wet_bulb + self.approach_temp 

    def calc_fan_power(self, load_fraction: float) -> float:        # faux
        """
        Fan affinity law: P_fan ∝ speed³, and speed ∝ load^(1/3) (VFD control).
        P_fan = P_design · load_fraction^(1/3)
        """
        design_fan_kW = 0.015 * self.design_capacity_kW   # ~1.5 % of capacity
        return design_fan_kW * max(0.0, load_fraction) ** (1.0 / 3.0)

    def calc_heat_rejected(self) -> float:
        """
        Q = m_dot · Cp · ΔT  (condenser loop sensible heat)
        """
        delta_T = self.entering_water_temp - self.leaving_water_temp
        return self.flow_rate_kgs * self.SPECIFIC_HEAT_WATER * max(0.0, delta_T)

    def step(self, outdoor: OutdoorEnvironment,
             condenser_heat_kW: float) -> None:
        """Update tower state given current outdoor conditions and heat load."""
        load_fraction = _clamp(condenser_heat_kW / self.design_capacity_kW, 0.0, 1.2)
        self.leaving_water_temp = self.calc_leaving_water_temp(outdoor.wet_bulb_temp)
        self.entering_water_temp = self.leaving_water_temp + condenser_heat_kW / (
            self.flow_rate_kgs * self.SPECIFIC_HEAT_WATER)          # faux
        self.heat_rejected_kW = self.calc_heat_rejected()
        self.power_consummed_kW = self.calc_fan_power(load_fraction)

    def __repr__(self) -> str:
        return (f"CoolingTower(Tlwt={self.leaving_water_temp:.1f}°C, "
                f"Q_rej={self.heat_rejected_kW:.1f} kW, "
                f"P_fan={self.power_consummed_kW:.1f} kW)")


# ---------------------------------------------------------------------------
# 3. Chiller
# ---------------------------------------------------------------------------



def Temp_state_change_liquid_gaz_C(P: float, refrigerant: str):
    if refrigerant == 'R-123': 
        T = P*10 # lol c est la pire equation # faux
    return T + 273.15

class Chiller_water_cooled:
    """
    Vapour-compression chiller plant producing chilled water for CRAC/CRAH units.

    Key attributes
    --------------
    chilled_water_supply_temp : supply water temp to CRAC     [°C]
    chilled_water_return_temp : return water temp from CRAC   [°C]
    cop                         : Coefficient of Performance    [-]
    compressor_power_kW         : compressor shaft power        [kW]
    heat_rejected_kW           : heat dumped to condenser loop [kW]
    cooling_capacity_kW         : useful refrigeration effect   [kW]
    power_consummed_kW           : total electrical input        [kW]
    """
    ## A FAIRE Ne pas voir le chiller en terme d eau chilled, supply, return etc mais en terme de T_evap, T_cond, power compressor. 
    def __init__(self,
                 design_cooling_kW: float = 400.0,
                 chws_setpoint: float = 7.0,
                 chwr_temp: float = 12.0):
        
        self.design_cooling_kW = design_cooling_kW      # Is the maximum cooling possible
        self.chws_setpoint = chws_setpoint
        self.chilled_water_supply_temp = chws_setpoint
        self.chilled_water_return_temp = chwr_temp
        self.water_flow_rate: float = 20.0      # L/s
        self.cop: float = 3.5   # initial value, varies with plr
        self.heat_rejected_kW: float = 0.0      # on of the 2 ddl with the compressor energy
        self.cooling_instruction_kW: float = 0.0
        self.refrigerant: str = 'R-123'     # faux a changer avec vraie valeur
        self.power_consummed_kW: float = 0.0
        self.part_load_ratio: float = 0.0

    # --- Equations -----------------------------------------------------------
    ### Depends on the refrigerant R-...
    ### plr for Part Load ratio.
    def calc_cop(self, compressor_power_kW: float,
                 plr: float) -> float:
        """
        Modified Carnot COP with part-load degradation:
          COP_Carnot = T_evap / (T_cond - T_evap)   [Kelvin]
          COP_actual = η · COP_Carnot · f(plr)
        where η ≈ 0.55 (compressor efficiency) and
              f(plr) = 0.12 + 1.30·plr - 0.42·plr²  (ASHRAE curve fit)
        """
        P_evap = f(compressor_power_kW, self.heat_rejected_kW)
        T_evap = Temp_state_change_liquid_gaz_C(P_evap, self.refrigerant) 
        P_cond = f(compressor_power_kW, self.heat_rejected_kW)
        T_cond = Temp_state_change_liquid_gaz_C(P_cond, self.refrigerant)   # 5 K lift in condenser HX # faux
        if T_cond <= T_evap:
           print('pb: T_cond <= T_evap')
        cop_carnot = T_evap / (T_cond - T_evap)
        plr_c = _clamp(plr, 0.1, 1.0)
        f_plr = 0.12 + 1.30 * plr_c - 0.42 * plr_c ** 2
        cop = 0.55 * cop_carnot * f_plr 
        return max(1.0, cop)        # faux

    def calc_chiller_power(self, cooling_demand_kW: float,
                              cop: float) -> float:
        """W_comp = Q_evap / COP"""
        # simplified model, COP without pumps
        return cooling_demand_kW / cop

    def step(self, cooling_demand_kW: float,
             heat_rejected_kW: float) -> None:
        """Solve chiller thermodynamic state for given load and sink temp."""
        self.cooling_instruction_kW = _clamp(cooling_demand_kW, 0.0, self.design_cooling_kW)
        self.part_load_ratio = self.cooling_instruction_kW / self.design_cooling_kW

        evap_temp = self.chilled_water_supply_temp - 3.0   # refrigerant evap temp  # faux
        self.cop = self.calc_cop(condenser_water_temp, evap_temp, self.part_load_ratio)
        self.power_consummed_kW = self.calc_chiller_power(cooling_demand_kW, self.cop)
        self.condenser_heat_kW = self.cooling_instruction_kW + self.compressor_power_kW

        # Chilled water supply temp drifts slightly with load
        self.chilled_water_supply_temp = self.chws_setpoint + 0.5 * (
            self.part_load_ratio - 0.5) # faux ? PQ 0.5 * ?
        self.chilled_water_return_temp = (self.chilled_water_supply_temp
                                            + cooling_demand_kW / (
                                                self.water_flow_rate * 4.186))   

    def __repr__(self) -> str:
        return (f"Chiller(Q_cool={self.cooling_instruction_kW:.1f} kW, "
                f"COP={self.cop:.2f}, "
                f"P_comp={self.power_consummed_kW:.1f} kW, "
                f"PLR={self.part_load_ratio:.2f})")


# ---------------------------------------------------------------------------
# 4. CRAC / CRAH Unit  (Computer Room Air Conditioning / Handling)
# ---------------------------------------------------------------------------

class CRACUnit:
    """
    In-row or perimeter cooling unit that conditions IT-room air.

    Key attributes
    --------------
    supply_air_temp   : air temperature delivered to cold aisle [°C]
    return_air_temp   : air temperature drawn from hot aisle    [°C]
    airflow_m3s         : volumetric airflow                      [m³/s]
    fan_power_kW        : fan electrical power                    [kW]
    heat_removed_coil     : heat removed from air at the coil       [kW]
    heat_power_generated_kW   : total CRAC electrical power             [kW]
    """

    VOLUMIC_MASS_AIR = 1.2        # kg/m³
    SPECIFIC_HEAT_AIR = 1.005      #C_p at constant pressure, kJ/(kg·K)
    CONVECTION_HEAT_TRANSFER_AIR =  60 # W/m²K 
    FIN_EFFICIENCY = 0.8    # adim
    CONTACT_AREA = 80 # m²
    def __init__(self,
                 design_airflow_m3s: float = 5.0,
                 supply_air_setpoint: float = 18.0,
                 name: str = "CRAC-1"):
        self.name = name
        self.design_airflow_m3s = design_airflow_m3s
        self.supply_air_setpoint = supply_air_setpoint
        self.supply_air_temp: float = supply_air_setpoint       # more accurate to start with room temperature, but we look for steady state # faux
        self.return_air_temp: float = 30.0                      # assumption that the IT room starts at 30 degrees
        self.airflow_m3s: float = design_airflow_m3s
        self.heat_removed_coil: float = 0.0
        self.power_consummed_kW: float = 0.0
        self.chws_temp: float = 7.0     # faux, more 12 degrees
    # --- Equations -----------------------------------------------------------
    # power_consummed_kW = fan_power_kW
    def calc_fan_power(self, airflow_fraction: float) -> float:
        """
        Fan cube law:  P_fan = P_design · (Q / Q_design)³
        P_design ≈ 2 kW per m³/s of design airflow.
        """
        p_design = 2.0 * self.design_airflow_m3s
        return p_design * max(0.0, airflow_fraction) ** 3 

    def calc_cooling_coil(self) -> float:
        """
        Q_coil = rho_air ·  flow_air · Cp · (T_return - T_supply)
        """
        delta_T = self.return_air_temp - self.supply_air_temp
        return (self.VOLUMIC_MASS_AIR * self.SPECIFIC_HEAT_AIR
                * self.airflow_m3s * max(0.0, delta_T))

    def calc_supply_air_temp(self, chws_temp: float) -> float:
        """
        First-order coil model:
        T_supply ≈ T_chws + (T_return - T_chws) · exp(-NTU)     # cf https://en.wikipedia.org/wiki/NTU_method : NTU takes into account the geometry of the heat exchanger
        where NTU depends inversely on IT load fraction.
        """
        max_capacity_kW = (self.VOLUMIC_MASS_AIR * self.SPECIFIC_HEAT_AIR
                        * self.airflow_m3s                          # in theory it is C-min so either the air or the water
                        * (self.return_air_temp - chws_temp))       # simplification, in case the flow rate of water is very fast but good
        # load_fraction = _clamp(it_heat_load_kW / max_capacity, 0.0, 1.0)        # assumption: max_capacity != 0
        ntu = (self.CONVECTION_HEAT_TRANSFER_AIR * self.FIN_EFFICIENCY * self.CONTACT_AREA)/self.airflow_m3s     
        effectiveness = 1.0 - math.exp(-ntu)     # Assumption: first order geometry, C_r = C air for easy calculation
        Q_removed_kW = effectiveness * max_capacity_kW
        t_supply = self.return_air_temp - Q_removed_kW / (self.VOLUMIC_MASS_AIR 
                        * self.SPECIFIC_HEAT_AIR
                        * self.airflow_m3s)
        return t_supply

    def step(self, return_air_temp: float,
             chws_temp: float) -> None:
        self.return_air_temp = return_air_temp
        self.chws_temp = chws_temp

        # Simple Control loop for fans: Modulate airflow with VFD based on return-air temperature error
        temp_error = return_air_temp - 26.0          # setpoint 26 °C return
        airflow_fraction = _clamp(0.7 + 0.1 * temp_error, 0.3, 1.1)
        self.airflow_m3s = self.design_airflow_m3s * airflow_fraction

        self.supply_air_temp = self.calc_supply_air_temp(chws_temp)
        self.power_consummed_kW = self.calc_fan_power(airflow_fraction)
        self.heat_removed_coil = self.calc_cooling_coil()

    def __repr__(self) -> str:
        return (f"{self.name}(T_sup={self.supply_air_temp:.1f}°C, "
                f"T_ret={self.return_air_temp:.1f}°C, "
                f"Q_coil={self.heat_removed_coil:.1f} kW, "
                f"P_fan={self.power_consummed_kW:.2f} kW)")


# ---------------------------------------------------------------------------
# 5. Server
# ---------------------------------------------------------------------------

class Server:
    """
    Individual compute server node.

    Key attributes
    --------------
    cpu_utilisation     : 0 – 1 fraction
    power_consummed_W    : server total power draw          [W]
    heat_power_generated_W : heat generated from computation    [W]
    cpu_temp          : CPU die temperature              [°C]
    inlet_air_temp    : air temperature at server inlet  [°C]
    exhaust_air_temp  : heated air leaving server rear   [°C]
    thermal_design_W    : TDP (max heat dissipation)       [W]
    """

    def __init__(self,
                 name: str = "SRV-001",
                 tdp_W: float = 400.0,
                 idle_power_W: float = 80.0):
        self.name = name
        self.tdp_W = tdp_W      # thermal design power refers to the maximum amount of heat that a computer processor or graphics card is expected to generate under normal workloads.
        self.idle_power_W = idle_power_W

        self.cpu_utilisation: float = 0.3
        self.heat_power_generated_W: float = 0
        self.power_consummed_W: float = idle_power_W
        self.cpu_temp: float = 45.0
        self.inlet_air_temp: float = 18.0
        self.exhaust_air_temp: float = 28.0
        self.fan_speed_pct: float = 40.0
        self.thermal_resistance_per_W: float = 0.05  # chassis-level

    # --- Equations -----------------------------------------------------------

    def calc_power(self, cpu_util: float) -> float:
        """
        SPEC-power inspired model:
        P = P_idle + (P_tdp - P_idle) · (c·u + b·u² + a·u³)
        Coefficients tuned to give ~10 % idle, linear-ish ramp.
        """
        a, b, c = 0.25, 0.35, 0.40
        u = _clamp(cpu_util, 0.0, 1.0)
        p = self.idle_power_W + (self.tdp_W - self.idle_power_W) * (c * u + b * u ** 2 + a * u ** 3)
        return p
    
    def calc_heat_generated(self) -> float:
        return self.power_consummed_W       # for the moment basic model
    

    def calc_cpu_temp(self, inlet: float, power_W: float,
                      fan_speed_pct: float) -> float:
        """
        TPU = T_inlet + R_ja · P
        where R_ja decreases with higher fan speed (better convection):
        R_ja = R_base / (0.4 + 0.6 · (fan% / 100))
        """
        r_base = self.thermal_resistance_per_W
        r_ja = r_base / (0.4 + 0.6 * (fan_speed_pct / 100.0))       # pas d acc avec ces valeurs # faux
        return inlet + r_ja * power_W 

    def calc_exhaust_temp(self, inlet: float, power_W: float,
                          airflow_fraction: float) -> float:
        """
        Energy balance:  Q = m_dot · Cp · ΔT
        ΔT = P / (rho · Cp · Q_air_design · airflow_fraction)
        Design airflow ≈ 0.02 m³/s per 100 W TDP.
        """
        q_design_m3s = 0.0002 * self.tdp_W
        q_m3s = max(q_design_m3s * airflow_fraction, 1e-4)
        rho_cp = 1.2 * 1005.0   # J/(m³·K)
        return inlet + power_W / (rho_cp * q_m3s)

    def calc_fan_speed(self, cpu_temp: float) -> float:
        """
        Proportional fan control with temperature thresholds.
        """
        # Very detailed for a rough model
        if cpu_temp < 50.0:
            return 25.0
        elif cpu_temp < 70.0:
            return 25.0 + 3.0 * (cpu_temp - 50.0)
        else:
            return min(100.0, 85.0 + 1.5 * (cpu_temp - 70.0))

    def step(self, inlet_air_temp: float, cpu_utilisation: Optional[float] = None, power_IT: Optional[float] = None) -> None:
        if cpu_utilisation is not None:
            self.cpu_utilisation = _clamp(cpu_utilisation, 0.0, 1.0)
            self.power_consummed_W =self.calc_power(self.cpu_utilisation)
        if power_IT is not None:
            self.power_consummed_W = power_IT
        self.heat_power_generated_W = self.calc_heat_generated()
        self.inlet_air_temp = inlet_air_temp
        self.fan_speed_pct = self.calc_fan_speed(self.cpu_temp)
        airflow_fraction = _clamp(self.fan_speed_pct / 100.0, 0.2, 1.0)
        self.cpu_temp = self.calc_cpu_temp(
            inlet_air_temp, self.power_consummed_W, self.fan_speed_pct)
        self.exhaust_air_temp = self.calc_exhaust_temp(
            inlet_air_temp, self.heat_power_generated_W, airflow_fraction)

    def __repr__(self) -> str:
        return (f"{self.name}(util={self.cpu_utilisation*100:.0f}%, "
                f"P={self.power_consummed_W:.0f} W, "
                f"T_cpu={self.cpu_temp:.1f}°C, "
                f"T_exhaust={self.exhaust_air_temp:.1f}°C)")


# ---------------------------------------------------------------------------
# 8. IT Room
# ---------------------------------------------------------------------------

class ITRoom_aisles:
    """
    The data hall containing server racks, PDUs, and CRAC units.
    Uses a hot-aisle / cold-aisle containment model.

    Key attributes
    --------------
    cold_aisle_temp : average cold-aisle temperature      [°C]
    hot_aisle_temp  : average hot-aisle temperature       [°C]
    room_temp       : mixed average room temperature      [°C]
    total_it_load_kW  : aggregate server power              [kW]
    total_cooling_kW  : aggregate CRAC cooling capacity     [kW]
    heat_power_generated_kW : IT + PDU + UPS losses               [kW]
    """

    def __init__(self,
                 n_servers: int = 50,
                 n_crac_units: int = 4,
                 room_volume_m3: float = 1500.0):
        self.room_volume_m3 = room_volume_m3
        self.cold_aisle_temp: float = 20.0
        self.hot_aisle_temp: float = 35.0
        self.room_temp: float = 24.0
        self.total_cooling_kW: float = 0.0
        self.heat_power_generated_kW: float = 0.0

        # Sub-components
        self.servers: List[Server] = [
            Server(name=f"Server-{i+1:03d}",
                   tdp_W=random.uniform(300, 600),
                   idle_power_W=random.uniform(60, 120))
            for i in range(n_servers)
        ]
        self.crac_units: List[CRACUnit] = [
            CRACUnit(name=f"CRAC-{i+1}",
                     design_airflow_m3s=random.uniform(4.0, 7.0),
                     supply_air_setpoint=18.0)
            for i in range(n_crac_units)
        ]

    # --- Equations -----------------------------------------------------------

    def calc_hot_aisle_temp(self, cold_aisle: float,
                            it_load_kW: float,
                            total_airflow_m3s: float) -> float:
        """
        Mixed energy balance across server rows:
        T_hot = T_cold + Q_IT / (rho · Cp · Q_air)
        """
        rho_cp = 1.2 * 1.005   # kJ/(m³·K)
        if total_airflow_m3s < 0.01:
            return cold_aisle + 20.0 # faux
        return cold_aisle + it_load_kW / (rho_cp * total_airflow_m3s)  
 

    def calc_room_temp(self, cold: float, hot: float,
                       leakage_fraction: float = 0.15) -> float:
        """
        Room average mixes cold and hot air via bypass leakage.
        T_room = (1 - leak) · T_cold + leak · T_hot
        """
        return (1.0 - leakage_fraction) * cold + leakage_fraction * hot     # faux

    def step(self, chws_temp: float) -> None:
        """Advance IT room thermals by one time step."""

        # 1 – Step all servers
        for srv in self.servers:
            srv.step(inlet_air_temp=self.cold_aisle_temp)   # faux, ajouter les input

        # 4 – Total heat power generated in the room (feeds chiller demand)
        self.heat_power_generated_kW = sum(s.heat_power_generated_W for s in self.servers) / 1000.0


        # 5 – Step CRAC units
        total_airflow = 0.0
        total_cooling_crac = 0.0
        for crac in self.crac_units:
            crac.step(return_air_temp=self.hot_aisle_temp,
                      chws_temp=chws_temp)          # bizarre les cracs sont indifferents de la heat generated
            total_airflow += crac.airflow_m3s       
            total_cooling_crac += crac.heat_removed_coil
        # total_airflow = total_airflow/ len(self.crac_units) # arflow uniform in the volume
        self.total_cooling_kW = total_cooling_crac

        # 6 – Update temperatures
        self.hot_aisle_temp = self.calc_hot_aisle_temp(
            self.cold_aisle_temp, self.heat_power_generated_kW, total_airflow)
        self.cold_aisle_temp = (
            sum(c.supply_air_temp for c in self.crac_units) / len(self.crac_units)
          )
        self.room_temp = self.calc_room_temp(
            self.cold_aisle_temp, self.hot_aisle_temp)

    def __repr__(self) -> str:
        return (f"ITRoom(IT={self.heat_power_generated_kW:.1f} kW, "
                f"T_cold={self.cold_aisle_temp:.1f}°C, "
                f"T_hot={self.hot_aisle_temp:.1f}°C, "
                f"Q_cool={self.total_cooling_kW:.1f} kW)")


# ---------------------------------------------------------------------------
# 9. Data Center Facility  (Top-level orchestrator)
# ---------------------------------------------------------------------------

class DataCenterFacility:
    """
    Full facility model integrating all subsystems.

    Key attributes
    --------------
    pue                   : Power Usage Effectiveness = total / IT load
    total_power_kW        : facility total electrical consumption   [kW]
    it_power_kW           : IT equipment power                      [kW]
    cooling_power_kW      : chiller + towers + CRAC fans            [kW]
    simulation_time_hours : elapsed simulated time                  [h]
    """

    def __init__(self,
                 n_servers: int = 100,
                 n_crac_units: int = 6,
                 design_it_load_kW: float = 200.0):
        self.design_it_load_kW = design_it_load_kW
        self.simulation_time_hours: float = 0.0
        self.dt_hours: float = 20.0 / 60.0   # 20-minute time steps

        # Instantiate subsystems
        self.outdoor = OutdoorEnvironment(ambient_temp=28.0, relative_humidity=0.55)
        self.it_room = ITRoom_aisles(n_servers=n_servers, n_crac_units=n_crac_units)
        self.chiller = Chiller_water_cooled(design_cooling_kW=design_it_load_kW * 1.3)           # faux
        self.cooling_tower = CoolingTower(design_capacity_kW=design_it_load_kW * 1.5)       # faux

        # KPIs
        self.pue: float = 1.5
        self.total_power_kW: float = 0.0
        self.it_power_kW: float = 0.0
        self.cooling_power_kW: float = 0.0

        # History log
        self.history: List[dict] = []

    # --- Equations -----------------------------------------------------------

    def calc_pue(self, total_kW: float, it_kW: float) -> float:
        """PUE = Total facility power / IT load power."""
        return total_kW / max(it_kW, 1e-3)

    def calc_total_power(self) -> float:
        """Sum all electrical consumers."""
        crac_fan_kW = sum(c.power_consummed_kW for c in self.it_room.crac_units)
        return (self.it_room.heat_power_generated_kW
                + self.chiller.power_consummed_kW
                + self.cooling_tower.power_consummed_kW
                + crac_fan_kW)

    def step(self) -> dict:
        """Advance simulation by one time step (dt_hours)."""
        self.simulation_time_hours += self.dt_hours

        # 1. Outdoor environment progresses
        self.outdoor.step(self.dt_hours, ambient_temp, relative_humidity)       # faux

        # 2. Cooling tower determines leaving chilled-water temp
        self.cooling_tower.step(self.outdoor,
                                self.chiller.condenser_heat_kW)

        # 3. Chiller satisfies IT-room cooling demand
        it_cooling_demand = self.it_room.heat_power_generated_kW   # rough equal
        self.chiller.step(cooling_demand_kW=it_cooling_demand,
                          condenser_water_temp=self.cooling_tower.leaving_water_temp)

        # 4. IT Room thermal step
        self.it_room.step(chws_temp=self.chiller.chilled_water_supply_temp)

        # 5. Facility KPIs
        self.it_power_kW = self.it_room.heat_power_generated_kW
        self.total_power_kW = self.calc_total_power()
        self.cooling_power_kW = (self.chiller.heat_power_generated_kW
                                 + self.cooling_tower.heat_power_generated_kW
                                 + sum(c.power_consummed_kW for c in self.it_room.crac_units))
        self.pue = self.calc_pue(self.total_power_kW, self.it_power_kW)
            
        # 6. Log snapshot
        snapshot = {
            "time_h":           round(self.simulation_time_hours, 4),
            "outdoor_temp":   round(self.outdoor.ambient_temp, 2),
            "it_load_kW":       round(self.it_power_kW, 2),
            "total_power_kW":   round(self.total_power_kW, 2),
            "cooling_power_kW": round(self.cooling_power_kW, 2),
            "pue":              round(self.pue, 3),
            "chiller_cop":      round(self.chiller.cop, 3),
            "cold_aisle":     round(self.it_room.cold_aisle_temp, 2),
            "hot_aisle":      round(self.it_room.hot_aisle_temp, 2),
            "chws":           round(self.chiller.chilled_water_supply_temp, 2),
            "tower_lwt":      round(self.cooling_tower.leaving_water_temp, 2),
        }
        self.history.append(snapshot)
        return snapshot

    def run(self, duration_hours: float = 24.0,
            verbose: bool = True,
            report_interval_h: float = 1.0) -> None:
        """Run simulation for a given duration."""
        steps = int(duration_hours / self.dt_hours)
        report_every = max(1, int(report_interval_h / self.dt_hours))

        print("=" * 70)
        print(f"  DATA CENTER THERMAL SIMULATION  |  duration={duration_hours}h")
        print("=" * 70)
        print(f"  Servers   : {len(self.it_room.servers)}")
        print(f"  CRAC units: {len(self.it_room.crac_units)}")
        print(f"  Chiller   : {self.chiller.design_cooling_kW:.0f} kW design")
        print(f"  Tower     : {self.cooling_tower.design_capacity_kW:.0f} kW design")
        print("-" * 70)

        header = (f"{'Time':>6}  {'T_out':>6}  {'IT_kW':>7}  "
                  f"{'Tot_kW':>7}  {'PUE':>5}  {'COP':>5}  "
                  f"{'T_cold':>7}  {'T_hot':>6}  {'CHWS':>6}")
        if verbose:
            print(header)
            print("-" * 70)

        for i in range(steps):
            snap = self.step()
            if verbose and i % report_every == 0:
                print(f"{snap['time_h']:>6.2f}  "
                      f"{snap['outdoor_temp']:>6.1f}  "
                      f"{snap['it_load_kW']:>7.1f}  "
                      f"{snap['total_power_kW']:>7.1f}  "
                      f"{snap['pue']:>5.3f}  "
                      f"{snap['chiller_cop']:>5.2f}  "
                      f"{snap['cold_aisle']:>7.1f}  "
                      f"{snap['hot_aisle']:>6.1f}  "
                      f"{snap['chws']:>6.1f}")

        # Summary statistics
        if self.history:
            avg_pue = sum(h["pue"] for h in self.history) / len(self.history)
            avg_cop = sum(h["chiller_cop"] for h in self.history) / len(self.history)
            avg_it  = sum(h["it_load_kW"] for h in self.history) / len(self.history)
            total_e = sum(h["total_power_kW"] for h in self.history) * self.dt_hours
            print("=" * 70)
            print("  SIMULATION SUMMARY")
            print(f"  Average PUE        : {avg_pue:.3f}")
            print(f"  Average Chiller COP: {avg_cop:.2f}")
            print(f"  Average IT load    : {avg_it:.1f} kW")
            print(f"  Total energy used  : {total_e:.1f} kWh")
            print("=" * 70)

    def status(self) -> None:
        """Print a rich one-shot status report of all subsystems."""
        print("\n" + "=" * 60)
        print("  FACILITY STATUS SNAPSHOT")
        print("=" * 60)
        print(f"  Simulation time  : {self.simulation_time_hours:.2f} h")
        print(f"  PUE              : {self.pue:.3f}")
        print(f"  Total power      : {self.total_power_kW:.1f} kW")
        print(f"  IT power         : {self.it_power_kW:.1f} kW")
        print(f"  Cooling power    : {self.cooling_power_kW:.1f} kW")
        print("-" * 60)
        print(f"  {self.outdoor}")
        print(f"  {self.cooling_tower}")
        print(f"  {self.chiller}")
        print(f"  {self.it_room}")
        for crac in self.it_room.crac_units:
            print(f"  {crac}")
        print("=" * 60 + "\n")

    def __repr__(self) -> str:
        return (f"DataCenterFacility(PUE={self.pue:.3f}, "
                f"IT={self.it_power_kW:.1f} kW, "
                f"total={self.total_power_kW:.1f} kW)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(42)          # reproducible run

    dc = DataCenterFacility(
        n_servers=80,
        n_crac_units=6,
        design_it_load_kW=250.0,
    )

    # Warm-up: 10 steps to initialise temperatures
    for _ in range(10):
        dc.step()

    # Show snapshot after warm-up
    dc.status()

    # Run a 24-hour simulation, print hourly summaries
    dc.run(duration_hours=24.0, verbose=True, report_interval_h=2.0)