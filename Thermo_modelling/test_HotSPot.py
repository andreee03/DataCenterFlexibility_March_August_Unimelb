"""
Minimal Python wrapper around HotSpot:
https://github.com/uvahotspot/HotSpot

Windows version.

HotSpot is a C executable, not a Python package. This script:

1. Creates a simple one-block CPU floorplan.
2. Creates a power trace.
3. Runs the compiled HotSpot executable.
4. Reads steady-state and transient temperatures.
5. Compares two ambient-temperature scenarios.
"""

from pathlib import Path
import subprocess


# ============================================================
# USER PATHS
# ============================================================

# Folder where you cloned and compiled HotSpot.
#
# Based on your Git Bash commands, this is probably:
# C:\Users\andre\HotSpot
#
HOTSPOT_DIR = Path(r"C:\Users\andre\HotSpot")

# HotSpot example directory.
# We use example1 because it contains:
#   example.config
#   example.materials
#   package.config
EXAMPLE_DIR = HOTSPOT_DIR / "examples" / "example1"

# Directory where you want your simulation input/output files.
WORK_DIR = Path(r"C:\Users\andre\UniMelb\Thermo_modelling")


# ============================================================
# HOTSPOT FILES
# ============================================================

# On Windows / MinGW, make normally produces hotspot.exe.
# The second option is kept as a fallback.
if (HOTSPOT_DIR / "hotspot.exe").exists():
    HOTSPOT_BIN = HOTSPOT_DIR / "hotspot.exe"
else:
    HOTSPOT_BIN = HOTSPOT_DIR / "hotspot"

CONFIG_FILE = EXAMPLE_DIR / "example.config"
MATERIALS_FILE = EXAMPLE_DIR / "example.materials"


# ============================================================
# INPUT / OUTPUT FILES
# ============================================================

FLOORPLAN_FILE = WORK_DIR / "cpu.flp"
POWER_TRACE_FILE = WORK_DIR / "cpu.ptrace"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_hotspot_installation():
    """
    Check that HotSpot and its required files exist before starting.
    """

    required_files = {
        "HotSpot executable": HOTSPOT_BIN,
        "HotSpot config": CONFIG_FILE,
        "HotSpot materials file": MATERIALS_FILE,
        "HotSpot example directory": EXAMPLE_DIR,
    }

    print("Checking HotSpot installation:")

    all_ok = True

    for description, path in required_files.items():
        exists = path.exists()

        print(f"  {description}:")
        print(f"    {path}")
        print(f"    Exists: {exists}")

        if not exists:
            all_ok = False

    if not all_ok:
        raise FileNotFoundError(
            "\nOne or more HotSpot files could not be found.\n"
            "Check HOTSPOT_DIR at the top of the script."
        )

    print("\nHotSpot installation found.\n")


def write_floorplan(
    path,
    name="CPU",
    width_m=0.013,
    height_m=0.013,
):
    """
    Write a simple one-block HotSpot floorplan.

    Geometry:
        width  = 13 mm
        height = 13 mm
    """

    path = Path(path)

    with path.open("w", newline="\n") as f:
        f.write("# name\twidth\theight\tleft-x\tbottom-y\n")
        f.write(
            f"{name}\t"
            f"{width_m}\t"
            f"{height_m}\t"
            f"0.0\t"
            f"0.0\n"
        )


def write_power_trace(path, block_name, watts_per_step):
    """
    Write a HotSpot power trace.

    First row:
        names of the blocks

    Following rows:
        power in Watts for each timestep
    """

    path = Path(path)

    with path.open("w", newline="\n") as f:
        f.write(block_name + "\n")

        for power_w in watts_per_step:
            f.write(f"{power_w}\n")


