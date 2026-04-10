import numpy as np
import pandas as pd
import joblib

from tensorflow.keras.models import load_model


# load model
model = load_model(
    "lstm_vitals_model.h5",
    compile=False
)


# load scaler
scaler = joblib.load("scaler.save")

print("Loaded successfully")

df = pd.read_csv("combined_data.csv")

df['time_stamp'] = pd.to_datetime(
    df['time_stamp'],
    format="%d-%m-%Y %H:%M"
)

df = df.sort_values(['patient_id','time_stamp'])


# pick patient
patient_id = df['patient_id'].unique()[0]

patient_df = df[df['patient_id']==patient_id]

last_12 = patient_df.tail(12)


input_seq = last_12[['glucose','heart_rate']].values

input_scaled = scaler.transform(input_seq)

input_scaled = np.expand_dims(input_scaled, axis=0)


pred = model.predict(input_scaled)[0]

pred_real = scaler.inverse_transform(pred)

minutes = [5*i for i in range(1,13)]

result = pd.DataFrame({

    "minutes_ahead": minutes,

    "predicted_glucose": pred_real[:,0],

    "predicted_heart_rate": pred_real[:,1]

})

print(result)