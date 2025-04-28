import joblib
import pandas as pd
from math import ceil
# class TimePred:
#     def __init__(self):
#         self.defaultTime = 15

#     def getTime(self,total_vehicles,prediction):
#         if prediction == 'low':
#             pass
#         elif prediction == 'normal':
#             pass
#         elif prediction == 'high':
#             # high has more no of heavy vehicles
#             pass
#         elif prediction == 'heavy':
#             pass


from datetime import datetime

def get_time_period():
    now = datetime.now()
    current_hour = now.hour

    if 9 <= current_hour < 12:
        return 'A'
    elif 12 <= current_hour < 15:
        return 'B'
    elif 15 <= current_hour < 18:
        return 'C'
    elif 18 <= current_hour < 21:
        return 'D'
    else:
        return None 

def loadtime_model():
    pipeline = joblib.load("model/greentime_pipeline.pkl")
    return pipeline

def run_time_model(dict,traffic_status):
    model = loadtime_model()
    time = get_time_period()
    vehicles = sum(dict.values())

    

    df = pd.DataFrame([{
        "Vehicle Count": vehicles,
        "Current Time": time,
        'Weekend/Weekday':1,
        "Road Type":"A",
        "Status": traffic_status,
    }])

    print(df)

    prediction = model.predict(df)
    return ceil(prediction[0])
          


