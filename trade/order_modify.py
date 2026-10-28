"""Modify a position's SL/TP in Nonapi copier, then poll account positions.

Run: python trade/order_modify.py
Python 3.9+; standard library only. Tradovate is not supported.
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
POSITION_ID = "85007534"
STOP_LOSS = None  # Omitted when None; the current stop loss stays unchanged.
TAKE_PROFIT = 1.236  # Omitted when None; provide at least one of SL or TP.
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /order_modify
# Content-Type: application/json
# TP only:
# {"account":"60072671","platform":"MT5","positionId":"123456789","takeProfit":1.1}
# SL only:
# {"account":"60072671","platform":"MT5","positionId":"123456789","stopLoss":1.05}
# Both:
# {"account":"60072671","platform":"MT5","positionId":"123456789","stopLoss":1.05,"takeProfit":1.1}
# Response: {"success":true,"message":"processed"}
# No symbol is needed. Prices are finite positive numbers; omitted SL/TP is preserved.
# The command is sent once, followed by one-second position enquiries for up to
# five attempts. The acknowledgement does not mean the broker accepted the change.


def main() -> int:
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

    try:
        if not all(isinstance(value, str) and value.strip() for value in (ACCOUNT, PLATFORM, POSITION_ID)):
            raise ValueError("Set ACCOUNT, PLATFORM, and POSITION_ID as non-empty strings.")
        if PLATFORM.casefold() == "tradovate":
            raise ValueError("order_modify is not supported for Tradovate.")
        settings = {key: value for key, value in (("stopLoss", STOP_LOSS), ("takeProfit", TAKE_PROFIT))
                    if value is not None}
        if not settings:
            raise ValueError("Provide at least one of STOP_LOSS or TAKE_PROFIT.")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
               for value in settings.values()):
            raise ValueError("SL and TP must be finite positive numbers, or None to omit.")
        result = send("order_modify", {"account": ACCOUNT, "platform": PLATFORM,
                                      "positionId": POSITION_ID, **settings})
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("success") is not True:
            return 1

        for attempt in range(1, POLL_ATTEMPTS + 1):
            time.sleep(1)
            try:
                status = send("query_one_account_positions", {"account": ACCOUNT, "platform": PLATFORM})
            except HTTPError as error:
                if error.code != 429:
                    raise
                print(error.read().decode("utf-8", errors="replace"), file=sys.stderr)
                continue
            print(f"Position enquiry {attempt}:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            if status.get("success") is not True or len(status["accounts"]) != 1:
                raise ValueError("The enquiry did not return exactly one account.")
            account = status["accounts"][0]
            if account["status"] != "connected":
                continue
            matches = [position for position in account["positions"] if position.get("positionId") == POSITION_ID]
            if len(matches) != 1:
                print("The position ID is missing or ambiguous; inspect the account response.", file=sys.stderr)
                return 1
            if all(math.isclose(float(matches[0][key]), float(value), rel_tol=1e-8, abs_tol=1e-8)
                   for key, value in settings.items()):
                return 0
        print("The requested SL/TP was not confirmed. Check the broker result before resending.", file=sys.stderr)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(f"Could not contact Nonapi copier: {error}. Check positions before resending.", file=sys.stderr)
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError) as error:
        print(f"Invalid request or server response: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
