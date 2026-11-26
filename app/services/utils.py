# utils.py
from datetime import datetime
import pytz

philippines_tz = pytz.timezone("Asia/Manila")

def now_ph():
    return datetime.now(philippines_tz).replace(tzinfo=None)

def today_ph():
    return now_ph().strftime("%Y-%m-%d")