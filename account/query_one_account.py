"""Query one non-deleted account from a running Nonapi copier app.

Set ACCOUNT below, then run: python account/query_one_account.py
Requires Python 3.9+; no external packages or access token are needed.
"""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
URL = f"{SERVER_ADDRESS}:{PORT}/query_one_account"
TIMEOUT_SECONDS = 5

# Rate limit: all enquiry routes share one request per 250 ms.
# Leave at least 250 ms between queries, including queries from other scripts.
# Excess requests return HTTP 429; wait before retrying.
ACCOUNT = "60072671"  # Account names must be strings, including numeric names.
PLATFORM = None  # Optional: "MT4", "MT5", "cTrader", "TradeLocker", or "Tradovate".

# Request example 1: account only (all platforms with this account name).
# POST http://127.0.0.1:52895/query_one_account
# Content-Type: application/json
# {"account": "60072671"}
#
# Request example 2: account and platform (only the specified platform).
# POST http://127.0.0.1:52895/query_one_account
# Content-Type: application/json
# {"account": "60072671", "platform": "MT5"}
# Set PLATFORM = "MT5" above to send the second form; None sends the first.
#
# Example response:
# {
#   "success": true,
#   "accounts": [{
#     "account": "60072671",
#     "platform": "MT5",
#     "connection_status": "Connected",
#     "operation_status": "On"
#   }]
# }
# With account only, accounts can contain multiple entries with the same name.
# Unavailable statuses are JSON null (Python None).


def main() -> int:
    payload = {"account": ACCOUNT}
    if PLATFORM is not None:
        payload["platform"] = PLATFORM
    request = Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
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
