#%%
import os
from datetime import date

import matplotlib.pyplot as plt
import seaborn as sns

import pandas as pd
from scipy.stats import fisher_exact, boschloo_exact
import numpy as np

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
# import geopandas.testing
import contextily as cx
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import transform
from pyproj import CRS, pyproj


# %matplotlib inline

# Load LSOA data
# lsoas_link = "../data/LSOA/LSOA_2011_London_gen_MHW.shp"
# lsoas = gpd.read_file(lsoas_link)
# lsoas = lsoas.to_crs(epsg=3857)  # for cx.add_basemap

lsoas2 = gpd.read_file(
    "data/LSOA_(2011)_to_LSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales.csv"
)

# TODO: why this alternative key?
# lsoas2['LSOA11CD'] = lsoas2['F_LSOA11CD']

del lsoas2["geometry"]
# lsoas2 = gpd.GeoDataFrame(pd.merge(lsoas2, lsoas, on="LSOA11CD"))
# lsoa_col = 'F_LSOA11CD'

lsoa_borough = "LAD22NM"
lsoa_uid = "F_LSOA11CD"

lsoa_th_df = lsoas2[lsoas2[lsoa_borough] == "Tower Hamlets"]
lsoa_th = lsoa_th_df[lsoa_uid].to_list()

inner_boroughs = ['Camden', 'Greenwich', 'Hackney', 'Hammersmith and Fulham', 'Islington', 'Kensington and Chelsea', 'Lambeth', 'Lewisham', 'Southwark', 'Tower Hamlets', 'Wandsworth', 'Westminster', 'City of London']
lsoa_inner_df = lsoas2[lsoas2[lsoa_borough].isin(inner_boroughs)]
lsoa_inner = lsoa_inner_df[lsoa_uid].to_list()

lsoa_th_and_neigh_df = lsoas2[lsoas2[lsoa_borough].isin(['Tower Hamlets', 'Hackney', 'City of London'])]
lsoa_th_and_neigh = lsoa_th_and_neigh_df[lsoa_uid].to_list()

# lsoa_th_df.plot()
# lsoa_inner_df.plot()

# Define LTNs in Tower Hamlets

# list of LSOA with traffic filters

# TODO: this is superceded by filters_df below?
# ltns = ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204", "E01004311", "E01004312", "E01004313", "E01004315", "E01004316"]
# ltns += ["E01004318", "E01004314"] # NOTE: north of Weavers
# lsoa_ltn_df = lsoa_th_df[lsoa_th_df[lsoa_uid].isin(ltns)]

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

# #%%
# # Load boundary roads

# road_link = "../data/greater-london-latest-free/gis_osm_roads_free_1.shp"
# roads = gpd.read_file(road_link).to_crs(epsg=3857)
# roads_of_interest = ['Hackney Road', 'Bethnal Green Road', 'Cambridge Heath Road', 'Shoreditch High Street']
# roads = roads[roads['name'].isin(roads_of_interest)]
# roads.plot()

# not used
# project = partial(
# pyproj.transform,
# pyproj.Proj('EPSG:4326'),
# pyproj.Proj('EPSG:3857'))

# by human hand
ltn_borders_list = [
    (51.532572, -0.057133), (51.531395, -0.064693), (51.530846, -0.072525), (51.529827, -0.074711), (51.529258, -0.074914), (51.527835, -0.076487),
    (51.526941, -0.077971), (51.526306, -0.078077), (51.524729, -0.077161),
    (51.523735, -0.077214), (51.523701, -0.075217), (51.523917, -0.074064), (51.525771, -0.069619), (51.526525, -0.064638),
    (51.527547, -0.055430), (51.530254, -0.056104)]
ltn_borders_list = [(lon, lat) for lat, lon in ltn_borders_list] #NOTE: swap lat and lon
ltn_borders_list = [Point(lat, lon) for lat, lon in ltn_borders_list]

# polyLatLon is the polygon of the ltn using lat and lon coordinates
polyLatLon = Polygon(ltn_borders_list)

