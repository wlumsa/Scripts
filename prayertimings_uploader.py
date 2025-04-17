import pandas as pd
from supabase import create_client, Client
import uuid
from dotenv import load_dotenv
import os
from datetime import datetime
import math

# Initialize the Supabase client
load_dotenv()
url=""
key=""
supabase: Client = create_client(url, key)

# Load the Excel file
file_path = "Prayer_timings.xlsx"
xls = pd.ExcelFile(file_path)

# Updated column names mapping
column_names = [
    "Day", "Fajr Dawn", "Shorok Sunrise", "Dhuhr Noon", "Asr Afternoon", "Magrib Sunset", "Isha Evening",
    "Fajr Iqamah", "Dhuhr 1", "Dhuhr 2", "Asr Aftern'n",
    "Magrib Sunset Iqamah", "Isha Evening Iqamah"
]

# Month mapping for sheet names
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
    12: "December",
}
def ensure_month_exists(month_name):
    # Check if the month already exists
    existing_month = supabase.table("prayer_timings_month").select("id").eq("month", month_name).execute()
    
    if not existing_month.data:
        # If it doesn't exist, insert a new row in prayer_timings to get an ID
        prayer_timing_data = {
            # Add any necessary fields for the prayer_timings table
        }
        prayer_timing_response = supabase.table("prayer_timings").insert(prayer_timing_data).execute()
        parent_id = prayer_timing_response.data[0]['id']  # Get the newly created ID

        # Generate a unique ID for the month
        month_id = str(uuid.uuid4())  # Generate a unique ID for the month

        # Now insert the month with the new _parent_id
        month_data = {
            "id": month_id,  # Set the generated ID
            "month": month_name,  # Adjust this based on your actual column name
            "_order": 1,  # Set a default order value
            "_parent_id": parent_id  # Set the parent ID to the newly created ID
        }
        response = supabase.table("prayer_timings_month").insert(month_data).execute()
        return response.data[0]['id']  # Return the newly created month ID
    else:
        return existing_month.data[0]['id']  # Return the existing month ID

# Function to convert time objects to strings
def convert_time_to_string(value):
    if isinstance(value, pd.Timestamp):
        return value.strftime('%H:%M')  # Convert to string in HH:MM format
    return value

# Function to safely handle NaN values
def handle_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return None  # Replace NaN with None
    return value

# Process and insert data for each sheet (month)
for i in range(1, 4):  # Loop through sheets 1 to 3
    sheet_name = f"Table {i}"
    month_name = month_mapping[i]
    
    # Ensure the month exists in the prayer_timings_month table and get its ID
    month_id = ensure_month_exists(month_name)
    
    df = pd.read_excel(xls, sheet_name=sheet_name, header=1)
    df.columns = column_names

    # Insert data into Supabase
    for index, row in df.iterrows():
        data = {
            "id": str(uuid.uuid4()),  # Generate a unique ID
            "_order": index + 1,  # Set the order based on the index
            "day": handle_nan(row["Day"]),
            "fajr": handle_nan(convert_time_to_string(row["Fajr Dawn"])),
            "sunrise": handle_nan(convert_time_to_string(row["Shorok Sunrise"])),
            "dhuhr": handle_nan(convert_time_to_string(row["Dhuhr Noon"])),
            "asr": handle_nan(convert_time_to_string(row["Asr Afternoon"])),
            "maghrib": handle_nan(convert_time_to_string(row["Magrib Sunset"])),
            "isha": handle_nan(convert_time_to_string(row["Isha Evening"])),
            "fajr_iqamah": handle_nan(convert_time_to_string(row["Fajr Iqamah"])),
            "dhuhr_iqamah_1": handle_nan(convert_time_to_string(row["Dhuhr 1"])),
            "dhuhr_iqamah_2": handle_nan(convert_time_to_string(row["Dhuhr 2"])),
            "asr_iqamah_1": handle_nan(convert_time_to_string(row["Asr Aftern'n"])),
            "maghrib_iqamah": handle_nan(convert_time_to_string(row["Magrib Sunset Iqamah"])),
            "isha_iqamah": handle_nan(convert_time_to_string(row["Isha Evening Iqamah"])),
            "_parent_id": month_id  # Link to the month ID
        }
        
        # Insert the data into the Supabase table
        supabase.table("prayer_timings_month_days").insert(data).execute()

print("Data insertion completed successfully.")

