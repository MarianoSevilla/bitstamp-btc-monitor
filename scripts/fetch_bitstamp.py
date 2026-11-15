#!/usr/bin/env python3
"""Descarga velas diarias COMPLETAS BTC/USD desde Bitstamp; no ejecuta operaciones."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
from urllib.request import Request, urlopen

URL = ("https://www.bitstamp.net/api/v2/ohlc/btcusd/"
       "?step=86400&limit=60&exclude_current_candle=true")
FIELDS = ("open", "high", "low", "close", "volume")


def validate_and_format(payload, now=None):
    now = now or datetime.now(timezone.utc)
    midnight = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    midnight_ts = int(midnight.timestamp())
    rows = payload["data"]["ohlc"]
    if payload["data"].get("pair", "").upper() != "BTC/USD":
        raise ValueError("Par inesperado: se esperaba BTC/USD")
    if not isinstance(rows, list) or len(rows) < 3:
        raise ValueError("Faltan velas en la respuesta")
    candles, seen = [], set()
    for row in rows:
        ts = int(row["timestamp"])
        if ts % 86400:
            raise ValueError("Timestamp no alineado a medianoche UTC")
        if ts in seen:
            raise ValueError("Timestamp duplicado")
        if ts >= midnight_ts:
            raise ValueError("Respuesta incluye una vela abierta; publicación bloqueada")
        seen.add(ts)
        vals = {key: Decimal(str(row[key])) for key in FIELDS}
        if any(not x.is_finite() for x in vals.values()):
            raise ValueError("Dato no finito")
        o, h, l, c = (vals[k] for k in ("open", "high", "low", "close"))
        if l <= 0 or h < max(o, c, l) or l > min(o, c) or vals["volume"] < 0:
            raise ValueError("Datos OHLC incoherentes")
        candles.append({
            "date_utc": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"),
            "timestamp": ts,
            **{k: row[k] for k in FIELDS},
        })
    candles.sort(key=lambda x: x["timestamp"])
    if candles[-1]["timestamp"] != midnight_ts - 86400:
        raise ValueError("Datos obsoletos: falta la última vela UTC completada")
    if any(b["timestamp"] - a["timestamp"] != 86400
           for a, b in zip(candles, candles[1:])):
        raise ValueError("Hueco en secuencia de velas diarias")
    return {
        "source": "Bitstamp API publica: OHLC BTC/USD",
        "source_url": URL,
        "pair": "BTC/USD",
        "step_seconds": 86400,
        "exclude_current_candle": True,
        "fetched_at_utc": now.isoformat(timespec="seconds"),
        "latest_completed_utc": candles[-1]["date_utc"],
        "candles": candles,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/bitstamp_btcusd_daily.json")
    args = parser.parse_args()
    request = Request(URL, headers={"User-Agent": "Bitstamp-BTC-daily-monitor/1.0"})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Bitstamp HTTP {response.status}")
        payload = json.load(response)
    result = validate_and_format(payload)
    target = Path(args.output)
    if target.exists():
        previous = json.loads(target.read_text(encoding="utf-8"))
        if previous.get("candles") == result["candles"]:
            print("Sin nuevas velas completadas")
            return
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(target)
    print(f"Actualizado hasta cierre UTC {result['latest_completed_utc']}")


if __name__ == "__main__":
    main()