# epsg 3857 is Mercator, ltn_borders_df is the vertices of the solid polygon of the ltn
ltn_borders_df = gpd.GeoDataFrame(geometry=ltn_borders_list, crs=CRS.from_epsg(4326)).to_crs(epsg=3857)

# polyMercator is made from ltn_borders_df, which is in Mercator coords
polyMercator = Polygon(ltn_borders_df['geometry'].to_list())

# epsg 3857 is Mercator, ltn_df is the solid polygon of the ltn
ltn_df = gpd.GeoDataFrame(geometry=[polyLatLon], crs=CRS.from_epsg(4326)).to_crs(epsg=3857)

# ltn_df.plot()
# ltn_borders_df.plot()

# poly_in_3857_coords = transform(project, poly)


# %%
# Load # road collisions
# https://www.data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data

collision_path = "data/road_collisions"
collision_dfs = []
casualty_path = "data/road_casualties"
casualties_dfs = []

list_of_years = range(2017, 2023+1)
# list_of_years = range(2018, 2023+1)
# list_of_years = range(2023, 2023+1)

for year in list_of_years:
    collision_dfs.append(pd.read_csv(os.path.join(collision_path, f"{year}.csv")))
    casualties_dfs.append(pd.read_csv(os.path.join(casualty_path, f"{year}.csv")))
collision_df = pd.concat(collision_dfs)
casualties_df = pd.concat(casualties_dfs)

# cast to same type so that we can pd.merge later on these columns
collision_df['accident_index'] = collision_df['accident_index'].astype(str)
casualties_df['accident_index'] = casualties_df['accident_index'].astype(str)
#%%
# main data frame from now on
df = collision_df

lsoa_lookup = pd.read_csv("data/LSOA/LSOA11_WD20_LAD20_EW_LU_v2.csv")
df = pd.merge(df, lsoa_lookup, left_on='lsoa_of_accident_location', right_on='LSOA11CD')
# df["lsoa_uid"] = df["lsoa_of_accident_location"]

# accidents in or neighbouring th?
df['is_th_and_neigh'] = df["lsoa_of_accident_location"].isin(lsoa_th_and_neigh)
df = df[df['is_th_and_neigh']]

gpd_geometry_from_xy = gpd.points_from_xy(df.longitude, df.latitude)
# in the below we give 'geometry' of df the points in Mercator because of the crs conversion,
# and then readd 'LatLon_geometry'
df = gpd.GeoDataFrame(df, geometry=gpd_geometry_from_xy, crs=CRS.from_epsg(4326)).to_crs(epsg=3857)
df['LatLon_geometry'] = gpd_geometry_from_xy

df['og_date'] = df['date']

#%%

# Define injuries
# cf https://findingspress.org/article/18330-the-impact-of-introducing-low-traffic-neighbourhoods-on-road-traffic-injuries
# 1. Injuries inside the LTN, defined as injuries at least 25m inside the LTN boundary, and not recorded as being at the intersection with a boundary road.
# 2. Injuries at the LTN boundary, defined being located from 25m inside to 50m outside the LTN boundary.
# 3. Elsewhere in Tower Hamlets.
# 4. Elsewhere in Inner London.
# df['is_ltn'] = df["LSOA21CD"].isin(ltns)

# NOTE: LTN = low traffic neighbourhood. Injuries are limited to those that are neither on an A or B road, nor at the intersection with an A or B road.
# dist_int_ltn = 50
dist_int_ltn = 30
# dist_int_ltn = 25 # weird serious collision id 2021010350973
dist_ext_ltn = 50

df['is_ltn'] = df['LatLon_geometry'].apply(lambda x: polyLatLon.contains(x))
df['dist_to_boundary_roads'] = df.apply(lambda x: polyMercator.exterior.distance(x['geometry']), axis=1)

