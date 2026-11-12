from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Iterable


MSUN_IN_G = 1.9892e33
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
SECTION2_DIR = BRONZE_DIR / "apj522871section2" / "progenitor_models"
SECTION3_DIR = BRONZE_DIR / "apj522871section3" / "explosion_results_PHOTB"
SECTION6_DIR = BRONZE_DIR / "apj522871section6" / "nucleosynthesis_yields"

PROGENITOR_FEATURES_PATH = SILVER_DIR / "progenitor_features.csv"
ENGINE_OUTCOMES_PATH = SILVER_DIR / "engine_outcomes.csv"
AUXILIARY_YIELDS_PATH = SILVER_DIR / "auxiliary_yields.csv"

# The 12.25-13.0 M_sun pre-supernova profiles use the "s" prefix, while the
# explosion results identify the same Woosley & Heger (2015) models with "w".
OUTCOME_MODEL_ALIASES = {
    "w12.25": "s12.25",
    "w12.5": "s12.5",
    "w12.75": "s12.75",
    "w13.0": "s13.0",
}

MASS_TARGETS = [1.5, 2.0, 2.5, 3.0, 4.0]
SELECTED_YIELD_ISOTOPES = [
    "h1",
    "he4",
    "c12",
    "n14",
    "o16",
    "ne20",
    "mg24",
    "si28",
    "s32",
    "ar36",
    "ca40",
    "ti44",
    "fe54",
    "fe56",
    "ni56",
]


def parse_float(value: str) -> float | None:
    value = value.strip()
    if not value or value == "---":
        return None
    return float(value)


def split_columns(line: str) -> list[str]:
    # The source tables use groups of spaces to separate fields.
    return re.split(r"\s{2,}", line.strip())


def read_text_lossy(path: Path) -> str:
    return path.read_text(encoding="latin-1", errors="ignore")


def model_mass_from_name(model_name: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)", model_name)
    if not match:
        raise ValueError(f"Could not extract the initial mass from {model_name}")
    return float(match.group(1))


def safe_log10(value: float | None) -> float | None:
    if value is None or value <= 0:
        return None
    return math.log10(value)


def format_value(value: object) -> object:
    if isinstance(value, float):
        if math.isfinite(value):
            return round(value, 8)
        return None
    return value


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return

    preferred = [
        "model",
        "progenitor_family",
        "zams_mass_msun",
        "engine",
        "result_model_name",
        "outcome",
        "label_ns_vs_bh",
    ]
    all_fields = set()
    for row in rows:
        all_fields.update(row.keys())
    ordered = [field for field in preferred if field in all_fields]
    ordered.extend(sorted(all_fields - set(ordered)))

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(row.get(key)) for key in ordered})


def nearest_zone(rows: list[dict], target_mass_msun: float) -> dict | None:
    for row in rows:
        if row["mass_msun"] >= target_mass_msun:
            return row
    return None


def outermost_mass_where(rows: Iterable[dict], predicate) -> float | None:
    candidate = None
    for row in rows:
        if predicate(row):
            candidate = row["mass_msun"]
    return candidate


