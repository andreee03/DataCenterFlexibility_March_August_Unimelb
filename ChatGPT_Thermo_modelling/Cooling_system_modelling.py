### All temperatures are in degree Celsius

import math
import os
import json
import random as rd
from typing import List

import pandas as pd
import matplotlib.pyplot as plt
import re

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

try:
    from Dataset_treatment import dataset_input
except ModuleNotFoundError:
    # Changed: Added a deterministic fallback dataset so the cooling model runs
    # independently when Dataset_treatment.py is not present.
    dataset_input = {
        "time_utc": list(range(24)),
        "T_hot": [45 for h in range(24)],
#+ 10 * math.sin(2 * math.pi * h / 24) for h in range(24)
        "ambient_temp": [26 + 6 * math.sin(2 * math.pi * (h - 6) / 24) for h in range(24)],
        "relative_humidity": [55 + 10 * math.sin(2 * math.pi * (h + 3) / 24) for h in range(24)],
    }

# ---------------------------------------------------------------------------
# Physical constants and defaults
# ---------------------------------------------------------------------------

RHO_CP_WATER = 4186
VOLUMIC_MASS_AIR = 1.2
AIR_SPECIFIC_HEAT = 1.005

C_CFM_to_m3s = 0.472 / 1000
C_GPM_to_m3s = 6.31 * 10**(-5)
C_gallon_to_m3 = 0.00454609
C_ton_evap_to_kW = 3.52
C_F_to_Celisus = 5 / 9

DT = 60
ROOM_INITIAL_TEMP = 25

CRAC_CC_range = (230, 465)
Cool_Tower_CC_range = (53.5, 22300)
fans_cool_t_fr = 3

AVG_TO_MAX_RATIO = 0.8
evap_ratio = 2.4
cond_ratio = 3.0
EIR = (0.171, 0.588, 0.237)
CAPFT = (0.25211, 0.013241, -0.0086373, 0.085811, -0.0042612, 0.0086619)
EIRFT = (1, 0, 0, 0, 0, 0)
CHILLER_CACHE_JSON = os.path.join("ep_chiller_cache", "chiller_database.json")
SETPOINT = 7.2
AIRFLOW_PER_COOL_CAPA = 400
EPSILON_RATED = 0.7
EPSILON_CALIBR = (95 - 85) / (95 - 78)
MIN_APPROACH = 3
vol_ton_ratio = 10


def P_sat(T):
    return 0.6112 * math.exp(17.67 * T / (T + 243.5))


def w_sat(T):
    P_atm = 101.3
    return 0.622 * P_sat(T) / (P_atm - P_sat(T))


def h_sat(T):
    C_p_water_gaz = 1.864
    h_fg = 2501
    return AIR_SPECIFIC_HEAT * T + w_sat(T) * (h_fg + C_p_water_gaz * T)


def m_star(T_in, T_out, a_fr, w_fr):
    def C_s():
        return (h_sat(T_in) - h_sat(T_out)) / (T_in - T_out)

    C_water = w_fr * RHO_CP_WATER
    return a_fr * VOLUMIC_MASS_AIR * C_s() / C_water


def heat_exchanger(T_hot_in, T_cold_in, Ctot_hot, Ctot_cold, eps) -> tuple:
    C_min = min(Ctot_hot, Ctot_cold)
    power_transfered_kW = C_min * eps * (T_hot_in - T_cold_in)
    T_hot_out = T_hot_in - power_transfered_kW / Ctot_hot
    T_cold_out = T_cold_in + power_transfered_kW / Ctot_cold
    return T_hot_out, T_cold_out, C_min


def compute_UA(epsilon_calibr, C_min, K):
    if C_min <= 0:
        raise ValueError("C_min must be positive to compute UA")
    if not 0 <= epsilon_calibr < 1:
        raise ValueError("epsilon_calibr must be in [0, 1)")
    # Changed: Handle the counter-flow Cr ~= 1 limit explicitly.
    if math.isclose(K, 1.0, rel_tol=1e-9, abs_tol=1e-12):
        return C_min * epsilon_calibr / (1 - epsilon_calibr)
    if K > 1:
        print("in compute UA from epsilon, K > 1. The limiting fluid is not the one expected")
    return C_min * math.log((1 - epsilon_calibr) / (1 - epsilon_calibr * K)) / (K - 1)


