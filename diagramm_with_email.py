import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend to avoid Tkinter
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
# Generate Visualization
def generate_visualizations():
    conn = sqlite3.connect('energy_prices.db')
    cursor = conn.cursor()

    # Get tomorrow's data
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    cursor.execute('SELECT hour, price FROM energy_prices WHERE date = ? ORDER BY hour', (tomorrow_date,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No data found for tomorrow.")
        return None

    hours = [row[0] for row in rows]
    prices = [row[1] for row in rows]

    # Calculate average price, cheapest and most expensive hours
    total_price = sum(prices)
    average_price = total_price / len(prices)

    cheapest_hour_time = hours[prices.index(min(prices))]
    cheapest_hour_price = min(prices)

    most_expensive_hour_time = hours[prices.index(max(prices))]
    most_expensive_hour_price = max(prices)

    # Visualization 1: Hourly Price Development
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=hours, y=prices, marker='o')
    plt.title('Hourly Electricity Prices for Tomorrow')
    plt.xlabel('Hour')
    plt.ylabel('Price (€/MWh)')
    plt.grid(True)
    plt.savefig('price_line_chart.png')
    plt.close()

    # Visualization 2: Price Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(prices, bins=10, kde=True, color='skyblue')
    plt.title('Price Distribution for Tomorrow')
    plt.xlabel('Price (€/MWh)')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.savefig('price_distribution_chart.png')
    plt.close()

    return hours, prices, average_price, cheapest_hour_time, cheapest_hour_price, most_expensive_hour_time, most_expensive_hour_price, ['price_line_chart.png', 'price_distribution_chart.png']

# Send Email with Visualizations
def send_email_with_charts():
    data = generate_visualizations()
    if not data:
        print("No data to visualize.")
        return

    hours, prices, average_price, cheapest_hour_time, cheapest_hour_price, most_expensive_hour_time, most_expensive_hour_price, images = data
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    # Generate HTML table for the email
    html_table = """
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>Hour</th>
            <th>Price</th>
            <th>Unit</th>
        </tr>
    """
    for i in range(len(hours)):
        hour = hours[i]
        price = prices[i]
        html_table += f"""
        <tr>
            <td>{hour}:00</td>
            <td>{price:.2f}</td>
            <td>€/MWh</td>
        </tr>
        """
    html_table += "</table>"

    # Email setup
    sender_email = "mostafasheikh2001@gmail.com"
    recipient_emails = ["mostafa.shikhahmad@hotmail.com","ivana.ferlin@edu.fh-joanneum.at"]
    password = "vrzt jzez okjv itbv"

    subject = "Strompreisprognose für morgen"
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

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    # Attach images
    for image_path in images:
        with open(image_path, 'rb') as f:
            mime = MIMEBase('image', 'png', filename=image_path)
            mime.add_header('Content-Disposition', 'attachment', filename=image_path)
            mime.add_header('X-Attachment-Id', image_path)
            mime.add_header('Content-ID', f"<{image_path}>")
            mime.set_payload(f.read())
            encoders.encode_base64(mime)
            msg.attach(mime)

    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())
            print("Email with visualizations sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")



##--------------------------------------------DISPLAY THE DB DATA ON THE TERMINAL----------------------------------------------------
def fetch_data_from_db():
    # Connect to the SQLite database
    conn = sqlite3.connect('energy_prices.db')
    cursor = conn.cursor()

    # Get tomorrow's date
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    # Query the database for data for tomorrow
    cursor.execute('SELECT hour, price, unit FROM energy_prices WHERE date = ? ORDER BY hour', (tomorrow_date,))
    rows = cursor.fetchall()

    conn.close()

    # If no data is found, print a message
    if not rows:
        print("No data found for tomorrow.")
        return

    # Display the data
    print(f"Electricity Price Data for {tomorrow_date}:")
    print("{:<10} {:<15} {:<10}".format("Hour", "Price (€/MWh)", "Unit"))
    print("-" * 40)
    for row in rows:
        hour, price, unit = row
        print("{:<10} {:<15} {:<10}".format(f"{hour}:00", f"{price:.2f}", unit))


send_email_with_charts()
fetch_data_from_db()