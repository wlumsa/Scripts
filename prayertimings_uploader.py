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

    # Assuming the first row contains the column headers, we'll reassign them just to be sure
    df.columns = ["Day", 
                  "Fajr", "Sunrise", "Dhuhr", "Asr", 
                  "Magrib", "Isha",
                  "Fajr Iqamah", "Dhuhr Iqamah", "Asr Iqamah", 
                  "Magrib Iqamah", "Isha Iqamah"]

    # Remove any rows where 'Day' is not a digit (just in case there are any such rows)
    df = df[df['Day'].apply(lambda x: str(x).isdigit())]

    # Convert the dataframe to a dictionary
    data_dict = df.to_dict(orient='records')

    # Reference to Firestore document for the month
    month_ref = db.collection('PrayerTimings').document(sheet_name)

    # Batch write operation
    for record in data_dict:
        # Check if 'Day' is a digit and convert it to a string
        if str(record['Day']).isdigit():
            day = str(int(record['Day']))  # Convert day to string
            # Create a document reference for the day number
            day_ref = month_ref.collection(day)

            # Add a document with a predefined ID, such as 'timings'
            day_ref.document(record).set(record)

    print(f"Data from sheet '{sheet_name}' uploaded to Firestore under 'PrayerTimings/{sheet_name}'")

# Usage
excel_file_path = 'yearly_timetable.xlsx'
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

for month in months:
    upload_monthly_data(excel_file_path, month)

print('All data uploaded successfully.')