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
# path_census = (
#     "data/Census_Residential_Data_Pack_2011/Local_Authority_Districts/E09000030/"
# )
# lsoas_link = path_census + "shapefiles/E09000030.shp"
lsoas_link = "data/Index_of_Multiple_Deprivation_IMD/Local_Authority_Districts/E09000030/shapefiles/E09000030.shp"
# lsoas_link = "data/LLSOA_Dec_2021/LSOA_PopCentroids_EW_2021_V3.shp"
lsoas = gpd.read_file(lsoas_link)
lsoas = lsoas.to_crs(epsg=3857)  # for cx.add_basemap
lsoas['LSOA21CD'] = lsoas['lsoa11cd']

lsoas2 = gpd.read_file(
    "data/LSOA_(2011)_to_LSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales.csv"
)
# lsoa_col = 'F_LSOA11CD'
lsoa_col = 'LSOA21CD'
lsoa_th = lsoas2[lsoas2["LAD22NM"] == "Tower Hamlets"][lsoa_col].to_list()
inner_boroughs = ['Camden', 'Greenwich', 'Hackney', 'Hammersmith and Fulham', 'Islington', 'Kensington and Chelsea', 'Lambeth', 'Lewisham', 'Southwark', 'Tower Hamlets', 'Wandsworth', 'Westminster']
lsoa_inner = lsoas2[lsoas2["LAD22NM"].isin(inner_boroughs)][lsoa_col].to_list()


#%%
road_link = "data/greater-london-latest-free/gis_osm_roads_free_1.shp"
roads = gpd.read_file(road_link)
lsoas = lsoas.to_crs(epsg=3857)
# roads_of_interest = ['Hackney Road', 'Bethnal Green Road', 'Cambridge Heath Road']
# roads = roads[roads['name'].isin(roads_of_interest)]
roads_of_interest = ['A1208', 'A1209', 'A107', 'A10']
roads = roads[roads['ref'].isin(roads_of_interest)]

# %%

# road accidents / casualties
# https://www.data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data
path_road = "data/road_collisions"
dfs = []
for year in [2018, 2019, 2020, 2021, 2022, '2023_mid_year_unvalidated']:
    data = pd.read_csv(os.path.join(path_road, f"{year}.csv"))
    # in_th_idx = data["lsoa_of_accident_location"].isin(lsoa_th)
    # dfs.append(data[in_th_idx])
    dfs.append(data)
df = pd.concat(dfs)

# df["lsoa11cd"] = df["lsoa_of_accident_location"]
# df = gpd.GeoDataFrame(pd.merge(df, lsoas, on="lsoa11cd"))
df["LSOA21CD"] = df["lsoa_of_accident_location"]
df = gpd.GeoDataFrame(pd.merge(df, lsoas, on="LSOA21CD"))

# %%

# Parse traffic filters

# list of LSOA with traffic filters
# ltns = {
#     "obgr": ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204"],
#     "weavers": ["E01004311", "E01004312", "E01004313", "E01004315", "E01004316"],
# }
# ltns = {
#     "obgr": ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204"],
#     "weavers": ["E01004311", "E01004312", "E01004313", "E01004315", "E01004316"],
# }
ltns = ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204", "E01035664", "E01004311", "E01004312", "E01004313", "E01004315", "E01004316"]
# idx_obgr = df["lsoa11cd"].isin(ltns["obgr"])
# idx_weavers = df["lsoa11cd"].isin(ltns["weavers"])

crs = CRS.from_epsg(4326)
# min_lat, min_lon, max_lat, max_lon = 51.510000, -0.078000, 51.536322, -0.035000
# min_lat, min_lon, max_lat, max_lon = 51.510000, -0.078000, 51.536322, -0.035000
min_lat, min_lon, max_lat, max_lon = 51.520000, -0.078000, 51.536322, -0.05
bounds = gpd.GeoDataFrame(
    geometry=[Point([min_lon, min_lat]), Point([max_lon, max_lat])], crs=crs
)
minx, miny, maxx, maxy = bounds.to_crs(epsg=3857).total_bounds
# minx, miny, maxx, maxy = df.total_bounds


#%%

# Define injuries
# cf https://findingspress.org/article/18330-the-impact-of-introducing-low-traffic-neighbourhoods-on-road-traffic-injuries
# 1. Injuries inside the LTN, defined as injuries at least 25m inside the LTN boundary, and not recorded as being at the intersection with a boundary road.
# 2. Injuries at the LTN boundary, defined being located from 25m inside to 50m outside the LTN boundary.
# 3. Elsewhere in Tower Hamlets.
# 4. Elsewhere in Inner London.
df['is_ltn'] = df["LSOA21CD"].isin(ltns)
# NOTE: LTN = low traffic neighbourhood. Injuries are limited to those that are neither on an A or B road, nor at the intersection with an A or B road.
# TODO: need to remove A or B road
df['is_th'] = df["lsoa_of_accident_location"].isin(lsoa_th) & ~df['is_ltn']
df['is_inner'] = df["lsoa_of_accident_location"].isin(lsoa_inner) & ~df['is_th']

