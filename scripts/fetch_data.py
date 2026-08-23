#!/usr/bin/env python3
"""
fetch_data.py — pulls the Nifty 500 universe + prices + date-aligned betas and
writes data/data.json, which the screener page reads at load time.

Run by GitHub Actions on a schedule (see .github/workflows/update.yml), or
manually:  python scripts/fetch_data.py

Design notes:
  * Universe and cap classification come from NSE's own index constituent
    files (Nifty 100 = large, Midcap 150 = mid, Smallcap 250 = small), so the
    labels are official rather than guessed. If NSE is unreachable, the last
    good universe cached in data/universe.json is reused.
  * Betas are computed in pandas on DATE-ALIGNED returns vs ^NSEI. Aligning by
    position instead of date silently destroys the correlation — that bug is
    why this is done here rather than in the browser.
  * Writes atomically-ish (temp then replace) so the page never reads a
    half-written file.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT = os.path.join(DATA_DIR, "data.json")
UNIVERSE_CACHE = os.path.join(DATA_DIR, "universe.json")

NSE_INDEX_FILES = {
    "Large": "ind_nifty100list.csv",
    "Mid": "ind_niftymidcap150list.csv",
    "Small": "ind_niftysmallcap250list.csv",
}
NSE_BASE = "https://nsearchives.nseindia.com/content/indices/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "Accept": "text/csv,*/*",
}

LOOKBACK_BARS = 252         # ~1 year of closes — the accuracy comes from this
HL_BARS = 60                # high/low kept only for recent window (spread/Parkinson)
FETCH_PERIOD = "400d"       # enough calendar days to yield LOOKBACK_BARS
CHUNK = 40                  # tickers per yfinance batch


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def build_universe() -> dict:
    """Fetch NSE constituent lists; fall back to the cached copy on failure."""
    uni = {}
    for cap, fn in NSE_INDEX_FILES.items():
        try:
            req = urllib.request.Request(NSE_BASE + fn, headers=HEADERS)
            raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
            for row in csv.DictReader(io.StringIO(raw)):
                sym = (row.get("Symbol") or "").strip()
                if sym and sym not in uni:
                    uni[sym] = {"cap": cap,
                                "industry": (row.get("Industry") or "").strip(),
                                "name": (row.get("Company Name") or "").strip()}
            log(f"universe: {cap} ok ({len(uni)} cumulative)")
        except Exception as e:
            log(f"universe: {cap} FAILED ({e})")

    # Require ALL THREE cap buckets. A partial fetch (e.g. only the smallcap
    # file succeeding) would otherwise pass a naive size check and silently
    # produce a screener missing every large and mid cap.
    caps_found = {v["cap"] for v in uni.values()}
    missing = set(NSE_INDEX_FILES) - caps_found
    if missing or len(uni) < 400:
        log(f"universe: INCOMPLETE (missing {sorted(missing) or 'none'}, "
            f"{len(uni)} symbols) — falling back to cache")
        if os.path.exists(UNIVERSE_CACHE):
            cached = json.load(open(UNIVERSE_CACHE))
            log(f"universe: using cached copy ({len(cached)} symbols)")
            return cached
        sys.exit("Could not build a complete universe and no cache available.")

    os.makedirs(DATA_DIR, exist_ok=True)
    json.dump(uni, open(UNIVERSE_CACHE, "w"))
    log(f"universe: complete ({len(uni)} symbols) — cache updated")
    return uni


def fetch_prices(symbols: list[str], uni: dict) -> list[dict]:
    out = []
    for i in range(0, len(symbols), CHUNK):
        batch = symbols[i:i + CHUNK]
        try:
            raw = yf.download(batch, period=FETCH_PERIOD, interval="1d",
                              auto_adjust=True, progress=False,
                              group_by="ticker", threads=True)
        except Exception as e:
            log(f"prices: batch {i} failed ({e})")
            continue
        for t in batch:
            try:
                df = raw[t][["High", "Low", "Close"]].dropna()
            except Exception:
                continue
            if len(df) < 120:          # need real history, not a new listing
                continue
            df = df.tail(LOOKBACK_BARS)
            base = t[:-3]
            out.append({
                "t": t,
                "cap": uni[base]["cap"],
                "ind": uni[base]["industry"],
                "c": [round(float(x), 2) for x in df["Close"]],              # full year
                "h": [round(float(x), 2) for x in df["High"].tail(HL_BARS)],  # recent only
                "l": [round(float(x), 2) for x in df["Low"].tail(HL_BARS)],
                "d": str(df.index[-1].date()),
            })
        log(f"prices: {min(i + CHUNK, len(symbols))}/{len(symbols)} — kept {len(out)}")
    return out


def compute_betas(symbols: list[str]) -> dict:
    """Date-aligned beta/correlation vs NIFTY (^NSEI)."""
    try:
        px = yf.download(symbols + ["^NSEI"], period="400d", interval="1d",
                         auto_adjust=True, progress=False)["Close"]
    except Exception as e:
        log(f"betas: download failed ({e}) — skipping")
        return {}
    rets = np.log(px / px.shift(1)).dropna(how="all").tail(LOOKBACK_BARS)   # 1y
    if "^NSEI" not in rets.columns:
        log("betas: no index data — skipping")
        return {}
    mkt = rets["^NSEI"]
    bm = {}
    for t in symbols:
        if t not in rets.columns:
            continue
        pair = pd.concat([rets[t], mkt], axis=1).dropna()   # <- date alignment
        if len(pair) < 60:
            continue
        a, b = pair.iloc[:, 0].values, pair.iloc[:, 1].values
        vb = b.var(ddof=1)
        if vb <= 0:
            continue
        bm[t] = {"b": round(float(np.cov(a, b, ddof=1)[0, 1] / vb), 3),
                 "cr": round(float(np.corrcoef(a, b)[0, 1]), 3)}
    if bm:
        mean_b = sum(v["b"] for v in bm.values()) / len(bm)
        log(f"betas: {len(bm)} computed, mean {mean_b:.2f} (sanity: on 1y this should be ~0.9–1.1)")
    return bm


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    uni = build_universe()
    symbols = [s + ".NS" for s in uni]
    log(f"universe size {len(symbols)}")

    stocks = fetch_prices(symbols, uni)
    if not stocks:
        sys.exit("No price data fetched — leaving previous data.json untouched.")

    betas = compute_betas(symbols)
    for s in stocks:
        b = betas.get(s["t"], {})
        s["b"] = b.get("b")
        s["cr"] = b.get("cr")

    if len(stocks) < 400:
        log(f"REFUSING to write: only {len(stocks)} stocks fetched (expected ~500). "
            "Keeping the previous data.json so the page never degrades silently.")
        sys.exit(1)

    asof = max(s["d"] for s in stocks)
    payload = {
        "asof": asof,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(stocks),
        "stocks": stocks,
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, OUT)

    caps = {}
    for s in stocks:
        caps[s["cap"]] = caps.get(s["cap"], 0) + 1
    log(f"WROTE {OUT}: {len(stocks)} stocks {caps} as-of {asof}")


if __name__ == "__main__":
    main()
