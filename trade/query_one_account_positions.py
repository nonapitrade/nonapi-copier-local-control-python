"""Query one account's positions and balance from Nonapi copier.

Run: python trade/query_one_account_positions.py
Requires Python 3.9+; no external packages or access token are needed.
"""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
URL = f"{SERVER_ADDRESS}:{PORT}/query_one_account_positions"
TIMEOUT_SECONDS = 5

# Rate limit: all enquiry routes share one request per 250 ms.
# Leave at least 250 ms between queries, including queries from other scripts.
# Excess requests return HTTP 429; wait before retrying.
ACCOUNT = "60072671"  # The account name/login ID, as shown by query_all_accounts.
PLATFORM = "MT5"  # Required: MT4, MT5, cTrader, TradeLocker, or Tradovate.

# POST http://127.0.0.1:52895/query_one_account_positions
# Content-Type: application/json
# {"account": "60072671", "platform": "MT5"}
# Both fields are required strings. Account names are case-sensitive;
# friendly platform names are matched case-insensitively.
# Example response:
# {
#   "success": true,
#   "accounts": [{
#     "account": "60072671",
#     "platform": "MT5",
#     "balance": 10000.25,
#     "status": "connected",
#     "positions": [{
#       "positionId": "123456789",
#       "symbol": "EURUSD",
#       "volume": 0.1,
#       "side": "buy",
#       "stopLoss": 1.05,
#       "takeProfit": 1.1
#     }]
#   }]
# }
# The accounts array contains only matches for the specified account/platform.
# Disconnected accounts return status=not_connected and omit positions.
# Tradovate positions omit positionId, stopLoss, and takeProfit.
# Unknown balance values are null (Python None); connected empty positions are [].


def main() -> int:
    request = Request(
        URL,
        data=json.dumps({"account": ACCOUNT, "platform": PLATFORM}).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            result = json.load(response)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("success") is True else 1
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(
            f"Could not query Nonapi copier: {error}\n"
            "Open the app, log in, and enable Local Control in General Settings.",
            file=sys.stderr,
        )
    except (ValueError, UnicodeError) as error:
        print(f"The server returned an invalid JSON response: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
