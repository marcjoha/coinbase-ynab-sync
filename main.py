import logging
import os
import sys

from dotenv import load_dotenv

from coinbase import get_coinbase_balance
from ynab import get_ynab_balance, adjust_ynab_balance

# Configure log level as INFO, unless overriden by environment
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger("coinbase-ynab-sync")

# Load environment variables from .env file
load_dotenv()


def main():
    COINBASE_KEY = os.getenv("COINBASE_KEY")
    COINBASE_SECRET = os.getenv("COINBASE_SECRET")
    YNAB_TOKEN = os.getenv("YNAB_TOKEN")
    YNAB_BUDGET = os.getenv("YNAB_BUDGET")
    YNAB_ACCOUNT = os.getenv("YNAB_ACCOUNT")
    FIAT_CURRENCY = os.getenv("FIAT_CURRENCY")

    if not COINBASE_KEY or not COINBASE_SECRET:
        log.error("Coinbase API credentials are missing.")
        return 1

    if not YNAB_TOKEN or not YNAB_BUDGET or not YNAB_ACCOUNT:
        log.error("YNAB API credentials are missing.")
        return 1

    if not FIAT_CURRENCY:
        log.error("Fiat currency is not specified.")
        return 1

    log.debug("Environment Variables:")
    log.debug(f"  COINBASE_KEY: {COINBASE_KEY}")
    log.debug(f"  COINBASE_SECRET: {COINBASE_SECRET}")
    log.debug(f"  YNAB_TOKEN: {YNAB_TOKEN}")
    log.debug(f"  YNAB_BUDGET: {YNAB_BUDGET}")
    log.debug(f"  YNAB_ACCOUNT: {YNAB_ACCOUNT}")
    log.debug(f"  FIAT_CURRENCY: {FIAT_CURRENCY}")

    # Get latest balance from Coinbase, in specifed fiat currency
    new_balance = get_coinbase_balance(COINBASE_KEY, COINBASE_SECRET, FIAT_CURRENCY)
    if new_balance is None:
        log.error("Failed to get Coinbase balance.")
        return 1
    else:
        log.info(f"Total balance in Coinbase ({FIAT_CURRENCY}): {new_balance}")

    # Get Ynab balance
    old_balance = get_ynab_balance(YNAB_TOKEN, YNAB_BUDGET, YNAB_ACCOUNT)
    if old_balance is None:
        log.error("Failed to get YNAB balance.")
        return 1
    else:
        log.info(f"Total balance in YNAB: {old_balance}")

    # Calculate the difference
    difference = new_balance - old_balance
    log.info(f"Difference between Coinbase and YNAB: {difference}")

    # Send an adjustment transaction to Ynab
    success = adjust_ynab_balance(YNAB_TOKEN, YNAB_BUDGET, YNAB_ACCOUNT, difference)
    if success:
        log.info("Balance adjustment sent to YNAB.")
        return 0
    else:
        log.error("Failed to send balance adjustment to YNAB.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
