import pandas as pd
import re
import hashlib
from unidecode import unidecode

districts = pd.read_csv(
  "data/vote_districts.csv", 
  encoding="utf-8", 
  sep=";", 
  converters={
    "full_name": lambda x: hashlib.md5(unidecode(x).lower().encode()).hexdigest(),
    "street": lambda x: unidecode(x)
    }
)
#using an MD5 hash as a unique identifier (much better than full address)

print("Before:", len(districts.index))
districts_u = districts.drop(columns=["obw", "Duda", "Trzaskowski"])
districts_u = districts_u.drop_duplicates(subset=["full_name"], keep="first")
districts_u["lat"] = [0] * len(districts_u.index)
districts_u["lng"] = [0] * len(districts_u.index)
print("After:", len(districts_u.index))

for i, row in districts_u.iterrows():
  city = row.city

  if (re.match("[\w\s]+,\s?[\w\s]+", city)):
    print(city)
    new_city_name = re.sub(",\s?[\w\s]+", "", city)
    districts_u.loc[districts_u.city == city, "city"] = new_city_name

districts_u.to_csv("data/districts_u.csv", encoding="utf-8", index=False, sep=";")
print("Saved unique districts. Grouping vote results...")

districts = districts.drop(columns=["TERYT", "obw", "county", "city", "street", "building_num"]).set_index("full_name")
districts = districts.groupby(["full_name"], sort=False).sum()
districts.to_csv("data/vote_results_ids.csv", encoding="utf-8", index_label="uuid", sep=";")

print("Saved grouped vote results.")