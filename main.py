from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sort import GroupPreference, score_by_groups          # scoring
from utils import percentile_edges, percentile_labels      # percentile groups

# temp = float(input("Enter the temperature of the planet in Celsius: "))


#Temperatur calculations

def _logit(p):
    p = np.clip(p, 0.02, 0.98)
    return np.log(p / (1 - p))



cols = ["pl_name", "hostname", "sy_dist", "sy_pnum", "sy_snum", "cb_flag",
        "st_age", "st_lum", "st_met", "st_teff", "st_rad", "st_mass",
        "pl_eqt", "pl_rade", "pl_bmasse", "pl_dens", "pl_insol",
        "pl_orbsmax", "pl_orbper"]

planets = NasaExoplanetArchive.query_criteria(table="pscomppars", select=",".join(cols))
df = planets.to_pandas()
def _sigmoid(x):
    return 1 / (1 + np.exp(-x))



def solid(df):
    r = df["pl_rade"]
    m = df["pl_bmasse"]
    d = df["pl_dens"]

    p_radius = _sigmoid(-(r - 1.7) / 0.2)
    p_density = _sigmoid((d - 2.5) / .6)
    p_mass = _sigmoid(-(np.log10(m) - np.log10(6.0)) / 0.25)

    clues = pd.concat([p_radius, p_density, p_mass], axis=1)
    weights = np.array([1.0, 1.5, 0.5])   

    logits = clues.apply(_logit)
    mask = clues.notna()                   
    weighted_sum = (logits.fillna(0) * weights).sum(axis=1)
    weight_total = (mask * weights).sum(axis=1)

    score = _sigmoid(weighted_sum / weight_total.replace(0, np.nan))
    return score    





def get_teq(row, albedo=0.3):

    if pd.notna(row["st_teff"]) and pd.notna(row["st_rad"]) and pd.notna(row["pl_orbsmax"]) and row["pl_orbsmax"] > 0:
        return row["st_teff"] * (1 - albedo) ** 0.25 * np.sqrt(row["st_rad"] * 0.00465047 / (2 * row["pl_orbsmax"]))
    return row["pl_eqt"]


def estimate_surface_temp(row):
    teq = get_teq(row)
    if pd.isna(teq):
        return pd.Series({"surface_temp_k": np.nan, "temp_note": "insufficient data"})


    if pd.notna(row["pl_insol"]) and row["pl_insol"] > 10:
        return pd.Series({"surface_temp_k": teq, "temp_note": "likely airless (heavily irradiated)"})

    mass = row["pl_bmasse"]
    tau = 0.0 if (pd.notna(mass) and mass < 0.2) else 0.5
    ts = teq * (1 + 0.75 * tau) ** 0.25
    return pd.Series({"surface_temp_k": ts, "temp_note": "estimated, assumes atmosphere"})


#initial calculations
df[["surface_temp_k", "temp_note"]] = df.apply(estimate_surface_temp, axis=1)
df["surface_temp_c"] = df["surface_temp_k"] - 273.15
df["solid_score"] = solid(df)



# 1. Archive-provided flux (Earth = 1)
flux = df["pl_insol"].copy()

# 2. Fallback: luminosity / distance^2. st_lum is log10(solar), so convert it first
lum = 10 ** df["st_lum"]
flux = flux.fillna(lum / df["pl_orbsmax"] ** 2)

# 3. Second fallback: luminosity from star radius and temperature (Sun = 5772 K)
lum_from_rt = df["st_rad"] ** 2 * (df["st_teff"] / 5772) ** 4
flux = flux.fillna(lum_from_rt / df["pl_orbsmax"] ** 2)

# Brightest to darkest
f = flux.dropna().sort_values(ascending=False)
names_by_brightness = df.loc[f.index, "pl_name"].tolist()

# Temperature categories
bins = [-np.inf, -50, 0, 30, 100, 400, np.inf]
labels = ["Frozen", "Very cold", "Cool", "Temperate", "Hot", "Scorching"]
df["temp_category"] = pd.cut(df["surface_temp_c"], bins=bins, labels=labels)

d = df["sy_dist"].dropna().sort_values()          # nearest to farthest
names_by_distance = df.loc[d.index, "pl_name"].tolist()

a = df["st_age"].dropna().sort_values()              # youngest to oldest
names_by_star_age = df.loc[a.index, "pl_name"].tolist()

m = df["st_met"].dropna().sort_values(ascending=False)    # most to least metal-rich
names_by_star_metallicity = df.loc[m.index, "pl_name"].tolist()

n = (df["sy_pnum"] - 1).dropna().sort_values(ascending=False)   # most to fewest neighbors
names_by_neighbors = df.loc[n.index, "pl_name"].tolist()

names_by_mass = (df.dropna(subset=["pl_bmasse"]).sort_values("pl_bmasse")["pl_name"].tolist())
g = (df["pl_bmasse"] / df["pl_rade"] ** 2).dropna().sort_values()   # weakest to strongest
names_by_gravity = df.loc[g.index, "pl_name"].tolist()
# Sort and inspect
df = df.sort_values("surface_temp_c")
print(df[["pl_name", "surface_temp_c", "temp_category", "temp_note"]].head(10))
print(df["temp_category"].value_counts(dropna=False))

