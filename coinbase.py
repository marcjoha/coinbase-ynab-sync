import logging
import secrets
import time

import jwt
import requests
from cryptography.hazmat.primitives import serialization

log = logging.getLogger("coinbase-ynab-sync")

API_BASE_URL = "https://api.coinbase.com"


def get_coinbase_balance(key, secret, fiat_currency):
    """Retrieves the total Coinbase balance in the specified fiat currency."""
    headers = _get_auth_headers(key, secret, f"{API_BASE_URL}/v2/accounts")
    all_accounts = _fetch_paginated_data(f"{API_BASE_URL}/v2/accounts", headers)
    if all_accounts is None:
        return None

    balances = []
    for account in all_accounts:
        try:
            balance_amount = float(account["balance"]["amount"])
            if balance_amount > 0:
                log.info(f"Account: {account['name']}. Balance: {account['balance']}")
                balances.append(account["balance"])
            else:
                log.debug(f"Zero-balance in account: {account['name']}")

        except (KeyError, ValueError) as e:
            log.error(f"Could not parse balance for account: {account}. Error: {e}")
            return None

    exchange_rates = _get_exchange_rates(fiat_currency)
    if exchange_rates is None:
        log.error(f"Failed to fetch exchange rates for {fiat_currency}.")
        return None

    total_balance = 0
    for balance in balances:
        try:
            total_balance += float(balance["amount"]) / float(
                exchange_rates[balance["currency"]]
            )
        except (KeyError, ValueError) as e:
            log.error(f"Could not calculate balance for {balance}. Error: {e}")
            return None

    return total_balance


def _get_auth_headers(key, secret, uri):
    """Generates auth headers with JWT token for Coinbase API authentication."""
    try:
        private_key = serialization.load_pem_private_key(
            secret.encode("utf-8"), password=None
        )
    except ValueError as e:
        log.error(f"Error loading private key: {e}")
        return None

    jwt_payload = {
        "sub": key,
        "iss": "cdp",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "uri": "GET " + uri.replace("https://", ""),
    }

    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key, "nonce": secrets.token_hex()},
    )

    return {"Authorization": f"Bearer {jwt_token}"}


def _fetch_paginated_data(url, headers):
    """Fetches data from a paginated API endpoint."""
    all_data = []
    next_uri = url

    while next_uri:
        log.debug(f"Fetching data from: {next_uri}")
        try:
            response = requests.get(next_uri, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            all_data.extend(data["data"])

            pagination = data.get("pagination")
            if pagination and pagination.get("next_uri"):
                next_uri = f"{API_BASE_URL}{pagination['next_uri']}"
            else:
                next_uri = None
        except Exception as e:
            log.error(f"Error fetching data from {next_uri}: {e}")
            return None

    return all_data


def _get_exchange_rates(currency):
    """Retrieves exchange rates for the specified fiat currency."""
    try:
        response = requests.get(f"{API_BASE_URL}/v2/exchange-rates?currency={currency}")
        response.raise_for_status()
        data = response.json()
        return data["data"]["rates"]
    except Exception as e:
        log.error(f"Error fetching exchange rates: {e}")
        return None
