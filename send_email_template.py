import smtplib

from emailSendWithPrices import server

email = input("Sender Email: ")
reciever_email = input("Reciever Email: ")
subject = input("Subject: ")
message = input("Message: ")

text = f"Subject: {subject}\n\n{message}"

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(email, "vrzt jzez okjv itbv ")
server.sendmail(email, reciever_email, text)
server.quit()