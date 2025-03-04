# Iftar Volunteering Registration Scheduling Script
# Last Updated: 3/2/2025
# Name: Yusra Hassan (169024293)
# Notes:
# - This code was written for the "Daily Iftar Coordination" spreadsheet and uses the input data of the form responses sheet
# - Outputs schedule in "Registration.csv" (same folder)
# - Ensure columns match perfectly if reusing code, and make sure the results make sense!
# - The code can be improved by coming up with an algorithm for volunteering distribution (currently we have random selection)

# Set-up  --------------------------------------------------
import pandas as pd
import numpy as np
import datetime as dt
raw_data = pd.read_csv("Daily Iftar Coordination - Form_Responses.csv")
iftars = raw_data
bro_needed = 6
sis_needed = 4

# Function to assign roles
def assign_roles(row):
    brothers = row["Brothers"][:]  # Copy to avoid modifying the original list
    sisters = row["Sisters"][:]

    np.random.shuffle(brothers) # in-place shuffle
    np.random.shuffle(sisters)
    
    # Assign setup/distribution teams
    setup_distr_brothers = brothers[:4]  # First 4 brothers
    remaining_brothers = brothers[4:]  # Remaining brothers after setup
    
    setup_distr_sisters = sisters[:2]  # First 2 sisters
    remaining_sisters = sisters[2:]  # Remaining sisters after setup
    
    # Assign registration teams
    registration_brothers = remaining_brothers[:2]  # Next 2 brothers if available
    registration_sisters = remaining_sisters[:2]  # Next 2 sisters if available
    
    return pd.Series({
        "Setup + Distribution (4 Brothers)": setup_distr_brothers,
        "Setup + Distribution (2 Sisters)": setup_distr_sisters,
        "Registration (2 Brothers)": registration_brothers,
        "Registration (2 Sisters)": registration_sisters,
        "Pickup": ""
    })

# Clean-up --------------------------------------------------
# Remove Furqan and Syed, since they'll be there anyway
iftars["Full Name"] = iftars["First Name"].str.capitalize() + " " + iftars["Last Name"].str.capitalize()
iftars = iftars.loc[~iftars["Full Name"].isin(["Furqan Siddiqui", "Syed Ahmed"])]
iftars = iftars.reset_index()

# Remove extra spacing in gender
iftars["Gender"] = iftars["Gender"].str.replace(r" ", r"")

# Combine week dates into one column
iftars["Date String"] = iftars.filter(like="Week").fillna('').agg(','.join, axis=1) # combine week columns info into one
iftars['Date String'] = iftars['Date String'].str.findall(r'[^,]+').str.join(', ') # remove leading/lagging commas/spaces
iftars['Date String'] = iftars['Date String'].replace("", np.nan)
iftars = iftars.filter(regex='^(?!First|Last|Week)', axis = 1) # ?!: negative lookahead. Don't select stuff that starts with first, last or week

# Keep track of date counts per person, **** In the future: optimize who is picked for volunteering here!
# iftars["Num Dates"] = iftars["Date String"].str.count(",") + 1
# iftars["Num Dates"] = iftars["Num Dates"].fillna(0)
# unassigned = iftars[iftars["Num Dates"] == 0]
# record = pd.DataFrame({"Name" : iftars[iftars["Num Dates"] != 0]["Full Name"], "Times Helped": 0})

# Separate the dates, so the data is clean and accessible
iftars["Date String"] = iftars["Date String"].str.split(", ")
iftars = iftars.explode("Date String")
iftars.index = list(range(len(iftars))) # re-set index

# Use regex to convert to standard date type
iftars["Date"] = iftars["Date String"].str.replace(r"\w+ (\w+ \d{1,2}).*", r"\1", regex=True) + ", 2025"
iftars["Date"] = pd.to_datetime(iftars["Date"]).dt.strftime("%m/%d/%Y")
iftars = iftars.sort_values("Date")

# Remove Grand Iftar day
iftars = iftars[iftars["Date"] != "03/18/2025"]

# Begin scheduling --------------------------------------------------
# Ensure there are enough volunteers per date (at least 6 guys, 4 girls for 2025)
sufficient = iftars.groupby(["Date", "Gender"])["index"].count().reset_index()
sufficient = sufficient.pivot(index='Date', columns='Gender', values='index').reset_index()
sufficient["Total"] = sufficient["Sister"] + sufficient["Brother"]

# Compute need (difference between required and real if > 0)
sufficient["No. Brothers Still Needed"] = bro_needed - sufficient["Brother"]
sufficient["No. Sisters Still Needed"] = sis_needed - sufficient["Sister"]
sufficient["No. Sisters Still Needed"] = np.where(sufficient["No. Sisters Still Needed"] < 0, 0, sufficient["No. Sisters Still Needed"])
sufficient["No. Brothers Still Needed"] = np.where(sufficient["No. Brothers Still Needed"] < 0, 0, sufficient["No. Brothers Still Needed"])
sufficient = sufficient.rename(columns={"Brother": "No.Brothers", "Sister": "No.Sisters"})

# Create a quick sched (can add stricter head after group to limit, but we won't do that for now)
brothers = (iftars[iftars["Gender"] == "Brother"]
            .groupby("Date")
            .head(12)
            .groupby("Date")
            .agg(list)["Full Name"]
            .reset_index()
            .rename(columns={"Full Name": "Brothers"}))
sisters = (iftars[iftars["Gender"] == "Sister"]
           .groupby("Date")
           .head(12)
           .groupby("Date")
           .agg(list)["Full Name"]
           .reset_index()
           .rename(columns={"Full Name": "Sisters"}))
sched = sisters.merge(brothers, on = "Date").merge(sufficient, on = "Date")

# apply role-assignment
sched[["Setup + Distribution (4 Brothers)", "Setup + Distribution (2 Sisters)", "Registration (2 Brothers)", "Registration (2 Sisters)", "Pickup"]] = sched.apply(assign_roles, axis=1)

# Save file --------------------------------------------------
# Print list results a little nicer
def list_to_str(lst):
    return ", ".join(lst)
sched = sched.map(lambda x: ", ".join(x) if isinstance(x, list) else x)

# Fix order
sched = sched[["Date", "Pickup", "Setup + Distribution (4 Brothers)", "Setup + Distribution (2 Sisters)", "Registration (2 Brothers)", "Registration (2 Sisters)", "Sisters", "Brothers", "No.Brothers", "No.Sisters", "Total",	"No. Brothers Still Needed", "No. Sisters Still Needed"]]
sched.to_csv("Registration.csv", index = False)


