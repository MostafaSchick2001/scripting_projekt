import requests
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3

# Funktion: Epoch-Timestamp in Millisekunden
def datetime_to_epoch(dt):
    return int(dt.timestamp() * 1000)

# Funktion: Strompreise für den nächsten Tag abrufen
def fetch_tomorrow_prices():
    current_time = datetime.now()
    if current_time.hour < 14:
        raise Exception("Preise für morgen sind erst nach 14:00 Uhr verfügbar.")

    # Zeitfenster für morgen berechnen
    start_time = datetime(current_time.year, current_time.month, current_time.day) + timedelta(days=1)
    end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

    start_epoch = datetime_to_epoch(start_time)
    end_epoch = datetime_to_epoch(end_time)

    url = f"https://api.awattar.at/v1/marketdata?start={start_epoch}&end={end_epoch}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Datenabruf fehlgeschlagen. Status-Code: {response.status_code}")

# Funktion: Preise analysieren
def analyze_prices(data):
    prices = [entry['marketprice'] for entry in data['data']]
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)

    min_hour = data['data'][prices.index(min_price)]['start_timestamp']
    max_hour = data['data'][prices.index(max_price)]['start_timestamp']

    min_hour = datetime.fromtimestamp(min_hour / 1000).hour
    max_hour = datetime.fromtimestamp(max_hour / 1000).hour

    return {
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "min_hour": min_hour,
        "max_hour": max_hour,
        "prices": prices
    }

# Funktion: HTML-E-Mail erstellen
def create_email(data, analysis):
    prices_table = ""
    for i, price in enumerate(analysis['prices']):
        hour = (datetime.fromtimestamp(data['data'][i]['start_timestamp'] / 1000).hour)
        prices_table += f"<tr><td>{hour}:00</td><td>{price:.2f} €</td></tr>"

    email_body = f"""
    <html>
    <body>
        <h2>Strompreisprognose für morgen</h2>
        <p>Durchschnittlicher Preis: {analysis['avg_price']:.2f} €/MWh</p>
        <p>Günstigste Stunde: {analysis['min_hour']}:00 ({analysis['min_price']:.2f} €/MWh)</p>
        <p>Teuerste Stunde: {analysis['max_hour']}:00 ({analysis['max_price']:.2f} €/MWh)</p>
        <p><strong>Empfehlung:</strong></p>
        <ul>
            <li>Verwenden Sie energieintensive Geräte um {analysis['min_hour']}:00 für geringere Stromkosten.</li>
            <li>Vermeiden Sie hohe Energieverbräuche um {analysis['max_hour']}:00.</li>
        </ul>
        <h3>Stündliche Preise</h3>
        <table border="1">
            <tr><th>Stunde</th><th>Preis (€)</th></tr>
            {prices_table}
        </table>
    </body>
    </html>
    """
    return email_body

# Funktion: E-Mail senden
def send_email(html_content):
    sender_email = "mostafasheikh2001@gmail.com"
    recipient_emails = ["mostafa.shikhahmad@hotmail.com"]
    password = "vrzt jzez okjv itbv "

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Morgen: Strompreisprognose"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_emails)

    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Sichere Verbindung herstellen
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())
        print("E-Mail erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")

# Hauptfunktion: Daten abrufen, analysieren und E-Mail senden
def main():
    try:
        data = fetch_tomorrow_prices()
        analysis = analyze_prices(data)
        email_content = create_email(data, analysis)
        send_email(email_content)
    except Exception as e:
        print(f"Fehler: {e}")

# Skript ausführen
if __name__ == "__main__":
    main()
