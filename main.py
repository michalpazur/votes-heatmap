import geopandas as gpd
import pandas as pd
import geoplot
import cartopy.crs as ccrs
import geoplot.crs as gcrs
import matplotlib.pyplot as plt
import seaborn as sns

print("Loading data")
pol = gpd.read_file("maps/gminy.shp", encoding="utf-8").to_crs("EPSG:4326")
vote_results = pd.read_excel("data/vote_res.xlsx", converters={"TERYT": str})

for index, row in pol.iterrows():
  try:
    teryt = row.CC_3[:-1]
    pol.at[index, 'CC_3'] = teryt
  except:
    pass

pol = pol.merge(vote_results, left_on="CC_3", right_on="TERYT")
pol_points = gpd.GeoDataFrame({"geometry": pol.centroid, "result": pol.result})
print("Merge successful!")

ax = geoplot.voronoi(
  pol_points, 
  projection=gcrs.WebMercator(), 
  clip=pol.geometry, 
  hue="result", 
  cmap=sns.diverging_palette(21, 216, s=100, l=45, as_cmap=True), 
  linewidth=0.5,
  edgecolor="white",
  figsize=(10, 10)
)

plt.savefig("map.png", transparent=True)