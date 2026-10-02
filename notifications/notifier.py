import os
import smtplib
from email.message import EmailMessage

def send_email(subject, body):
    """
    Optional SMTP notification. Configure environment variables:
    JOBBOT_SMTP_HOST, JOBBOT_SMTP_PORT, JOBBOT_SMTP_USER,
    JOBBOT_SMTP_PASSWORD, JOBBOT_TO_EMAIL.
    """
    host=os.getenv("JOBBOT_SMTP_HOST")
    port=int(os.getenv("JOBBOT_SMTP_PORT","587"))
    user=os.getenv("JOBBOT_SMTP_USER")
    password=os.getenv("JOBBOT_SMTP_PASSWORD")
    to=os.getenv("JOBBOT_TO_EMAIL")
    if not all([host,user,password,to]):
        return False, "SMTP configuration incomplete"

    msg=EmailMessage()
    msg["Subject"]=subject
    msg["From"]=user
    msg["To"]=to
    msg.set_content(body)

    with smtplib.SMTP(host,port,timeout=30) as server:
        server.starttls()
        server.login(user,password)
        server.send_message(msg)
    return True, "Email sent"
