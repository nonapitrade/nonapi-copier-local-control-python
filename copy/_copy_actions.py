"""Shared HTTP and one-second polling for the copy action examples."""

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def run_action(server_address, port, action, timeout_seconds, poll_attempts, name=None):
    base_url = f"{server_address}:{port}"
    payload = {} if name is None else {"name": name}
    all_copies = action in ("start_all_copies", "pause_all_copies")
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
        # Send the command once. "processed" acknowledges the request, not completion.
        result = send(action, "POST", payload)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("success") is not True:
            return 1

        for attempt in range(1, poll_attempts + 1):
            time.sleep(1)
            try:
                status = send("query_all_copies", "GET")
            except HTTPError as error:
                if error.code != 429:
                    raise
                print(error.read().decode("utf-8", errors="replace"), file=sys.stderr)
                continue
            if status.get("success") is not True:
                print(json.dumps(status, indent=2, ensure_ascii=False))
                return 1
            copies = status["copies"]
            if not all_copies:
                copies = [copy for copy in copies if copy["name"] == name]
                if len(copies) != 1:
                    print("The copy name is missing or no longer unique; check the app.", file=sys.stderr)
                    return 1
            print(f"Status enquiry {attempt}:")
            print(json.dumps({"success": True, "copies": copies}, indent=2, ensure_ascii=False))
            if all(copy["operation_status"] == expected_status for copy in copies):
                return 0
        print("The requested copy operation status was not confirmed within the polling attempts.", file=sys.stderr)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(
            f"Could not contact Nonapi copier: {error}\n"
            "Open the app, log in, and enable Local Control in General Settings.\n"
            "If the action response was lost, query status before sending it again.",
            file=sys.stderr,
        )
    except (ValueError, UnicodeError, KeyError, TypeError) as error:
        print(f"The server returned an invalid response: {error}", file=sys.stderr)
    return 1
