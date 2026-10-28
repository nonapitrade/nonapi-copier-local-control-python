"""Query positions and balances from a running Nonapi copier app.

Run: python trade/query_all_accounts_positions.py
Requires Python 3.9+; no external packages or access token are needed.
"""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
URL = f"{SERVER_ADDRESS}:{PORT}/query_all_accounts_positions"
TIMEOUT_SECONDS = 5

# Rate limit: all enquiry routes share one request per 250 ms.
# Leave at least 250 ms between queries, including queries from other scripts.
# Excess requests return HTTP 429; wait before retrying.

# GET http://127.0.0.1:52895/query_all_accounts_positions
# Example response:
# {
#   "success": true,
#   "accounts": [
#     {
#       "account": "60072671",
#       "platform": "MT5",
#       "balance": 10000.25,
#       "status": "connected",
#       "positions": [
#         {
#           "positionId": "123456789",
#           "symbol": "EURUSD",
#           "volume": 0.1,
#           "side": "buy",
#           "stopLoss": 1.05,
#           "takeProfit": 1.1
#         }
#       ]
#     },
#     {
#       "account": "DEMO975889",
#       "platform": "Tradovate",
#       "balance": 25000,
#       "status": "connected",
#       "positions": [{"symbol": "MESZ6", "volume": 1, "side": "sell"}]
#     },
#     {
#       "account": "6121079",
#       "platform": "cTrader",
#       "balance": null,
#       "status": "not_connected"
#     }
#   ]
# }
# Deleted accounts are excluded. Unknown balances are null (Python None).
# Disconnected accounts have status=not_connected and omit positions entirely.
# Connected accounts without open positions return positions=[].
# Tradovate positions omit positionId, stopLoss, and takeProfit.
# Volume is in lots, or contracts for Tradovate.


def main() -> int:
    request = Request(URL, headers={"Accept": "application/json"}, method="GET")
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
