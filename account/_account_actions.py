"""Shared HTTP and polling code for the four account action examples."""

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def run_action(server_address, port, action, timeout_seconds, poll_attempts,
               account=None, platform=None):
    base_url = f"{server_address}:{port}"
    payload = {}
    if account is not None:
        payload["account"] = account
        if platform is not None:
            payload["platform"] = platform
    all_accounts = action in ("start_all_accounts", "pause_all_accounts")
    expected_status = "On" if action.startswith("start_") else "Paused"
    opener = build_opener(ProxyHandler({}))

    def send(path, method, body=None):
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = Request(f"{base_url}/{path}", data=data, headers=headers, method=method)
        with opener.open(request, timeout=timeout_seconds) as response:
            return json.load(response)

    try:
        # Send the action once. "processed" acknowledges the request;
        # poll the account status to check the result.
        result = send(action, "POST", payload)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("success") is not True:
            return 1

        # Wait one second before each status enquiry; never resend the action.
        for attempt in range(1, poll_attempts + 1):
            time.sleep(1)
            try:
                status = send("query_all_accounts", "GET") if all_accounts else send(
                    "query_one_account", "POST", payload
                )
            except HTTPError as error:
                if error.code != 429:
                    raise
                print(error.read().decode("utf-8", errors="replace"), file=sys.stderr)
                continue
            print(f"Status enquiry {attempt}:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            if status.get("success") is not True:
                return 1
            accounts = status["accounts"]
            if not accounts and not all_accounts:
                print("No matching account remains.", file=sys.stderr)
                return 1
            if all(row["operation_status"] == expected_status for row in accounts):
                # On/Paused confirms operation state. Inspect connection_status
                # separately: On does not guarantee a successful connection.
                return 0
        print("The requested operation status was not confirmed within the polling attempts.", file=sys.stderr)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(
            f"Could not contact Nonapi copier: {error}\n"
            "Open the app, log in, and enable Local Control in General Settings.\n"
            "If the action response was lost, query status before sending the action again.",
            file=sys.stderr,
        )
    except (ValueError, UnicodeError, KeyError, TypeError) as error:
        print(f"The server returned an invalid response: {error}", file=sys.stderr)
    return 1
