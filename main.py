from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# temp = float(input("Enter the temperature of the planet in Celsius: "))


#Temperatur calculations

def _logit(p):
    p = np.clip(p, 0.02, 0.98)
    return np.log(p / (1 - p))



planets = NasaExoplanetArchive.query_criteria(
    table="pscomppars",
    select="pl_name, pl_eqt, pl_rade, pl_bmasse, pl_insol, pl_orbsmax,pl_dens, st_teff, st_rad",
)

def _sigmoid(x):
    return 1 / (1 + np.exp(-x))

df = planets.to_pandas()

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

# Temperature categories
bins = [-np.inf, -50, 0, 30, 100, 400, np.inf]
labels = ["Frozen", "Very cold", "Cool", "Temperate", "Hot", "Scorching"]
df["temp_category"] = pd.cut(df["surface_temp_c"], bins=bins, labels=labels)

names_by_mass = (df.dropna(subset=["pl_bmasse"]).sort_values("pl_bmasse")["pl_name"].tolist())
g = (df["pl_bmasse"] / df["pl_rade"] ** 2).dropna().sort_values()   # weakest to strongest
names_by_gravity = df.loc[g.index, "pl_name"].tolist()

# Sort and inspect
df = df.sort_values("surface_temp_c")
print(df[["pl_name", "surface_temp_c", "temp_category", "temp_note"]].head(10))
print(df["temp_category"].value_counts(dropna=False))

print(names_by_gravity[:5])    # five lightest
print(names_by_gravity[-5:])   



