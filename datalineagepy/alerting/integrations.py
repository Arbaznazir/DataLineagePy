"""
Alerting Integrations for DataLineagePy
Provides production-ready Slack and Email alerting utilities.
"""
import requests
import smtplib
from email.mime.text import MIMEText
from typing import Optional


def send_slack_alert(webhook_url: str, message: str, channel: Optional[str] = None) -> bool:
    """Send an alert to a Slack channel via webhook."""
    payload = {"text": message}
    if channel:
        payload["channel"] = channel
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200


def send_email_alert(smtp_server: str, smtp_port: int, sender: str, password: str, recipient: str, subject: str, body: str) -> bool:
    """Send an alert email using SMTP."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
        return True
    except Exception:
        return False
