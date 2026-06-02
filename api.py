import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://live.trading212.com/api/v0"


def _headers():
    key_id = os.getenv("T212_KEY_ID", "")
    secret = os.getenv("T212_SECRET", "")
    token = base64.b64encode(f"{key_id}:{secret}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def get_account_info():
    r = requests.get(f"{BASE_URL}/equity/account/info", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def get_cash():
    r = requests.get(f"{BASE_URL}/equity/account/cash", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def get_portfolio():
    r = requests.get(f"{BASE_URL}/equity/portfolio", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def get_orders(limit=50, cursor=None):
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    r = requests.get(f"{BASE_URL}/equity/history/orders", headers=_headers(),
                     params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_dividends(limit=50, cursor=None):
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    r = requests.get(f"{BASE_URL}/history/dividends", headers=_headers(),
                     params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_pies():
    r = requests.get(f"{BASE_URL}/equity/pies", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()
