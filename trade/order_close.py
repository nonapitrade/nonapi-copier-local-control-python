"""Close a position in Nonapi copier, then poll that account's positions.

Run: python trade/order_close.py
Requires Python 3.9+; standard library only.
"""

import json
import math
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
ACCOUNT = "60072671"
PLATFORM = "MT5"
SYMBOL = None  # Required for Tradovate; optional and ignored for other platforms.
POSITION_ID = "85013446"  # Set None to omit for Tradovate.
VOLUME = None  # Omit to close all; otherwise set a non-zero numeric volume.
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /order_close
# Content-Type: application/json
# Full close:
# {"account":"60072671","platform":"MT5","positionId":"123456789"}
# Partial close:
# {"account":"60072671","platform":"MT5","positionId":"123456789","volume":0.1}
# Tradovate:
# {"account":"DEMO975889","platform":"Tradovate","symbol":"MESZ6","volume":1}
# Response: {"success":true,"message":"processed"}
# The response acknowledges the request, not broker execution. This script sends the
# close once, then polls POST /query_one_account_positions at one-second intervals.
# Any requested volume exceeding the current position is capped to that position.


def main() -> int:
    payload = {"account": ACCOUNT, "platform": PLATFORM}
    if SYMBOL is not None:
        payload["symbol"] = SYMBOL
    if POSITION_ID is not None:
        payload["positionId"] = POSITION_ID
    if VOLUME is not None:
        payload["volume"] = VOLUME
    opener = build_opener(ProxyHandler({}))

    def send(path, body):
        request = Request(
            f"{SERVER_ADDRESS}:{PORT}/{path}",
            data=json.dumps(body, allow_nan=False).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)

    def account_state(response):
        if response.get("success") is not True or len(response["accounts"]) != 1:
            raise ValueError("The account enquiry did not return exactly one account.")
        return response["accounts"][0]

    def matching_positions(account):
        return [position for position in account.get("positions", [])
                if (position["symbol"].casefold() == SYMBOL.casefold() if PLATFORM.casefold() == "tradovate"
                    else position.get("positionId") == POSITION_ID)]

    try:
        if not all(isinstance(value, str) and value.strip() for value in (ACCOUNT, PLATFORM)):
            raise ValueError("Set ACCOUNT and PLATFORM as non-empty strings.")
        if PLATFORM.casefold() == "tradovate" and not (isinstance(SYMBOL, str) and SYMBOL.strip()):
            raise ValueError("Set SYMBOL for Tradovate.")
        if PLATFORM.casefold() != "tradovate" and not (isinstance(POSITION_ID, str) and POSITION_ID.strip()):
            raise ValueError("Set POSITION_ID for this platform.")
        if VOLUME is not None and (isinstance(VOLUME, bool) or not isinstance(VOLUME, (int, float))
                                   or not math.isfinite(VOLUME) or VOLUME == 0):
            raise ValueError("VOLUME must be a finite non-zero number, or None.")
        selector = {"account": ACCOUNT, "platform": PLATFORM}
        before = account_state(send("query_one_account_positions", selector))
        if before["status"] != "connected":
            raise ValueError("The account is not connected.")
        positions = matching_positions(before)
        if len(positions) != 1:
            raise ValueError("The symbol and position ID must identify exactly one open position.")
        original = positions[0]
        initial_volume = float(original["volume"])
        close_volume = min(initial_volume, initial_volume if VOLUME is None else abs(float(VOLUME)))
        expected_remaining = max(0, initial_volume - close_volume)

        result = send("order_close", payload)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("success") is not True:
            return 1
        for attempt in range(1, POLL_ATTEMPTS + 1):
            time.sleep(1)
            try:
                status = send("query_one_account_positions", selector)
            except HTTPError as error:
                if error.code != 429:
                    raise
                print(error.read().decode("utf-8", errors="replace"), file=sys.stderr)
                continue
            print(f"Position enquiry {attempt}:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            account = account_state(status)
            if account["status"] != "connected":
                continue
            remaining = matching_positions(account)
            if not remaining:
                print("The original position is no longer listed; inspect the response for any replacement tickets.")
                return 0
            if len(remaining) != 1 or remaining[0]["side"] != original["side"]:
                print("The position changed direction or became ambiguous; inspect the response before sending another close.", file=sys.stderr)
                return 1
            if float(remaining[0]["volume"]) <= expected_remaining + 1e-9:
                return 0
        print("The close result was not confirmed within the polling attempts. Check positions before resending.", file=sys.stderr)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(f"Could not contact Nonapi copier: {error}. Check positions before resending the close.", file=sys.stderr)
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError) as error:
        print(f"Invalid request or server response: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
