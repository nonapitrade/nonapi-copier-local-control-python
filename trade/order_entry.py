"""Place a market order in Nonapi copier and poll the account's positions.

Run: python trade/order_entry.py
Python 3.9+; standard library only.
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
SYMBOL = "EURUSD"
SIDE = "buy"  # buy or sell
VOLUME = 0.01  # Lots; for Tradovate use a whole number of contracts.
STOP_LOSS = None  # Optional; omitted when None.
TAKE_PROFIT = None  # Optional; omitted when None.
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# POST /order_entry
# Content-Type: application/json
# Without SL/TP:
# {"account":"60072671","platform":"MT5","symbol":"EURUSD","side":"buy","volume":0.1}
# With SL/TP:
# {"account":"60072671","platform":"MT5","symbol":"EURUSD","side":"buy","volume":0.1,"stopLoss":1.05,"takeProfit":1.1}
# Tradovate:
# {"account":"DEMO975889","platform":"Tradovate","symbol":"MESZ6","side":"sell","volume":1}
# Tradovate ignores stopLoss and takeProfit.
# Response: {"success":true,"message":"processed"}
# The command is sent once. The script then polls positions once per second, up
# to five times, and checks the symbol's signed volume change. This also handles
# netting accounts where an entry reduces or reverses an existing position.


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

    def account_state(response):
        if response.get("success") is not True or len(response["accounts"]) != 1:
            raise ValueError("The account enquiry did not return exactly one account.")
        return response["accounts"][0]

    def net_volume(account):
        return sum(float(position["volume"]) * (1 if position["side"] == "buy" else -1)
                   for position in account.get("positions", [])
                   if position["symbol"].casefold() == SYMBOL.strip().casefold())

    try:
        if not all(isinstance(value, str) and value.strip() for value in (ACCOUNT, PLATFORM, SYMBOL)):
            raise ValueError("Set ACCOUNT, PLATFORM, and SYMBOL as non-empty strings.")
        if not isinstance(SIDE, str) or SIDE.strip().casefold() not in ("buy", "sell"):
            raise ValueError("SIDE must be buy or sell.")
        if isinstance(VOLUME, bool) or not isinstance(VOLUME, (int, float)) or not math.isfinite(VOLUME) or VOLUME <= 0:
            raise ValueError("VOLUME must be a finite positive number.")
        if PLATFORM.casefold() == "tradovate" and VOLUME != math.trunc(VOLUME):
            raise ValueError("Tradovate volume must be a whole number of contracts.")
        settings = {key: value for key, value in (("stopLoss", STOP_LOSS), ("takeProfit", TAKE_PROFIT))
                    if value is not None}
        if PLATFORM.casefold() != "tradovate" and any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
            for value in settings.values()
        ):
            raise ValueError("SL and TP must be finite positive numbers, or None to omit.")
        side = SIDE.strip().casefold()
        selector = {"account": ACCOUNT, "platform": PLATFORM}
        before = account_state(send("query_one_account_positions", selector))
        if before["status"] != "connected":
            raise ValueError("The account is not connected.")
        expected_net = net_volume(before) + (float(VOLUME) if side == "buy" else -float(VOLUME))
        result = send("order_entry", {**selector, "symbol": SYMBOL.strip(), "side": side,
                                      "volume": VOLUME, **settings})
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
            if account["status"] == "connected" and math.isclose(net_volume(account), expected_net, rel_tol=1e-8, abs_tol=1e-8):
                return 0
        print("The entry result was not confirmed. Check positions and broker results before resending.", file=sys.stderr)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(f"Could not contact Nonapi copier: {error}. Check positions before resending.", file=sys.stderr)
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError, OverflowError) as error:
        print(f"Invalid request or server response: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
