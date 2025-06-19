import requests
import os
import datetime
from dotenv import load_dotenv
from plyer import notification

load_dotenv()

# Settings
MUTE_ALERTS = os.getenv("MUTE_ALERTS", "false").lower() == "true"
WORK_HOURS_ONLY = os.getenv("DESKTOP_ONLY_DURING_WORK_HOURS", "false").lower() == "true"
LOG_ALERTS = True  # Always log alerts (could make this configurable too)


def log_alert(title, message, method):
    if not LOG_ALERTS:
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ({method}) {title}: {message}"
    print(log_entry)
    # Optional: write to file
    with open("alerts.log", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def is_work_hours():
    now = datetime.datetime.now()
    return 9 <= now.hour < 17  # Customize as needed


def send_telegram_notification(title, message):
    if MUTE_ALERTS:
        return
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram not configured.")
        return

    full_message = f"{title}\n\n{message}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": full_message})
        if response.status_code != 200:
            print(f"Telegram error: {response.text}")
        else:
            log_alert(title, message, method="Telegram")
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")


def send_desktop_notification(title, message):
    if MUTE_ALERTS:
        return
    if WORK_HOURS_ONLY and not is_work_hours():
        return
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=10
        )
        log_alert(title, message, method="Desktop")
    except Exception as e:
        print(f"Failed to send desktop notification: {e}")


def send_alert(title, message):
    send_telegram_notification(title, message)
    send_desktop_notification(title, message)
