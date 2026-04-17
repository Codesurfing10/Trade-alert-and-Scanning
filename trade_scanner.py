#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ScannerConfig:
    input_csv: Path
    symbols: Optional[set[str]]
    min_price: float
    max_price: float
    min_volume: int
    alert_above: Optional[float]
    alert_below: Optional[float]
    alert_change_pct: Optional[float]
    cooldown_seconds: int
    output_json: Optional[Path]


def _parse_symbols(raw: Optional[str]) -> Optional[set[str]]:
    if not raw:
        return None
    symbols = {token.strip().upper() for token in raw.split(",") if token.strip()}
    return symbols or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan market rows from CSV and emit configured trade alerts."
    )
    parser.add_argument("--input-csv", required=True, help="Path to input market CSV file.")
    parser.add_argument(
        "--symbols",
        default="",
        help="Comma-separated symbols to include. Empty means all symbols.",
    )
    parser.add_argument("--min-price", type=float, default=0.0, help="Minimum price filter.")
    parser.add_argument(
        "--max-price", type=float, default=float("inf"), help="Maximum price filter."
    )
    parser.add_argument("--min-volume", type=int, default=0, help="Minimum volume filter.")
    parser.add_argument(
        "--alert-above",
        type=float,
        default=None,
        help="Emit alert when price is greater than or equal to this value.",
    )
    parser.add_argument(
        "--alert-below",
        type=float,
        default=None,
        help="Emit alert when price is less than or equal to this value.",
    )
    parser.add_argument(
        "--alert-change-pct",
        type=float,
        default=None,
        help="Emit alert when absolute price change from previous row for a symbol reaches this percent.",
    )
    parser.add_argument(
        "--cooldown-seconds",
        type=int,
        default=0,
        help="Minimum seconds between alerts for the same symbol and rule.",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional file path to write alert list as JSON.",
    )
    return parser


def parse_args() -> ScannerConfig:
    args = build_parser().parse_args()
    return ScannerConfig(
        input_csv=Path(args.input_csv),
        symbols=_parse_symbols(args.symbols),
        min_price=args.min_price,
        max_price=args.max_price,
        min_volume=args.min_volume,
        alert_above=args.alert_above,
        alert_below=args.alert_below,
        alert_change_pct=args.alert_change_pct,
        cooldown_seconds=args.cooldown_seconds,
        output_json=Path(args.output_json) if args.output_json else None,
    )


def _parse_timestamp(value: Optional[str], fallback_index: int) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.fromtimestamp(fallback_index)


def run_scanner(config: ScannerConfig) -> List[dict]:
    if not config.input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {config.input_csv}")

    alerts: List[dict] = []
    previous_price: Dict[str, float] = {}
    last_alert_time: Dict[tuple[str, str], datetime] = {}

    with config.input_csv.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"symbol", "price", "volume"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV must contain headers: symbol, price, volume")

        for index, row in enumerate(reader):
            symbol = str(row["symbol"]).strip().upper()
            if not symbol:
                continue
            if config.symbols and symbol not in config.symbols:
                continue

            try:
                price = float(row["price"])
                volume = int(float(row["volume"]))
            except (TypeError, ValueError):
                continue

            if price < config.min_price or price > config.max_price:
                continue
            if volume < config.min_volume:
                continue

            ts = _parse_timestamp(row.get("timestamp"), index)

            def can_alert(rule: str) -> bool:
                if config.cooldown_seconds <= 0:
                    return True
                key = (symbol, rule)
                previous = last_alert_time.get(key)
                if previous is None:
                    return True
                return (ts - previous).total_seconds() >= config.cooldown_seconds

            def emit(rule: str, message: str) -> None:
                last_alert_time[(symbol, rule)] = ts
                alerts.append(
                    {
                        "timestamp": ts.isoformat(),
                        "symbol": symbol,
                        "price": price,
                        "volume": volume,
                        "rule": rule,
                        "message": message,
                    }
                )

            if config.alert_above is not None and price >= config.alert_above and can_alert("above"):
                emit("above", f"{symbol} price {price:.4f} is >= {config.alert_above:.4f}")

            if config.alert_below is not None and price <= config.alert_below and can_alert("below"):
                emit("below", f"{symbol} price {price:.4f} is <= {config.alert_below:.4f}")

            if config.alert_change_pct is not None and symbol in previous_price:
                base = previous_price[symbol]
                if base != 0:
                    move_pct = ((price - base) / base) * 100
                    if abs(move_pct) >= config.alert_change_pct and can_alert("change_pct"):
                        emit(
                            "change_pct",
                            f"{symbol} moved {move_pct:.2f}% (from {base:.4f} to {price:.4f})",
                        )
            previous_price[symbol] = price

    if config.output_json:
        config.output_json.parent.mkdir(parents=True, exist_ok=True)
        config.output_json.write_text(json.dumps(alerts, indent=2), encoding="utf-8")

    return alerts


def main() -> int:
    config = parse_args()
    alerts = run_scanner(config)
    if not alerts:
        print("No alerts triggered.")
        return 0
    for alert in alerts:
        print(f"[{alert['timestamp']}] {alert['rule'].upper()}: {alert['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
