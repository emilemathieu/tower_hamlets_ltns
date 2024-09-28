#%%
import os
from datetime import date

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# %matplotlib inline


th_df = pd.read_csv("../data/LFB/th.csv")
th_df['is_th'] = True
E2_df = pd.read_csv("../data/LFB/E2.csv")
E2_df['is_E2'] = True
ltn_df = pd.read_csv("../data/LFB/ltn.csv")
ltn_df['is_inside_ltn'] = True

df = pd.concat([th_df, E2_df, ltn_df])
df['response_time_s'] = df['AverageOfAttendanceTime'].apply(lambda x: int(x.split(":")[-2]) * 60 + int(x.split(":")[-1]))
df['pd_date'] = pd.to_datetime(df['YearMonth'], format='%Y%m')
df = df.fillna(False)

pre_ltn_date = date(2020,6,1)
post_ltn_date = date(2021,7,1)

dict_str = {
    'is_inside_ltn': 'inside of LTN',
    'is_E2': 'inside of E2',
    'is_boundary_ltn': 'boundary of LTN',
    'is_th': 'Rest of Tower Hamlets',
    'is_inner': 'Iner boroughs',
}

#%%
fig, axes = plt.subplots(2, 1, figsize=(8, 8))

kwargs = {'lw': 3}
ymin, ymax = np.inf, -np.inf

for col, ax in zip(['response_time_s', 'Incidents'], axes):
    for series_name in ['is_inside_ltn', 'is_E2', 'is_th']:
        time_series = df[df[series_name]].resample('6M', on='pd_date').mean(numeric_only=True)[col]#
        dates = time_series.index
        # ys = time_series[series_name]
        ys = time_series
        zs = ys
        zs = (ys - ys[0]) / ys[0]
        ax.plot(dates, zs, label=dict_str[series_name], **kwargs)

        ymin = np.min(zs) if np.min(zs) < ymin else ymin
        ymax = np.max(zs) if np.max(zs) > ymax else ymax
        ax.vlines(pre_ltn_date, ymin=ymin, ymax=ymax, color='black', linestyle='--')#, label='pre LTN')
        ax.vlines(post_ltn_date, ymin=ymin, ymax=ymax, color='black', linestyle='--')#, label='pre LTN')

axes[0].legend(loc='lower right', ncol=1)


axes[0].set_title('Variation in response time of LFB in Tower Hamlets')
axes[1].set_title('Variation in incidents managed by LFB in Tower Hamlets')


# %%
