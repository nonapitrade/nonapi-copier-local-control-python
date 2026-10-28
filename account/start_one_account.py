"""Start matching accounts in Nonapi copier, then poll their operation status.

Run: python account/start_one_account.py
Python 3.9+; keep _account_actions.py alongside this file.
"""

import sys
from _account_actions import run_action

SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
ACCOUNT = "60072671"
PLATFORM = None  # Optional: "MT4", "MT5", "cTrader", "TradeLocker", or "Tradovate".
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /start_one_account
# Content-Type: application/json
# {"account": "60072671"}
# Or narrow by platform: {"account": "60072671", "platform": "MT5"}
# Account only starts every non-deleted account with this name, across platforms.
# Response: {"success": true, "message": "processed"}
# This acknowledges the request; poll status to check the connection result.
# The helper polls POST /query_one_account once per second, up to five times.
# It checks operation_status == "On"; inspect connection_status separately.
# Repeating Start does not pause an account that is already On.

if __name__ == "__main__":
    sys.exit(run_action(SERVER_ADDRESS, PORT, "start_one_account", TIMEOUT_SECONDS,
                        POLL_ATTEMPTS, account=ACCOUNT, platform=PLATFORM))