# Define dates
# 1. Pre-LTN: January 2018 to June 2020
# 2. Post-LTN: July 2021 to May 2023

df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
df['pre_ltn'] = df['date'] < '01/06/2020'
df['post_ltn'] = df['date'] >= '01/07/2021'

#%%
# Ratios calculated as ‘% injuries inside LTNs in post period’/‘% injuries inside LTNs in pre period’
print('LTN versus Tower Hamlets')

in_ltn_pre_ltn = ((df['is_ltn'] == True) & (df['pre_ltn'] == True)).sum()
in_ltn_post_ltn = ((df['is_ltn'] == True) & (df['post_ltn'] == True)).sum()

in_th_pre_ltn = ((df['is_th'] == True) & (df['pre_ltn'] == True)).sum()
in_th_post_ltn = ((df['is_th'] == True) & (df['post_ltn'] == True)).sum()

ratio_ltn_vs_th = (in_ltn_post_ltn / in_th_post_ltn) / (in_ltn_pre_ltn / in_th_pre_ltn)

print(f"LTN:   {in_ltn_pre_ltn} vs {in_ltn_post_ltn}")
print(f"TH:    {in_th_pre_ltn} vs {in_th_post_ltn}")
print(f"ratio: {ratio_ltn_vs_th}")

print('LTN versus Inner London')

in_inner_pre_ltn = ((df['is_inner'] == True) & (df['pre_ltn'] == True)).sum()
in_inner_post_ltn = ((df['is_inner'] == True) & (df['post_ltn'] == True)).sum()

ratio_ltn_vs_inner = (in_ltn_post_ltn / in_inner_post_ltn) / (in_ltn_pre_ltn / in_inner_pre_ltn)

print(f"LTN:   {in_ltn_pre_ltn} vs {in_ltn_post_ltn}")
print(f"INNER: {in_inner_pre_ltn} vs {in_inner_post_ltn}")
print(f"ratio: {ratio_ltn_vs_inner}")


#%%
collision_dfs, colors = [], []

# dfs = [
#     df[df['pre_ltn'] & (df['is_ltn'] | df['is_th'])],
#     df[df['post_ltn'] & (df['is_ltn'] | df['is_th'])]
# ]
dfs = [
    df[df['pre_ltn'] & (df['is_ltn'])],
    df[df['post_ltn'] & (df['is_ltn'])]
]
# dfs = [
#     df[df['is_ltn']],
# ]

severity_color = {1: 'yellow', 2: 'orange', 3: 'red'}
for subset_df in dfs:
    geometry = [Point([lon, lat]) for lon, lat in zip(subset_df['longitude'], subset_df['latitude'])]
    collision_dfs.append(gpd.GeoDataFrame(geometry=geometry, crs=CRS.from_epsg(4326)).to_crs(epsg=3857))
    colors.append(subset_df['accident_severity'].apply(lambda x: severity_color[int(x)]))
titles = ['pre LTN', 'post LTN']
# %%
cmaps = [
    sns.color_palette("mako", as_cmap=True),
    sns.color_palette("mako_r", as_cmap=True),
]


# fig, axes = plt.subplots(1, len(collision_dfs), figsize=(20, 20))
fig, axes = plt.subplots(len(collision_dfs), 1, figsize=(20, 20))
axes = axes if isinstance(axes, np.ndarray) else [axes]
# cmap = sns.color_palette("crest", as_cmap=True)
for i, (ax, collision_df, color, title, cmap) in enumerate(zip(axes, collision_dfs, colors, titles, cmaps)):
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # title = 'Multiple deprivation index per LSOA in Tower Hamlets'
    ax.set_title(title, fontdict={"fontsize": "30", "fontweight": "3"})
    ax.axis("off")
    ax = collision_df.plot(
            ax=ax,
            markersize=100,
            color=color.to_list(),
            marker="*",
            label="collisions",
            zorder=0,
        )
    ax = roads.plot(ax=ax, label='roads', color='black')
    # df[df['is_ltn']].plot(ax=ax, alpha=0.1, edgecolor="k", column='is_ltn')
    # sm = plt.cm.ScalarMappable(
    #     cmap=cmap, norm=plt.Normalize(vmin=df[metric].min(), vmax=df[metric].max())
    # )  # empty array for the data range
    # cbar = fig.colorbar(sm, shrink=0.4, ax=ax)
    # cx.add_basemap(ax)
    # ax.legend()
fig.tight_layout()



# plot(metrics, cmaps)
# %%
from shapely.geometry import LineString, Point

# line_strings = [LineString([(-1.15, 0.12), (9.9, -1.15), (0.13, 9.93)]),
#                     LineString([(-2.15, 0.12), (8.9, -2.15), (0.13 , 8.93)])]
# points = [Point(5.41, 3.9), Point (6.41, 2.9)]

# geom = line_strings + points
# gdf = gpd.GeoDataFrame(geometry=geom)

# gdf.plot()
roads.plot(ax=ax, label='roads', color='black')