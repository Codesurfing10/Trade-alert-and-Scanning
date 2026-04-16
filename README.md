# Trade-alert-and-Scanning

Alert + scanning web app using the AIH framework logic (Stage 2, volume confirmation, shallow pullback, extension checks) powered by Finnhub data.

## Architecture

- **Backend (Render, Python/Flask):** fetches Finnhub candles with secret key and computes L1/L2/L3 signals.
- **Frontend (GitHub Pages):** static UI in `docs/` that calls backend API and shows scan results.

## Backend setup (local)

1. Create venv and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Set environment variables:
   ```bash
   export FINNHUB_API_KEY=your_finnhub_key
   export FRONTEND_ORIGIN=https://<your-username>.github.io
   ```
3. Run:
   ```bash
   python app.py
   ```

Server defaults to `http://localhost:8000`.

## API

### `GET /health`
Health check.

### `POST /api/scan`
Request body:
```json
{
  "symbols": ["AAPL", "MSFT", "NVDA"],
  "resolution": "D",
  "lookback_days": 420
}
```

Response includes metrics and signal classification (`L1`, `L2`, `L3`, or `NONE`) for each symbol.

## Render deployment

- `render.yaml` is included for web service deployment.
- Add environment variable in Render dashboard:
  - `FINNHUB_API_KEY` (required)
  - `FRONTEND_ORIGIN` (optional, for CORS tightening)

## GitHub Pages deployment

1. In GitHub repo settings, enable Pages and select `docs/` folder.
2. Open `docs/app.js` and set `DEFAULT_BACKEND_URL` to your Render URL (or use the UI field).

## Indicator logic implemented

- SMA(50), SMA(150), SMA(200)
- Stage 2 trend gate
- Volume ratio + L1/L2/L3 tiers (1.5x/2.0x/3.0x)
- Not extended (`<= 20%` above SMA50)
- Shallow pullback (`<= 8%` from recent 20-bar high)
- Breakout (close > prior 20-bar high + L2 volume)
- Signal classification:
  - `L1`: Stage2 + L1 volume + not extended + not L2
  - `L2`: Stage2 + L2 volume + not extended + (breakout or shallow pullback)
  - `L3`: Stage2 + L3 volume + not extended + breakout
