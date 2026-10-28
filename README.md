# Nonapi copier Local Control Python examples

Use Python to query and control the running Nonapi copier app over local HTTP.
Examples use Python 3.9+ and the standard library; no package installation or token
is required. Open Nonapi copier, log in, and enable **Local Control?** in General
Settings before running an example.

## Query all accounts

From this folder, run:

```sh
python account/query_all_accounts.py
```

This sends `GET http://127.0.0.1:52895/query_all_accounts` and prints the JSON response:

```json
{
  "success": true,
  "accounts": [
    {
      "account": "12345678",
      "platform": "MT5",
      "connection_status": "Connected",
      "operation_status": "On"
    }
  ]
}
```

Deleted accounts are excluded. Paused and disconnected accounts are included.
An empty list is returned when there are no accounts. Account names are strings.
Platform names are `MT4`, `MT5`, `cTrader`, `TradeLocker`, or `Tradovate`.
Connection status is `null` for not connected, or one of:
`Initial Connecting`, `Reconnecting`, `Connected`, or `Failed To Connect`.
Operation status is `On` or `Paused`. Unavailable status values are JSON `null`.
Account ordering is unspecified.

The example times out after five seconds and exits with a nonzero code on failure.
Enable Local Control before running an example; otherwise connection errors may occur.

## Query one account

Set `ACCOUNT` in `account/query_one_account.py`, then run:

```sh
python account/query_one_account.py
```

It sends `POST http://127.0.0.1:52895/query_one_account` with a JSON body:

```json
{"account": "60072671"}
```

The response contains an `accounts` array, using the same fields as query all accounts:

```json
{
  "success": true,
  "accounts": [{
    "account": "60072671",
    "platform": "MT5",
    "connection_status": "Connected",
    "operation_status": "On"
  }]
}
```

Account matching is exact and case-sensitive. With account only, all non-deleted
accounts with that name are returned, including matches on different platforms.
To narrow the result, set `PLATFORM` in the script. This adds, for example,
`"platform": "MT5"` to the body; platform matching is case-insensitive.
Missing or invalid account/platform fields return 400. A missing or deleted
account returns 404. GET returns 405.

## Start and pause accounts

```sh
python account/start_one_account.py
python account/pause_one_account.py
python account/start_all_accounts.py
python account/pause_all_accounts.py
```

Set `ACCOUNT` and optionally `PLATFORM` in either single-account example. Their
POST bodies accept both account-only and account-with-platform forms, like the
single-account query. Account-only actions affect all matching non-deleted
accounts across platforms. The two all-account actions POST an empty object `{}`.
The endpoint names match the filenames without `.py`.

Keep `account/_account_actions.py` with these examples. It supplies shared HTTP
handling and a short loop that waits one second before each status query, up to
`POLL_ATTEMPTS` times. A successful action request returns:

```json
{"success": true, "message": "processed"}
```

This is an acknowledgement, not confirmation that a connection or pause has
completed. Polling checks `operation_status` for `On` or `Paused` and prints the
full status response. Inspect `connection_status` separately: `On` does not mean
`Connected`. Actions are sent once and are not automatically retried.

## Query all copies

```sh
python copy/query_all_copies.py
```

This sends `GET /query_all_copies` and prints `{"success":true,"copies":[...]}`.
Deleted pairs are excluded; paused pairs are included. No copies returns an empty
array. The script contains a full commented response example.

Each copy starts with `name`, then `operation_status`. The remaining fields follow
the copy settings labels: `leader_platform`, `follower_platform`, `leader_account`,
`follower_account`, `lot_ratio`, `symbol_mapping_list`, `applicable_symbols`,
`reverse_trade`, `applicable_magic_list`, `copy_tp_sl`, `copy_price_mode`,
`suffix_removed_le`, `suffix_added_fl`, and `fixed_lot`.
Platforms use friendly names and operation status is `On` or `Paused` (unavailable
statuses are `null`). `copy_price_mode` is `By Price` or `By Distance`.
Flags are booleans, fixed lot is numeric, and ratios/list settings remain
strings. JSON property order is for readability; consumers should access keys by name.

## Start and pause copies

```sh
python copy/start_one_copy.py
python copy/pause_one_copy.py
python copy/start_all_copies.py
python copy/pause_all_copies.py
```

Keep `copy/_copy_actions.py` alongside these examples. Set `COPY_NAME` in either
single-copy example. They POST `{"name":"CP261028195530"}` to `/start_one_copy`
or `/pause_one_copy`. Matching is case-sensitive; a missing/deleted copy returns
404, an invalid name returns 400, and duplicate non-deleted names return 409.
Give copies distinct names in the app to select exactly one.

The all-copy scripts POST `{}` to `/start_all_copies` or `/pause_all_copies`.
These routes return `{"success":true,"message":"processed"}` to acknowledge
the request. Poll the status to check the result. Start and pause actions set
the requested operation status.

Each script waits one second before polling `GET /query_all_copies`, for up to
five attempts. Single-copy scripts select the matching name from the result.
Polling checks `operation_status` for `On` or `Paused`; it does not prove a trade
was copied. The command is sent once and never automatically resent.

## Edit one copy

Set `COPY_NAME` and `SETTINGS` in `copy/edit_one_copy.py`, then run:

```sh
python copy/edit_one_copy.py
```

The script POSTs a flat JSON object to `/edit_one_copy`, for example:

```json
{"name":"CP261028195530","lot_ratio":"2","copy_tp_sl":true}
```

`name` selects an existing copy; it cannot be renamed. At least one of these
editable fields must be present. Omitted fields remain unchanged.

