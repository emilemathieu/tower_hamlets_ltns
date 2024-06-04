#%%
import os
from functools import partial

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import contextily as cx
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import transform
from pyproj import CRS, pyproj

import numpy as np

# %matplotlib inline


#%%
# Load LSOA data

lsoas_link = "../data/LSOA/LSOA_2011_London_gen_MHW.shp"
lsoas = gpd.read_file(lsoas_link)
lsoas = lsoas.to_crs(epsg=3857)  # for cx.add_basemap
#%%

lsoas2 = gpd.read_file(
    "../data/LSOA_(2011)_to_LSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales.csv"
)
lsoas2['LSOA11CD'] = lsoas2['F_LSOA11CD']
del lsoas2["geometry"]
lsoas2 = gpd.GeoDataFrame(pd.merge(lsoas2, lsoas, on="LSOA11CD"))

lsoa_col = 'F_LSOA11CD'
# lsoa_col = 'LSOA21CD'
lsoa_th_df = lsoas2[lsoas2["LAD22NM"] == "Tower Hamlets"]
lsoa_th = lsoa_th_df[lsoa_col].to_list()
inner_boroughs = ['Camden', 'Greenwich', 'Hackney', 'Hammersmith and Fulham', 'Islington', 'Kensington and Chelsea', 'Lambeth', 'Lewisham', 'Southwark', 'Tower Hamlets', 'Wandsworth', 'Westminster', 'City of London']
lsoa_inner_df = lsoas2[lsoas2["LAD22NM"].isin(inner_boroughs)]
lsoa_inner = lsoa_inner_df[lsoa_col].to_list()
lsoa_th_and_neigh_df = lsoas2[lsoas2["LAD22NM"].isin(['Tower Hamlets', 'Hackney', 'City of London'])]
lsoa_th_and_neigh = lsoa_th_and_neigh_df[lsoa_col].to_list()

lsoa_th_df.plot()
lsoa_inner_df.plot()

# %%
# Load # road collisions
# https://www.data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data

path_road = "../data/road_collisions"
dfs = []
for year in [2018, 2019, 2020, 2021, 2022, '2023_mid_year_unvalidated']:
    data = pd.read_csv(os.path.join(path_road, f"{year}.csv"))
    # in_th_idx = data["lsoa_of_accident_location"].isin(lsoa_th)
    # dfs.append(data[in_th_idx])
    dfs.append(data)
df = pd.concat(dfs)
df["LSOA21CD"] = df["lsoa_of_accident_location"]
# df = gpd.GeoDataFrame(pd.merge(df, lsoas, on="LSOA21CD"))

df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=CRS.from_epsg(4326)).to_crs(epsg=3857)
df['og_geometry'] = gpd.points_from_xy(df.longitude, df.latitude)
df['is_th_and_neigh'] = df["lsoa_of_accident_location"].isin(lsoa_th_and_neigh)

#%%
# Load boundary roads

road_link = "../data/greater-london-latest-free/gis_osm_roads_free_1.shp"
roads = gpd.read_file(road_link).to_crs(epsg=3857)
roads_of_interest = ['Hackney Road', 'Bethnal Green Road', 'Cambridge Heath Road', 'Shoreditch High Street']
roads = roads[roads['name'].isin(roads_of_interest)]
roads.plot()

# %%

# Define LTNs in Tower Hamlets

# list of LSOA with traffic filters
# ltns = {
#     "obgr": ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204"],
#     "weavers": ["E01004311", "E01004312", "E01004313", "E01004315", "E01004316"],
# }
ltns = ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204", "E01004311", "E01004312", "E01004313", "E01004315", "E01004316"]
ltns += ["E01004318", "E01004314"] # NOTE: north of Weavers
# idx_obgr = df["lsoa11cd"].isin(ltns["obgr"])
# idx_weavers = df["lsoa11cd"].isin(ltns["weavers"])
lsoa_ltn_df = lsoa_th_df[lsoa_th_df['LSOA11CD'].isin(ltns)]

# latitude and longitude of traffic filters from https://talk.towerhamlets.gov.uk/4093/widgets/12671/documents/29230 and https://talk.towerhamlets.gov.uk/4093/widgets/12671/documents/29229
traffic_filters = {
    "Temple Street": [51.52973, -0.05994],
    "Canrobert Street": [51.52940, -0.06055],
    "Clarkson Street": [51.52879, -0.05898],
    "Punderson's Gardens": [51.52829, -0.05788],
    "Teesdale Street": [51.529305, -0.061291],
    "Pollard Row": [51.527873, -0.063878],
    "Quilter Street": [51.52867, -0.06989],
    "Wellington Row": [51.52850, -0.06723],
    "Gosset Street": [51.528313, -0.071200],
    "Old Nichol Street": [51.52470, -0.07642],
    "Arnold Circus": [51.526051, -0.074899],
}
geometry = [Point(reversed(v)) for _, v in traffic_filters.items()]

filters_df = gpd.GeoDataFrame(geometry=geometry, crs=CRS.from_epsg(4326)).to_crs(epsg=3857)

