import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred = credentials.Certificate('firebaseconfig.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def upload_monthly_data(excel_path, sheet_name):
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Print the original column names
    print("Original column names:", df.columns.tolist())

    # Define a mapping from original column names to new names
    # Example: {'OriginalName1': 'Day', 'OriginalName2': 'Fajr', ...}
    column_mapping = {
        'Beginning Time': 'Fajr',
        'Unnamed: 2': 'Sunrise',
        'Unnamed: 3': 'Dhuhr',
        'Unnamed: 4': 'Asr',
        'Unnamed: 5': 'Maghrib',
        'Unnamed: 6': 'Isha',
        'Eqama Time': 'FajrIqamah',
        'Unnamed: 8': 'DhuhrIqamah',
        'Unnamed: 9': 'AsrIqamah',
        'Unnamed: 10': 'MaghribIqamah',
        'Unnamed: 11': 'IshaIqamah'
    }

    df.rename(columns=column_mapping, inplace=True)

    # Convert 'Day' to numeric and drop NaNs
    df['Day'] = pd.to_numeric(df['Day'], errors='coerce')
    df = df.dropna(subset=['Day'])
    df['Day'] = df['Day'].astype(int)

    # Convert the dataframe to a dictionary
    data_dict = df.to_dict(orient='records')

    # Reference to Firestore collection for the month
    month_ref = db.collection('PrayerTimings')

    # Batch write operation
    for record in data_dict:
        day = str(record['Day'])
        month_ref.document(sheet_name).collection('Days').document(day).set(record)

    print(f"Data from sheet '{sheet_name}' uploaded to Firestore under 'PrayerTimings/{sheet_name}/Days'")

# Usage


# Usage
excel_file_path = 'yearly_timetable.xlsx'
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
for month in months:
    upload_monthly_data(excel_file_path, month)

print('All data uploaded successfully.')