def parse_presn_file(path: Path) -> dict:
    lines = read_text_lossy(path).splitlines()
    header_line = next(line for line in lines if line.strip().startswith("grid"))
    header_columns = split_columns(header_line)
    isotope_names = header_columns[14:]

    # Keep only the numbered stellar zones, from the center outwards.
    rows = []
    for line in lines:
        if not re.match(r"\s*\d+:", line):
            continue

        row_text = re.sub(r"^\s*\d+:\s*", "", line)
        tokens = split_columns(row_text)
        if len(tokens) != 13 + len(isotope_names):
            continue

        numeric = [parse_float(token) for token in tokens[:11]]
        abundances = {
            isotope_names[index]: parse_float(tokens[13 + index]) or 0.0
            for index in range(len(isotope_names))
        }
        rows.append(
            {
                "mass_msun": (numeric[0] or 0.0) / MSUN_IN_G,
                "radius_cm": numeric[1],
                "velocity_cm_s": numeric[2],
                "density_g_cm3": numeric[3],
                "temperature_k": numeric[4],
                "pressure": numeric[5],
                "specific_energy": numeric[6],
                "entropy": numeric[7],
                "angular_velocity": numeric[8],
                "a_bar": numeric[9],
                "y_e": numeric[10],
                "stability": tokens[11],
                "network": tokens[12],
                "abundances": abundances,
            }
        )

    if not rows:
        raise ValueError(f"Could not parse stellar zones from {path}")

    first = rows[0]
    last = rows[-1]
    model_name = path.name.replace("_presn", "")

    features = {
        "model": model_name,
        "progenitor_family": model_name[0],
        "zams_mass_msun": model_mass_from_name(model_name),
        "final_mass_msun": last["mass_msun"],
        "zone_count": len(rows),
        "central_density_g_cm3": first["density_g_cm3"],
        "central_log10_density": safe_log10(first["density_g_cm3"]),
        "central_temperature_k": first["temperature_k"],
        "central_log10_temperature": safe_log10(first["temperature_k"]),
        "central_entropy": first["entropy"],
        "central_y_e": first["y_e"],
        "central_a_bar": first["a_bar"],
        "surface_radius_cm": last["radius_cm"],
        "surface_log10_radius": safe_log10(last["radius_cm"]),
        "surface_density_g_cm3": last["density_g_cm3"],
        "surface_temperature_k": last["temperature_k"],
        "surface_h1": last["abundances"].get("H1", 0.0),
        "surface_he4": last["abundances"].get("He4", 0.0),
        "surface_c12": last["abundances"].get("C12", 0.0),
        "surface_o16": last["abundances"].get("O16", 0.0),
        "surface_fe56": last["abundances"].get("Fe56", 0.0),
        "helium_core_mass_msun": outermost_mass_where(
            rows, lambda row: row["abundances"].get("H1", 0.0) <= 0.1
        ),
        "co_core_mass_msun": outermost_mass_where(
            rows,
            lambda row: row["abundances"].get("He4", 0.0) <= 0.1
            and (row["abundances"].get("C12", 0.0) + row["abundances"].get("O16", 0.0)) >= 0.5,
        ),
        "oxygen_rich_mass_msun": outermost_mass_where(
            rows, lambda row: row["abundances"].get("O16", 0.0) >= 0.5
        ),
        "silicon_rich_mass_msun": outermost_mass_where(
            rows,
            lambda row: (
                row["abundances"].get("Si28", 0.0)
                + row["abundances"].get("S32", 0.0)
                + row["abundances"].get("Ar36", 0.0)
                + row["abundances"].get("Ca40", 0.0)
            )
            >= 0.5,
        ),
        "iron_core_mass_msun": outermost_mass_where(
            rows,
            lambda row: (
                row["abundances"].get("Fe54", 0.0)
                + row["abundances"].get("Ni56", 0.0)
                + row["abundances"].get("Fe56", 0.0)
                + row["abundances"].get("'Fe'", 0.0)
            )
            >= 0.5,
        ),
    }

    # Sample each profile at fixed enclosed masses for comparable features.
    for target in MASS_TARGETS:
        zone = nearest_zone(rows, target)
        suffix = str(target).replace(".", "p")
        if zone is None or not zone["radius_cm"]:
            features[f"radius_at_{suffix}_msun_cm"] = None
            features[f"xi_{suffix}"] = None
            features[f"entropy_at_{suffix}_msun"] = None
            features[f"ye_at_{suffix}_msun"] = None
            features[f"log10_density_at_{suffix}_msun"] = None
            continue

        features[f"radius_at_{suffix}_msun_cm"] = zone["radius_cm"]
        features[f"xi_{suffix}"] = target / (zone["radius_cm"] / 1.0e8)
        features[f"entropy_at_{suffix}_msun"] = zone["entropy"]
        features[f"ye_at_{suffix}_msun"] = zone["y_e"]
        features[f"log10_density_at_{suffix}_msun"] = safe_log10(zone["density_g_cm3"])

    return features


def parse_outcome_file(path: Path) -> list[dict]:
    engine = path.name.replace("results_", "").replace(".txt", "")
    lines = read_text_lossy(path).splitlines()
    blocks = []
    current = []

    # Each model starts a block that contains its explosion results.
    for line in lines:
        if re.match(r"^[a-z]\d+(?:\.\d+)? \(", line.strip()):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)

    if current:
        blocks.append(current)

    records = []
    for block in blocks:
        text = "\n".join(block)
        first_line = block[0].strip()
        result_model_name = first_line.split()[0]
        model_name = OUTCOME_MODEL_ALIASES.get(result_model_name, result_model_name)
        e_exp_match = re.search(r"E_exp\s*=\s*([0-9.E+-]+)", text)
        e_exp = float(e_exp_match.group(1)) if e_exp_match else None
        # Implosions have no positive explosion energy in these source files.
        is_black_hole = e_exp is None or e_exp <= 0.0

        def extract(name: str) -> float | None:
            match = re.search(rf"{re.escape(name)}\s*=\s*([0-9.E+-]+)", text)
            return float(match.group(1)) if match else None

        records.append(
            {
                "engine": engine,
                "result_model_name": result_model_name,
                "model": model_name,
                "progenitor_family": model_name[0],
                "zams_mass_msun": model_mass_from_name(model_name),
                "e_exp_foe": e_exp,
                "m_mass_cut_after_fb_msun": extract("M_mass_cut_after_fb"),
                "m_fallback_msun": extract("M_fallback"),
                "m_special_msun": extract("M_special"),
                "m_outside_ni_fb_msun": extract("M_outside(Ni)"),
                "m_outside_tr_fb_msun": extract("M_outside(Tr)"),
                "m_outside_alpha_fb_msun": extract("M_outside(alpha)"),
                "outcome": "BH" if is_black_hole else "NS",
                "label_ns_vs_bh": 1 if is_black_hole else 0,
            }
        )

    return records


