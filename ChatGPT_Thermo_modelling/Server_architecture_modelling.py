### Single-server thermal resistance model
### All temperatures are in degrees Celsius.

import math
import os
import re

import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------------------
# Default values from the original thermodynamic model
# ---------------------------------------------------------------------------

ROOM_INITIAL_TEMP = 25

VOLUMIC_MASS_AIR = 1.2        # kg/m3
AIR_SPECIFIC_HEAT = 1.005     # kJ/(kg.K)
C_CFM_to_m3s = 0.472 / 1000

CPU_TDP = 95                  # W
AIRFLOW_PER_HEATSINK = 12.6 * C_CFM_to_m3s

R_jc = 0.2                    # C/W, junction to case
R_cs = 0.1                    # C/W, case to heat sink
Psi_ca_worst = 0.295          # C/W, junction-to-air reference from original model
R_sa = Psi_ca_worst - R_cs    # C/W, heat sink to inlet air


try:
    from Dataset_treatment import dataset_input
except ModuleNotFoundError:
    # Changed: Added a tiny fallback dataset so this single-server example can
    # be run directly without any external file.
    dataset_input = {
        "time_utc": list(range(24)),
        "input_power_IT_room_kW": [
            0.065 + 0.030 * (0.5 + 0.5 * math.sin(2 * math.pi * (h - 6) / 24))
            for h in range(24)
        ],
        "inlet_air_temp": [
            24 + 2 * math.sin(2 * math.pi * (h - 4) / 24)
            for h in range(24)
        ],
    }


def set_server_parameters(
    r_jc=R_jc,
    r_cs=R_cs,
    r_sa=R_sa,
    airflow_per_heatsink=AIRFLOW_PER_HEATSINK,
    tdp_W=CPU_TDP,
):
    """Wrap the default parameters for one server.

    Changed: Kept only the parameters that are useful to showcase the thermal
    resistance chain of one server.
    """
    return {
        "R_jc": r_jc,
        "R_cs": r_cs,
        "R_sa": r_sa,
        "airflow_per_heatsink": airflow_per_heatsink,
        "tdp_W": tdp_W,
    }


class ServerThermalModel:
    """One-server steady-state thermal resistance model."""

    def __init__(self, parameters=None):
        if parameters is None:
            parameters = set_server_parameters()

        self.R_jc = parameters["R_jc"]
        self.R_cs = parameters["R_cs"]
        self.R_sa = parameters["R_sa"]
        self.airflow_per_heatsink = parameters["airflow_per_heatsink"]
        self.tdp_W = parameters["tdp_W"]

        self.time_utc = 0
        self.input_power_IT_room_kW = 0
        self.server_power_consumed_W = 0
        self.inlet_air_temp = ROOM_INITIAL_TEMP

        self.heatsink_temp = ROOM_INITIAL_TEMP
        self.case_temp = ROOM_INITIAL_TEMP
        self.junction_temp = ROOM_INITIAL_TEMP
        self.exit_air_heatsink_temp = ROOM_INITIAL_TEMP
        self.entropy_violated = False

    def step(self, time_utc, input_power_IT_room_kW, inlet_air_temp, values_for_plot=None):
        """Run one time step.

        Inputs:
        - input_power_IT_room_kW: power of this one server, in kW
        - inlet_air_temp: server inlet air temperature, in C

        Outputs are stored on the object and optionally appended to a dictionary.
        """
        self.time_utc = time_utc
        self.input_power_IT_room_kW = input_power_IT_room_kW
        self.server_power_consumed_W = input_power_IT_room_kW * 1000
        self.inlet_air_temp = inlet_air_temp

        C_air_W_per_K = (
            AIR_SPECIFIC_HEAT
            * VOLUMIC_MASS_AIR
            * self.airflow_per_heatsink
            * 1000
        )

        power_W = self.server_power_consumed_W

        # Changed: Made the thermal-resistance chain explicit for readability.
        self.exit_air_heatsink_temp = self.inlet_air_temp + power_W / C_air_W_per_K
        self.heatsink_temp = self.inlet_air_temp + power_W * self.R_sa
        self.case_temp = self.heatsink_temp + power_W * self.R_cs
        self.junction_temp = self.case_temp + power_W * self.R_jc

        self.entropy_violated = self.exit_air_heatsink_temp > self.heatsink_temp
        if self.entropy_violated:
            print("Entropy broken, wrong server heat transfer at:", time_utc)

        if values_for_plot is not None:
            self.update_dict(values_for_plot)

    def run_series(self, time_utc, input_power_IT_room_kW, inlet_air_temp, values_for_plot):
        # Changed: Added a simple list-input runner for plotting time series.
        if not (len(time_utc) == len(input_power_IT_room_kW) == len(inlet_air_temp)):
            raise ValueError(
                "time_utc, input_power_IT_room_kW, and inlet_air_temp must have the same length"
            )

        for j in range(len(time_utc)):
            self.step(
                time_utc=time_utc[j],
                input_power_IT_room_kW=input_power_IT_room_kW[j],
                inlet_air_temp=inlet_air_temp[j],
                values_for_plot=values_for_plot,
            )
        return values_for_plot

    def update_dict(self, values_dict):
        for key in values_dict:
            value = getattr(self, key)
            values_dict[key].append(
                round(value, 2)
                if isinstance(value, (int, float)) and not isinstance(value, bool)
                else value
            )


def create_server_model():
    return ServerThermalModel(set_server_parameters())


def initialise_dict_for_plot(keys):
    return {key: [] for key in keys}


def plotting(values_dict):
    if os.environ.get("THERMO_SHOW_PLOTS", "0") != "1":
        # Changed: Keep plotting opt-in so command-line tests do not block.
        print("Plotting skipped. Set THERMO_SHOW_PLOTS=1 to display figures.")
        print("Number of points plotted", len(values_dict["time_utc"]))
        return

    dico_dfs = {"temp": [], "power": []}
    pat = r"(temp|power)"
    for key in values_dict:
        if key != "time_utc":
            match = re.search(pat, key)
            y_key = match.group(1) if match else "other"
            dico_dfs.setdefault(y_key, [])
            dico_dfs[y_key].append(pd.DataFrame({
                "time_utc": values_dict["time_utc"],
                y_key: values_dict[key],
                "Description": key,
            }))

    for key, frames in dico_dfs.items():
        if frames:
            df_all = pd.concat(frames, ignore_index=True)
            fig = px.line(df_all, x="time_utc", y=key, color="Description")
            fig.show()

    print("Number of points plotted", len(values_dict["time_utc"]))


if __name__ == "__main__":
    keys_to_plot = [
        "time_utc",
        "input_power_IT_room_kW",
        "server_power_consumed_W",
        "inlet_air_temp",
        "exit_air_heatsink_temp",
        "heatsink_temp",
        "case_temp",
        "junction_temp",
        "entropy_violated",
    ]

    results = initialise_dict_for_plot(keys_to_plot)
    server = create_server_model()
    server.run_series(
        time_utc=dataset_input["time_utc"],
        input_power_IT_room_kW=dataset_input["input_power_IT_room_kW"],
        inlet_air_temp=dataset_input["inlet_air_temp"],
        values_for_plot=results,
    )

    print("last_junction_temp", results["junction_temp"][-1])
    print("last_exit_air_heatsink_temp", results["exit_air_heatsink_temp"][-1])
    plotting(results)
