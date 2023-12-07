import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred = credentials.Certificate('firebaseconfig.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def upload_monthly_data(excel_path, sheet_name):
    # Read the specific sheet of the Excel file into a pandas dataframe
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=0)

    # Set the column names
    df.columns = ["Day", 
                  "Fajr", "Sunrise", "Dhuhr", "Asr", 
                  "Magrib", "Isha",
                  "Fajr Iqamah", "Dhuhr Iqamah", "Asr Iqamah", 
                  "Magrib Iqamah", "Isha Iqamah"]

    # Convert the dataframe to a dictionary
    data_dict = df.to_dict(orient='records')

    # Reference to Firestore collection for the month
    month_ref = db.collection('PrayerTimings')

    # Batch write operation
    for record in data_dict:
        day = str(record['Day'])  # Convert day to string to use as document ID
       # Set the document in Firestore using the day as the document ID
        month_ref.document(sheet_name).collection('Days').document(day).set(record)


    print(f"Data from sheet '{sheet_name}' uploaded to Firestore under 'PrayerTimings/{sheet_name}/Days/{day}'")

# Usage
excel_file_path = 'yearly_timetable.xlsx'
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

for month in months:
    upload_monthly_data(excel_file_path, month)

print('All data uploaded successfully.')
