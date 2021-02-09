import geopandas as gpd
import pandas as pd
import geoplot.ops as ops

print("Loading data...")
districts = pd.read_csv(
  "data/districts_u.csv", 
  encoding="utf-8", 
  sep=";",
  converters={"TERYT": str}
).drop(columns=["lat", "lng"])

vote_results = pd.read_csv("data/vote_results_ids.csv", encoding="utf-8", sep=";")
districts = districts.join(vote_results).drop(columns=["uuid"])
geo_districts = pd.read_csv(
  "geocode/geo_districts.csv",
  encoding="utf-8",
  sep=";", 
  converters={"lat": str, "lng": str,}
).drop(columns=["county", "city", "street", "building_num"])
geo_districts = geo_districts[geo_districts.lat != "0.0"]
districts = districts.merge(geo_districts, left_on="full_name", right_on="full_name").drop(columns=["TERYT"])

print("Data loaded. Grouping districts...")
#Using lat/lng combination as a unique identifier.
#Some places have the same address but due to poorly prepared data it can differ
#by a letter or two so the md5 hash used before as an id is useless.
districts["latlng"] = districts.lat + ";" + districts.lng
districs_sum = districts.drop(columns=["lat", "lng", "full_name"])
districts = districts.drop(columns=["Duda", "Trzaskowski", "full_name"]).drop_duplicates(["latlng"])
districs_sum = districs_sum.groupby(["latlng"], as_index=False).sum()
districts = districts.merge(districs_sum, on="latlng")

print("Districts have been grouped. Creating geometry...")
pol_points = gpd.GeoDataFrame({"geometry": gpd.points_from_xy(districts.lng, districts.lat)})
triangles = gpd.GeoDataFrame(geometry=ops.build_voronoi_polygons(pol_points))

pol = gpd.read_file("maps/pl.shp", encodoing="utf-8").to_crs("EPSG:4326")
pol = pol.unary_union
triangles = triangles.assign(geometry=triangles.geometry.intersection(pol))
print("Geometry created. Saving data...")

districts = gpd.GeoDataFrame(districts, geometry=triangles.geometry.values).drop(columns=["county", "lat", "lng", "latlng"])
districts.to_file("maps/districts.json", driver="GeoJSON", encoding="utf-8")
