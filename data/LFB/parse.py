#%%
import pandas as pd
from time import gmtime, strftime
from datetime import date

#%%

# Data from https://i.heartbg.uk/LFB-response-time-analysis
df_safer_streets = pd.read_csv("FSB-TH-response-times@2.csv")


# %%

# Downloaded “LFB Incident Data from 2018“ data from https://data.london.gov.uk/dataset/london-fire-brigade-incident-records
# and exported as csv, although one could directly open the excel file apprently
# df_response_times = pd.read_excel("LFB Incident data from 2018 onwards.csv.xlsx")
df_response_times = pd.read_csv("LFB-response-times.csv")

# Only keep Tower Hamlets
df = df_response_times[df_response_times['IncGeo_BoroughName'] == 'TOWER HAMLETS']
# Remove rows with missing values for response time
df = df[df["FirstPumpArriving_AttendanceTime"].notna()]

# %%

# Trying to figure out how parse df as df_safer_streets (the one from the safer sreets website)

# columns from df_safer_streets
columns = ['IncidentNumber', 'Month', 'Year', 'Period', "TimeOfCall", "DayOfCall", "utcTimeOfCall", "IncidentGroup", "Postcode_full", "Postcode_district", "Borough", "WardName", "Easting_rounded", "Northing_rounded", "ResponseTime-millisecs", "ResponseTime-secs", "ResponseTime-mins", "DeployedFromStation"]

def check_columns(df, columns):
    existing_columns = []
    not_existing_columns = []
    for column in columns:
        if column in df.columns:
            existing_columns.append(column)
        else:
            not_existing_columns.append(column)
    return existing_columns, not_existing_columns

# %%
df['Year'] = df['CalYear']
df['DayOfCall'] = df['DateOfCall']
df['Borough'] = df['IncGeo_BoroughName'].apply(lambda x: x.title())
df['WardName'] = df['IncGeo_WardName'].apply(lambda x: x.upper())
df['DeployedFromStation'] = df['IncidentStationGround']

df["ResponseTime-mins"] = df["FirstPumpArriving_AttendanceTime"].apply(lambda x: strftime("%M:%S", gmtime(x)))
df["ResponseTime-secs"] = df["FirstPumpArriving_AttendanceTime"].astype(int)
df["ResponseTime-millisecs"] = df["ResponseTime-secs"] * 1000
df["ResponseTime-millisecs"].astype(int)

df["utcTimeOfCall"] = pd.to_datetime(df['DateOfCall'] + '/' + df['TimeOfCall'], format='%d-%b-%y/%H:%M:%S', utc=True)
df['DayOfCall'] = df["utcTimeOfCall"].apply(lambda x: x.strftime("%d/%m/%Y"))
df['Month'] = df["utcTimeOfCall"].apply(lambda x: x.strftime("%Y-%m"))
df["utcTimeOfCall"] = df["utcTimeOfCall"].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

df["DateTimeOfCall"] = pd.to_datetime(df['DateOfCall'] + '/' + df['TimeOfCall'], format='%d-%b-%y/%H:%M:%S', utc=False)

#%%

pre_ltn_date = pd.Timestamp(date(2020,6,1))
post_ltn_date = pd.Timestamp(date(2021,7,1))

def get_period(day_of_call):
    # ('2019-01-01', '2019-06-30')
    if day_of_call <= pd.Timestamp(date(2019, 6, 30)) and day_of_call >= pd.Timestamp(date(2019, 1, 1)):
        return "Before-6-month"
    # ('2019-07-01', '2021-06-30')
    elif day_of_call <= post_ltn_date:
    # elif day_of_call >= date(2019, 7, 1) and day_of_call <= date(2021, 6, 30):
        return "Before"
    # ('2022-01-01', '2022-06-30')
    elif day_of_call >= post_ltn_date + pd.DateOffset(months=6) and day_of_call <= pd.Timestamp(date(2022, 6, 30)):
        return "After-6-month"
    # ('2021-07-01', '2021-12-31')
    elif day_of_call >= post_ltn_date:
    # elif day_of_call >= date(2021, 7, 1) and day_of_call <= date(2021, 12, 31):
        return "After"
    else:
        raise ValueError("Invalid date")
df['Period'] = df["DateTimeOfCall"].apply(get_period)

#%%
# for column in df.columns:
#     if column not in columns:
#         del df[column]
df = df[columns]
df.to_csv("LFB-TH-response-times.csv", index=False)
# %%
