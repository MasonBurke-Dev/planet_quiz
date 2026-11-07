from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive


temp = float(input("Enter the temperature of the planet in Celsius: "))



planets = NasaExoplanetArchive.query_criteria(
    table="pscomppars",
    select="pl_name,pl_rade,pl_bmasse,pl_orbper,pl_eqt,pl_insol,pl_dens",
)
df = planets.to_pandas()

print(df.head())