from datetime import date
import logging

import requests


log = logging.getLogger("coinbase-ynab-sync")

API_BASE_URL = "https://api.ynab.com/v1"


def get_ynab_balance(token, budget, account):
    """Retrieves the balance of a particular budget account in YNAB."""
    headers = {"Authorization": "Bearer " + token}
    uri = f"{API_BASE_URL}/budgets/{budget}/accounts/{account}"

    log.debug(f"Fetching data from: {uri}")
    try:
        response = requests.get(uri, headers=headers)
        response.raise_for_status()
        data = response.json()
        balance = float(data["data"]["account"]["balance"]) / 1000
        return balance
    except Exception as e:
        log.error(f"Error fetching data from {uri}: {e}")
        return None


def adjust_ynab_balance(token, budget, account, amount):
    """Adjusts the balance of a particular budget account in YNAB."""
    headers = {"Authorization": "Bearer " + token}
    uri = f"{API_BASE_URL}/budgets/{budget}/transactions"
    data = {
        "transaction": {
            "account_id": account,
            "date": date.today().strftime("%Y-%m-%d"),
            "amount": int(amount * 1000),
            "payee_name": "Automatic Balance Adjustment by coinbase-ynab-sync",
            "cleared": "cleared",
            "approved": True,
        }
    }

    log.debug(f"Sending data {data} to: {uri}")
    try:
        response = requests.post(uri, json=data, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Error sending data to {uri}: {e}")
        return False
