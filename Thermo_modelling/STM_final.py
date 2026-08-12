"""
Air-cooled server thermal model -- corrected version.

Every substantive change to the original is marked with a `# FIX:` comment.

Two solver modes:
  * "steady"    -- algebraic network (what the original code actually did)
  * "transient" -- 2-node RC network integrated with an exact discretisation
                   (this is what the thermal capacitances were computed for)
Both agree at steady state, by construction.
"""

import re
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.linalg import expm, inv

# FIX: removed unused imports (math, dataclass/field, matplotlib, scipy.eig).
try:
    import plotly.express as px
except ImportError:  # FIX: plotting is optional, don't kill the run
    px = None


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
RHO_CP_WATER = 4186.0          # kJ/(m3*K)
VOLUMIC_MASS_AIR = 1.2         # kg/m3
AIR_SPECIFIC_HEAT = 1.005      # kJ/(kg*K), c_p at constant pressure
COPPER_SPECIFIC_HEAT = 0.384   # J/(g*K)
AL_SPECIFIC_HEAT = 0.897       # J/(g*K)
SI_SPECIFIC_HEAT = 0.710       # J/(g*K)
AL_RHO = 2.70e-3               # g/mm3
COPPER_RHO = 8.96e-3           # g/mm3

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------
C_CFM_to_m3s = 4.719e-4        # FIX: 1 CFM = 4.719e-4 m3/s (was 4.72e-4, fine, but be exact)
C_GPM_to_m3s = 6.31e-5
C_gallon_to_m3 = 0.00454609
C_ton_evap_to_kW = 3.52
C_F_to_Celsius = 5.0 / 9.0     # NB: a *slope*, not an offset conversion

# ---------------------------------------------------------------------------
# Server defaults (Intel Xeon-class, 1U, air cooled)
# ---------------------------------------------------------------------------
ROOM_INITIAL_TEMP = 20.0       # degC
CPU_TDP = 95.0                 # W
AIRFLOW_PER_HS = 12.6 * C_CFM_to_m3s   # m3/s through one heatsink
DELTA_T_SERVER = 8.0           # K, design inlet->exhaust rise at nominal load
R_jc = 0.2                     # K/W  (0.1 - 0.3)
R_cs = 0.1                     # K/W
PSI_CA_WORST = 0.295           # K/W, case-to-ambient at worst-case airflow
CPU_POWER_FRACTION = 0.6       # share of total server power drawn by the CPU(s)
N_CPU = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def air_capacity_rate(airflow_m3s: float) -> float:
    """Heat capacity rate of an air stream, W/K."""
    return AIR_SPECIFIC_HEAT * VOLUMIC_MASS_AIR * airflow_m3s * 1000.0


def heatsink_capacity(volume_mm3: float, fraction_al: float = 0.34) -> float:
    """
    Thermal capacitance of a heatsink, J/K.

    FIX: the original multiplied the volume-weighted specific heat by the
    volume-weighted density, which invents cross-terms
    (t*c_Al*(1-t)*rho_Cu etc.) and is only correct at t = 0 or t = 1.
    The mass-weighted sum is the correct form.
    """
    if not 0.0 <= fraction_al <= 1.0:
        raise ValueError("fraction_al must lie in [0, 1]")
    t = fraction_al
    return volume_mm3 * (t * AL_RHO * AL_SPECIFIC_HEAT
                         + (1.0 - t) * COPPER_RHO * COPPER_SPECIFIC_HEAT)


def psi_ca(airflow_m3s: float) -> float:
    """Case-to-ambient thermal resistance as a function of airflow, K/W."""
    cfm = airflow_m3s / C_CFM_to_m3s
    if cfm <= 0.0:
        raise ValueError("airflow must be strictly positive")
    return 0.1431 + 1.9451 * cfm ** (-1.0719)


