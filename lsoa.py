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
# Load data

# LSOA
path_census = (
    "data/Census_Residential_Data_Pack_2011/Local_Authority_Districts/E09000030/"
)
lsoas_link = path_census + "shapefiles/E09000030.shp"
lsoas = gpd.read_file(lsoas_link)

# Indices of deprivation
path_imd = "data/Index_of_Multiple_Deprivation_IMD/Local_Authority_Districts/E09000030/"
imd = gpd.read_file(path_imd + "tables/E09000030_2019.csv")
TH_lsoas = imd["lsoa11cd"]

# motorised vehicules data
dvla = gpd.read_file("data/DVLA_FOI_LSOA_201126/DVLA_FOI_LSOA_V3.csv")
dvla["lsoa11cd"] = dvla["lsoac"]
dvla_th = dvla[dvla["lsoa11cd"].isin(TH_lsoas)]
dvla_2019 = dvla_th[dvla_th["year"] == "2019"]
dvla_2019["car_density"] = dvla_2019["cars"].astype(int) / dvla_2019[
    "pop18plus"
].astype(int)

# merge dataframe
df = gpd.GeoDataFrame(pd.merge(imd, dvla_2019, on="lsoa11cd"))
df = gpd.GeoDataFrame(pd.merge(df, lsoas, on="lsoa11cd"))
df = df.to_crs(epsg=3857)  # for cx.add_basemap

#%%
# Parse traffic filters

# list of LSOA with traffic filters
ltns = {
    "obgr": ["E01004198", "E01004199", "E01004200", "E01004203", "E01004204"],
    "weavers": ["E01004311", "E01004312", "E01004313", "E01004315", "E01004316"],
}
idx_obgr = df["lsoa11cd"].isin(ltns["obgr"])
idx_weavers = df["lsoa11cd"].isin(ltns["weavers"])

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

crs = CRS.from_epsg(4326)
filters_df = gpd.GeoDataFrame(geometry=geometry, crs=crs)
filters_df = filters_df.to_crs(epsg=3857)

# Set bounds
min_lat, min_lon, max_lat, max_lon = 51.510000, -0.078000, 51.536322, -0.035000
bounds = gpd.GeoDataFrame(
    geometry=[Point([min_lon, min_lat]), Point([max_lon, max_lat])], crs=crs
)
minx, miny, maxx, maxy = bounds.to_crs(epsg=3857).total_bounds
# minx, miny, maxx, maxy = df.total_bounds

#%%
# Define plotting function


def plot(metrics, cmaps):
    fig, axes = plt.subplots(1, len(metrics), figsize=(20, 20))
    axes = axes if isinstance(axes, np.ndarray) else [axes]
    # cmap = sns.color_palette("crest", as_cmap=True)
    for ax, metric, cmap in zip(axes, metrics, cmaps):
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)

        # title = 'Multiple deprivation index per LSOA in Tower Hamlets'
        ax.set_title(metric, fontdict={"fontsize": "15", "fontweight": "3"})
        ax.axis("off")

        df.plot(ax=ax, alpha=0.8, edgecolor="k", column=metric, cmap=cmap)
        filters_df.plot(
            ax=ax,
            markersize=200,
            color="red",
            marker="*",
            label="modal filters",
            zorder=3,
        )
        sm = plt.cm.ScalarMappable(
            cmap=cmap, norm=plt.Normalize(vmin=df[metric].min(), vmax=df[metric].max())
        )  # empty array for the data range
        cbar = fig.colorbar(sm, shrink=0.4, ax=ax)
        cx.add_basemap(ax)
        ax.legend()
    fig.tight_layout()
    return fig


#%%
# Plot Tower Hamlet map with metrics of interest

# metrics = ["IMDScore", "IMD_Decile"]
# metrics = ["IMDScore", "car_density"]
# metrics = ["EnvScore", "IncScore"]
metrics = ["IMD_Decile", "car_density"]
cmaps = [
    sns.color_palette("mako", as_cmap=True),
    sns.color_palette("mako_r", as_cmap=True),
]

plot(metrics, cmaps)
#%%
# Plot metrics for ltns vs rest of TH

metric = "IMD_Decile"
avg_obgr = df[idx_obgr][metric].astype(float).mean()
avg_weavers = df[idx_weavers][metric].astype(float).mean()
avg_borough = df[metric].astype(float).mean()
print(f"{metric}")
print(f"obgr:    {avg_obgr:.2f} vs {avg_borough:.2f}")
print(f"weavers: {avg_weavers:.2f} vs {avg_borough:.2f}")

df["avg_IMD_Decile"] = df["IMD_Decile"]
df.loc[:, "avg_IMD_Decile"] = avg_borough
df.loc[idx_obgr, "avg_IMD_Decile"] = avg_obgr
df.loc[idx_weavers, "avg_IMD_Decile"] = avg_weavers

avg_obgr = (
    df[idx_obgr]["cars"].astype(int).sum() / df[idx_obgr]["pop18plus"].astype(int).sum()
)
avg_weavers = (
    df[idx_weavers]["cars"].astype(int).sum()
    / df[idx_weavers]["pop18plus"].astype(int).sum()
)
avg_borough = df["cars"].astype(int).sum() / df["pop18plus"].astype(int).sum()
print(f"Car density")
print(f"obgr:    {avg_obgr:.2f} vs {avg_borough:.2f}")
print(f"weavers: {avg_weavers:.2f} vs {avg_borough:.2f}")

df["avg_car_density"] = df["car_density"]
df.loc[:, "avg_car_density"] = avg_borough
df.loc[idx_obgr, "avg_car_density"] = avg_obgr
df.loc[idx_weavers, "avg_car_density"] = avg_weavers

plot(["avg_IMD_Decile", "avg_car_density"], cmaps)

#%%
cmap = cmaps[0]
metric = metrics[0]
sm = plt.cm.ScalarMappable(
    cmap=cmap, norm=plt.Normalize(vmin=df[metric].min(), vmax=df[metric].max())
)
df.explore(
    column=metric,  # make choropleth based on "BoroName" column
    tooltip="lsoa11cd",  # show "BoroName" value in tooltip (on hover)
    popup=False,  # show all values in popup (on click)
    tiles="CartoDB positron",  # use "CartoDB positron" tiles
    cmap=sm,  # use "Set1" matplotlib colormap
    style_kwds=dict(color="black"),  # use black outline
    vmin=df[metrics[0]].astype(int).min(),
    vmax=df[metrics[0]].astype(int).max(),
)

# %%
from scipy import stats

ci = 0.95
alpha = (1 - ci) / 2


def half_ci(group):
    data = group.dropna().to_numpy()
    sem = stats.sem(data)
    t2 = stats.t.ppf(1 - alpha, len(data) - 1) - stats.t.ppf(alpha, len(data) - 1)
    return sem * (t2 / 2)


def lower_ci(group):
    data = group.dropna().to_numpy()
    sem = stats.sem(data)
    mean = data.mean()
    t = stats.t.ppf(alpha, len(data) - 1)
    return mean + sem * t


def upper_ci(group):
    data = group.dropna().to_numpy()
    sem = stats.sem(data)
    mean = data.mean()
    t = stats.t.ppf(1 - alpha, len(data) - 1)
    return mean + sem * t


reducers = ["mean", "std", "sem", lower_ci, upper_ci, half_ci, "count"]
group_by
metric = metric if isinstance(metric, list) else [metric]
metrics_to_agg = {key: reducers for key in metric}
results = results.groupby(by=["group"] + group_by).agg(metrics_to_agg)
