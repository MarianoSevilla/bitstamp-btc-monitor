"""Pruebas sin Internet del validador de velas UTC."""
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_bitstamp.py"
spec = importlib.util.spec_from_file_location("fetch_bitstamp", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CandleValidationTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
        self.items = []
        for date in (11, 12, 13, 14):
            ts = int(datetime(2026, 11, date, tzinfo=timezone.utc).timestamp())
            self.items.append({
                "timestamp": str(ts),
                "open": "70000",
                "high": "72000",
                "low": "68000",
                "close": "71000",
                "volume": "12",
            })
        self.payload = {"data": {"pair": "BTC/USD", "ohlc": self.items}}

    def test_candles_are_complete(self):
        result = module.validate_and_format(self.payload, self.now)
        self.assertEqual(result["latest_completed_utc"], "2026-11-14")
        self.assertEqual(len(result["candles"]), 4)

    def test_open_candle_is_rejected(self):
        self.items.append({**self.items[-1], "timestamp": str(int(datetime(2026, 11, 15, tzinfo=timezone.utc).timestamp()))})
        with self.assertRaisesRegex(ValueError, "abierta"):
            module.validate_and_format(self.payload, self.now)

    def test_stale_data_is_rejected(self):
        self.items.pop()
        with self.assertRaisesRegex(ValueError, "obsoletos"):
            module.validate_and_format(self.payload, self.now)

    def test_invalid_ohlc_is_rejected(self):
        self.items[-1]["low"] = "75000"
        with self.assertRaisesRegex(ValueError, "incoherentes"):
            module.validate_and_format(self.payload, self.now)

    def test_missing_day_is_rejected(self):
        self.items.pop(1)
        with self.assertRaisesRegex(ValueError, "Hueco"):
            module.validate_and_format(self.payload, self.now)


if __name__ == "__main__":
    unittest.main()