| JSON field | Type |
|---|---|
| `lot_ratio` | Decimal string or `SYMBOL,RATIO;` list |
| `symbol_mapping_list` | String, `LEADER_SYMBOL,FOLLOWER_SYMBOL;` list |
| `applicable_symbols` | Comma-separated string |
| `reverse_trade` | Boolean |
| `applicable_magic_list` | Comma-separated string |
| `copy_tp_sl` | Boolean |
| `copy_price_mode` | `By Price` or `By Distance` |
| `suffix_removed_le` | Comma-separated string |
| `suffix_added_fl` | String |
| `fixed_lot` | Finite non-negative number; 0 disables fixed lot |

Empty strings clear list/suffix settings. Ratios must be non-negative finite
decimals. Whitespace around list entries is optional.
Unknown fields, invalid types/values, or an empty edit return 400. Missing/deleted
copies return 404; duplicate copy names return 409. Copy identity and operation
status are preserved, including when editing a paused copy.

The server returns `{"success":true,"message":"processed"}` to acknowledge the edit request.
The example polls once per second for up to five attempts to check the edited
values. All POST routes reject malformed JSON with a JSON error response.

## Query positions

```sh
python trade/query_all_accounts_positions.py
```

This sends `GET /query_all_accounts_positions`. The
response is `{"success":true,"accounts":[...]}`. Deleted accounts are excluded.
Each account contains `account`, friendly `platform`, numeric `balance` (or
`null` when unavailable), and `status`.

Disconnected accounts have `"status":"not_connected"` and no `positions` field.
Connected accounts have `"status":"connected"` and a `positions` array, empty
when there are no open positions. Each non-Tradovate position includes
`positionId`, `symbol`, `volume`, `side` (`buy`/`sell`), `stopLoss`, and `takeProfit`.
Tradovate positions contain only `symbol`, `volume`, and `side`.
Volume is in lots, or contracts for Tradovate.
The script includes a full response example.

To query just one account, set `ACCOUNT` and `PLATFORM`, then run:

```sh
python trade/query_one_account_positions.py
```

It sends `POST /query_one_account_positions` with both required fields:

```json
{"account":"60072671","platform":"MT5"}
```

The response uses the same `accounts` array and position format, filtered to
that account/platform. Use the account name/login ID from `query_all_accounts`.
Account names are case-sensitive;
platform names are case-insensitive friendly names. Invalid/missing fields return
400 and a missing/deleted account returns 404. Malformed JSON returns 400.

## Close a position

Set the account, platform, symbol, position ID, and optional volume in
`trade/order_close.py`, then run:

```sh
python trade/order_close.py
```

The script POSTs `/order_close`, for example:

```json
{"account":"60072671","platform":"MT5","symbol":"EURUSD","positionId":"123456789","volume":0.1}
```

`account` and `platform` are required strings. `positionId` identifies the position
on non-Tradovate platforms; any supplied `symbol` is ignored on those platforms.
Tradovate requires `symbol` and may omit `positionId`.
`volume` is an optional finite non-zero number; omit it to
close the position's full volume. A close never requests more than the available
position volume. Account/platform identify one account, and position ID (or
Tradovate symbol) identifies one open position. The account must be On and connected; investor-mode
MT4/MT5 accounts cannot trade.

The server returns `{"success":true,"message":"processed"}` without waiting for
broker execution. The example reads the initial position, sends the close once,
then polls the account's positions once per second for up to five attempts.
It prints the full response so remaining positions can be inspected. The close
is not automatically resent. Normal broker volume increments and trade rules apply.

## Modify a position

Set `ACCOUNT`, `PLATFORM`, `POSITION_ID`, and at least one of `STOP_LOSS` or
`TAKE_PROFIT` in `trade/order_modify.py`, then run:

```sh
python trade/order_modify.py
```

It POSTs `/order_modify`, for example:

```json
{"account":"60072671","platform":"MT5","positionId":"123456789","takeProfit":1.1}
```

Tradovate is not supported. Identify the position with `positionId`; no symbol
field is needed. Both SL and TP may be supplied, but at least one is required.
Omitting one of the fields leaves it unchanged. Supplied values must be
finite positive JSON numbers; this endpoint does not clear stops using zero.
The account must be On, connected, and permitted to trade. Broker price precision
and stop-distance rules apply.

The response is `{"success":true,"message":"processed"}`. The script then polls
the account's positions once per second for up to five attempts to check only
the supplied SL/TP fields. It does not automatically resend the modification.

## Enter a market order

Set the account, platform, symbol, side, and volume in `trade/order_entry.py`, then run:

```sh
python trade/order_entry.py
```

The script POSTs `/order_entry`:

```json
{"account":"60072671","platform":"MT5","symbol":"EURUSD","side":"buy","volume":0.1,"stopLoss":1.05,"takeProfit":1.1}
```

`account`, `platform`, `symbol`, `side`, and `volume` are required. Side is `buy`
or `sell` (case-insensitive); volume is a finite positive number, using lots or
whole contracts for Tradovate. SL and TP are optional finite positive numbers
and may be supplied independently. Tradovate ignores SL/TP fields.
The symbol must exist on an account that is On, connected, and permitted to trade.
Normal broker volume increments, limits, and price rules apply.

The server returns `{"success":true,"message":"processed"}` to acknowledge the
request; this does not confirm broker execution. The example reads the initial
positions, submits the entry once, then polls once per second for up to five
attempts. It compares the symbol's signed net volume before and after entry, so
it also handles netting reductions and reversals. It prints all account positions
for inspection and never automatically resends an entry.
