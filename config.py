import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_TOKEN"]

ADMIN_IDS = set()
raw_admins = os.environ.get("ADMIN_IDS", "")
for x in raw_admins.split(","):
    x = x.strip()
    if x.isdigit():
        ADMIN_IDS.add(int(x))
