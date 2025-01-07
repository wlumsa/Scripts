import pandas as pd
from datetime import datetime

def is_valid_date(date_string):
    try:
        # If the string can be parsed into a date, it's a valid date
        datetime.strptime(date_string, '%B %d')
        return True
    except ValueError:
        # If a ValueError occurs, it's not a valid date string
        return False

def process_volunteer_data(file_path):
    # Load the Excel file
    data = pd.read_excel(file_path)
    
    # Check for the 'FormQId' identifier in the first row and drop it if necessary
    data_cleaned = data.drop(index=0) if data.iloc[0, 0] == 'FormQId' else data
    
    # Initialize an empty dictionary to store availability
    availability_dict_with_gender = {}

    for index, row in data_cleaned.iterrows():
        name = f"{row['What is your first name?'].strip()} {row['What is your last name?'].strip()}"
        gender = "Brother" if row['Are you a brother or a sister?'].strip().lower() == "brother" else "Sister"
        name_with_gender = f"{name} ({gender})"
        
        # Split the days by comma and strip each one
        available_days = [day.strip() for day in str(row["Please select all that apply "]).split(',')]
        
        for day in available_days:
            if day and is_valid_date(day):  # Check if the day is not empty and is a valid date
                if day not in availability_dict_with_gender:
                    availability_dict_with_gender[day] = []
                availability_dict_with_gender[day].append(name_with_gender)

    return availability_dict_with_gender

def write_to_excel(availability, output_file_path):
    # Create a dictionary where each key is a date and the value is a list of volunteers
    organized_data = {date: volunteers for date, volunteers in availability.items() if is_valid_date(date)}
    
    # Create a DataFrame with the maximum length to accommodate the longest list
    max_len = max(len(v) for v in organized_data.values())
    df_output = pd.DataFrame(index=range(max_len))
    
    # Assign the lists to the DataFrame, with dates as column headers
    for date, volunteers in organized_data.items():
        df_output[date] = pd.Series(volunteers)
    
    # Write the DataFrame to an Excel file
    df_output.to_excel(output_file_path, index=False)
def get_volunteer_counts(availability):
    # Initialize a dictionary to hold the count of appearances for each volunteer
    volunteer_counts = {}

    # Iterate through each date's volunteers in the availability dictionary
    for volunteers in availability.values():
        for volunteer in volunteers:
            # If the volunteer is already in the dictionary, increment their count
            if volunteer in volunteer_counts:
                volunteer_counts[volunteer] += 1
            # Otherwise, add them to the dictionary with a count of 1
            else:
                volunteer_counts[volunteer] = 1

    return volunteer_counts
# Example usage
file_path = 'volunteers.xlsx'  # Replace with your actual file path
output_file_path = 'volunteer_availability.xlsx'  # The path where you want to save the output Excel file

volunteer_availability = process_volunteer_data(file_path)



volunteer_counts = get_volunteer_counts(volunteer_availability)

# Display the counts
for volunteer, count in volunteer_counts.items():
    print(f"{volunteer}: {count}")


