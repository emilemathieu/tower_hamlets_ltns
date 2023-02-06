#%%
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import contextily as cx
from shapely.geometry import Point
from pyproj import CRS
import numpy as np

# %matplotlib inline


#%%
# LSOA
path_census = (
    "data/Census_Residential_Data_Pack_2011/Local_Authority_Districts/E09000030/"
)
lsoas_link = path_census + "shapefiles/E09000030.shp"
lsoas = gpd.read_file(lsoas_link)

lsoas2 = gpd.read_file(
    "data/LSOA_(2011)_to_LSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales.csv"
)
th_lsoa = lsoas2[lsoas2["LAD22NM"] == "Tower Hamlets"]["F_LSOA11CD"].to_list()

# %%


# road accidents / casualties
path_road = "data/road_accidents"
dfs = []
for year in [2019, 2020, 2021, 2022]:
    data = pd.read_file(os.path.join(path_road, f"{year}.csv"))
    in_th_idx = data["lsoa_of_accident_location"].isin(th_lsoa)
    dfs.append(data[in_th_idx])
df = pd.concat(dfs)