# min_lat, min_lon, max_lat, max_lon = 51.510000, -0.078000, 51.536322, -0.035000
min_lat, min_lon, max_lat, max_lon = 51.520000, -0.080000, 51.536322, -0.052
bounds = gpd.GeoDataFrame(
    geometry=[Point([min_lon, min_lat]), Point([max_lon, max_lat])], crs=CRS.from_epsg(4326)
)
minx, miny, maxx, maxy = bounds.to_crs(epsg=3857).total_bounds


#%%


project = partial(
pyproj.transform,
pyproj.Proj('EPSG:4326'),
pyproj.Proj('EPSG:3857'))
# pyproj.Proj('EPSG:32633'))
# pyproj.Proj('EPSG:4326'))

ltn_borders_list = [
    (51.532572, -0.057133), (51.531395, -0.064693), (51.530846, -0.072525), (51.529827, -0.074711), (51.529258, -0.074914), (51.527835, -0.076487),
    (51.526941, -0.077971), (51.526306, -0.078077), (51.524729, -0.077161),
    (51.523735, -0.077214), (51.523701, -0.075217), (51.523917, -0.074064), (51.525771, -0.069619), (51.526525, -0.064638),
    (51.527547, -0.055430), (51.530254, -0.056104)]
ltn_borders_list = [(lon, lat) for lat, lon in ltn_borders_list] #NOTE: swap lat and lon
ltn_borders_list = [Point(lat, lon) for lat, lon in ltn_borders_list]
poly = Polygon(ltn_borders_list)
ltn_df = gpd.GeoDataFrame(geometry=[poly], crs=CRS.from_epsg(4326)).to_crs(epsg=3857)
ltn_borders = gpd.GeoDataFrame(geometry=np.array(ltn_borders_list), crs=CRS.from_epsg(4326)).to_crs(epsg=3857)
ltn_df.plot()
ltn_borders.plot()

poly2 = Polygon(ltn_borders['geometry'].to_list())


# poly_in_3857_coords = transform(project, poly)
df['is_ltn'] = df['og_geometry'].apply(lambda x: poly.contains(x))


# def dist_to_boundary_roads(point, bool=True):
#     min_dist = float('inf')
#     if not bool:
#         return min_dist
#     for _, road in roads.iterrows():
#         line = road.geometry
#         dist = point.distance(line)
#         if dist < min_dist:
#             min_dist = dist
#     return min_dist

# df['dist_to_boundary_roads'] = df.apply(lambda x: dist_to_boundary_roads(x['geometry'], x['is_ltn']), axis=1)
# df['dist_to_boundary_roads'] = df.apply(lambda x: dist_to_boundary_roads(x['geometry'], x['is_th_and_neigh']), axis=1)
df['dist_to_boundary_roads'] = df.apply(lambda x: poly2.exterior.distance(x['geometry']), axis=1)


#%%

# Define injuries
# cf https://findingspress.org/article/18330-the-impact-of-introducing-low-traffic-neighbourhoods-on-road-traffic-injuries
# 1. Injuries inside the LTN, defined as injuries at least 25m inside the LTN boundary, and not recorded as being at the intersection with a boundary road.
# 2. Injuries at the LTN boundary, defined being located from 25m inside to 50m outside the LTN boundary.
# 3. Elsewhere in Tower Hamlets.
# 4. Elsewhere in Inner London.
# df['is_ltn'] = df["LSOA21CD"].isin(ltns)
# NOTE: LTN = low traffic neighbourhood. Injuries are limited to those that are neither on an A or B road, nor at the intersection with an A or B road.
dist_int_ltn = 50
dist_ext_ltn = 50
df['is_inside_ltn'] = df['is_ltn'] & (df['dist_to_boundary_roads'] > dist_int_ltn)
df['is_th'] = df["lsoa_of_accident_location"].isin(lsoa_th) & ~df['is_ltn']
df['is_inner'] = df["lsoa_of_accident_location"].isin(lsoa_inner) & ~df['is_th']
df['is_boundary_ltn'] = (df['is_ltn'] & (df['dist_to_boundary_roads'] <= dist_int_ltn)) | ((~df['is_ltn'] & df['is_th_and_neigh']) & (df['dist_to_boundary_roads'] <= dist_ext_ltn))
# df['is_boundary_ltn'] = (~df['is_ltn'] & df['is_th_and_neigh']) & (df['dist_to_boundary_roads'] <= 50)
print(df['is_boundary_ltn'].sum())

# Define dates
# 1. Pre-LTN: January 2018 to June 2020
# 2. Post-LTN: July 2021 to May 2023

df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
df['pre_ltn'] = df['date'] < '01/06/2020'
df['post_ltn'] = df['date'] >= '01/07/2021'

#%%
# Ratios calculated as ‘% injuries inside LTNs in post period’/‘% injuries inside LTNs in pre period’
from scipy.stats import fisher_exact


