import os
import smtplib
import ssl
from smtplib import SMTPAuthenticationError, SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email, subject, message):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")

    msg = MIMEMultipart()
    msg["From"] = "itsupport.kweph@kwe.com"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["CC"] = "reginamaye.banadera@kwe.com" #For testing only

    msg.attach(MIMEText(message, "html"))

    try:
        print("=== SENDING EMAIL ===")
        print("SMTP SERVER:", SMTP_SERVER)
        print("SMTP PORT:", SMTP_PORT)
        print("FROM:", msg["From"])
        print("TO:", msg["To"])

        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT), timeout=30) as server:
            server.set_debuglevel(1)

            server.sendmail(
                msg["From"],
                [msg["To"]],
                msg.as_string()
            )

        print("=== EMAIL SENT SUCCESSFULLY ===")

    except Exception as e:
        import traceback

        print("=== EMAIL ERROR ===")
        print("ERROR:", str(e))
        traceback.print_exc()

        raise