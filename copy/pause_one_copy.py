"""Pause a named copy in Nonapi copier, then poll its operation status.

Run: python copy/pause_one_copy.py
Python 3.9+; keep _copy_actions.py alongside this file.
"""

import sys
from _copy_actions import run_action

SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
COPY_NAME = "CP261028195530"
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /pause_one_copy
# Content-Type: application/json
# {"name": "CP261028195530"}
# Response: {"success": true, "message": "processed"}
# This requests Pause for the named copy; poll status to check the result.
# The helper polls GET /query_all_copies once per second, up to five times,
# selects COPY_NAME, and checks operation_status == "Paused".
# Names are case-sensitive and must identify one non-deleted copy; duplicates return 409.
# Repeating Pause does not start a copy that is already Paused.

if __name__ == "__main__":
    sys.exit(run_action(SERVER_ADDRESS, PORT, "pause_one_copy", TIMEOUT_SECONDS,
                        POLL_ATTEMPTS, name=COPY_NAME))
