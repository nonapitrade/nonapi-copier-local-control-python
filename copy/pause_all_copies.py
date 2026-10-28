"""Use Nonapi copier's Pause All Copies action, then poll operation status.

Run: python copy/pause_all_copies.py
Python 3.9+; keep _copy_actions.py alongside this file.
"""

import sys
from _copy_actions import run_action

SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /pause_all_copies
# Content-Type: application/json
# {}
# Response: {"success": true, "message": "processed"}
# This requests Pause for all copies; poll status to check the result.
# Deleted copies are excluded; copies already Paused remain Paused.
# The helper polls GET /query_all_copies once per second, up to five times,
# and checks that each returned copy has operation_status == "Paused".

if __name__ == "__main__":
    sys.exit(run_action(SERVER_ADDRESS, PORT, "pause_all_copies", TIMEOUT_SECONDS, POLL_ATTEMPTS))