def read_steady_state(path):
    """
    Read the HotSpot steady-state output file.

    Returns:
        dict:
            block/node name -> temperature in Kelvin
    """

    path = Path(path)

    steady = {}

    with path.open("r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) < 2:
                continue

            name = parts[0]
            temperature_k = float(parts[1])

            steady[name] = temperature_k

    return steady


def read_transient_trace(path, block_name):
    """
    Read the transient temperature trace.

    The first row contains block names.
    Each following row contains temperatures.

    Returns the temperature history for the requested block.
    """

    path = Path(path)

    with path.open("r") as f:

        header = f.readline().split()

        if block_name not in header:
            raise RuntimeError(
                f"Block '{block_name}' was not found in "
                f"HotSpot output header:\n{header}"
            )

        block_index = header.index(block_name)

        temperatures_k = []

        for line in f:
            line = line.strip()

            if not line:
                continue

            values = line.split()

            if len(values) <= block_index:
                raise RuntimeError(
                    f"Invalid temperature trace line:\n{line}"
                )

            temperatures_k.append(
                float(values[block_index])
            )

    return temperatures_k


def run_hotspot(
    flp,
    ptrace,
    block_name,
    ambient_c,
    sampling_interval_s,
    ttrace_out,
    steady_out,
):
    """
    Run HotSpot.

    Parameters
    ----------
    ambient_c:
        Ambient/inlet air temperature in Celsius.

    sampling_interval_s:
        Duration represented by one row of the power trace.

    Returns
    -------
    steady:
        Dictionary of steady-state temperatures in Kelvin.

    transient:
        List of transient temperatures for block_name in Kelvin.
    """

    flp = Path(flp).resolve()
    ptrace = Path(ptrace).resolve()
    ttrace_out = Path(ttrace_out).resolve()
    steady_out = Path(steady_out).resolve()

    ambient_k = ambient_c + 273.15

    # We explicitly override ambient and init_temp from example.config.
    #
    # Setting init_temp = ambient means both scenarios begin from
    # their corresponding ambient temperature.
    cmd = [
        str(HOTSPOT_BIN),

        "-c",
        str(CONFIG_FILE),

        "-f",
        str(flp),

        "-p",
        str(ptrace),

        "-materials_file",
        str(MATERIALS_FILE),

        "-model_type",
        "block",

        "-sampling_intvl",
        str(sampling_interval_s),

        "-ambient",
        str(ambient_k),

        "-init_temp",
        str(ambient_k),

        "-o",
        str(ttrace_out),

        "-steady_file",
        str(steady_out),
    ]

    print("=" * 70)
    print(f"Running HotSpot with ambient = {ambient_c:.1f} °C")
    print(f"Executable: {HOTSPOT_BIN}")
    print("=" * 70)

    try:
        result = subprocess.run(
            cmd,

            # Important:
            # Run from example1 so relative files referenced by
            # example.config (e.g. package.config) can be found.
            cwd=str(EXAMPLE_DIR),

            capture_output=True,
            text=True,
        )

    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "\nWindows could not start HotSpot.\n\n"
            f"Expected executable:\n{HOTSPOT_BIN}\n\n"
            "Check that HotSpot was compiled correctly."
        ) from exc

    if result.returncode != 0:

        raise RuntimeError(
            "\nHotSpot failed.\n\n"
            f"Command:\n{' '.join(cmd)}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    # Check that the expected files were actually created.
    if not ttrace_out.exists():
        raise RuntimeError(
            f"HotSpot finished but did not create:\n{ttrace_out}"
        )

    if not steady_out.exists():
        raise RuntimeError(
            f"HotSpot finished but did not create:\n{steady_out}"
        )

    steady = read_steady_state(steady_out)

    transient = read_transient_trace(
        ttrace_out,
        block_name,
    )

    return steady, transient


def build_workload_trace(n_steps):
    """
    Synthetic workload:

        first third:   idle  = 20 W
        middle third:  load  = 90 W
        final third:   idle  = 20 W
    """

    idle_w = 20.0
    load_w = 90.0

    third = n_steps // 3

    return (
        [idle_w] * third
        + [load_w] * (n_steps - 2 * third)
        + [idle_w] * third
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    # --------------------------------------------------------
    # Check paths
    # --------------------------------------------------------

    WORK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    check_hotspot_installation()

    # --------------------------------------------------------
    # Simulation settings
    # --------------------------------------------------------

    BLOCK = "CPU"

    N_STEPS = 120

    # 10 seconds per row
    STEP_S = 10.0

    total_time_s = N_STEPS * STEP_S
    total_time_min = total_time_s / 60.0

    print(
        f"Simulation duration: "
        f"{total_time_s:.0f} s "
        f"({total_time_min:.1f} min)"
    )

    # --------------------------------------------------------
    # Build power workload
    # --------------------------------------------------------

    watts = build_workload_trace(N_STEPS)

    # --------------------------------------------------------
    # Generate HotSpot input files
    # --------------------------------------------------------

    write_floorplan(
        FLOORPLAN_FILE,
        name=BLOCK,
        width_m=0.013,
        height_m=0.013,
    )

    write_power_trace(
        POWER_TRACE_FILE,
        BLOCK,
        watts,
    )

    print("\nCreated input files:")

    print(
        f"  Floorplan:\n"
        f"    {FLOORPLAN_FILE}"
    )

    print(
        f"  Power trace:\n"
        f"    {POWER_TRACE_FILE}"
    )

    # --------------------------------------------------------
    # Ambient temperature scenarios
    # --------------------------------------------------------

    scenarios = {
        "baseline_27C": 27.0,
        "raised_inlet_32C": 32.0,
    }

    results = {}

    # --------------------------------------------------------
    # Run simulations
    # --------------------------------------------------------

    for label, ambient_c in scenarios.items():

        transient_output = (
            WORK_DIR / f"out_{label}.ttrace"
        )

        steady_output = (
            WORK_DIR / f"steady_{label}.txt"
        )

        steady, transient = run_hotspot(
            flp=FLOORPLAN_FILE,
            ptrace=POWER_TRACE_FILE,
            block_name=BLOCK,
            ambient_c=ambient_c,
            sampling_interval_s=STEP_S,
            ttrace_out=transient_output,
            steady_out=steady_output,
        )

        if BLOCK not in steady:
            raise RuntimeError(
                f"'{BLOCK}' was not found in steady-state output.\n"
                f"Available nodes:\n{list(steady.keys())}"
            )

        if not transient:
            raise RuntimeError(
                "HotSpot returned an empty transient trace."
            )

        steady_die_k = steady[BLOCK]

        peak_die_k = max(transient)

        steady_die_c = steady_die_k - 273.15
        peak_die_c = peak_die_k - 273.15

        results[label] = {
            "ambient_C": ambient_c,
            "steady_die_K": steady_die_k,
            "transient_K": transient,
            "peak_die_K": peak_die_k,
        }

        print()
        print(f"Scenario: {label}")
        print(f"  Ambient:      {ambient_c:.2f} °C")
        print(f"  Peak CPU:     {peak_die_c:.2f} °C")
        print(f"  Steady CPU:   {steady_die_c:.2f} °C")
        print(f"  Trace points: {len(transient)}")

    # --------------------------------------------------------
    # Compare scenarios
    # --------------------------------------------------------

    baseline = results["baseline_27C"]
    raised = results["raised_inlet_32C"]

    baseline_peak_k = baseline["peak_die_K"]
    raised_peak_k = raised["peak_die_K"]

    delta_peak_k = raised_peak_k - baseline_peak_k

    baseline_steady_k = baseline["steady_die_K"]
    raised_steady_k = raised["steady_die_K"]

    delta_steady_k = (
        raised_steady_k
        - baseline_steady_k
    )

    print()
    print("=" * 70)
    print("COMPARISON")
    print("=" * 70)

    print(
        f"Ambient increase: "
        f"{raised['ambient_C'] - baseline['ambient_C']:.2f} K"
    )

    print(
        f"Peak CPU temperature increase: "
        f"{delta_peak_k:.2f} K"
    )

    print(
        f"Steady-state CPU temperature increase: "
        f"{delta_steady_k:.2f} K"
    )

    print()
    print("Output files are located in:")
    print(WORK_DIR)


if __name__ == "__main__":
    main()