import pandas as pd

df = pd.read_csv("sample.csv").dropna(how="all")
df["dt"] = pd.to_datetime(
    df["Datum"] + " " + df["Zeit"], format="%d.%m.%Y %H:%M Uhr"
)
for _, month in df.groupby(pd.Grouper(key="dt", freq="ME")):
    dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
    fname = f"{dt}-amazonvisa.csv"
    month = month.drop("dt", axis=1).to_csv(fname, index=False)
