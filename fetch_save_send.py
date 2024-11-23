import requests
from datetime import datetime, timedelta, timezone
import json
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ----------------------------------------------- SCRIPT TO FETCH THE DATA AND SAVE TO DB --------------------------------------------

# Function to convert datetime to epoch in milliseconds
def datetime_to_epoch(dt):
    return int(dt.timestamp() * 1000)

# Function to save data to SQLite database
def save_to_database(data):
    conn = sqlite3.connect('energy_prices.db')
    cursor = conn.cursor()

    # Clear the existing data from the database before inserting new data
    cursor.execute('DELETE FROM energy_prices')

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

    conn.commit()
    conn.close()

# Function to download electricity price data for all hours of tomorrow
def download_tomorrow_prices():
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
        # Save the data to a JSON file
        filename = f"awattar_prices_{start_time.strftime('%Y-%m-%d')}.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

        # Save data to your database
        save_to_database(data)
    else:
        print(f"Failed to download data. Status code: {response.status_code}")

# ----------------------------------------------- SCRIPT TO SEND EMAIL --------------------------------------------

def send_email_with_prices():
    conn = sqlite3.connect('energy_prices.db')
    cursor = conn.cursor()

    # Get tomorrow's date
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    # Query data for tomorrow
    cursor.execute('SELECT hour, price, unit FROM energy_prices WHERE date = ? ORDER BY hour', (tomorrow_date,))
    rows = cursor.fetchall()
    conn.close()

    # If no data is found, exit
    if not rows:
        print("No data found for tomorrow.")
        return

    # Calculate statistics
    prices = [row[1] for row in rows]
    average_price = sum(prices) / len(prices)
    cheapest_hour = min(rows, key=lambda x: x[1])  # Row with the lowest price
    most_expensive_hour = max(rows, key=lambda x: x[1])  # Row with the highest price

    # Extract details for recommendations
    cheapest_hour_time = f"{cheapest_hour[0]}:00"
    cheapest_hour_price = cheapest_hour[1]
    most_expensive_hour_time = f"{most_expensive_hour[0]}:00"
    most_expensive_hour_price = most_expensive_hour[1]

    # Generate HTML table for the email
    html_table = """
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>Hour</th>
            <th>Price</th>
            <th>Unit</th>
        </tr>
    """
    for row in rows:
        hour, price, unit = row
        html_table += f"""
        <tr>
            <td>{hour}:00</td>
            <td>{price:.2f}</td>
            <td>{unit}</td>
        </tr>
        """
    html_table += "</table>"

    # Create email content
    subject = f"Electricity Prices for {tomorrow_date}"
    body = f"""
    <h2>Electricity Price Preview for {tomorrow_date}</h2>
    <p><strong>Average Price:</strong> {average_price:.2f} €/MWh</p>
    <p><strong>Cheapest Hour:</strong> {cheapest_hour_time} ({cheapest_hour_price:.2f} €/MWh)</p>
    <p><strong>Most Expensive Hour:</strong> {most_expensive_hour_time} ({most_expensive_hour_price:.2f} €/MWh)</p>
    <h3>Recommendations:</h3>
    <ul>
        <li>Use energy-intensive appliances at <strong>{cheapest_hour_time}</strong> to save costs.</li>
        <li>Avoid high energy usage at <strong>{most_expensive_hour_time}</strong>.</li>
    </ul>
    <h3>Full Price Table:</h3>
    {html_table}
    <p>Plan your energy usage wisely!</p>
    """

    # Email setup
    sender_email = "mostafasheikh2001@gmail.com"
    recipient_emails = ["mostafa.shikhahmad@hotmail.com"]
    password = "vrzt jzez okjv itbv"

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)  # Convert list to comma-separated string
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


# ----------------------------------------------- GET DATA FROM THE DB --------------------------------------------
def display_prices():
    conn = sqlite3.connect('energy_prices.db')
    cursor = conn.cursor()

    # Query all data, ordered by date and hour starting from 00
    cursor.execute('SELECT date, hour, price, unit FROM energy_prices ORDER BY date, hour')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No data available in the database.")
        return

    # Display as a table with proper formatting
    print(f"{'Date':<12} {'Hour':<6} {'Price (€/MWh)':<15} {'Unit':<5}")
    print("-" * 40)
    for row in rows:
        date, hour, price, unit = row
        # Ensure hour is displayed as two digits (e.g., '03' instead of '3')
        hour_str = f"{hour:02d}"
        print(f"{date:<12} {hour_str:<6} {price:<15.2f} {unit:<5}")
# ----------------------------------------------- RUN SCRIPTS --------------------------------------------

download_tomorrow_prices()
send_email_with_prices()
display_prices()