def epsilon_from_UA(UA, C_min, K):
    if C_min <= 0:
        raise ValueError("C_min must be positive to compute epsilon")
    NTU = UA / C_min
    # Changed: Use the correct Cr ~= 1 limit for counter-flow heat exchangers.
    if math.isclose(K, 1.0, rel_tol=1e-9, abs_tol=1e-12):
        return NTU / (1 + NTU)
    num = 1 - math.exp(-NTU * (1 - K))
    denom = 1 - K * math.exp(-NTU * (1 - K))
    return num / denom


def find_n_min(boundaries: tuple, target_cool_capa: float):
    a, b = boundaries
    if target_cool_capa < a:
        print("target Cooling capacity too small,for the given range, CRAC or Cool T oversized")
    k = 1
    while target_cool_capa / k > b:
        k += 1
    return k


def _as_float(value, default=None):
    if value in (None, ""):
        return default
    return float(value)


def _parse_curve_coeffs(coeffs):
    if isinstance(coeffs, str):
        return tuple(float(value) for value in coeffs.split())
    return tuple(float(value) for value in coeffs)


def _curve_domain(curve):
    return {
        "min_x": _as_float(curve.get("min_x")),
        "max_x": _as_float(curve.get("max_x")),
        "min_y": _as_float(curve.get("min_y")),
        "max_y": _as_float(curve.get("max_y")),
        "min_output": _as_float(curve.get("min_output")),
        "max_output": _as_float(curve.get("max_output")),
    }


def _clamp(value, lower, upper):
    if lower is not None:
        value = max(lower, value)
    if upper is not None:
        value = min(upper, value)
    return value


def _biquadratic(coeffs, x, y):
    a, b, c, d, e, f = coeffs
    return a + b * x + c * x**2 + d * y + e * y**2 + f * x * y


def _quadratic(coeffs, x):
    a, b, c = coeffs
    return a + b * x + c * x**2


