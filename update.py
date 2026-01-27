#!/usr/bin/env python3
"""
Daily portfolio updater.
Fetches Yahoo Finance prices for all positions, updates priceCache and saves a daily snapshot.
Designed to run via GitHub Actions cron at HK market close (16:30 HKT = 08:30 UTC).
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
import urllib.request

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
HKT = timezone(timedelta(hours=8))


def fetch_yahoo_price(ticker: str) -> dict:
    """Fetch price from Yahoo Finance chart API (no CORS needed server-side)."""
    clean = ticker.replace("b.HK", ".HK")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean}?interval=1d&range=5d"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  FAIL {clean}: {e}")
        return {"success": False, "error": str(e)}

    result = data.get("chart", {}).get("result", [None])[0]
    if not result:
        print(f"  FAIL {clean}: no result")
        return {"success": False, "error": "No data"}

    meta = result.get("meta", {})
    price = meta.get("regularMarketPrice")
    if price is None:
        print(f"  FAIL {clean}: no price")
        return {"success": False, "error": "No price"}

    # Extract yesterday's close from time series
    closes = (result.get("indicators", {}).get("quote", [{}])[0].get("close") or [])
    previous_close = price
    if len(closes) >= 2:
        for i in range(len(closes) - 2, -1, -1):
            if closes[i] is not None:
                previous_close = closes[i]
                break
    else:
        previous_close = meta.get("previousClose") or meta.get("chartPreviousClose") or price

    print(f"  OK {clean}: {price} (prevClose: {previous_close})")
    return {
        "success": True,
        "price": price,
        "previousClose": previous_close,
        "change": round(price - previous_close, 4),
        "changePercent": round(((price - previous_close) / previous_close) * 100, 4) if previous_close else 0,
        "currency": meta.get("currency", "HKD"),
        "lastUpdated": datetime.now(HKT).isoformat(),
    }


def run():
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found")
        sys.exit(1)

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    positions = data.get("positions", [])
    price_cache = data.get("priceCache", {})
    snapshots = data.get("snapshots", [])
    closed_trades = data.get("closedTrades", [])
    transactions = data.get("transactions", [])

    if not positions:
        print("No positions, nothing to do.")
        return

    today = datetime.now(HKT).strftime("%Y-%m-%d")
    print(f"=== Portfolio Update {today} ===")
    print(f"Positions: {len(positions)}")

    # 1. Fetch prices
    print("\nFetching prices...")
    for p in positions:
        ticker = p["ticker"]
        clean = ticker.replace("b.HK", ".HK")
        result = fetch_yahoo_price(ticker)
        if result["success"]:
            price_cache[clean] = result
            p["currentPrice"] = result["price"]

    # 2. Calculate snapshot
    current_value = sum(p["quantity"] * p.get("currentPrice", p.get("entryPrice", 0)) for p in positions)
    capital_engaged = sum(p["quantity"] * p.get("entryPrice", 0) for p in positions)
    realized_pnl = sum((t.get("exitPrice", 0) - t.get("entryPrice", 0)) * t.get("quantity", 0) for t in closed_trades)
    total_dividends = sum(t.get("amount", 0) for t in transactions if t.get("type") == "dividend")

    snapshot = {
        "date": today,
        "capitalEngaged": round(capital_engaged, 2),
        "portfolioValue": round(current_value, 2),
        "unrealizedPnL": round(current_value - capital_engaged, 2),
        "realizedPnL": round(realized_pnl, 2),
        "totalDividends": round(total_dividends, 2),
        "positionCount": len(positions),
    }

    # Replace today's snapshot if exists, otherwise append
    existing_idx = next((i for i, s in enumerate(snapshots) if s["date"] == today), None)
    if existing_idx is not None:
        snapshots[existing_idx] = snapshot
        print(f"\nUpdated existing snapshot for {today}")
    else:
        snapshots.append(snapshot)
        snapshots.sort(key=lambda s: s["date"])
        print(f"\nNew snapshot for {today}")

    print(f"  Value: {current_value:,.0f} HKD | Capital: {capital_engaged:,.0f} HKD | P&L: {current_value - capital_engaged:,.0f} HKD")

    # 3. Save
    data["priceCache"] = price_cache
    data["positions"] = positions
    data["snapshots"] = snapshots

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {DATA_FILE} ({len(snapshots)} snapshots)")


if __name__ == "__main__":
    run()