for variable in ['is_inside_ltn', 'is_boundary_ltn']:
    for control in ['is_th', 'is_inner']:

        print(f'### {variable} versus {control}')

        in_ltn_pre_ltn = ((df[variable] == True) & (df['pre_ltn'] == True)).sum()
        in_ltn_post_ltn = ((df[variable] == True) & (df['post_ltn'] == True)).sum()

        in_th_pre_ltn = ((df[control] == True) & (df['pre_ltn'] == True)).sum()
        in_th_post_ltn = ((df[control] == True) & (df['post_ltn'] == True)).sum()

        ratio_ltn_vs_th = (in_ltn_post_ltn / in_th_post_ltn) / (in_ltn_pre_ltn / in_th_pre_ltn)
        table = np.array([[in_ltn_post_ltn, in_ltn_pre_ltn], [in_th_post_ltn, in_th_pre_ltn]])
        # p_value = fisher_exact(table, alternative='greater')[1]

        print(f"Variable:   {in_ltn_pre_ltn} vs {in_ltn_post_ltn}")
        print(f"Control:    {in_th_pre_ltn} vs {in_th_post_ltn}")
        print(f"ratio:      {ratio_ltn_vs_th:.2f}")
        # print(f"p_value:    {p_value:.2f}")

#%%
collision_dfs, colors = [], []

dfs = [
    df[df['pre_ltn'] & (df['is_th_and_neigh'])],
    df[df['post_ltn'] & (df['is_th_and_neigh'])]
]

severity_color = {1: 'yellow', 2: 'orange', 3: 'red'}
for subset_df in dfs:
    collision_dfs.append(subset_df)
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
for i, (ax, sub_df, color, title, cmap) in enumerate(zip(axes, collision_dfs, colors, titles, cmaps)):
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    ax.set_title(title, fontdict={"fontsize": "30", "fontweight": "3"})
    ax.axis("off")
    kwargs = {"marker": "*", "zorder": 3}
    filters_df.plot(ax=ax, markersize=200, color="blue", marker="x", label="modal filters")
    sub_df[sub_df['is_th_and_neigh']].plot(ax=ax, color='black', **kwargs, markersize=200, label="all collisions")
    sub_df[sub_df['is_inside_ltn']].plot(ax=ax, color='red', **kwargs, markersize=150, label="inner LTN collisions")
    sub_df[sub_df['is_boundary_ltn']].plot(ax=ax, color='orange', **kwargs, label="boundary roads collisions")
    roads.plot(ax=ax, label='roads', color='black')
    # lsoa_ltn_df.plot(ax=ax, alpha=0.5, edgecolor="k")
    ltn_df.plot(ax=ax, alpha=0.5, edgecolor="k", label='LTN polygon')
    ltn_borders.plot(ax=ax, alpha=1., edgecolor="k", markersize=300, label='LTN vertices')
    cx.add_basemap(ax)
    ax.legend()
fig.tight_layout()

# plot(metrics, cmaps)

# %%

# def is_side_of(point, road, side, bool=True):
#     out = False
#     if not bool:
#         return out
#     point = transform(project, point)
#     for _, road in roads.iterrows():
#         geometry = transform(project, road.geometry)
#         for lat, lon in geometry.coords:
#             print(lat, lon, ' vs ', point.x, point.y)
#             if side == 'east' and lon < point.y:
#                 return True
#             if side == 'west' and lon > point.y:
#                 return True
#             if side == 'south' and lat > point.x:
#                 return True
#             if side == 'north' and lat < point.x:
#                 return True
#     return out

# def is_west_of_cambridge_heath_rd(point, bool=True):
#     cambridge_heath_rd = roads[roads['name'] == 'Cambridge Heath Road']
#     return is_side_of(point, cambridge_heath_rd, side='west', bool=bool)

# def is_north_of_bethnal_green_rd(point, bool=True):
#     bethnal_green_rd = roads[roads['name'] == 'Bethnal Green Road']
#     return is_side_of(point, bethnal_green_rd, side='north', bool=bool)

# if df['is_west_of_cambridge_heath_rd'].sum() == 0:
#     df['is_west_of_cambridge_heath_rd'] = None
#     df.loc[df['is_ltn'], 'is_west_of_cambridge_heath_rd'] = df[df['is_ltn']].apply(lambda x: is_west_of_cambridge_heath_rd(x['geometry']), axis=1)

# if df['is_north_of_bethnal_green_rd'].sum() == 0:
#     df['is_north_of_bethnal_green_rd'] = None
#     df.loc[df['is_ltn'], 'is_north_of_bethnal_green_rd'] = df[df['is_ltn']].apply(lambda x: is_north_of_bethnal_green_rd(x['geometry']), axis=1)


# df['is_inside_ltn'] = df['is_ltn'] & (df['dist_to_boundary_roads'] > 25) & df['is_west_of_cambridge_heath_rd'] & df['is_north_of_bethnal_green_rd']
# df['is_boundary_ltn'] = df['is_ltn'] & (df['dist_to_boundary_roads'] <= 25) | (df['is_inner'] & (df['dist_to_boundary_roads'] <= 50)) | (df['is_th'] & (df['dist_to_boundary_roads'] <= 50))