# 'is_inside_ltn': in the LTN and also more than dist_int_ltn metres inside the LTN
# 'is_th': in tower hamlets and not in the LTN, NOTE: ~ is negation of a series in pandas
# 'is_inner': in inner boroughs but not tower hamlets
# 'is_boundary_ltn': TODO: we double count here? all the of the second clause (after the or) is either in is_th or is_inner?
df['is_inside_ltn'] = df['is_ltn'] & (df['dist_to_boundary_roads'] > dist_int_ltn)
df['is_boundary_ltn'] = (df['is_ltn'] & (df['dist_to_boundary_roads'] <= dist_int_ltn)) | ((~df['is_ltn'] & df['is_th_and_neigh']) & (df['dist_to_boundary_roads'] <= dist_ext_ltn))
df['is_th'] = df["lsoa_of_accident_location"].isin(lsoa_th) & ~df['is_ltn'] & ~df['is_boundary_ltn']
df['is_inner'] = df["lsoa_of_accident_location"].isin(lsoa_inner) & ~df['is_th'] & ~df['is_ltn'] & ~df['is_boundary_ltn']
# df['is_boundary_ltn'] = (~df['is_ltn'] & df['is_th_and_neigh']) & (df['dist_to_boundary_roads'] <= 50)
# print(df['is_boundary_ltn'].sum())

# Define dates
# 1. Pre-LTN: January 2018 to June 2020
# 2. Post-LTN: July 2021 to May 2023

df['date'] = pd.to_datetime(df['og_date'], format='%d/%m/%Y')
df['date'] = df['date'].apply(lambda x: x.date())
pre_ltn_date = date(2020,6,1)
post_ltn_date = date(2021,7,1)
df['pre_ltn'] = df['date'] < pre_ltn_date # '01/06/2020'
df['post_ltn'] = df['date'] >= post_ltn_date # '01/07/2021'

nb_days_after_ltn = (pre_ltn_date - df['date'].min()).days
print(f"Nb of days before ltn: {nb_days_after_ltn}")
nb_days_after_ltn = (df['date'].max() - post_ltn_date).days
print(f"Nb of days after ltn: {nb_days_after_ltn}")

#%%
# Join casualties dataset with collisions dataset
casualties_df.drop(columns=['accident_year', 'accident_reference'])
casualties_df = casualties_df[casualties_df['accident_index'].isin(df['accident_index'])]
df = pd.merge(casualties_df, df, on='accident_index', how='left')

#%%
# Ratios calculated as ‘% injuries inside LTNs in post period’/‘% injuries inside LTNs in pre period’
from collections import defaultdict
severity_dict = {"Fatal": 1, "Serious": 2, "Slight": 3}
casualty_type_dict = defaultdict(lambda : list(range(-1, 100)), {'Pedestrian': 0, 'Cyclist': 1, 'Motorcycle 50cc and under rider or passenger': 2, 'Motorcycle 125cc and under rider or passenger': 3, 'Motorcycle over 125cc and up to 500cc rider or  passenger': 4, 'Motorcycle over 500cc rider or passenger': 5, 'Taxi/Private hire car occupant': 8, 'Car occupant': 9, 'Minibus (8 - 16 passenger seats) occupant': 10, 'Bus or coach occupant (17 or more pass seats)': 11, 'Horse rider': 16, 'Agricultural vehicle occupant': 17, 'Tram occupant': 18, 'Van / Goods vehicle (3.5 tonnes mgw or under) occupant': 19, 'Goods vehicle (over 3.5t. and under 7.5t.) occupant': 20, 'Goods vehicle (7.5 tonnes mgw and over) occupant': 21, 'Mobility scooter rider': 22, 'Electric motorcycle rider or passenger': 23, 'Other vehicle occupant': 90, 'Motorcycle - unknown cc rider or passenger': 97, 'Goods vehicle (unknown weight) occupant': 98, 'Unknown vehicle type (self rep only)': 99})

severities = ["Fatal", "Serious"]
# severities = ["Slight"]
# severities = ["Fatal", "Serious", "Slight"]
casualty_types = ["Cyclist"]
# casualty_types = ["Pedestrian"]
# casualty_types = list(casualty_type_dict.keys())[:-1] # all


dict_str = {
    'is_inside_ltn': 'inside of LTN',
    'is_boundary_ltn': 'boundary of LTN',
    'is_th': 'Rest of Tower Hamlets',
    'is_inner': 'Inner boroughs',
}

