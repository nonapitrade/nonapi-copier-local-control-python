"""Edit allowed settings of a named copy in Nonapi copier.

Run: python copy/edit_one_copy.py
Python 3.9+; standard library only. Set COPY_NAME and SETTINGS below.
"""

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


SERVER_ADDRESS = "http://127.0.0.1"
PORT = 52895
COPY_NAME = "CP261028195530"
TIMEOUT_SECONDS = 5
POLL_ATTEMPTS = 5

# Keep only the fields you want to edit. Omitted fields stay unchanged.
# lot_ratio                 
# symbol_mapping_list        
# applicable_symbols        
# reverse_trade              
# applicable_magic_list      
# copy_tp_sl                
# copy_price_mode           
# suffix_removed_le        
# suffix_added_fl           
# fixed_lot 
                
SETTINGS = {
    "lot_ratio": "1",
    "symbol_mapping_list": "",
    "applicable_symbols": "",
    "reverse_trade": False,
    "applicable_magic_list": "",
    "copy_tp_sl": True,
    "copy_price_mode": "By Price",
    "suffix_removed_le": "",
    "suffix_added_fl": "",
    "fixed_lot": 0,
}

# POST /edit_one_copy
# Content-Type: application/json
# Request example (partial edit):
# {"name": "CP261028195530", "lot_ratio": "2", "copy_tp_sl": true}
# Response: {"success": true, "message": "processed"}
# name selects one existing copy; it does not rename it. Duplicate names return 409.
# Only the ten SETTINGS keys above can be changed. Operation status stays unchanged.
# Strings remain strings, flags must be JSON booleans, and fixed_lot must be a
# finite non-negative number (0 disables fixed lot). Price modes: By Price/By Distance.
# lot_ratio accepts a non-negative decimal string or SYMBOL,RATIO; entries.
# symbol_mapping_list accepts LEADER_SYMBOL,FOLLOWER_SYMBOL; entries or an empty string.
# Whitespace around list entries is optional. An empty string clears a list setting.
# "processed" acknowledges the request, not completion. The loop below polls once
# per second and checks the supplied settings. The edit command is never resent.


def setting_matches(key, actual, expected):
    if key in ("symbol_mapping_list", "lot_ratio") and "," in expected:
        def pairs(value):
            return [tuple(item.strip() for item in row.split(",") if item.strip())
                    for row in value.split(";") if row.strip()]
        return pairs(actual) == pairs(expected)
    if key in ("applicable_symbols", "applicable_magic_list", "suffix_removed_le"):
        return [item.strip() for item in actual.split(",") if item.strip()] == [
            item.strip() for item in expected.split(",") if item.strip()
        ]
    if key == "copy_price_mode":
        return actual.casefold() == expected.strip().casefold()
    return actual == (expected.strip() if isinstance(expected, str) else expected)


def main() -> int:
    opener = build_opener(ProxyHandler({}))

    def send(path, method, body=None):
        data = None if body is None else json.dumps(body, allow_nan=False).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(f"{SERVER_ADDRESS}:{PORT}/{path}", data=data, headers=headers, method=method)
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)

    try:
        result = send("edit_one_copy", "POST", {"name": COPY_NAME, **SETTINGS})
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("success") is not True:
            return 1
        for attempt in range(1, POLL_ATTEMPTS + 1):
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
            matches = [copy for copy in status["copies"] if copy["name"] == COPY_NAME]
            if len(matches) != 1:
                print("The copy name is missing or no longer unique; check the app.", file=sys.stderr)
                return 1
            copy = matches[0]
            print(f"Settings enquiry {attempt}:")
            print(json.dumps(copy, indent=2, ensure_ascii=False))
            if all(setting_matches(key, copy[key], value) for key, value in SETTINGS.items()):
                return 0
        print("The edited settings were not confirmed within the polling attempts.", file=sys.stderr)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    except (URLError, TimeoutError, OSError) as error:
        print(f"Could not contact Nonapi copier: {error}. Query status before resending the edit.", file=sys.stderr)
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError) as error:
        print(f"Invalid settings or server response: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
