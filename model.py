import numpy as np
import joblib
import pandas as pd
from sklearn.preprocessing import QuantileTransformer
import time



def normalisedf(df):
    scaler = QuantileTransformer(output_distribution='normal')
    df[['CarCount', 'BikeCount', 'BusCount', 'TruckCount']] = scaler.fit_transform(df[['CarCount', 'BikeCount', 'BusCount', 'TruckCount']])
    print(df)
    return df



def load_model():
    pipeline = joblib.load("/Users/akashzamnani/Desktop/Traffic-BE-proj/Traffic-Manager/model/traffic_pipeline1.pkl",)
    return pipeline

def run_model(dict):

    am_pm = time.strftime('%p')
    current_date = time.strftime("%d")
    current_day = time.strftime("%A")
    current_hour = int(time.strftime("%H"))
    is_weekend = current_day in ["Saturday", "Sunday"]
    print(am_pm)
    print(current_date)
    df = pd.DataFrame([{                                                # "Time": "11:30:00 AM",
        "Date": int(current_date),
        "Day of the week": current_day,
        "CarCount": dict['car'],
        "BikeCount": dict['motorbike'],
        "BusCount": dict['bus'],
        "TruckCount": dict['truck'],
        "Total": sum(dict.values()),
        "Weekend": is_weekend,
        "Hour": current_hour,
        "AM/PM": am_pm
    }])

#     df = pd.DataFrame([{
#     "Date": 17,
#     "Day of the week": "Thursday",
#     "CarCount": 50,
#     "BikeCount":120,
#     "BusCount": 10,
#     "TruckCount": 20,
#     "Total": 200,
#     "Weekend": False,
#     "Hour": 12,
#     "AM/PM":'PM'
# }])
####
    model = load_model()
    print(df)
    df = normalisedf(df)
    prediction = model.predict(df)
    return prediction[0]