print(f'Casualty types: {casualty_types}')
print(f'Severities: {severities}')
for variable in ['is_inside_ltn', 'is_boundary_ltn']:
    # for control in ['is_th', 'is_inner']:
    for control in ['is_th']:

        print(f'### {dict_str[variable]} vs {dict_str[control]}')
        print(f'#      Pre LTN vs Post LTN')

        severity = df['accident_severity'].isin([severity_dict[key] for key in severities])
        casualty_type = df['casualty_type'].isin([casualty_type_dict[key] for key in casualty_types])

        in_ltn_pre_ltn = df[((df[variable] == True) & (df['pre_ltn'] == True) & severity & casualty_type)]['number_of_casualties'].count()
        in_ltn_post_ltn = df[((df[variable] == True) & (df['post_ltn'] == True) & severity & casualty_type)]['number_of_casualties'].count()

        in_th_pre_ltn = df[((df[control] == True) & (df['pre_ltn'] == True) & severity & casualty_type)]['number_of_casualties'].count()
        in_th_post_ltn = df[((df[control] == True) & (df['post_ltn'] == True) & severity & casualty_type)]['number_of_casualties'].count()

        ratio_ltn_vs_th = (in_ltn_post_ltn / in_th_post_ltn) / (in_ltn_pre_ltn / in_th_pre_ltn)
        # table = np.array([[in_ltn_post_ltn, in_ltn_pre_ltn], [in_th_post_ltn, in_th_pre_ltn]])
        table = np.array([[in_ltn_pre_ltn, in_th_pre_ltn], [in_ltn_post_ltn, in_th_post_ltn]])
        
        p_value = fisher_exact(table)[1]
        # p_value = barnard_exact(table).pvalue
        # p_value = boschloo_exact(table).pvalue
        # p_value = chi2_contingency(table)[1]

        print(f"Variable:   {in_ltn_pre_ltn} -> {in_ltn_post_ltn}")
        print(f"Control:    {in_th_pre_ltn} -> {in_th_post_ltn}")
        print(f"ratio:      {ratio_ltn_vs_th:.3f}")
        print(f"p_value:    {p_value:.3f}")
        # print(f"p_value_b:  {p_value_b:.2f}")

# %%
# checking p-value via Fisher's exact against Tab. 1 of https://findingspress.org/article/18330-the-impact-of-introducing-low-traffic-neighbourhoods-on-road-traffic-injuries
# Pedestrian casualty and LTN versus Waltham Forest should be 0.06
a = 16
b = 129
c = 8
d = 153

ratio = (c/d)/(a/b) # should approx equal 0.45
print(ratio)
tab = np.array([[a,b],[c,d]])
pval = fisher_exact(tab)[1] # should approx equal 0.06
print(pval)

# Casualty using any mode and LTN versus Waltham Forest
a = 51
b = 469
c = 18
d = 572

ratio = (c/d)/(a/b) # should approx equal 0.31
print(ratio)
tab = np.array([[a,b],[c,d]])
pval = fisher_exact(tab)[1] # should be <= 0.01
print(pval)

#%%
collision_dfs = [
    df[df['pre_ltn'] & (df['is_th_and_neigh'])],
    df[df['post_ltn'] & (df['is_th_and_neigh'])]
]
titles = ['pre LTN', 'post LTN']

cmaps = [
    sns.color_palette("mako", as_cmap=True),
    sns.color_palette("mako_r", as_cmap=True),
]

# fig, axes = plt.subplots(1, len(collision_dfs), figsize=(20, 20))
fig, axes = plt.subplots(len(collision_dfs), 1, figsize=(20, 20))
axes = axes if isinstance(axes, np.ndarray) else [axes]
# cmap = sns.color_palette("crest", as_cmap=True)

