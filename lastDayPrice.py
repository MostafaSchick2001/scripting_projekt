import requests
from datetime import datetime, timedelta
import json

# Function to convert datetime to epoch in milliseconds
def datetime_to_epoch(dt):
    return int(dt.timestamp() * 1000)

# Function to download electricity price data for yesterday
def download_yesterday_prices():
    # Get the current time
    current_time = datetime.now()

    # Calculate the start time for yesterday (00:00)
    start_time = datetime(current_time.year, current_time.month, current_time.day) - timedelta(days=1)

    # Calculate the end time for yesterday (23:59:59)
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


# Run the function to download data for yesterday
download_yesterday_prices()
