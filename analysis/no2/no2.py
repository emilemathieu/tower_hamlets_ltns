#%%
import pandas as pd

#%%
years = list(range(2015,2022+1))
appended_data = pd.DataFrame()

for y in years:
    df_years = pd.read_csv('../../data/Data_NO2/'+ str(y) + '.csv')
    # df_years = df_years.drop(columns=['Site no','Grid squaresX', 'Grid squaresY', 'Site Type'])
    df_years = df_years.drop(columns=['Site no', 'Site Type'])
    # df_years = (df_years.set_index(['Location'])
    df_years = (df_years.set_index(['Location','Grid squaresX', 'Grid squaresY'])
            .stack()
            .reset_index(name='Value')
            .rename(columns={'level_3':'Date'}))
    appended_data = appended_data.append(df_years,ignore_index=True)


#%%
from convertbng.util import convert_bng, convert_lonlat
eastings = appended_data["Grid squaresX"]
northings = appended_data["Grid squaresY"]
lon, lat = convert_lonlat(eastings, northings)
appended_data['lat'] = lat
appended_data['lon'] = lon
appended_data = appended_data.drop(columns=['Grid squaresX', 'Grid squaresY'])

#%%
# list of 

#%%
# All empty cells will say 'Missing'
appended_data = appended_data.replace('','Missing')
appended_data = appended_data.replace('missing','Missing')

# Check all unique location names to identify issues (e.g. unintended duplicates)
unique_names = pd.unique(appended_data['Location'])
unique_names = pd.DataFrame(unique_names)
unique_names.columns = ['Name']
unique_names = unique_names.sort_values('Name')
unique_names.to_csv('unique_names.csv')

# Create new column to define type of location (inner, boundary, external)
appended_data['Type'] = 'to be defined'

#Export to csv
appended_data.to_csv('test.csv')
# %%
# operational date for LTNs ~  1 July 2021: https://i.heartbg.uk/LFB-response-time-analysis
# %%
