# Trade-alert-and-Scanning

Python scanner and alert utility for market rows in CSV format.

## Input CSV format

Required headers:
- `symbol`
- `price`
- `volume`

Optional header:
- `timestamp` (ISO format, for example `2026-04-17T01:30:00`)

## Parameters

- `--input-csv` (required): path to CSV input file.
- `--symbols`: comma-separated symbols to include (example: `AAPL,MSFT,BTCUSD`).
- `--min-price`: scanner filter for minimum price.
- `--max-price`: scanner filter for maximum price.
- `--min-volume`: scanner filter for minimum volume.
- `--alert-above`: trigger alert when price is `>=` this value.
- `--alert-below`: trigger alert when price is `<=` this value.
- `--alert-change-pct`: trigger alert when absolute percent change vs previous symbol price meets/exceeds this value.
- `--cooldown-seconds`: suppress repeated alerts per `(symbol, rule)` for this number of seconds.
- `--output-json`: optional path to write all triggered alerts as JSON.

## Run

```bash
python3 trade_scanner.py \
  --input-csv ./market_data.csv \
  --symbols AAPL,MSFT \
  --min-price 10 \
  --min-volume 1000 \
  --alert-above 250 \
  --alert-change-pct 2 \
  --cooldown-seconds 60 \
  --output-json ./alerts.json
```
