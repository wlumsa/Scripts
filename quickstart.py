import datetime
import os.path
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import time

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.settings.readonly",
    "https://www.googleapis.com/auth/calendar.addons.execute"
]

# Get user inputs
NAME = input("Enter the name of the Person: ")
SPREADSHEET_ID = input("Enter the spreadsheet ID: ")
SEMESTER = input("Enter the semester(Fall 2024 or Winter 2025): ")

def get_range_name(semester):
    """Return the range name based on the semester."""
    if semester == "Fall 2024":
        return 'Fall!A1:H'
    elif semester == "Winter 2025":
        return 'Winter!A1:H'
    else:
        raise ValueError("Invalid semester")

def extract_classes_schedule(df, semester="Fall 2024"):
    """Extract class schedules from the DataFrame."""
    classes = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Define start and end dates for each semester
    if semester == "Fall 2024":
        start_dates = ["2024-09-09", "2024-09-10", "2024-09-11", "2024-09-12", "2024-09-13", "2024-09-14", "2024-09-15"]
        end_dates = ["2024-11-25", "2024-12-05", "2024-12-06", "2024-12-07", "2024-12-08", "2024-12-09", "2024-12-10"]
    elif semester == "Winter 2025":
        start_dates = ["2025-01-06", "2025-01-07", "2025-01-08", "2025-01-09", "2025-01-10", "2025-01-11", "2025-01-12"]
        end_dates = ["2025-03-31", "2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04", "2025-04-05", "2025-04-06"]
    
    date_map = {day: (start, end) for day, start, end in zip(days, start_dates, end_dates)}

    # Extract class schedules for each day
    for day in days:
        day_classes = df[["Time", day]].dropna()
        if not day_classes.empty:
            grouped = day_classes.groupby(day)
            for class_info, times in grouped:
                start_time = times["Time"].iloc[0].strftime("%H:%M")
                end_time = times["Time"].iloc[-1].strftime("%H:%M")
                class_entry = {
                    "Subject": class_info,
                    "Start Date": date_map[day][0],
                    "Start Time": start_time,
                    "End Date": date_map[day][1],
                    "End Time": end_time,
                    "Day": day  # Add the day of the week to the class entry
                }
                classes.append(class_entry)
    
    return classes

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # Check if token.json file exists for storing user's access and refresh tokens
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build the service for Google Calendar and Sheets API
        service = build("calendar", "v3", credentials=creds)
        serviceSheets = build('sheets', 'v4', credentials=creds)

        sheet = serviceSheets.spreadsheets()
        
        # Get the range name based on the semester
        RANGE_NAME = get_range_name(SEMESTER)
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        print(result)
        
        # Process the data from the spreadsheet
        columns = result['values'][0]
        data = result['values'][1:]
        for row in data:
            while len(row) < len(columns):
                row.append('')
        df = pd.DataFrame(data, columns=columns)
        df.replace("None", pd.NA, inplace=True)
        df["Time"] = pd.to_datetime(df["Time"], errors='coerce')
        
        # Extract class schedules and convert to DataFrame
        classes = extract_classes_schedule(df)
        classes_df = pd.DataFrame(classes)
        classes_df = classes_df.dropna(subset=["Subject"])
        classes_df = classes_df[classes_df["Subject"] != ""]
        print(classes_df)
        
        # Create a new calendar
        calendar = {
            'summary': f"{NAME} {SEMESTER}",
            'timeZone': 'America/New_York'
        }
        created_calendar = service.calendars().insert(body=calendar).execute()
        calendar_id = created_calendar['id']

        # Insert events into the calendar
        for class_event in classes_df.to_dict(orient="records"):
            event = {
                'summary': class_event['Subject'],
                'start': {
                    'dateTime': f"{class_event['Start Date']}T{class_event['Start Time']}:00",
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': f"{class_event['Start Date']}T{class_event['End Time']}:00",
                    'timeZone': 'America/New_York',
                },
                'recurrence': [
                    f"RRULE:FREQ=WEEKLY;UNTIL={class_event['End Date'].replace('-', '')}T235959Z"
                ],
            }
            created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"Event created: {created_event.get('htmlLink')}")
            time.sleep(1)  # Delay to avoid exceeding quota limits

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()