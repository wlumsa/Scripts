import pandas as pd
from supabase import create_client, Client
import uuid
from dotenv import load_dotenv
import os
# Initialize the Supabase client
load_dotenv()

# Get the API keys from environment variables
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

month_mapping = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

def insert_prayer_timing():
    prayer_timing_data = {
        "updated_at": "2024-07-28T15:05:32.685+00",
        "created_at": "2024-07-28T15:05:32.685+00"
    }
    try:
        prayer_timing_response = supabase.table('prayer_timings').insert(prayer_timing_data).execute()
        print("Prayer timing response:", prayer_timing_response)
        return prayer_timing_response.data[0]['id']
    except Exception as e:
        print("Error inserting prayer timing:", e)
        raise

def insert_month(prayer_timing_id, month, order):
    month_data = {
        "id": str(uuid.uuid4()),  # Generate a unique ID
        "_order": order,
        "_parent_id": prayer_timing_id,
        "month": month
    }
    try:
        month_response = supabase.table('prayer_timings_month').insert(month_data).execute()
        print("Month response:", month_response)
        return month_response.data[0]['id']
    except Exception as e:
        print("Error inserting month:", e)
        raise

def insert_days(month_id, df):
    days_data = []
    for _, row in df.iterrows():
        if pd.isna(row["Day"]):
            continue  # Skip rows where "Day" is NaN
        day_data = {
            "id": str(uuid.uuid4()),  # Generate a unique ID for each day
            "_order": int(row["Day"]),
            "_parent_id": month_id,
            "day": int(row["Day"]),
            "fajr": row.get("Fajr Dawn", None),  # Use .get() to avoid KeyError
            "fajr_iqamah": row.get("Fajr Dawn Iqamah", None),
            "sunrise": row.get("Shorok Sunrise", None),
            "dhuhr": row.get("Dhuhr Noon", None),
            "dhuhr_iqamah": row.get("Dhuhr Noon Iqamah", None),
            "asr": row.get("Asr Afternoon", None),
            "asr_iqamah": row.get("Asr Afternoon Iqamah", None),
            "maghrib": row.get("Magrib Sunset", None),
            "maghrib_iqamah": row.get("Magrib Sunset Iqamah", None),
            "isha": row.get("Isha Evening", None),
            "isha_iqamah": row.get("Isha Evening Iqamah", None)
        }
        days_data.append(day_data)
    
    for day_data in days_data:
        try:
            day_response = supabase.table('prayer_timings_month_days').insert(day_data).execute()
            print("Day response:", day_response)
        except Exception as e:
            print("Error inserting day:", e)
            raise

# Load the Excel file
file_path = "yearly_timetable_cleaned.xlsx"
xls = pd.ExcelFile(file_path)
column_names = [
    "Day", "Fajr Dawn", "Shorok Sunrise", "Dhuhr Noon", "Asr Afternoon", "Magrib Sunset", "Isha Evening",
    "Fajr Dawn Iqamah", "Dhuhr Noon Iqamah", "Asr Afternoon Iqamah", "Magrib Sunset Iqamah", "Isha Evening Iqamah"
]
# Insert the prayer_timing and get the prayer_timing ID
prayer_timing_id = insert_prayer_timing()

# Process and insert data for each sheet (month)
for i in range(1, 13):
    sheet_name = f"Table {i}"
    month_name = month_mapping[i]
    df = pd.read_excel(xls, sheet_name=sheet_name, header=1)  # Read the Excel file, skipping the first row
    df.columns = column_names  # Set the correct column names
    
    # Insert the month and get the month ID
    month_id = insert_month(prayer_timing_id, month_name, i)  # Pass the order as the loop index
    
    # Insert the days
    insert_days(month_id, df)

print("Data insertion completed successfully.")