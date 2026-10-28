"""Query non-deleted copy pairs from a running Nonapi copier app.

Run: python copy/query_all_copies.py
Requires Python 3.9+; no external packages or access token are needed.
"""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
URL = f"{SERVER_ADDRESS}:{PORT}/query_all_copies"
TIMEOUT_SECONDS = 5

# Rate limit: all enquiry routes share one request per 250 ms.
# Leave at least 250 ms between queries, including queries from other scripts.
# Excess requests return HTTP 429; wait before retrying.

# GET http://127.0.0.1:52895/query_all_copies
# Example response (name is first, operation_status is second):
# {
#   "success": true,
#   "copies": [
#     {
#       "name": "CP261028195530",
#       "operation_status": "On",
#       "leader_platform": "MT5",
#       "follower_platform": "TradeLocker",
#       "leader_account": "920258",
#       "follower_account": "155686",
#       "lot_ratio": "1",
#       "symbol_mapping_list": "",
#       "applicable_symbols": "",
#       "reverse_trade": true,
#       "applicable_magic_list": "",
#       "copy_tp_sl": true,
#       "copy_price_mode": "By Price",
#       "suffix_removed_le": "",
#       "suffix_added_fl": "",
#       "fixed_lot": 0
#     },
#     {
#       "name": "CP261006165227",
#       "operation_status": "On",
#       "leader_platform": "MT5",
#       "follower_platform": "TradeLocker",
#       "leader_account": "65072279",
#       "follower_account": "1733685",
#       "lot_ratio": "1",
#       "symbol_mapping_list": "",
#       "applicable_symbols": "",
#       "reverse_trade": false,
#       "applicable_magic_list": "",
#       "copy_tp_sl": true,
#       "copy_price_mode": "By Price",
#       "suffix_removed_le": "",
#       "suffix_added_fl": "",
#       "fixed_lot": 0
#     }
#   ]
# }
# Deleted pairs are excluded; paused pairs are included.
# copy_price_mode is "By Price" or "By Distance".
# Lot ratios and list settings remain strings; flags are booleans and fixed_lot is a number.


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
