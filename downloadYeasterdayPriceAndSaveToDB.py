import requests
from datetime import datetime, timedelta, timezone
import json
import sqlite3




#-----------------------------------------------SCRIPT TO FETCH THE DATA AND SAVE TO DB--------------------------------------------


# Function to convert datetime to epoch in milliseconds
def datetime_to_epoch(dt):
    return int(dt.timestamp() * 1000)

# Function to save data to SQLite database
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
            print(f"Data for {date_str} {hour}:00 already exists, skipping.")

    # Commit the transaction and close the connection
    conn.commit()

    # Display the data from the database
    cursor.execute('SELECT date, hour, price, unit FROM energy_prices')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.close()

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
        save_to_database(data)  # Save the data to the database
    else:
        print(f"Failed to download data. Status code: {response.status_code}")

# Run the function to download data for yesterday
download_yesterday_prices()



#-----------------------------------------------SCRIPT TO DISPLAY THE DATA--------------------------------------------
import sqlite3
# Connect to the database
conn = sqlite3.connect('energy_prices.db')
cursor = conn.cursor()

# Query the data
cursor.execute('SELECT date, hour, price, unit FROM energy_prices')

# Fetch the column names
column_names = [description[0] for description in cursor.description]
print(" | ".join(column_names))  # Print column names as a header

# Fetch and print the data
rows = cursor.fetchall()
for row in rows:
    print(" | ".join(map(str, row)))  # Print each row of data

# Close the connection
conn.close()
