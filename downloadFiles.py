import os
import sqlite3

import requests
from datetime import datetime, timezone
import time
import lastDayPrice
import nextDayPrice

# Function to create the directory to save CSV files in your project
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to download a single CSV file with retry logic and backoff
def download_csv(url, save_path, retries=5, delay=5, max_delay=60):
    attempt = 0
    while attempt < retries:
        response = requests.get(url)

        # If the request is successful
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {save_path}")
            return True

        # If rate-limited (status code 429)
        elif response.status_code == 429:
            print(f"Rate-limited. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)  # Exponential backoff, max delay = 60 seconds
            attempt += 1

        # If the request failed for other reasons (e.g., 500 server error)
        else:
            print(f"Failed to download {url}. Status code: {response.status_code}")
            attempt += 1
            time.sleep(delay)  # Wait before retrying

    print(f"Failed to download {url} after {retries} attempts.")
    return False

# Main function to download all the CSV files from 2023 to now
def download_awattar_csvs(start_year=2023, end_year=None):
    # If no end year is provided, use the current year
    if end_year is None:
        end_year = datetime.now().year

    base_url = "https://api.awattar.at/v1/marketdata/csv"

    # Use the current working directory (project folder) to save the files
    save_directory = os.path.join(os.getcwd(), "awattar_csv_files")

    create_directory(save_directory)

    # Counter to track the number of downloads
    download_counter = 0

    # Loop through years and months
    for year in range(start_year, end_year + 1):
        # Start from January (1) to December (12) or the current month
        start_month = 1
        end_month = 12 if year < end_year else datetime.now().month

        for month in range(start_month, end_month + 1):
            # Generate URL for each month (e.g., https://api.awattar.at/v1/marketdata/csv/2023/1/)
            url = f"{base_url}/{year}/{month}/"
            file_name = f"{year}_{month}.csv"
            save_path = os.path.join(save_directory, file_name)

            # Attempt to download the CSV file with retry logic
            success = download_csv(url, save_path)
            if success:
                download_counter += 1

            # After every 8 successful downloads, wait for 5 seconds
            if download_counter % 8 == 0:
                print(f"Downloaded 8 files, waiting for 5 seconds...")
                time.sleep(6)


# Run the script
#download_awattar_csvs()

#get the next day price
#nextDayPrice.download_next_day_prices()

#lastdayprice -> only for test
lastDayPrice.download_yesterday_prices()

def save_to_database(data):
    conn = sqlite3.connect('energy_prices.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS energy_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        hour INTEGER,
                        price REAL,
                        unit TEXT,
                        UNIQUE(date, hour))''')

    # Insert data into the database
    for price_data in data['data']:
        # Convert the timestamp to a timezone-aware datetime object and then format as string
        timestamp = price_data['start_timestamp'] / 1000  # Convert from milliseconds to seconds
        price_datetime = datetime.fromtimestamp(timestamp, timezone.utc)
        date_str = price_datetime.date().strftime('%Y-%m-%d')  # Format date as string
        hour = price_datetime.hour
        price = price_data['marketprice']
        unit = price_data['unit']

        # Check if the entry for this date and hour already exists
        cursor.execute('''SELECT * FROM energy_prices WHERE date = ? AND hour = ?''', (date_str, hour))
        existing_entry = cursor.fetchone()

        if existing_entry is None:
            # Insert the new record if it doesn't exist
            cursor.execute('''INSERT INTO energy_prices (date, hour, price, unit)
                              VALUES (?, ?, ?, ?)''', (date_str, hour, price, unit))
            print(f"Inserted data for {date_str} {hour}:00")
        else:
            # If it exists, you can either update or skip
            # Uncomment the following to update the existing record (if needed)
            # cursor.execute('''UPDATE energy_prices SET price = ?, unit = ? WHERE date = ? AND hour = ?''',
            #                (price, unit, date_str, hour))
            print(f"Data for {date_str} {hour}:00 already exists, skipping.")

    conn.commit()
    conn.close()

