"""
ep_chiller_parser.py

Downloads the EnergyPlus chiller performance-curve datasets (raw .idf text files
straight from the NREL/EnergyPlus GitHub repo -- no EnergyPlus install required)
and parses them into a single Python dictionary keyed by chiller name, containing:

    - manufacturer, model line, compressor type, condenser type, refrigerant
      (parsed from the comment block that precedes each chiller object)
    - reference capacity (W), reference COP (PLR=1, W/W)
    - reference leaving chilled water temp, reference entering condenser fluid temp
    - CAPFT, EIRFT (Curve:Biquadratic) and EIRFPLR (Curve:Quadratic/Cubic) coefficients
    - the valid domain (min/max x, min/max y, min/max curve output) for each curve,
      i.e. exactly what you need to clamp inputs and avoid extrapolation blow-ups
    - min/max/optimum part load ratio, condenser type, source file

Usage:
    python ep_chiller_parser.py                # downloads + parses + saves JSON
    from ep_chiller_parser import *
    db = load_or_build_database()
    matches = filter_chillers(db, capacity_kw=100, tol=0.3, compressor_type="Scroll",
                               condenser_type="AirCooled")
    cap = eval_biquadratic(matches[name]["capft"], T_evap_leaving=7.0, T_cond=32.0)
"""

import json
import os
import re
import urllib.request

DATASET_URLS = {
    "AirCooledChiller.idf": "https://raw.githubusercontent.com/NREL/EnergyPlus/develop/datasets/AirCooledChiller.idf",
    "Chillers.idf": "https://raw.githubusercontent.com/NREL/EnergyPlus/develop/datasets/Chillers.idf",
}

CACHE_DIR = "ep_chiller_cache"
DB_JSON_PATH = os.path.join(CACHE_DIR, "chiller_database.json")

CHILLER_FIELD_NAMES = [
    "name", "reference_capacity_W", "reference_cop", "ref_leaving_chw_temp_C",
    "ref_entering_cond_fluid_temp_C", "ref_chw_flow_m3s", "ref_cond_flow_m3s",
    "capft_curve_name", "eirft_curve_name", "eirfplr_curve_name",
    "min_plr", "max_plr", "optimum_plr", "min_unloading_ratio",
    "chw_inlet_node", "chw_outlet_node", "cond_inlet_node", "cond_outlet_node",
    "condenser_type", "condenser_fan_power_ratio", "frac_compressor_elec_rejected",
    "leaving_chw_lower_temp_limit_C", "chiller_flow_mode", "design_heat_recovery_flow_m3s",
]

META_RE = re.compile(
    r"!\s*Manufacturer\s*=\s*(?P<manufacturer>[^,]*),?\s*(?:Model Line\s*=\s*(?P<model_line>.*))?\n"
    r"!\s*Reference Capacity\s*=\s*(?P<ref_cap_txt>[^\n]*)\n"
    r"!\s*Compressor Type\s*=\s*(?P<compressor_type>[^,]*),?\s*(?:Condenser Type\s*=\s*(?P<condenser_type_txt>[^\n]*))?\n"
    r"(?:!\s*Refrigerant\s*=\s*(?P<refrigerant>[^\n]*)\n)?",
    re.IGNORECASE,
)


def download_datasets(cache_dir=CACHE_DIR):
    """Downloads the raw .idf dataset files if not already cached locally."""
    os.makedirs(cache_dir, exist_ok=True)
    paths = {}
    for fname, url in DATASET_URLS.items():
        local_path = os.path.join(cache_dir, fname)
        if not os.path.exists(local_path):
            print(f"Downloading {fname} ...")
            urllib.request.urlretrieve(url, local_path)
        else:
            print(f"Using cached {fname}")
        paths[fname] = local_path
    return paths


def _strip_inline_comment(line):
    """Removes a trailing '!' field-name comment from an idf line, keeping content before it."""
    idx = line.find("!")
    return line if idx == -1 else line[:idx]


def _split_top_level_object(idf_text, start_idx):
    """
    Given the full text and the index where an object keyword starts (e.g. 'Chiller:Electric:EIR,'),
    returns (field_list, end_index) where field_list are the comma-separated field values with
    per-line '!' comments stripped, and end_index is the position right after the closing ';'.
    """
    end_idx = idf_text.find(";", start_idx)
    raw_block = idf_text[start_idx:end_idx]
    cleaned_lines = [_strip_inline_comment(l) for l in raw_block.split("\n")]
    joined = " ".join(cleaned_lines)
    fields = [f.strip() for f in joined.split(",")]
    # first field is the object type itself (e.g. "Chiller:Electric:EIR"); drop it
    fields = fields[1:]
    fields = [f for f in fields if f != ""] if fields and fields[-1] == "" else fields
    return fields, end_idx + 1


