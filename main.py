from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
import numpy as np
import pandas as pd

# temp = float(input("Enter the temperature of the planet in Celsius: "))


#Temperatur calculations



planets = NasaExoplanetArchive.query_criteria(
    table="pscomppars",
    select="pl_name, pl_eqt, pl_rade, pl_bmasse, pl_insol, pl_orbsmax, st_teff, st_rad",

)

df = planets.to_pandas()

def get_teq(row, albedo=0.3):

    if pd.notna(row["st_teff"]) and pd.notna(row["st_rad"]) and pd.notna(row["pl_orbsmax"]) and row["pl_orbsmax"] > 0:
        return row["st_teff"] * (1 - albedo) ** 0.25 * np.sqrt(row["st_rad"] * 0.00465047 / (2 * row["pl_orbsmax"]))
    return row["pl_eqt"]


def estimate_surface_temp(row):
    teq = get_teq(row)
    if pd.isna(teq):
        return pd.Series({"surface_temp_k": np.nan, "temp_note": "insufficient data"})

    if pd.notna(row["pl_rade"]) and row["pl_rade"] > 1.6:
        return pd.Series({"surface_temp_k": np.nan, "temp_note": "gas/ice-rich; no solid surface"})

    if pd.notna(row["pl_insol"]) and row["pl_insol"] > 10:
        return pd.Series({"surface_temp_k": teq, "temp_note": "likely airless (heavily irradiated)"})

    mass = row["pl_bmasse"]
    tau = 0.0 if (pd.notna(mass) and mass < 0.2) else 0.5
    ts = teq * (1 + 0.75 * tau) ** 0.25
    return pd.Series({"surface_temp_k": ts, "temp_note": "estimated, assumes atmosphere"})

df[["surface_temp_k", "temp_note"]] = df.apply(estimate_surface_temp, axis=1)
df["surface_temp_c"] = df["surface_temp_k"] - 273.15

# Temperature categories
bins = [-np.inf, -50, 0, 30, 100, 400, np.inf]
labels = ["Frozen", "Very cold", "Cool", "Temperate", "Hot", "Scorching"]
df["temp_category"] = pd.cut(df["surface_temp_c"], bins=bins, labels=labels)

# Sort and inspect
df = df.sort_values("surface_temp_c")
print(df[["pl_name", "surface_temp_c", "temp_category", "temp_note"]].head(10))
print(df["temp_category"].value_counts(dropna=False))


print(df.head(200))

