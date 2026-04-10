import pandas as pd
from pymongo import MongoClient


# ---------- CONFIG ----------

CSV_FILE = "C:\\Users\\Ani R\\Desktop\\Project@HITAM\\Major\\combined_data.csv"
MONGO_URI = "mongodb+srv://cluster2024:cluster2024@cluster2024.8qmtq.mongodb.net/?appName=cluster2024"
DB_NAME = "users_vital_data"


# ---------- CONNECT TO MONGODB ----------

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


# ---------- LOAD CSV ----------

df = pd.read_csv(CSV_FILE)


# ---------- PREPROCESS ----------

# convert timestamp (adjust format if needed)
df["time_stamp"] = pd.to_datetime(
    df["time_stamp"],
    format="%d-%m-%Y %H:%M"
)

# sort data properly
df = df.sort_values(["patient_id", "time_stamp"])


# ---------- INSERT DATA INTO MONGODB ----------

for patient_id in df["patient_id"].unique():

    print(f"Processing patient: {patient_id}")

    patient_data = df[df["patient_id"] == patient_id]

    # create collection (name = patient_id)
    collection = db[str(patient_id)]

    # OPTIONAL: clear old data to avoid duplicates
    collection.delete_many({})

    records = []

    for _, row in patient_data.iterrows():

        record = {
            "time_stamp": row["time_stamp"],
            "glucose": float(row["glucose"]),
            "heart_rate": float(row["heart_rate"])
        }

        records.append(record)

    # insert into MongoDB
    if records:
        collection.insert_many(records)
        print(f"Inserted {len(records)} records into {patient_id}")


print("\n✅ All patient data inserted successfully into MongoDB!")