def _to_float(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def parse_meta_block(preceding_text):
    """Parses the '! Manufacturer = ... / Reference Capacity = ... / Compressor Type = ...'
    comment block that precedes most chiller objects in these datasets. Returns a dict;
    missing fields are None if the block isn't present in that exact format."""
    # Only look at the tail of preceding_text (last ~6 lines) to avoid matching unrelated comments
    tail = "\n".join(preceding_text.strip("\n").split("\n")[-6:]) + "\n"
    m = META_RE.search(tail)
    if not m:
        return {
            "manufacturer": None, "model_line": None, "compressor_type": None,
            "condenser_type_meta": None, "refrigerant": None,
        }
    d = m.groupdict()
    return {
        "manufacturer": (d.get("manufacturer") or "").strip() or None,
        "model_line": (d.get("model_line") or "").strip() or None,
        "compressor_type": (d.get("compressor_type") or "").strip() or None,
        "condenser_type_meta": (d.get("condenser_type_txt") or "").strip() or None,
        "refrigerant": (d.get("refrigerant") or "").strip() or None,
    }


def parse_biquadratic_fields(fields):
    """Curve:Biquadratic field order:
    Name, C1..C6, min_x, max_x, min_y, max_y, [min_out, max_out], [in_unit_x, in_unit_y, out_unit]"""
    f = fields + [None] * 16
    return {
        "name": f[0],
        "coeffs": [_to_float(f[i]) for i in range(1, 7)],  # C1..C6
        "min_x": _to_float(f[7]), "max_x": _to_float(f[8]),
        "min_y": _to_float(f[9]), "max_y": _to_float(f[10]),
        "min_output": _to_float(f[11]), "max_output": _to_float(f[12]),
    }


def parse_quadratic_or_cubic_fields(fields, cubic=False):
    """Curve:Quadratic field order: Name, C1, C2, C3, min_x, max_x, [min_out, max_out]
    Curve:Cubic field order:      Name, C1, C2, C3, C4, min_x, max_x, [min_out, max_out]"""
    n_coeffs = 4 if cubic else 3
    f = fields + [None] * 10
    return {
        "name": f[0],
        "coeffs": [_to_float(f[i]) for i in range(1, 1 + n_coeffs)],
        "min_x": _to_float(f[1 + n_coeffs]), "max_x": _to_float(f[2 + n_coeffs]),
        "min_output": _to_float(f[3 + n_coeffs]), "max_output": _to_float(f[4 + n_coeffs]),
    }


HEADER_TABLE_RE = re.compile(
    r"^!\s*(?P<name>ElectricEIRChiller.+?)\s{2,}"
    r"(?P<compressor_type>Centrifugal|Screw|Reciprocating|Scroll)\s+"
    r"(?P<cap_kw>[\d.]+)\s*\((?P<tons>[\d.]+)\)\s+"
    r"(?P<cop>[\d.]+)\s*(?P<control>.*?)\s*$",
    re.MULTILINE,
)


def parse_header_summary_table(text):
    """Chillers.idf (water-cooled dataset) documents compressor type / capacity / COP /
    control type (Inlet Vanes vs VSD) in one big comment table near the top of the file
    instead of a per-object comment block. This parses that table into name -> metadata."""
    out = {}
    for m in HEADER_TABLE_RE.finditer(text):
        d = m.groupdict()
        out[d["name"].strip()] = {
            "compressor_type": d["compressor_type"],
            "capacity_control": d["control"].strip() or None,  # e.g. "Inlet Vanes" or "VSD"
        }
    return out


def parse_idf_file(idf_path, source_label):
    """Parses one dataset .idf file and returns dict[chiller_name] = full record."""
    text = open(idf_path, encoding="latin-1").read()
    header_meta = parse_header_summary_table(text)

    # --- Pass 1: collect every Curve:Biquadratic / Curve:Quadratic / Curve:Cubic by name ---
    curves = {}
    for keyword, kind in [("Curve:Biquadratic,", "biquadratic"),
                           ("Curve:Quadratic,", "quadratic"),
                           ("Curve:Cubic,", "cubic")]:
        pos = 0
        while True:
            idx = text.find(keyword, pos)
            if idx == -1:
                break
            fields, end_idx = _split_top_level_object(text, idx)
            if kind == "biquadratic":
                parsed = parse_biquadratic_fields(fields)
            else:
                parsed = parse_quadratic_or_cubic_fields(fields, cubic=(kind == "cubic"))
            parsed["curve_type"] = kind
            curves[parsed["name"]] = parsed
            pos = end_idx

    # --- Pass 2: collect every Chiller:Electric:EIR object + its preceding meta comment ---
    chillers = {}
    keyword = "Chiller:Electric:EIR,"
    pos = 0
    while True:
        idx = text.find(keyword, pos)
        if idx == -1:
            break
        preceding_text = text[max(0, idx - 700):idx]
        meta = parse_meta_block(preceding_text)

        fields, end_idx = _split_top_level_object(text, idx)
        rec = dict(zip(CHILLER_FIELD_NAMES, fields))

        rec["reference_capacity_W"] = _to_float(rec.get("reference_capacity_W"))
        rec["reference_cop"] = _to_float(rec.get("reference_cop"))
        rec["ref_leaving_chw_temp_C"] = _to_float(rec.get("ref_leaving_chw_temp_C"))
        rec["ref_entering_cond_fluid_temp_C"] = _to_float(rec.get("ref_entering_cond_fluid_temp_C"))
        rec["min_plr"] = _to_float(rec.get("min_plr"))
        rec["max_plr"] = _to_float(rec.get("max_plr"))
        rec["optimum_plr"] = _to_float(rec.get("optimum_plr"))
        rec["min_unloading_ratio"] = _to_float(rec.get("min_unloading_ratio"))
        rec["leaving_chw_lower_temp_limit_C"] = _to_float(rec.get("leaving_chw_lower_temp_limit_C"))

        rec["manufacturer"] = meta["manufacturer"]
        rec["model_line"] = meta["model_line"]
        rec["compressor_type"] = meta["compressor_type"]
        rec["refrigerant"] = meta["refrigerant"]
        # prefer the explicit IDF field for condenser type, fall back to the comment block
        if not rec.get("condenser_type"):
            rec["condenser_type"] = meta["condenser_type_meta"]

        # fall back to the file's header summary table (used by Chillers.idf) if the
        # per-object comment block didn't give us a compressor type
        hmeta = header_meta.get(rec["name"])
        if hmeta:
            if not rec.get("compressor_type"):
                rec["compressor_type"] = hmeta.get("compressor_type")
            rec["capacity_control"] = hmeta.get("capacity_control")  # "Inlet Vanes" / "VSD" / None
        else:
            rec.setdefault("capacity_control", None)

        rec["capft"] = curves.get(rec.get("capft_curve_name"))
        rec["eirft"] = curves.get(rec.get("eirft_curve_name"))
        rec["eirfplr"] = curves.get(rec.get("eirfplr_curve_name"))

        rec["source_file"] = source_label
        rec["reference_capacity_kW"] = (
            rec["reference_capacity_W"] / 1000.0 if rec["reference_capacity_W"] else None
        )

        chillers[rec["name"]] = rec
        pos = end_idx

    return chillers


def build_database(cache_dir=CACHE_DIR, save_json=True):
    paths = download_datasets(cache_dir)
    db = {}
    db.update(parse_idf_file(paths["AirCooledChiller.idf"], "AirCooledChiller.idf"))
    db.update(parse_idf_file(paths["Chillers.idf"], "Chillers.idf"))
    if save_json:
        with open(DB_JSON_PATH, "w") as f:
            json.dump(db, f, indent=2)
        print(f"Saved {len(db)} chillers to {DB_JSON_PATH}")
    return db


def load_or_build_database(cache_dir=CACHE_DIR, force_rebuild=False):
    db_path = os.path.join(cache_dir, "chiller_database.json")
    if os.path.exists(db_path) and not force_rebuild:
        with open(db_path) as f:
            return json.load(f)
    return build_database(cache_dir)


def filter_chillers(db, capacity_kw=None, tol=0.3, compressor_type=None, condenser_type=None):
    """Filter the database by target capacity (+/- tol fraction), compressor type
    ('Scroll'/'Screw'/'Centrifugal'/'Reciprocating'), and condenser type ('AirCooled'/'WaterCooled')."""
    out = {}
    for name, rec in db.items():
        if capacity_kw is not None:
            cap = rec.get("reference_capacity_kW")
            if cap is None or abs(cap - capacity_kw) / capacity_kw > tol:
                continue
        if compressor_type is not None:
            ct = (rec.get("compressor_type") or "")
            if compressor_type.lower() not in ct.lower():
                continue
        if condenser_type is not None:
            cdt = (rec.get("condenser_type") or "")
            if condenser_type.lower() not in cdt.lower().replace(" ", "").replace("-", ""):
                continue
        out[name] = rec
    return out


def eval_biquadratic(curve, x, y, clamp=True):
    """Evaluates a Curve:Biquadratic: C1 + C2*x + C3*x^2 + C4*y + C5*y^2 + C6*x*y
    x, y are clamped to the curve's valid domain by default (recommended -- see min/max fields)."""
    if clamp:
        x = min(max(x, curve["min_x"]), curve["max_x"])
        y = min(max(y, curve["min_y"]), curve["max_y"])
    c1, c2, c3, c4, c5, c6 = curve["coeffs"]
    val = c1 + c2 * x + c3 * x**2 + c4 * y + c5 * y**2 + c6 * x * y
    if curve.get("min_output") is not None:
        val = max(val, curve["min_output"])
    if curve.get("max_output") is not None:
        val = min(val, curve["max_output"])
    return val


def eval_quadratic_or_cubic(curve, x, clamp=True):
    """Evaluates Curve:Quadratic (C1+C2x+C3x^2) or Curve:Cubic (+C4x^3), clamped to its valid x range."""
    if clamp:
        x = min(max(x, curve["min_x"]), curve["max_x"])
    coeffs = curve["coeffs"]
    val = sum(c * x**i for i, c in enumerate(coeffs))
    if curve.get("min_output") is not None:
        val = max(val, curve["min_output"])
    if curve.get("max_output") is not None:
        val = min(val, curve["max_output"])
    return val


if __name__ == "__main__":
    db = build_database()
    print(f"\nTotal chillers parsed: {len(db)}")
    name0 = next(iter(db))
    print(f"\nExample record ('{name0}'):")
    print(json.dumps(db[name0], indent=2))