minx, miny, maxx, maxy = ltn_df.total_bounds
margin = 100
for i, (ax, sub_df, title, cmap) in enumerate(zip(axes, collision_dfs, titles, cmaps)):
    ax.set_xlim(minx - margin, maxx + margin)
    ax.set_ylim(miny - margin, maxy + margin)

    # cond = sub_df['accident_severity'].isin([1, 2, 3]) # all
    cond = sub_df['accident_severity'].isin([severity_dict[severity] for severity in severities]) # serious or fatal
    # cond = sub_df['accident_severity'] == 3 # slight

    ax.set_title(title + " -- severities=" + "/".join(severities), fontdict={"fontsize": "30", "fontweight": "3"})
    ax.axis("off")
    kwargs = {"marker": "*", "zorder": 3}
    filters_df.plot(ax=ax, markersize=200, color="blue", marker="x", label="modal filters")
    sub_df[sub_df['is_th_and_neigh'] & cond].plot(ax=ax, color='black', **kwargs, markersize=200, label=" collisions outside LTN & boundary roads (i.e. control variable)")
    sub_df[sub_df['is_inside_ltn'] & cond].plot(ax=ax, color='red', **kwargs, markersize=150, label="inner LTN collisions")
    sub_df[sub_df['is_boundary_ltn'] & cond].plot(ax=ax, color='orange', **kwargs, label="boundary roads collisions")
    # roads.plot(ax=ax, label='roads', color='black')
    ltn_df.plot(ax=ax, alpha=0.5, edgecolor="k", label='LTN polygon')
    ltn_borders_df.plot(ax=ax, alpha=1., edgecolor="k", markersize=300, label='LTN vertices')
    cx.add_basemap(ax)
    ax.legend()

fig.tight_layout()
fig.savefig('./output.png')


# %%

time_series = df.resample('6M', on='pd_date').sum().reset_index()
dates = time_series['pd_date']

fig, ax = plt.subplots(1, 1, figsize=(8, 4))

kwargs = {'lw': 3}

for series_name in ['is_inside_ltn', 'is_boundary_ltn', 'is_th']:
    ys = time_series[series_name]
    # zs = ys
    zs = (ys - ys[0]) / ys[0]
    ax.plot(dates, zs, label=dict_str[series_name], **kwargs)

fig.legend()

ax.vlines(pre_ltn_date, ymin=0, ymax=10, color='black', linestyle='--', label='pre LTN')
ax.vlines(post_ltn_date, ymin=0, ymax=10, color='black', linestyle='--', label='pre LTN')

ax.set_title('Relative variation of collision in Tower Hamlets')


# %%


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

#%%
# columns = ['IncidentNumber', 'Month', 'Year', 'Period', "TimeOfCall", "DayOfCall", "utcTimeOfCall", "IncidentGroup", "Postcode_full", "Postcode_district", "Borough", "WardName"]

columns = ['accident_index', 'Month', 'Year', 'Period', 'Location', 'latitude', 'longitude', "utcTime", "Borough", "WardName", "accident_severity", "number_of_casualties"]

utc_time = pd.to_datetime(df['og_date'] + '-' + df['time'], format='%d/%m/%Y-%H:%M', utc=True)
df["utcTime"] = utc_time.apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000Z'))
df["Month"] = utc_time.apply(lambda x: x.strftime("%Y-%m"))
df["Year"] = df["accident_year"]

def get_period (x):
    if x.date() >= post_ltn_date:
        return 'post LTN'
    elif x.date() < pre_ltn_date:
        return 'pre LTN'
    elif (x.date() < post_ltn_date) and (x.date() >= pre_ltn_date):
        return 'in between'
    else:
        raise ValueError(f"Invalid period: {x.date()}")
        # return 'None'

df["Period"] = utc_time.apply(get_period)

def get_area (x):
    if x['is_inside_ltn']:
        return 'Inside LTN'
    elif x['is_boundary_ltn']:
        return 'Boundary LTN'
    elif x['is_th']:
        return 'Rest of Tower Hamlets'
    elif x['is_inner']:
        return 'Inner adjacent boroughs'
    else:
        raise ValueError("Invalid area")
        # return 'None'

df['Location'] = df.apply(get_area, axis=1)

df['Borough'] = df['LAD20NM'].apply(lambda x: x.title())
df['WardName'] = df['WD20NM'].apply(lambda x: x.upper())

df[columns].to_csv("data/road_collisions/TH-LTN-collision.csv", index=False)

#%%

# %%

29/01/2017?
# 11th March 2017
27/05/2017?
# 24/07/2017
01/11/2017?
#  25th February 2018
# 19/06/2018
# 16/05/2019
# 07/03/2020