print(names_by_gravity[:5])    # five lightest
print(names_by_gravity[-5:])   



# =====================================================================
# QUIZ (new): 10 questions, answered 1-5, one planet picked at the end
# =====================================================================

POINTS = 10            # points a planet earns per question for being in the picked group
TOP_N = 20             # the winner is drawn at random from this many top scorers
MIN_COVERAGE = 0.7     # ignore planets with data for fewer than 70% of the questions
SEED = None            # set to a number (e.g. 42) for repeatable results in a demo

# These three give "fixed points for the picked group only".
# To use sort.py's extra behavior (half points for the next group over, smaller
# weight for middle groups) set FALLOFF = 0.5, REACH = 2, MIDDLE_WEIGHT = 0.5.
FALLOFF = 0.0
REACH = 0
MIDDLE_WEIGHT = 1.0

# table column -> question text (1 = lowest values, 5 = highest values)
QUESTIONS = {
    "temperature": "How hot do you like it? (1 = frozen, 5 = scorching)",
    "size":        "How big a planet do you want? (1 = tiny, 5 = huge)",
    "mass":        "How heavy a planet? (1 = very light, 5 = very heavy)",
    "gravity":     "How strong should gravity be? (1 = floaty, 5 = crushing)",
    "brightness":  "How bright should the sunlight be? (1 = dim, 5 = blinding)",
    "distance":    "How far from Earth? (1 = right next door, 5 = very far)",
    "star_age":    "How old should its star be? (1 = newborn, 5 = ancient)",
    "metallicity": "How metal-rich a star system? (1 = metal-poor, 5 = metal-rich)",
    "neighbors":   "How many neighboring planets? (1 = none, 5 = a crowded system)",
    "solidity":    "What should the planet be made of? (1 = gassy, 5 = solid rock)",
}

# One table with a column per question; this is what sort.py and utils.py read.
# It reuses the sorted Series above (g, f, d, a, m, n), matched back to df by index.
table = pd.DataFrame({
    "planet":      df["pl_name"],
    "temperature": df["surface_temp_c"],
    "size":        df["pl_rade"],
    "mass":        df["pl_bmasse"],
    "gravity":     g,
    "brightness":  f,
    "distance":    d,
    "star_age":    a,
    "metallicity": m,
    "neighbors":   n,
    "solidity":    df["solid_score"],
}, index=df.index).replace([np.inf, -np.inf], np.nan)

group_labels = {column: percentile_labels(table[column]) for column in QUESTIONS}


def ask():
    """Ask every question and return {column: pick from 1 to 5}."""
    answers = {}
    for column, text in QUESTIONS.items():
        while True:
            reply = input(text + " ").strip()
            if reply in {"1", "2", "3", "4", "5"}:
                answers[column] = int(reply)
                break
            print("Please enter a number from 1 to 5.")
    return answers


def pick_planet(answers, rng):
    """Score every planet, then draw one winner at random from the top TOP_N."""
    prefs = [
        GroupPreference(column, selected=(pick - 1,), weight=POINTS,
                        falloff=FALLOFF, reach=REACH, middle_weight=MIDDLE_WEIGHT, label=column)
        for column, pick in answers.items()
    ]
    scored = score_by_groups(table, prefs, name_col="planet", min_coverage=MIN_COVERAGE)
    if scored.empty:
        return None

    # Shuffle first so ties at the cutoff are broken randomly, then keep the top scorers
    pool = (scored.sample(frac=1, random_state=rng)
                  .sort_values("score", ascending=False, kind="stable")
                  .head(TOP_N))
    return pool.sample(1, random_state=rng).iloc[0]


def show_result(answers, winner):
    idx = winner.name
    print(f"\nYour ideal planet is {winner['planet']}!")
    print(f"Match score: {winner['score']:.0f}/100 (data available for {winner['coverage'] * 100:.0f}% of the questions)\n")

    for column, pick in answers.items():
        edges = percentile_edges(table, column)
        low, high = edges[pick - 1], edges[pick]
        group = group_labels[column].get(idx)
        value = table.loc[idx, column]
        if pd.isna(group):
            print(f"  {column:12} you wanted {low:.3g} to {high:.3g}  |  no data for this planet")
        else:
            hit = "match" if int(group) == pick - 1 else "miss "
            print(f"  {column:12} you wanted {low:.3g} to {high:.3g}  |  planet: {value:.3g}  [{hit}]")


if __name__ == "__main__":
    print("\nAnswer each question with a number from 1 to 5.\n")
    answers = ask()
    winner = pick_planet(answers, np.random.default_rng(SEED))
    if winner is None:
        print("No planet had enough data to match. Try lowering MIN_COVERAGE.")
    else:
        show_result(answers, winner)