import pandas as pd
import geopandas as gpd
import requests
import os

def save(df: pd.DataFrame, index: int):
  print("Saving data...")
  df.to_csv("geocode/geo_districts.csv", encoding="utf-8", index=False, sep=";")
  with open("geocode/last_index.txt", "w") as f:
    f.write(str(index))
  print("Data saved.")

api_key = os.getenv("GOOGLE_API")
params = {"key": api_key, "language": "pl"}

#This was made to load data after exception as I didn't want to overwrite the original file
#If the sript is being run for the first time it should point to data/districts_u.csv instead
all_districts = pd.read_csv("data/districts_u.csv", encoding="utf-8", na_filter=False, sep=";")

with open("geocode/many_results.txt", "w") as f:
  f.write("")

last_index = 0
try:
  with open("geocode/last_index.txt", "r") as f:
    last_index = int(f.readline())
except:
  pass

print("Fetching geocode data...")
print("Starting with index {}.".format(last_index))

for i, row in all_districts.iterrows():
  if (i < last_index):
    continue

  city = row.city
  street = row.street
  number = row.building_num
  county = row.county
  uuid = row.full_name

  address = "{}{} {}{}".format(city, " " + street if street != "" else "", number, " " + county if county != city else "")
  params["address"] = address

  try:
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params)
    result = r.json()

    if (result["status"] != "OK" and result["status"] != "ZERO_RESULTS"):
      raise Exception("Request to {} failed with code {}.".format(r.url, result["status"]))
    elif (result["status"] == "ZERO_RESULTS"):
      #Doubling the request as some addresses with street number return empty results
      #even though such request should return street coordinates
      address = "{}{}{}".format(city, " " + street if street != "" else "", " " + county if county != city else "")
      params["address"] = address
      r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params)
      result = r.json()

      if (result["status"] != "OK"):
        #Well, that was my last resort, even the street itself wasn't found. It's exception time!
        raise Exception("Request to {} failed with code {}.".format(r.url, result["status"]))
    
    if (len(result["results"]) > 1):
      #It's rather harmless as more than one result is found usually
      #when some kind of POI (i.e. a school or a hospital) is present at the same address.
      #Nevertheless, manual verification will be a nice touch
      print("More than one result at index {} and address {}. Please verify later.".format(i, address))
      with open("geocode/many_results.txt", "a") as f:
        f.write("{}\n".format(i))

    geom = result["results"][0]["geometry"]["location"]
    lat = geom["lat"]
    lng = geom["lng"]
    all_districts.loc[all_districts.full_name == uuid, "lat"] = lat
    all_districts.loc[all_districts.full_name == uuid, "lng"] = lng
  except Exception as e:
    print("[Error] {}: {}".format(type(e), e))
    save(all_districts, i)
    print("Closing...")
    quit()

  if (i != 0 and i % 100 == 0):
    length = len(all_districts.index)
    print("Completed: {:.2f}%.".format((i/length)*100))
    save(all_districts, i)

print("All done.")
save(all_districts, i)
print("Closing...")