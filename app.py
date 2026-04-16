import os
import time
from dataclasses import dataclass, asdict
from typing import Any

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS


SMA_FAST = 50
SMA_SLOW = 150
SMA_TREND = 200
VOL_MA_PERIOD = 20
VOL_MULT_L1 = 1.5
VOL_MULT_L2 = 2.0
VOL_MULT_L3 = 3.0
PULLBACK_MAX = 8.0
EXTENDED_MAX = 20.0
STAGE2_SLOPE_BARS = 10
TRADING_DAYS_1Y = 252


@dataclass
class ScanResult:
    symbol: str
    signal: str
    stage2: bool
    breakout_bar: bool
    shallow_pullback: bool
    not_extended: bool
    vol_ratio: float
    pct_above_fast: float
    pullback_pct: float
    close: float
    sma_fast: float
    sma_slow: float
    sma_trend: float
    error: str | None = None


app = Flask(__name__)
frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": frontend_origin}})


def _avg(values: list[float]) -> float:
    return sum(values) / len(values)


def _sma(values: list[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"Not enough data for SMA{period}")
    return _avg(values[-period:])


def _finnhub_candles(symbol: str, resolution: str, lookback_days: int) -> dict[str, Any]:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY is not configured")

    now = int(time.time())
    start = now - (lookback_days * 24 * 60 * 60)
    resp = requests.get(
        "https://finnhub.io/api/v1/stock/candle",
        params={
            "symbol": symbol,
            "resolution": resolution,
            "from": start,
            "to": now,
            "token": api_key,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("s") != "ok":
        raise ValueError(data.get("s", "No candle data"))
    return data


def _compute_signal(symbol: str, data: dict[str, Any]) -> ScanResult:
    closes = [float(v) for v in data["c"]]
    highs = [float(v) for v in data["h"]]
    lows = [float(v) for v in data["l"]]
    volumes = [float(v) for v in data["v"]]

    # 252 is the approximate number of trading days in one market year.
    needed = max(SMA_TREND + STAGE2_SLOPE_BARS, TRADING_DAYS_1Y, 25)
    if len(closes) < needed:
        raise ValueError(f"Insufficient candles for {symbol}: need {needed}, got {len(closes)}")

    close = closes[-1]
    sma_fast = _sma(closes, SMA_FAST)
    sma_slow = _sma(closes, SMA_SLOW)
    sma_trend = _sma(closes, SMA_TREND)
    sma_slow_prev = _avg(closes[-(SMA_SLOW + STAGE2_SLOPE_BARS):-STAGE2_SLOPE_BARS])

    sma_slow_rising = sma_slow > sma_slow_prev
    sma_fast_above_slow = sma_fast > sma_slow
    price_above_fast = close > sma_fast
    price_above_slow = close > sma_slow
    stage2 = sma_slow_rising and sma_fast_above_slow and price_above_fast and price_above_slow

    vol_avg = _sma(volumes, VOL_MA_PERIOD)
    vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 0.0
    vol_l1 = vol_ratio >= VOL_MULT_L1
    vol_l2 = vol_ratio >= VOL_MULT_L2
    vol_l3 = vol_ratio >= VOL_MULT_L3

    pct_above_fast = ((close - sma_fast) / sma_fast) * 100 if sma_fast > 0 else 0.0
    not_extended = pct_above_fast <= EXTENDED_MAX

    recent_high = max(highs[-20:])
    pullback_pct = ((recent_high - close) / recent_high) * 100 if recent_high > 0 else 0.0
    shallow_pullback = (
        pullback_pct > 0
        and pullback_pct <= PULLBACK_MAX
        and close > sma_fast
        and stage2
    )

    prior_high_20 = max(highs[-21:-1])
    breakout_bar = close > prior_high_20 and vol_l2

    sig_l1 = stage2 and vol_l1 and not_extended and (not vol_l2)
    sig_l2 = stage2 and vol_l2 and not_extended and (breakout_bar or shallow_pullback)
    sig_l3 = stage2 and vol_l3 and not_extended and breakout_bar

    signal = "NONE"
    if sig_l3:
        signal = "L3"
    elif sig_l2:
        signal = "L2"
    elif sig_l1:
        signal = "L1"

    return ScanResult(
        symbol=symbol,
        signal=signal,
        stage2=stage2,
        breakout_bar=breakout_bar,
        shallow_pullback=shallow_pullback,
        not_extended=not_extended,
        vol_ratio=round(vol_ratio, 3),
        pct_above_fast=round(pct_above_fast, 3),
        pullback_pct=round(pullback_pct, 3),
        close=round(close, 3),
        sma_fast=round(sma_fast, 3),
        sma_slow=round(sma_slow, 3),
        sma_trend=round(sma_trend, 3),
    )


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok"})


@app.post("/api/scan")
def scan() -> Any:
    payload = request.get_json(silent=True) or {}
    symbols = payload.get("symbols", [])
    resolution = str(payload.get("resolution", "D"))
    lookback_days = int(payload.get("lookback_days", 420))

    if not symbols or not isinstance(symbols, list):
        return jsonify({"error": "symbols must be a non-empty array"}), 400

    cleaned = []
    for raw in symbols:
        symbol = str(raw).upper().strip()
        if symbol:
            cleaned.append(symbol)

    if not cleaned:
        return jsonify({"error": "No valid symbols provided"}), 400

    results: list[dict[str, Any]] = []
    for symbol in cleaned:
        try:
            candles = _finnhub_candles(symbol, resolution, lookback_days)
            item = _compute_signal(symbol, candles)
            results.append(asdict(item))
        except (RuntimeError, ValueError, requests.RequestException) as exc:
            results.append(
                asdict(
                    ScanResult(
                        symbol=symbol,
                        signal="NONE",
                        stage2=False,
                        breakout_bar=False,
                        shallow_pullback=False,
                        not_extended=False,
                        vol_ratio=0.0,
                        pct_above_fast=0.0,
                        pullback_pct=0.0,
                        close=0.0,
                        sma_fast=0.0,
                        sma_slow=0.0,
                        sma_trend=0.0,
                        error=str(exc),
                    )
                )
            )

    priority = {"L3": 0, "L2": 1, "L1": 2, "NONE": 3}
    results.sort(key=lambda r: (priority.get(r["signal"], 99), -r["vol_ratio"]))

    return jsonify(
        {
            "count": len(results),
            "generated_at": int(time.time()),
            "results": results,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