def parse_yield_file(path: Path, engine: str) -> dict:
    model_name = path.name
    for suffix in [".yield_table.txt", ".yield_table", ".full_zonal.yield"]:
        if model_name.endswith(suffix):
            model_name = model_name[: -len(suffix)]
            break

    lines = [line.rstrip() for line in read_text_lossy(path).splitlines() if line.strip()]
    header = lines[0].lower()
    # Some tables contain wind yields only, without an ejecta column.
    has_ejecta = "[ejecta]" in header

    isotope_rows = []
    for line in lines[1:]:
        tokens = line.split()
        if not tokens:
            continue
        if has_ejecta and len(tokens) >= 3:
            isotope, ejecta, wind = tokens[0], float(tokens[1]), float(tokens[2])
        elif len(tokens) >= 2:
            isotope, ejecta, wind = tokens[0], 0.0, float(tokens[1])
        else:
            continue
        isotope_rows.append((isotope.lower(), ejecta, wind))

    record = {
        "engine": engine,
        "model": model_name,
        "progenitor_family": model_name[0],
        "zams_mass_msun": model_mass_from_name(model_name),
        "yield_file_type": "full_zonal_sample" if path.name.endswith(".full_zonal.yield") else "yield_table",
        "yield_has_ejecta": int(has_ejecta),
        "yield_total_ejecta_msun": sum(ejecta for _, ejecta, _ in isotope_rows),
        "yield_total_wind_msun": sum(wind for _, _, wind in isotope_rows),
        "yield_total_msun": sum(ejecta + wind for _, ejecta, wind in isotope_rows),
    }

    isotope_map = {isotope: (ejecta, wind) for isotope, ejecta, wind in isotope_rows}
    for isotope in SELECTED_YIELD_ISOTOPES:
        ejecta, wind = isotope_map.get(isotope, (0.0, 0.0))
        record[f"yield_{isotope}_ejecta_msun"] = ejecta
        record[f"yield_{isotope}_wind_msun"] = wind
        record[f"yield_{isotope}_total_msun"] = ejecta + wind

    return record


def load_progenitor_features() -> list[dict]:
    return sorted(
        (parse_presn_file(path) for path in SECTION2_DIR.glob("*_presn")),
        key=lambda row: row["zams_mass_msun"],
    )


def load_outcomes() -> list[dict]:
    outcome_files = sorted(SECTION3_DIR.glob("results_*"))
    rows = []
    for path in outcome_files:
        rows.extend(parse_outcome_file(path))
    return sorted(rows, key=lambda row: (row["engine"], row["zams_mass_msun"]))


def load_yields() -> list[dict]:
    rows = []
    for directory in sorted(path for path in SECTION6_DIR.iterdir() if path.is_dir()):
        # The full zonal files are examples, not one yield table per model.
        if directory.name == "sample_full_zonal_yields":
            continue

        engine = directory.name.replace("implosions_", "")
        for path in sorted(directory.iterdir()):
            is_valid_yield = path.is_file() and (
                path.name.endswith(".yield_table")
                or path.name.endswith(".yield_table.txt")
            )
            if is_valid_yield:
                rows.append(parse_yield_file(path, engine=engine))
    return sorted(rows, key=lambda row: (row["engine"], row["zams_mass_msun"], row["model"]))


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    progenitor_features = load_progenitor_features()
    outcomes = load_outcomes()
    yields_rows = load_yields()

    write_csv(PROGENITOR_FEATURES_PATH, progenitor_features)
    write_csv(ENGINE_OUTCOMES_PATH, outcomes)
    write_csv(AUXILIARY_YIELDS_PATH, yields_rows)

    print("Silver files generated in:", SILVER_DIR)
    print(f"- progenitors: {len(progenitor_features)}")
    print(f"- outcomes: {len(outcomes)}")
    print(f"- yields: {len(yields_rows)}")
    for engine in sorted({row["engine"] for row in outcomes}):
        rows = [row for row in outcomes if row["engine"] == engine]
        bh_count = sum(row["label_ns_vs_bh"] for row in rows)
        print(f"- outcomes {engine}: {len(rows)} rows, {bh_count} BH, {len(rows) - bh_count} NS")


if __name__ == "__main__":
    main()
