"""Exoplanet data preparation and quiz scoring."""

import os
from functools import lru_cache

import numpy as np
import pandas as pd
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

from sort import GroupPreference, score_by_groups
from utils import percentile_edges, percentile_labels

POINTS = 10
TOP_N = 20
MIN_COVERAGE = 0.7
SEED = None
FALLOFF = 0.0
REACH = 0
MIDDLE_WEIGHT = 1.0

QUESTIONS = {
    "temperature": "How hot do you like it? (1 = frozen, 5 = scorching)",
    "size": "How big a planet do you want? (1 = tiny, 5 = huge)",
    "mass": "How heavy a planet? (1 = very light, 5 = very heavy)",
    "gravity": "How strong should gravity be? (1 = floaty, 5 = crushing)",
    "brightness": "How bright should the sunlight be? (1 = dim, 5 = blinding)",
    "distance": "How far from Earth? (1 = right next door, 5 = very far)",
    "star_age": "How old should its star be? (1 = newborn, 5 = ancient)",
    "metallicity": "How metal-rich a star system? (1 = metal-poor, 5 = metal-rich)",
    "neighbors": "How many neighboring planets? (1 = none, 5 = a crowded system)",
    "solidity": "What should the planet be made of? (1 = gassy, 5 = solid rock)",
}

ARCHIVE_COLUMNS = [
    "pl_name", "sy_dist", "sy_pnum", "st_lum", "st_teff", "st_rad",
    "pl_eqt", "pl_rade", "pl_bmasse", "pl_dens", "pl_insol", "pl_orbsmax",
    "ra", "dec",
]

CACHE_FILE = "planets_cache.csv"   # delete this file to download fresh archive data


def _sigmoid(value):
    return 1 / (1 + np.exp(-value))


def _logit(probability):
    probability = np.clip(probability, 0.02, 0.98)
    return np.log(probability / (1 - probability))


def _solid_score(df):
    radius = df["pl_rade"]
    mass = df["pl_bmasse"]
    density = df["pl_dens"]

    clues = pd.concat(
        [
            _sigmoid(-(radius - 1.7) / 0.2),
            _sigmoid((density - 2.5) / 0.6),
            _sigmoid(-(np.log10(mass) - np.log10(6.0)) / 0.25),
        ],
        axis=1,
    )
    weights = np.array([1.0, 1.5, 0.5])
    mask = clues.notna()
    weighted_sum = (_logit(clues).fillna(0) * weights).sum(axis=1)
    weight_total = (mask * weights).sum(axis=1)
    return _sigmoid(weighted_sum / weight_total.replace(0, np.nan))


def _equilibrium_temperature(row, albedo=0.3):
    if (
        pd.notna(row["st_teff"])
        and pd.notna(row["st_rad"])
        and pd.notna(row["pl_orbsmax"])
        and row["pl_orbsmax"] > 0
    ):
        return row["st_teff"] * (1 - albedo) ** 0.25 * np.sqrt(
            row["st_rad"] * 0.00465047 / (2 * row["pl_orbsmax"])
        )
    return row["pl_eqt"]


def _estimate_surface_temperature(row):
    equilibrium_temperature = _equilibrium_temperature(row)
    if pd.isna(equilibrium_temperature):
        return np.nan
    if pd.notna(row["pl_insol"]) and row["pl_insol"] > 10:
        return equilibrium_temperature

    mass = row["pl_bmasse"]
    optical_depth = 0.0 if pd.notna(mass) and mass < 0.2 else 0.5
    return equilibrium_temperature * (1 + 0.75 * optical_depth) ** 0.25


def build_planet_table(df):
    """Derive the numeric columns consumed by the quiz from archive records."""
    data = df.copy()
    data["surface_temp_k"] = data.apply(_estimate_surface_temperature, axis=1)
    data["surface_temp_c"] = data["surface_temp_k"] - 273.15
    data["solid_score"] = _solid_score(data)

    flux = data["pl_insol"].copy()
    luminosity = 10 ** data["st_lum"]
    flux = flux.fillna(luminosity / data["pl_orbsmax"] ** 2)
    luminosity_from_star = data["st_rad"] ** 2 * (data["st_teff"] / 5772) ** 4
    flux = flux.fillna(luminosity_from_star / data["pl_orbsmax"] ** 2)

    return pd.DataFrame(
        {
            "planet": data["pl_name"],
            "temperature": data["surface_temp_c"],
            "size": data["pl_rade"],
            "mass": data["pl_bmasse"],
            "gravity": data["pl_bmasse"] / data["pl_rade"] ** 2,
            "brightness": flux,
            "distance": data["sy_dist"],
            "star_age": data["st_age"],
            "metallicity": data["st_met"],
            "neighbors": data["sy_pnum"] - 1,
            "solidity": data["solid_score"],
            "ra_deg": data["ra"],
            "dec_deg": data["dec"],
            "distance_pc": data["sy_dist"],
        },
        index=data.index,
    ).replace([np.inf, -np.inf], np.nan)


@lru_cache(maxsize=1)
def load_planet_table():
    """Load archive data once per process (from a local cache file if present)."""
    if os.path.exists(CACHE_FILE):
        raw = pd.read_csv(CACHE_FILE)
    else:
        # dict.fromkeys removes duplicates; pl_dens is already in ARCHIVE_COLUMNS
        columns = list(dict.fromkeys(ARCHIVE_COLUMNS + ["st_age", "st_met", "pl_dens"]))
        planets = NasaExoplanetArchive.query_criteria(table="pscomppars", select=",".join(columns))
        raw = planets.to_pandas()
        raw.to_csv(CACHE_FILE, index=False)
    return build_planet_table(raw)


