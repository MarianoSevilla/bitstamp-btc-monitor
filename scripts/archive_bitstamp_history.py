#!/usr/bin/env python3
"""Archivo de datos PUBLICOS BTC/USD Bitstamp desde 2017 para auditoría estadística.

No lee cuentas personales, no evalúa cartera y no ejecuta operaciones.
Ejecutable solamente desde GitHub Actions (runner con Internet).
"""
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import time

PAIR = "BTC/USD"
DAY = 86400
START = datetime(2017, 1, 1, tzinfo=timezone.utc)
BASE = "https://www.bitstamp.net/api/v2/ohlc/btcusd/"

def pull_page(end):
    params = {
        "step": DAY, "limit": 1000, "end": end,
        "exclude_current_candle": "true"
    }
    url = BASE + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "BitstampHistoricalResearch/1.0"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError("HTTP " + str(response.status))
        result = json.load(response)
    if result.get("data", {}).get("pair") != PAIR:
        raise ValueError("Unexpected pair")
    rows = result["data"]["ohlc"]
    if len(rows) == 0 or len(rows) > 1000:
        raise ValueError("Empty or oversized page")
    return rows

def main():
    now = datetime.now(timezone.utc)
    today = int(datetime(now.year,now.month,now.day,tzinfo=timezone.utc).timestamp())
    latest_expected = today - DAY
    earliest_expected = int(START.timestamp())
    end = latest_expected
    all_rows = {}
    endpoints = 0
    while end >= earliest_expected and endpoints < 15:
        raw = pull_page(end)
        endpoints += 1
        times = []
        for row in raw:
            ts = int(row["timestamp"])
            if ts % DAY:
                raise ValueError("timestamp not midnight UTC")
            if ts >= today:
                raise ValueError("Open candle returned")
            nums = {k: Decimal(str(row[k])) for k in ("open","high","low","close","volume")}
            o,h,l,c = (nums[k] for k in ("open","high","low","close"))
            if any(not v.is_finite() for v in nums.values()) or l<=0 or h<max(o,c,l) or l>min(o,c) or nums["volume"]<0:
                raise ValueError("Invalid OHLC")
            times.append(ts)
            if earliest_expected <= ts <= latest_expected:
                if ts in all_rows and all_rows[ts] != row:
                    raise ValueError("Conflicting overlapping rows")
                all_rows[ts] = row
        mn = min(times)
        if mn > end:
            raise ValueError("Page does not honor end timestamp")
        next_end = mn-DAY
        if next_end >= end:
            raise ValueError("Non-progressing pagination")
        end = next_end
        time.sleep(0.3)
    expected = list(range(earliest_expected,latest_expected+1,DAY))
    missing = [ts for ts in expected if ts not in all_rows]
    if missing:
        missing_dates = [datetime.fromtimestamp(ts,timezone.utc).date().isoformat() for ts in missing[:12]]
        raise ValueError(f"Missing {len(missing)} daily candles: {missing_dates}")
    full = [all_rows[ts] for ts in expected]
    assert len(full) == len(expected)
    root = Path("data/history")
    root.mkdir(parents=True,exist_ok=True)
    for year in range(2017,now.year+1):
        subset = [x for x in full if datetime.fromtimestamp(int(x["timestamp"]),timezone.utc).year==year]
        out = {
            "source": "Bitstamp public original OHLC BTC/USD",
            "source_base_url": BASE,
            "query": "step=86400&limit=1000&end=<timestamp>&exclude_current_candle=true",
            "downloaded_utc": now.isoformat(timespec="seconds"),
            "year": year, "pair": PAIR,
            "candle_count": len(subset),
            "candles": [{"date_utc": datetime.fromtimestamp(int(x["timestamp"]),timezone.utc).date().isoformat(),**x} for x in subset]
        }
        path = root / f"btcusd_{year}.json"
        path.write_text(json.dumps(out,indent=1)+"\n", encoding="utf-8")
    print(f"Downloaded and validated {len(full)} daily Bitstamp candles in {endpoints} pages, "
          f"{START.date().isoformat()} to {datetime.fromtimestamp(latest_expected,timezone.utc).date().isoformat()}")
if __name__=="__main__":
    main()