def load_chiller_database(cache_json_path=CHILLER_CACHE_JSON):
    with open(cache_json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def select_chiller_model(
    demanded_capacity_kW,
    cache_json_path=CHILLER_CACHE_JSON,
    compressor_type=None,
    condenser_type=None,
    manufacturer=None,
    random_seed=None,
):
    """Select one EnergyPlus chiller record compatible with the requested load.

    Changed: Keep the random chiller selection simple but include condenser_type
    because AirCooled and WaterCooled chillers behave differently downstream.
    """
    database = load_chiller_database(cache_json_path)
    records = list(database.values())

    def text_matches(value, expected, fallback_name=""):
        if not expected:
            return True
        expected = expected.lower()
        value = "" if value is None else str(value).lower()
        fallback_name = "" if fallback_name is None else str(fallback_name).lower()
        return expected in value or expected in fallback_name

    def matches(record):
        capacity = _as_float(record.get("reference_capacity_kW"))
        if capacity is None or capacity < demanded_capacity_kW:
            return False
        if compressor_type and not text_matches(record.get("compressor_type"), compressor_type):
            return False
        if condenser_type and not text_matches(record.get("condenser_type") or record.get("cooling_type"), condenser_type):
            return False
        if manufacturer and not text_matches(record.get("manufacturer"), manufacturer, record.get("name")):
            return False
        return "capft" in record and "eirft" in record

    eligible = [record for record in records if matches(record)]
    if not eligible:
        raise ValueError("No chiller model matches the requested capacity, condenser type, manufacturer, and compressor type")

    rng = rd.Random(random_seed)
    selected = rng.choice(eligible)
    capft = selected["capft"]
    eirft = selected["eirft"]
    eirfplr = selected.get("eirfplr", {"coeffs": EIR, "min_x": 0, "max_x": 1.2})

    return {
        "name": selected.get("name"),
        "reference_capacity_kW": _as_float(selected.get("reference_capacity_kW")),
        "reference_cop": _as_float(selected.get("reference_cop")),
        "compressor_type": selected.get("compressor_type"),
        "condenser_type": selected.get("condenser_type"),
        "cooling_type": selected.get("cooling_type") or selected.get("condenser_type"),
        "is_air_cooled": bool(selected.get("is_air_cooled") or selected.get("condenser_type") == "AirCooled"),
        "is_water_cooled": bool(selected.get("is_water_cooled") or selected.get("condenser_type") == "WaterCooled"),
        "capacity_control": selected.get("capacity_control"),
        "manufacturer": selected.get("manufacturer"),
        "model_line": selected.get("model_line"),
        "refrigerant": selected.get("refrigerant"),
        "capft": {"coeffs": _parse_curve_coeffs(capft["coeffs"]), "domain": _curve_domain(capft)},
        "eirft": {"coeffs": _parse_curve_coeffs(eirft["coeffs"]), "domain": _curve_domain(eirft)},
        "eirfplr": {"coeffs": _parse_curve_coeffs(eirfplr["coeffs"]), "domain": _curve_domain(eirfplr)},
    }


def set_cooling_system_parameters(Cooling_capa_kW,
    COP_ref,
    dt=DT,
    crac_capacity_boundaries_kW=CRAC_CC_range,
    cooling_tower_capacity_boundaries_kW=Cool_Tower_CC_range,
    setpoint=SETPOINT,
    evaporator_ratio=evap_ratio,
    condenser_ratio=cond_ratio,
    eirfplr_params=EIR,
    eirft_params=EIRFT,
    capft_params=CAPFT,
    chiller_model=None,
    airflow_per_cooling_capacity=AIRFLOW_PER_COOL_CAPA,
    crac_epsilon=EPSILON_RATED,
    cooling_tower_epsilon=EPSILON_CALIBR,
    cooling_tower_min_approach=MIN_APPROACH,
    gallons_per_ton=vol_ton_ratio,
):
    """Return the component-info tuples expected by the cooling classes.

    Changed: Wrapped all default cooling-system parameters in one function so
    the cooling model is independent and configurable without server classes.
    """
    

    if chiller_model is not None:
        # Changed: Replace default CAPFT/EIRFT/EIRFPLR values with the selected
        # EnergyPlus chiller model curves and metadata.
        COP_ref = chiller_model["reference_cop"] or COP_ref
        capft_params = chiller_model["capft"]
        eirft_params = chiller_model["eirft"]
        eirfplr_params = chiller_model["eirfplr"]
    else:
        capft_params = {"coeffs": capft_params, "domain": {}}
        eirft_params = {"coeffs": eirft_params, "domain": {}}
        eirfplr_params = {"coeffs": eirfplr_params, "domain": {"min_x": 0, "max_x": 1.2}}

    chiller_info = {
        "Q_rated_kW": Cooling_capa_kW,
        "cop_ref": COP_ref,
        "eirfplr": eirfplr_params,
        "eirft": eirft_params,
        "capft": capft_params,
        "setpoint": setpoint,
        "evaporator_ratio": evaporator_ratio,
        "condenser_ratio": condenser_ratio,
        "selected_model": chiller_model,
    }

    n_cracs = find_n_min(crac_capacity_boundaries_kW, Cooling_capa_kW)
    crac_info = (
        n_cracs,
        (Cooling_capa_kW / n_cracs, airflow_per_cooling_capacity, crac_epsilon),
    )

    q_cond = Cooling_capa_kW * (1 + 1 / COP_ref)
    n_cooling_tower_cells = find_n_min(cooling_tower_capacity_boundaries_kW, q_cond)
    cooling_tower_info = (
        q_cond,
        n_cooling_tower_cells,
        cooling_tower_epsilon,
        cooling_tower_min_approach,
    )

    evap_loop_info = (Cooling_capa_kW, gallons_per_ton, dt, False)
    return {
        "CRAC_INFO": crac_info,
        "CHILLER_INFO": chiller_info,
        "EVAP_LOOP_INFO": evap_loop_info,
        "COOLING_TOWER_INFO": cooling_tower_info,
        "dt": dt,
    }


class OutdoorEnvironment:
    def __init__(self, ambient_temp, relative_humidity):
        self.ambient_temp = ambient_temp
        # Changed: Accept relative humidity as either 0-1 fraction or 0-100 percent.
        self.relative_humidity_pct = self._normalise_relative_humidity(relative_humidity)
        self.wet_bulb_temp = self.set_wet_bulb_temp()

    @staticmethod
    def _normalise_relative_humidity(relative_humidity):
        return relative_humidity * 100 if 0 <= relative_humidity <= 1 else relative_humidity

    def set_wet_bulb_temp(self):
        T = self.ambient_temp
        RH = min(100, max(0, self.relative_humidity_pct))
        Twb = (
            T * math.atan(0.151977 * math.sqrt(RH + 8.313659))
            + math.atan(T + RH)
            - math.atan(RH - 1.676331)
            + 0.00391838 * RH**1.5 * math.atan(0.023101 * RH)
            - 4.686035
        )
        self.wet_bulb_temp = round(Twb, 2)
        # Changed: Return the computed value so __init__ does not overwrite it with None.
        return self.wet_bulb_temp

    def step(self, ambient_temp: float, relative_humidity: float) -> None:
        self.ambient_temp = ambient_temp
        self.relative_humidity_pct = self._normalise_relative_humidity(relative_humidity)
        self.set_wet_bulb_temp()


class CoolingTower:
    def __init__(self, cool_tower_info):
        cooling_capacity_kW, n_coolingT_cells, eps, min_approach = cool_tower_info
        self.cooling_capacity_kW = cooling_capacity_kW
        self.n_cells = n_coolingT_cells
        self.waterflow = None
        self.airflow: float = 0.0
        self.leaving_water_temp: float = ROOM_INITIAL_TEMP - 10
        self.entering_water_temp: float = ROOM_INITIAL_TEMP
        self.wet_bulb_temp: float = 0
        self.min_approach = min_approach
        self.epsilon = eps
        self.UA_calibr = None

    def calibration(self, air_fr, w_fr):
        self.airflow = air_fr
        C_air = self.airflow * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
        self.waterflow = w_fr
        m_star_calibr = m_star((95 - 32) * C_F_to_Celisus, (85 - 32) * C_F_to_Celisus, self.airflow, self.waterflow)
        print("calibration Cool T: ", self.epsilon, m_star_calibr)
        self.UA_calibr = compute_UA(self.epsilon, C_air, m_star_calibr)

    def set_leaving_water_temp(self) -> bool:
        T_in, T_wb = self.entering_water_temp, self.wet_bulb_temp
        k = 0
        tolerance = 0.1
        delta = 1
        T_out = self.leaving_water_temp
        epsilon = self.epsilon

        while k < 5 and delta > tolerance:
            m_sta = m_star(T_in, T_in - 1, self.airflow, self.waterflow) if T_in == T_out else m_star(T_in, T_out, self.airflow, self.waterflow)
            C_air = self.airflow * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
            # Changed: epsilon_from_UA expects a heat-capacity rate, not raw airflow.
            epsilon = epsilon_from_UA(self.UA_calibr, C_air, m_sta)
            T_out_new = T_in - epsilon * (T_in - T_wb)
            delta = abs(T_out_new - T_out)
            T_out = T_out_new
            k += 1

        # Changed: A cooling tower cannot cool below wet-bulb + approach, but it
        # also should not heat condenser water already below that limit.
        lower_cooling_limit = self.wet_bulb_temp + self.min_approach
        T_cond_setpoint = T_in if T_in <= lower_cooling_limit else max(lower_cooling_limit, T_out)
        self.leaving_water_temp = round(T_cond_setpoint, 2)
        self.epsilon = epsilon
        return self.leaving_water_temp > T_in

    def step(self) -> bool:
        return self.set_leaving_water_temp()


class Chiller:
    def __init__(self, CHILLER_INFO):
        # Changed: CHILLER_INFO is now a dictionary so it can carry selected
        # EnergyPlus curve metadata and validity domains cleanly.
        self.Q_rated = CHILLER_INFO["Q_rated_kW"]
        self.cop_ref = CHILLER_INFO["cop_ref"]
        self.EIRFPLR_curve = CHILLER_INFO["eirfplr"]
        self.EIRFT_curve = CHILLER_INFO["eirft"]
        self.CAPFT_curve = CHILLER_INFO["capft"]
        self.selected_model = CHILLER_INFO.get("selected_model")
        
        set_p = CHILLER_INFO["setpoint"]
        self.setpoint_nom_temp = set_p
        self.setpoint_flexibility_temp = set_p
        evap_cc_ratio = CHILLER_INFO["evaporator_ratio"]
        cond_cc_ratio = CHILLER_INFO["condenser_ratio"]
        self.evap_flow_rate = self.Q_rated * evap_cc_ratio * C_GPM_to_m3s / C_ton_evap_to_kW
        self.cond_flow_rate = self.Q_rated * C_GPM_to_m3s / C_ton_evap_to_kW * cond_cc_ratio
        self.evap_w_out_temp = ROOM_INITIAL_TEMP
        self.evap_w_in_temp = ROOM_INITIAL_TEMP
        self.cond_w_out_temp = ROOM_INITIAL_TEMP
        self.cond_w_in_temp = ROOM_INITIAL_TEMP
        self.power_saved = 0
        self.power_kW = 0

    def _curve_temperatures(self, curve):
        domain = curve.get("domain", {})
        # Changed: CAPFT/EIRFT validity domains are applied before evaluating
        # EnergyPlus biquadratic curves. x is leaving chilled-water temperature;
        # y is entering condenser-fluid temperature.
        x = _clamp(self.evap_w_out_temp, domain.get("min_x"), domain.get("max_x"))
        y = _clamp(self.cond_w_in_temp, domain.get("min_y"), domain.get("max_y"))
        return x, y

    def CAPFT(self):
        x, y = self._curve_temperatures(self.CAPFT_curve)
        val = _biquadratic(self.CAPFT_curve["coeffs"], x, y)
        domain = self.CAPFT_curve.get("domain", {})
        return max(0, _clamp(val, domain.get("min_output"), domain.get("max_output")))

    def EIRFT(self):
        x, y = self._curve_temperatures(self.EIRFT_curve)
        val = _biquadratic(self.EIRFT_curve["coeffs"], x, y)
        domain = self.EIRFT_curve.get("domain", {})
        return max(0, _clamp(val, domain.get("min_output"), domain.get("max_output")))

    def EIRFPLR(self, PLR):
        domain = self.EIRFPLR_curve.get("domain", {})
        # Changed: Clamp PLR to the EIRFPLR curve validity domain when present.
        plr_clamped = _clamp(PLR, domain.get("min_x"), domain.get("max_x"))
        val = _quadratic(self.EIRFPLR_curve["coeffs"], plr_clamped)
        return max(0, _clamp(val, domain.get("min_output"), domain.get("max_output")))

    def cop(self, PLR):
        modifier = self.EIRFT() * self.EIRFPLR(PLR)
        return self.cop_ref / modifier if modifier > 0 else self.cop_ref

    def update_w_out(self) -> bool:
        C_water_evap = self.evap_flow_rate * RHO_CP_WATER
        C_water_cond = self.cond_flow_rate * RHO_CP_WATER
        self.evap_w_out_temp = self.setpoint_flexibility_temp
        Q_max = self.CAPFT() * self.Q_rated
        print("Q max allowed by the CAPFT", Q_max)

        # Changed: Clamp cooling demand at zero so the chiller never creates
        # negative load, negative PLR, or unphysical heating.
        Q_demand_flex = min(max(0, C_water_evap * (self.evap_w_in_temp - self.setpoint_flexibility_temp)), Q_max)
        Q_demand = min(max(0, C_water_evap * (self.evap_w_in_temp - self.setpoint_nom_temp)), Q_max)
        print("evap in , cond in:", self.evap_w_in_temp, self.cond_w_in_temp)

        PLR = Q_demand / self.Q_rated
        PLR_flex = Q_demand_flex / self.Q_rated
        self.evap_w_out_temp = self.evap_w_in_temp - Q_demand_flex / C_water_evap
        # Changed: EIRFT is now evaluated at the actual leaving chilled-water
        # temperature after capacity limiting, not only at the setpoint.
        COP = self.cop(PLR) if PLR > 0 else self.cop_ref
        COP_flex = self.cop(PLR_flex) if PLR_flex > 0 else self.cop_ref
        print(f"PLR:{PLR}, COP Operational: {COP}")

        self.power_kW = Q_demand / COP if Q_demand > 0 else 0
        self.cond_w_out_temp = self.cond_w_in_temp + (1 + 1 / COP) * C_water_evap / C_water_cond * (self.evap_w_in_temp - self.evap_w_out_temp)
        self.power_saved = self.power_kW - (Q_demand_flex / COP_flex if Q_demand_flex > 0 else 0)
        print("evap out , cond out:", self.evap_w_out_temp, self.cond_w_out_temp)
        return Q_demand < 0

    def step(self) -> bool:
        return self.update_w_out()


class Evaporator_loop:
    def __init__(self, EVAP_LOOP_INFO):
        cc_chiller, gall_per_ton, dt, TES_tank = EVAP_LOOP_INFO
        self.volume = cc_chiller * gall_per_ton * C_gallon_to_m3 / C_ton_evap_to_kW
        self.n_slices = None
        self.water = None
        self.dt = dt
        self.flow_rate = None
        self.TES_tank: bool = TES_tank
        self.chiller_index = None

    def calibration(self, evap_fr, set_p):
        self.flow_rate = evap_fr
        time_per_loop = self.volume / evap_fr
        # Changed: Keep at least two water slices so CRAC and chiller positions
        # are always valid even for large simulation time steps.
        self.n_slices = max(2, math.floor(self.volume / (self.flow_rate * self.dt)))
        self.water = [set_p for i in range(self.n_slices)]
        self.chiller_index = max(0, self.n_slices // 2 - 1)
        print("Water loop, time_per_loop is:", time_per_loop)

    def Thermal_Energy_Storage_tank(self, volume):
        if self.TES_tank:
            vol_per_slice = self.flow_rate * self.dt
            supplementary_slices = math.floor(volume / vol_per_slice)
            self.chiller_index += supplementary_slices
            self.n_slices += supplementary_slices
            self.volume += volume
            # Changed: Extend the slice-temperature state when storage volume is added.
            self.water.extend([self.water[-1] for i in range(supplementary_slices)])

    def update(self, IT_CRAC_w_out, Chiller_w_out):
        self.water[0] = IT_CRAC_w_out
        self.water[self.chiller_index + 1] = Chiller_w_out

    def step(self):
        w_crac_temp = self.water[-1]
        w_chiller_temp = self.water[self.chiller_index]
        last_slice = self.water[-1]
        for k in range(1, self.n_slices):
            self.water[self.n_slices - k] = self.water[self.n_slices - k - 1]
        self.water[0] = last_slice
        return w_crac_temp, w_chiller_temp


class CRACUnit:
    def __init__(self, crac_info, name: str = "CRAC_unit"):
        cc_crac, CFM_per_cool_capa, eps = crac_info
        self.name = name
        self.cool_capa_kW = cc_crac
        self.airflow = self.cool_capa_kW * CFM_per_cool_capa * C_CFM_to_m3s / C_ton_evap_to_kW
        self.waterflow = None
        self.epsilon = eps
        self.UA_rated = None
        self.a_out_temp = ROOM_INITIAL_TEMP
        self.a_in_temp = ROOM_INITIAL_TEMP
        self.w_out_temp = ROOM_INITIAL_TEMP
        self.w_in_temp = ROOM_INITIAL_TEMP
        self.power_transfered_W: float = 0.0

    def calibration(self, w_fr):
        C_air = self.airflow * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
        self.waterflow = w_fr
        C_r = C_air / (self.waterflow * RHO_CP_WATER)
        self.UA_rated = compute_UA(self.epsilon, C_air, C_r)

    def update_out_temps(self) -> bool:
        if self.waterflow == 0 or self.airflow == 0:
            print("cooling system does not work ! Flow rates= 0")
            return False
        C_water = self.waterflow * RHO_CP_WATER
        C_air = self.airflow * AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR
        self.epsilon = epsilon_from_UA(self.UA_rated, C_air, C_air / C_water)
        self.a_out_temp, self.w_out_temp, C_min = heat_exchanger(self.a_in_temp, self.w_in_temp, C_air, C_water, self.epsilon)
        return C_min != C_air

    def step(self) -> bool:
        return self.update_out_temps()


class CoolingSystemFacility:
    """Cooling-only model: CRACs, chilled-water loop, chiller, and cooling tower."""

    def __init__(self, CRAC_INFO: tuple, CHILLER_INFO: tuple, EVAP_LOOP_INFO: tuple, COOLING_TOWER_INFO: tuple, dt=DT):
        self.time_utc: float = 0.0
        self.dt = dt
        self.OutdoorEnvironment = OutdoorEnvironment(ambient_temp=28.0, relative_humidity=0.55)
        self.Chiller = Chiller(CHILLER_INFO)
        self.CoolingTower = CoolingTower(COOLING_TOWER_INFO)
        self.CoolingTower.calibration(fans_cool_t_fr, self.Chiller.cond_flow_rate)
        self.Evaporator_loop = Evaporator_loop(EVAP_LOOP_INFO)
        self.Evaporator_loop.calibration(self.Chiller.evap_flow_rate, self.Chiller.setpoint_nom_temp)
        n_crac_units, crac_info = CRAC_INFO
        self.CRACUnit: List[CRACUnit] = [CRACUnit(crac_info, name=f"CRAC-{i + 1}") for i in range(n_crac_units)]
        for cracU in self.CRACUnit:
            cracU.calibration(self.Chiller.evap_flow_rate / len(self.CRACUnit))

        self.total_IT_power_kW = 0.0
        self.cold_aisle_temp = ROOM_INITIAL_TEMP
        self.hot_aisle_temp = ROOM_INITIAL_TEMP
        self.entropy_violated = False
        self.tot_airflow_IT_room = sum(cracU.airflow for cracU in self.CRACUnit)

    def calc_cold_aisle_temp(self):
        self.cold_aisle_temp = sum(cracU.a_out_temp for cracU in self.CRACUnit) / len(self.CRACUnit)

    def heat_flow(self) -> bool:
        entropy_viol = False
        for cracU in self.CRACUnit:
            w_slice_to_CRAC, w_slice_to_chiller = self.Evaporator_loop.step()
            cracU.w_in_temp = w_slice_to_CRAC
            cracU.a_in_temp = self.hot_aisle_temp
            entropy_viol += cracU.step()

        w_slice_crac_to_loop = sum(cracU.w_out_temp * cracU.waterflow for cracU in self.CRACUnit) / sum(cracU.waterflow for cracU in self.CRACUnit)

        self.Chiller.evap_w_in_temp = w_slice_to_chiller
        if self.Chiller.condensor_type == 'WaterCooled':
            self.Chiller.cond_w_in_temp = self.CoolingTower.leaving_water_temp
            entropy_viol += self.Chiller.step()
           
            self.CoolingTower.entering_water_temp = self.Chiller.cond_w_out_temp
            self.CoolingTower.wet_bulb_temp = self.OutdoorEnvironment.wet_bulb_temp
            entropy_viol += self.CoolingTower.step()
        else: 
            self.Chiller.cond_w_in_temp = self.OutdoorEnvironment.ambient_temp
            entropy_viol += self.Chiller.step()
        w_slice_chiller_to_loop = self.Chiller.evap_w_out_temp
        
        self.Evaporator_loop.update(w_slice_crac_to_loop, w_slice_chiller_to_loop)
        
        return entropy_viol

    def update_dict(self, values_dict):
        for key in values_dict:
            owner = self._owner_for_key(key)
            value = getattr(owner, key)
            # Changed: Preserve boolean condenser-type flags as True/False in
            # the final dictionary instead of converting them to 0/1.
            values_dict[key].append(round(value, 2) if isinstance(value, (int, float)) and not isinstance(value, bool) else value)

    def _owner_for_key(self, key):
        if hasattr(self, key):
            return self
        for owner in [self.OutdoorEnvironment, self.CoolingTower, self.Chiller, self.Evaporator_loop]:
            if hasattr(owner, key):
                return owner
        if self.CRACUnit and hasattr(self.CRACUnit[0], key):
            return self.CRACUnit[0]
        raise KeyError(f"Unknown output key: {key}")

    def step(self, time_utc: float, T_hot: float, ambient_temp: float, relative_humidity: float, values_for_plot: dict) -> None:
        self.time_utc = time_utc
        self.entropy_violated = False
        self.hot_aisle_temp = T_hot
        self.OutdoorEnvironment.step(ambient_temp, relative_humidity)
        self.entropy_violated += self.heat_flow()
        if self.entropy_violated:
            print("Entropy broken, wrong heat transfer at:", time_utc)
        self.update_dict(values_for_plot)


def create_cooling_system(
    Cooling_capa_kW,
    COP_ref=6,
    dt=DT,
    chiller_category=None,
    cache_json_path=CHILLER_CACHE_JSON,
    random_seed=None,
):
    """Create a CoolingSystemFacility using a random matching chiller model.

    chiller_category can contain these optional filters:
    {
        "compressor_type": "Centrifugal",
        "condenser_type": "WaterCooled",
        "manufacturer": "Carrier",
    }
    """
    chiller_category = chiller_category or {}
    selected_chiller = select_chiller_model(
        demanded_capacity_kW=Cooling_capa_kW,
        cache_json_path=cache_json_path,
        compressor_type=chiller_category.get("compressor_type"),
        condenser_type=chiller_category.get("condenser_type") or chiller_category.get("condensor_type"),
        manufacturer=chiller_category.get("manufacturer"),
        random_seed=random_seed,
    )

    parameters = set_cooling_system_parameters(
        Cooling_capa_kW=Cooling_capa_kW,
        COP_ref=6,
        dt=dt,
        chiller_model=selected_chiller,
    )
    print(f"cooling system power:{parameters['CHILLER_INFO']['Q_rated_kW'] / parameters['CHILLER_INFO']['cop_ref']} kW for {Cooling_capa_kW} kW cooling capacity")
    print("selected chiller:", selected_chiller["name"])
    print(
        "chiller category:",
        {
            "compressor_type": selected_chiller["compressor_type"],
            "condenser_type": selected_chiller["condenser_type"],
            "cooling_type": selected_chiller["cooling_type"],
            "is_air_cooled": selected_chiller["is_air_cooled"],
            "is_water_cooled": selected_chiller["is_water_cooled"],
            "manufacturer": selected_chiller["manufacturer"],
            "reference_capacity_kW": selected_chiller["reference_capacity_kW"],
            "reference_cop": selected_chiller["reference_cop"],
        },
    )
    return CoolingSystemFacility(
        parameters["CRAC_INFO"],
        parameters["CHILLER_INFO"],
        parameters["EVAP_LOOP_INFO"],
        parameters["COOLING_TOWER_INFO"],
        parameters["dt"],
    )


def initialise_dict_for_plot(keys: list[str]) -> dict:
    return {key: [] for key in keys}


def plotting(values_dict: dict) -> None:
    if "time_utc" not in values_dict:
        raise KeyError("values_dict must contain a 'time_utc' key for plotting")

    dico_dfs = {"temp": [], "power": [], "other": []}
    metadata = {}
    pat = r"(temp|power)"
    for key in values_dict:
        if key != "time_utc":
            series = pd.Series(values_dict[key])
            numeric_series = pd.to_numeric(series, errors="coerce")
            if not numeric_series.notna().any():
                # Changed: Chiller metadata such as chiller_name,
                # compressor_type, and condenser_type is not plotted as a line.
                # It is printed once below instead.
                metadata[key] = series.dropna().unique().tolist()
                continue

            match = re.search(pat, key)
            y_key = match.group(1) if match else "other"
            dico_dfs[y_key].append(pd.DataFrame({
                "time_utc": values_dict["time_utc"],
                y_key: numeric_series,
                "Description": key,
            }))

    for category, values in dico_dfs.items():
        if not values:
            continue

        fig, ax = plt.subplots(figsize=(12, 6))
        for value in values:
            label = value["Description"].iloc[0]
            ax.plot(value["time_utc"], value[category], label=str(label))

        # Changed: Configure and show each category figure once, after all
        # series in that category have been added.
        ax.set_title(category)
        ax.set_xlabel("time_utc")
        ax.set_ylabel(category)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize="small")
        fig.tight_layout()

    if metadata:
        print("Non-numeric metadata not plotted:")
        for key, values in metadata.items():
            print(f"{key}: {values}")

    plt.show()

    print("Number of points plotted", len(values_dict["time_utc"]))


if __name__ == "__main__":
    List_keys_Chiller_coolT = [
        "ambient_temp",
        "wet_bulb_temp",
        "leaving_water_temp",
        "waterflow",
        "cond_w_in_temp",
        "cond_w_out_temp",
        "cold_aisle_temp",
        "evap_w_in_temp",
        "evap_w_out_temp",
        "power_kW",
        "power_saved",
        "chiller_name",
        "compressor_type",
        "condenser_type",
        "cooling_type",
        "is_air_cooled",
        "is_water_cooled",
        "time_utc",
    ]
    dict_for_plot = initialise_dict_for_plot(List_keys_Chiller_coolT)
    cooling_system = create_cooling_system(300, 6, DT)
    print(f"N CRACs = {len(cooling_system.CRACUnit)}")

    for j in range(len(dataset_input["time_utc"])):
        cooling_system.step(
            time_utc=dataset_input["time_utc"][j],
            T_hot=dataset_input["T_hot"][j],
            ambient_temp=dataset_input["ambient_temp"][j],
            relative_humidity=dataset_input["relative_humidity"][j],
            values_for_plot=dict_for_plot,
        )
    plotting(dict_for_plot)
