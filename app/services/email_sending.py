import os
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import getaddresses


def send_email(to_email, subject, message):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")

    cc_email = "reginamaye.banadera@kwe.com, eloisa.cruz@kwe.com"  # For testing only

    msg = MIMEMultipart()
    msg["From"] = "itsupport.kweph@kwe.com"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["CC"] = cc_email

    msg.attach(MIMEText(message, "html"))

    # Build actual SMTP recipients (TO + CC)
    recipients = [to_email]

    cc_recipients = [
        email for _, email in getaddresses([cc_email])
        if email
    ]

    recipients.extend(cc_recipients)

    try:
        print("=== SENDING EMAIL ===")
        print("SMTP SERVER:", SMTP_SERVER)
        print("SMTP PORT:", SMTP_PORT)
        print("FROM:", msg["From"])
        print("TO:", msg["To"])
        print("CC:", msg["CC"])
        print("ALL RECIPIENTS:", recipients)

        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT), timeout=30) as server:
            server.set_debuglevel(2)

            server.sendmail(
                msg["From"],
                recipients,
                msg.as_string()
            )

        print("=== EMAIL SENT SUCCESSFULLY ===")

    except Exception as e:
        print("=== EMAIL ERROR ===")
        print("ERROR:", str(e))
        traceback.print_exc()
        raise
