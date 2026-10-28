"""Use Nonapi copier's Start All Accounts action, then poll operation status.

Run: python account/start_all_accounts.py
Python 3.9+; keep _account_actions.py alongside this file.
"""

import sys
from _account_actions import run_action

SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /start_all_accounts
# Content-Type: application/json
# {}
# Response: {"success": true, "message": "processed"}
# This requests Start for all accounts; poll status to check the result.
# Deleted accounts are excluded; accounts already On remain On.
# The helper polls GET /query_all_accounts once per second, up to five times.
# It checks operation_status == "On"; inspect connection_status separately.

if __name__ == "__main__":
    sys.exit(run_action(SERVER_ADDRESS, PORT, "start_all_accounts", TIMEOUT_SECONDS, POLL_ATTEMPTS))
