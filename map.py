import geopandas as gpd
import pandas as pd
import geoplot.ops as ops

print("Loading data...")
districts = pd.read_csv(
  "data/districts_u.csv", 
  encoding="utf-8", 
  sep=";",
  converters={"TERYT": lambda x: "0" + str(x)[:-2] if len(str(x)) == 5 else str(x)[:-2]}
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
districts = districts.merge(geo_districts, left_on="full_name", right_on="full_name")

print("Data loaded. Grouping districts...")
#Using lat/lng combination as a unique identifier.
#Some places have the same address but due to poorly prepared data it can differ
#by a letter or two so the md5 hash used before as an id is useless.
districts["latlng"] = districts.lat + ";" + districts.lng
districs_sum = districts.drop(columns=["lat", "lng", "full_name", "TERYT"])
districs_sum = districs_sum.rename(str.lower, axis='columns')
districts = districts.drop(columns=["Duda", "Trzaskowski", "full_name"]).drop_duplicates(["latlng"])
districs_sum = districs_sum.groupby(["latlng"], as_index=False).sum()
districts = districts.merge(districs_sum, on="latlng")

print("Districts have been grouped. Creating geometry...")
pol_points = gpd.GeoDataFrame({"geometry": gpd.points_from_xy(districts.lng, districts.lat)})
triangles = gpd.GeoDataFrame(geometry=ops.build_voronoi_polygons(pol_points))

pol = gpd.read_file("maps/pl.shp", encodoing="utf-8").to_crs("EPSG:4326")
pol = pol.unary_union
triangles = triangles.assign(geometry=triangles.geometry.intersection(pol))

print("Geometry created. Merging by TERYT...")
#TERYT is a unique identifier for each of Poland's administrative divisions.
#In case of powiats it consists of four digits with first two being TERYT number
#of their respecitve voivodeship. Merging by name would be a bad idea as there are a few
#powiats with the same name in defferent voivodeships.
districts = gpd.GeoDataFrame(districts, geometry=triangles.geometry.values).drop(columns=["lat", "lng", "latlng"])
to_dissolve = districts.drop(columns=["city", "street", "building_num"])
powiats_u = to_dissolve.drop_duplicates(["TERYT"]).drop(columns=["duda", "trzaskowski", "geometry"])
dissolved = districts.dissolve(by="TERYT", aggfunc="sum", as_index=False)
dissolved = dissolved.merge(powiats_u, on="TERYT")

print("Created powiats. Creating district for each powiat...")
for i, row in dissolved.iterrows():
  print(row.county)
  powiat_districts = districts[districts.TERYT == row.TERYT]
  powiat_districts.drop(columns=["county"]).to_file("maps/powiats/{}.json".format(row.TERYT), driver="GeoJSON", encoding="utf-8")

print("Saved separate districts. Saving overall map...")
dissolved.to_file("maps/districts.json", driver="GeoJSON", encoding="utf-8")
