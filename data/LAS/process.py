import pandas as pd

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 250)

def process_data():

    df_2024 = pd.read_csv("data/LAS/FOI_6294.csv")
    df_old = pd.read_csv("data/LAS/ambulence_rt_dec_may@4.csv")

    # first we make a new column that has the mean sec time in ms from the format hh:mm:ss
    df_2024["mean ms"] = df_2024["mean sec"].apply(lambda x: int(x.split(":")[1])*60*1000 + int(x.split(":")[2])*1000)

    # We now get the timestamp to period map from the old data
    period_map = df_old.set_index("utctimestamp")["period"].to_dict()
    df_2024["period"] = df_2024["utctimestamp"].map(period_map).fillna("After")


    df_2024.to_csv("data/LAS/FOI_6294_processed.csv", index=False)


if __name__ == "__main__":
    process_data()