def pick_planet(answers, table, rng=None):
    """Score the answers and randomly pick from the top-scoring planets."""
    if set(answers) != set(QUESTIONS):
        raise ValueError("Answer every quiz question before submitting.")
    if any(type(pick) is not int or pick not in range(1, 6) for pick in answers.values()):
        raise ValueError("Answers must be integers from 1 to 5.")

    preferences = [
        GroupPreference(
            column,
            selected=(pick - 1,),
            weight=POINTS,
            falloff=FALLOFF,
            reach=REACH,
            middle_weight=MIDDLE_WEIGHT,
            label=column,
        )
        for column, pick in answers.items()
    ]
    scored = score_by_groups(
        table, preferences, name_col="planet", min_coverage=MIN_COVERAGE
    )
    if scored.empty:
        return None

    rng = rng or np.random.default_rng(SEED)
    pool = (
        scored.sample(frac=1, random_state=rng)
        .sort_values("score", ascending=False, kind="stable")
        .head(TOP_N)
    )
    return pool.sample(1, random_state=rng).iloc[0]


def get_match_details(answers, winner, table):
    """Describe the winning planet's data for each selected quiz answer."""
    details = []
    for column, pick in answers.items():
        value = table.loc[winner.name, column]
        if pd.isna(value):
            details.append({"question": column, "pick": pick, "value": None, "matches": False})
            continue

        try:
            group = percentile_labels(table[column]).loc[winner.name]
            edges = percentile_edges(table, column)
            low, high = edges[pick - 1], edges[pick]
        except ValueError:
            group = np.nan
            low = high = np.nan

        details.append(
            {
                "question": column,
                "pick": pick,
                "value": float(value),
                "matches": pd.notna(group) and int(group) == pick - 1,
                "range": (float(low), float(high)) if pd.notna(low) else None,
            }
        )
    return details


# label, format, and a multiplier applied to the stored value before it is shown
PLANET_VALUE_DISPLAY = {
    "temperature": ("Temperature", "{:.0f} °C", 1),
    "size": ("Size", "{:.2f} × Earth's radius", 1),
    "mass": ("Mass", "{:.2f} × Earth's mass", 1),
    "gravity": ("Gravity", "{:.2f} × Earth's gravity", 1),
    "brightness": ("Starlight", "{:.2f} × the sunlight Earth receives", 1),
    "distance": ("Distance from Earth", "{:,.1f} light-years", 3.26156),   # stored in parsecs
    "star_age": ("Star age", "{:.2f} billion years", 1),
    "metallicity": ("Star metallicity", "{:+.2f} (the Sun is 0)", 1),
    "neighbors": ("Neighboring planets", "{:.0f}", 1),
    "solidity": ("Solid-surface score", "{:.0f} / 100", 100),
}


def get_planet_values(winner, table):
    """The winning planet's own values, formatted for display (no match details)."""
    row = table.loc[winner.name]
    values = []
    for column, (label, template, scale) in PLANET_VALUE_DISPLAY.items():
        value = row[column]
        text = "no data for this planet" if pd.isna(value) else template.format(value * scale)
        values.append({"label": label, "text": text})
    return values


def get_galactic_position(winner, table):
    """Estimate a system's Milky Way position from its sky coordinates and distance."""
    row = table.loc[winner.name]
    required = ("ra_deg", "dec_deg", "distance_pc")
    if any(column not in row or pd.isna(row[column]) for column in required):
        return None

    ra_deg, dec_deg, distance_pc = (float(row[column]) for column in required)
    if not np.isfinite([ra_deg, dec_deg, distance_pc]).all() or distance_pc < 0:
        return None

    ra, dec = np.radians([ra_deg, dec_deg])
    equatorial = np.array(
        [np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)]
    )
    equatorial_to_galactic = np.array(
        [
            [-0.0548755604, -0.8734370902, -0.4838350155],
            [0.4941094279, -0.4448296300, 0.7469822445],
            [-0.8676661490, -0.1980763734, 0.4559837762],
        ]
    )
    galactic = equatorial_to_galactic @ equatorial
    longitude = np.arctan2(galactic[1], galactic[0]) % (2 * np.pi)
    latitude = np.arcsin(np.clip(galactic[2], -1, 1))
    distance_kpc = distance_pc / 1000
    x_kpc = -8.2 + distance_kpc * np.cos(latitude) * np.cos(longitude)
    y_kpc = distance_kpc * np.cos(latitude) * np.sin(longitude)

    # Mollweide projection for the bundled all-sky galactic-coordinate image.
    theta = latitude
    if abs(abs(latitude) - np.pi / 2) > 1e-10:
        target = np.pi * np.sin(latitude)
        for _ in range(10):
            residual = 2 * theta + np.sin(2 * theta) - target
            derivative = 2 + 2 * np.cos(2 * theta)
            if abs(derivative) < 1e-12:
                break
            theta -= residual / derivative

    map_longitude = longitude if longitude <= np.pi else longitude - 2 * np.pi
    map_x = 120 - 120 * map_longitude / np.pi * np.cos(theta)
    map_y = 60 - 60 * np.sin(theta)
    return {
        "galaxy": "Milky Way",
        "distance_pc": distance_pc,
        "longitude_deg": float(np.degrees(longitude)),
        "latitude_deg": float(np.degrees(latitude)),
        "galactocentric_distance_kpc": float(np.hypot(x_kpc, y_kpc)),
        "map_x": float(np.clip(map_x, 4, 236)),
        "map_y": float(np.clip(map_y, 4, 116)),
    }
