
import json
import requests
from datetime import datetime, timedelta

# Function to convert datetime to epoch in milliseconds
def datetime_to_epoch(dt):
    return int(dt.timestamp() * 1000)

# Function to download electricity price data for the next day (after 14:00)
def download_next_day_prices():
    # Get the current time
    current_time = datetime.now()

    # Check if the current time is after 14:00 (2 PM)
    if current_time.hour >= 14:
        # Calculate the start time for the next day (next 00:00)
        start_time = datetime(current_time.year, current_time.month, current_time.day) + timedelta(days=1)

        # Calculate the end time for the next day (next 23:59)
        end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

        # Convert both start and end times to epoch in milliseconds
        start_epoch = datetime_to_epoch(start_time)
        end_epoch = datetime_to_epoch(end_time)

        # API URL for fetching the data
        url = f"https://api.awattar.at/v1/marketdata?start={start_epoch}&end={end_epoch}"

        # Make the GET request to fetch the data
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            # Save the data to a file (you can change the filename as needed)
            with open(f"awattar_prices_{start_time.strftime('%Y-%m-%d')}.json", 'w') as file:
                json.dump(data, file, indent=4)

            print(f"Successfully downloaded data for {start_time.strftime('%Y-%m-%d')}")
        else:
            print(f"Failed to download data. Status code: {response.status_code}")
    else:
        print("It is not yet 14:00. Script will not run.")

# Run the function to download data for the next day
download_next_day_prices()