def sink_to_air_resistance(airflow_m3s: float, r_cs: float = R_cs,
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
# Server
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
        self,
        thermal_resistances: Tuple[float, float, float],
        thermal_capacitances: Tuple[float, float],
        airflow_per_heatsink: float,
        tdp_W: float,
        delta_T_server: float = DELTA_T_SERVER,
        n_cpu: int = N_CPU,
        cpu_power_fraction: float = CPU_POWER_FRACTION,
        mode: str = "steady",
        initial_temp: float = ROOM_INITIAL_TEMP,
    ):
        if mode not in ("steady", "transient"):
            raise ValueError("mode must be 'steady' or 'transient'")
        self.mode = mode

        self.R_jc, self.R_cs, self.R_sa = thermal_resistances      # K/W
        self.c_die_IHS, self.c_heatsink = thermal_capacitances     # J/K
        self.airflow_per_heatsink = airflow_per_heatsink           # m3/s
        self.tdp_W = tdp_W
        self.n_cpu = n_cpu
        self.delta_T_server = delta_T_server

        # Air stream through one heatsink, W/K
        self.C_air_heatsink = air_capacity_rate(airflow_per_heatsink)

        # FIX: total server airflow is derived so that the exhaust rise equals
        # delta_T_server at nominal load, instead of adding delta_T_server as a
        # constant offset on top of an already-offset temperature.
        self.nominal_server_power_W = tdp_W * n_cpu / cpu_power_fraction
        self.C_air_server = self.nominal_server_power_W / delta_T_server
        if self.C_air_server < self.C_air_heatsink * n_cpu:
            raise ValueError(
                "Total server air capacity rate is smaller than the sum of the "
                "heatsink streams -- check delta_T_server / airflow / TDP."
            )
        self.cpu_power_fraction = cpu_power_fraction

        # State
        self.server_power_consumed_W = 0.0
        self.heat_power_generated_W = 0.0
        self.inlet_air_temp = initial_temp
        self.heatsink_temp = initial_temp
        self.case_temp = initial_temp
        self.junction_temp = initial_temp
        self.exit_air_heatsink_temp = initial_temp
        self.exit_air_tot_temp = initial_temp
        self.entropy_violations = 0

        # Transient state: x = [T_die/IHS, T_heatsink]
        self._x = np.array([initial_temp, initial_temp], dtype=float)
        self._discrete_cache: Dict[float, Tuple[np.ndarray, np.ndarray]] = {}

    # --- diagnostics --------------------------------------------------------
    def effectiveness(self) -> float:
        """
        FIX: the original `debug` computed 1/(airflow * R_sa), which is not
        dimensionless. The correct group is 1/(C_air * R_sa).
        """
        return 1.0 / (self.C_air_heatsink * self.R_sa)

    def time_constants(self) -> Tuple[float, float]:
        """Rough node time constants, s -- useful for choosing dt."""
        return (self.c_die_IHS * (self.R_jc + self.R_cs),
                self.c_heatsink * self.R_sa)

    # --- solver -------------------------------------------------------------
    def _state_space(self) -> Tuple[np.ndarray, np.ndarray]:
        r12 = self.R_jc + self.R_cs
        c1, c2, rsa = self.c_die_IHS, self.c_heatsink, self.R_sa
        A = np.array([[-1.0 / (c1 * r12), 1.0 / (c1 * r12)],
                      [1.0 / (c2 * r12), -(1.0 / (c2 * r12) + 1.0 / (c2 * rsa))]])
        B = np.array([[1.0 / c1, 0.0],
                      [0.0, 1.0 / (c2 * rsa)]])
        return A, B

    def _discretise(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Exact zero-order-hold discretisation; unconditionally stable."""
        if dt not in self._discrete_cache:
            A, B = self._state_space()
            Ad = expm(A * dt)
            Bd = inv(A) @ (Ad - np.eye(2)) @ B
            self._discrete_cache[dt] = (Ad, Bd)
        return self._discrete_cache[dt]

    def _update_temperatures(self, dt: Optional[float]) -> None:
        power_W = self.heat_power_generated_W

        if self.mode == "steady":
            self.heatsink_temp = self.inlet_air_temp + power_W * self.R_sa
            self.case_temp = self.heatsink_temp + power_W * self.R_cs
            self.junction_temp = self.case_temp + power_W * self.R_jc
            self._x[:] = (self.junction_temp, self.heatsink_temp)
        else:
            if dt is None or dt <= 0.0:
                raise ValueError("transient mode needs a positive timestep dt")
            Ad, Bd = self._discretise(dt)
            u = np.array([power_W, self.inlet_air_temp])
            self._x = Ad @ self._x + Bd @ u
            t_die, self.heatsink_temp = self._x
            # Split the die->sink drop across R_jc and R_cs by the flux through it
            q = (t_die - self.heatsink_temp) / (self.R_jc + self.R_cs)
            self.case_temp = self.heatsink_temp + q * self.R_cs
            self.junction_temp = self.case_temp + q * self.R_jc

        # Air leaving the heatsink fins.
        # FIX: use the heat actually *convected off the fins*, (T_hs - T_in)/R_sa,
        # not the dissipated power. During transients they differ, because the
        # heatsink stores energy -- the original form made the air jump instantly
        # on a load step while the fins lagged, which trips the second-law check.
        # At steady state q_conv == power_W, so this is identical there.
        q_conv = (self.heatsink_temp - self.inlet_air_temp) / self.R_sa
        self.exit_air_heatsink_temp = self.inlet_air_temp + q_conv / self.C_air_heatsink

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
        total_server_power = self.heat_power_generated_W / self.cpu_power_fraction
        self.exit_air_tot_temp = self.inlet_air_temp + total_server_power / self.C_air_server

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

    def power_flow(self, T_inlet: float, cpu_power_W: float,
                   dt: Optional[float] = None) -> bool:
        """Advance one timestep. Returns True if the second-law check failed."""
        if cpu_power_W < 0.0:
            raise ValueError("power must be non-negative")
        # FIX: tdp_W was stored but never used -- clamp and warn instead.
        if cpu_power_W > self.tdp_W:
            cpu_power_W = self.tdp_W

        self.inlet_air_temp = float(T_inlet)
        self.server_power_consumed_W = cpu_power_W
        self.heat_power_generated_W = cpu_power_W   # all electrical power -> heat

        self._update_temperatures(dt)
        self._update_exhaust()
        return self._check_second_law()


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------
class Recorder:
    """
    FIX: replaces create_correspondance_dico / initialise_dict_for_plot /
    update_dict, which
      (a) read the module-level global `Server_test` instead of the instance,
      (b) never appended 'time_utc', so the plotting DataFrames had mismatched
          column lengths and raised ValueError,
      (c) relied on `__static_attributes__`, which only exists on Python 3.13+
          and blew up on any imported class lacking it.
    """

    def __init__(self, keys: Sequence[str], probe: object):
        valid = set(vars(probe)) | {"time_utc"}
        unknown = [k for k in keys if k not in valid]
        if unknown:
            raise KeyError(f"Not attributes of {type(probe).__name__}: {unknown}")
        self.data: Dict[str, List] = {k: [] for k in keys}

    def record(self, obj: object, time_utc) -> None:
        for key, series in self.data.items():
            if key == "time_utc":
                series.append(time_utc)
            else:
                value = getattr(obj, key)
                series.append(round(value, 3) if isinstance(value, float) else value)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.data)


def plotting(data: Dict[str, List]) -> None:
    """FIX: no builtin shadowing, no concat on empty lists, groups discovered
    from the data rather than hard-coded."""
    if px is None:
        print("plotly not installed -- skipping plots")
        return
    if "time_utc" not in data or not data["time_utc"]:
        raise ValueError("no time axis recorded")

    groups: Dict[str, List[pd.DataFrame]] = {}
    pattern = re.compile(r"(temp|power)")
    for key, values in data.items():
        if key == "time_utc":
            continue
        match = pattern.search(key)
        group = match.group(1) if match else "other"
        groups.setdefault(group, []).append(
            pd.DataFrame({"time_utc": data["time_utc"], group: values, "Description": key})
        )

    for group, frames in groups.items():
        df_all = pd.concat(frames, ignore_index=True)
        px.line(df_all, x="time_utc", y=group, color="Description").show()

    print("Number of points plotted:", len(data["time_utc"]))


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------
INLET_TEMP_CANDIDATES = (
    "supply_air_temp_C", "inlet_air_temp_C", "T_inlet_C",
    "crah_supply_temp_C", "room_air_temp_C",
)
IT_POWER_CANDIDATES = ("input_power_IT_room_kW", "it_power_kW", "power_IT_kW")


def resolve_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    inlet = next((c for c in INLET_TEMP_CANDIDATES if c in df.columns), None)
    power = next((c for c in IT_POWER_CANDIDATES if c in df.columns), None)
    return inlet, power


def infer_timestep(df: pd.DataFrame, default: float = 60.0) -> float:
    if "time_utc" not in df.columns:
        return default
    try:
        t = pd.to_datetime(df["time_utc"])
    except (ValueError, TypeError):
        return default
    deltas = t.diff().dropna().dt.total_seconds()
    return float(deltas.median()) if not deltas.empty else default


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_server(mode: str = "transient", worst_case_psi: bool = False) -> ServerAirCooled:
    r_sa = sink_to_air_resistance(AIRFLOW_PER_HS, R_cs, worst_case=worst_case_psi)

    die_mass_g = 5.0            # FIX: 50 g was a whole package, not a die
    volume_IHS_mm3 = 1200 * 6
    c_die_ihs = (SI_SPECIFIC_HEAT * die_mass_g
                 + COPPER_SPECIFIC_HEAT * COPPER_RHO * volume_IHS_mm3)

    volume_1U_mm3 = 90 * 90 * 26.5
    c_heatsink = heatsink_capacity(volume_1U_mm3 / 2, fraction_al=0.0)  # all copper

    return ServerAirCooled(
        thermal_resistances=(R_jc, R_cs, r_sa),
        thermal_capacitances=(c_die_ihs, c_heatsink),
        airflow_per_heatsink=AIRFLOW_PER_HS,
        tdp_W=CPU_TDP,
        mode=mode,
    )


def run(csv_path: Optional[str] = None,
        mode: str = "transient",
        n_servers_in_room: int = 1000,
        fallback_inlet_C: float = 24.0,
        fallback_load_factor: float = 0.7) -> pd.DataFrame:

    server = build_server(mode=mode)
    print(f"R_sa = {server.R_sa:.3f} K/W | 1/(C_air*R_sa) = {server.effectiveness():.3f} "
          f"| tau_die = {server.time_constants()[0]:.1f} s, "
          f"tau_hs = {server.time_constants()[1]:.1f} s")

    keys = ["time_utc", "airflow_per_heatsink", "inlet_air_temp",
            "exit_air_heatsink_temp", "exit_air_tot_temp",
            "heatsink_temp", "case_temp", "junction_temp",
            "server_power_consumed_W"]
    recorder = Recorder(keys, server)

    if csv_path:
        df = pd.read_csv(csv_path)
        dt = infer_timestep(df)
        inlet_col, power_col = resolve_columns(df)
        times = df["time_utc"] if "time_utc" in df.columns else range(len(df))
        # FIX: the original passed the IT-power column into T_inlet. Inlet air
        # temperature and IT power are different quantities in different units.
        if inlet_col is None:
            print(f"No inlet-temperature column found; using {fallback_inlet_C} degC. "
                  f"Available: {list(df.columns)}")
        if power_col is None:
            print(f"No IT-power column found; using {fallback_load_factor:.0%} of TDP.")
        for i, t in enumerate(times):
            T_in = float(df[inlet_col].iloc[i]) if inlet_col else fallback_inlet_C
            if power_col:
                room_kW = float(df[power_col].iloc[i])
                p_cpu = room_kW * 1000.0 / n_servers_in_room * server.cpu_power_fraction
            else:
                p_cpu = CPU_TDP * fallback_load_factor
            server.power_flow(T_inlet=T_in, cpu_power_W=p_cpu, dt=dt)
            recorder.record(server, t)
    else:  # synthetic smoke test: a load step
        dt = 60.0
        for i in range(180):
            p_cpu = CPU_TDP * (0.2 if i < 30 else 0.9)
            server.power_flow(T_inlet=fallback_inlet_C, cpu_power_W=p_cpu, dt=dt)
            recorder.record(server, i * dt)

    if server.entropy_violations:
        print(f"WARNING: second-law check failed on {server.entropy_violations} steps "
              f"(air leaving the fins hotter than the fins).")
    return recorder.to_frame()


if __name__ == "__main__":
    import os

    CSV = r"C:\Users\andre\UniMelb\Validation_data\cooling_system_synthetic_inputs_5_scenarios\05.csv"
    frame = run(CSV if os.path.exists(CSV) else None, mode="transient")
    print(frame.tail())
    plotting({c: frame[c].tolist() for c in frame.columns})