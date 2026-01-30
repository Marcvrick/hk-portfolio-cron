# Portfolio HK Tracker

Single-page React app for tracking a Hong Kong stock portfolio. Hosted on GitHub Pages with automated daily updates via GitHub Actions.

## Architecture

- **`index.html`** — Main app (also copied as `my_portfolio.html` in parent folder for local use)
- **`data.json`** — Portfolio data (positions, closed trades, transactions, price cache, snapshots)
- **`update.py`** — Python script that fetches Yahoo Finance prices and saves daily snapshots
- **`.github/workflows/daily-update.yml`** — Cron job running `update.py` Mon-Fri at 16:30 HKT (HK market close)

## Hosting

- **GitHub Pages**: `https://marcvrick.github.io/hk-portfolio-cron/`
- **Repo**: `https://github.com/marcvrick/hk-portfolio-cron` (public)
- Cron commits updated `data.json` daily with fresh prices and snapshots

## Tabs

1. **Positions** — Holdings table with entry/current price, P&L, days held, sort, add/close/delete. Per-line refresh button. Drawdown alerts inline (-8% warning, -10% stop loss). **Allocation pie chart** below with company name in tooltip. **Inline date editing** — click on entry date to modify.
2. **Performance** — Today's movers (daily % change, daily $ P&L, weight). Positions entered today use entry price as reference and show "NEW" badge. Closed trades from today included with "(sold)" label. Daily P&L calendar with live today value.
3. **History** — Equity curve (capital vs value over time). Snapshots generated automatically by cron.
4. **Trades completed** — Closed trades with **net P&L** (after fees). Shows gross P&L, fees breakdown on hover. Scatter chart duration vs P&L%. Stats par tranche de durée (0-7j, 8-30j, etc.) avec win rate et meilleur créneau.
5. **Transactions** — Deposits, withdrawals, dividends tracking.
6. **Settings** — CORS proxy selection, data import/export/reset.

## Key Features

### Trading Fees Calculation (HSBC HK)
When closing a position, the app calculates **HSBC Hong Kong trading fees**:
- **Buy fees**: Brokerage (0.25%, min HK$100) + Deposit charge (HK$5/lot, min 30, max 200) + Stamp duty (0.1%) + Regulatory fees
- **Sell fees**: Brokerage + Stamp duty + Regulatory fees (no deposit charge)
- **Net P&L** = Gross P&L - Total fees

The close modal shows a full breakdown before confirming.

### Partial Close Support
When closing a position, you can choose how many shares to sell:
- Default: full quantity
- Partial: enter a smaller quantity → remaining shares stay as open position
- Fee calculation adjusts based on sell quantity

### Auto-Price Fetch for New Positions
When adding a new position:
- Price is automatically fetched from Yahoo Finance
- Position appears immediately in Performance tab with live daily P&L
- "NEW" badge shown for same-day entries

### Real-Time Totals
Position tab footer totals update immediately when syncing prices (computed directly from priceCache).

## Key Behaviors

- **Auto-refresh on load**: Prices fetched from Yahoo Finance automatically when page opens (if cache >30min old)
- **Daily cron**: `update.py` runs via GitHub Actions at market close, updates `data.json` with prices and snapshots, commits and pushes
- **Same-day entries**: New positions entered today show daily P&L from entry price, not yesterday's close
- **Closed trades in daily P&L**: Positions closed today contribute their gain (exitPrice - previousClose) to Today's P&L
- **Snapshots**: Created automatically by cron and **updated in real-time** when trades are closed or positions change. Powers equity curve and calendar
- **Remote sync**: On page load, `index.html` fetches `data.json` from GitHub Pages to merge cron-updated snapshots and price cache

## Data

- **Remote**: `data.json` on GitHub (source of truth for snapshots/prices, updated by cron)
- **Local**: localStorage key `hk-portfolio-v7` (positions, trades, transactions edited in-browser)
- **Format**: JSON v7 with positions, closedTrades, transactions, priceCache, snapshots, settings
- **Price cache**: Stores price, previousClose (from time series), change, changePercent per ticker
- **Closed trades**: Now include `buyFees`, `sellFees`, `totalFees` for net P&L calculation

## Tech

- React 18 (CDN, no build)
- Recharts (CDN) — AreaChart, BarChart, ScatterChart, PieChart
- Tailwind CSS (CDN)
- Babel standalone (in-browser JSX)
- Python 3.12 (GitHub Actions) for daily updates

## Fee Reference

See `HSBC trading fees.md` for detailed fee structure and formulas.

## Changelog

### 2026-01-30
- **Fix**: Snapshots now update when trades are closed (previously only created if not existing)
  - Before: Closing a trade after cron ran would not update today's `realizedPnL` in the snapshot
  - After: Snapshot is updated whenever `realizedPnL`, `positionCount`, or `capitalEngaged` changes
  - This fixes the calendar not showing wins from trades closed after the daily cron run

### 2026-01-29
- Added TS Lines (2510.HK) to portfolio
- Closed Mongolian Mining (0975.HK) with +20,250 HKD profit

---

## What's Left to Improve

### Priority: GitHub API Persistence
**Done:**
- ✅ GitHub token storage in Settings tab
- ✅ "Push to GitHub" button to save data.json to repo
- ✅ "Pull from GitHub" button to fetch latest data.json and replace local data
- ✅ Full multi-device sync enabled (phone → push → computer → pull)

### Redesign: Light Theme (in progress)
Working file: `index-dev.html` (not deployed, for local testing only)

**New color palette:**
| Element | Color | Hex |
|---------|-------|-----|
| Background | Cream | `#f5f5e8` |
| Cards | White | `#ffffff` |
| Accent (buttons, highlights) | Lime green | `#c4e538` |
| Accent hover | Darker lime | `#a8c82a` |
| Text primary | Soft black | `#1a1a1a` |
| Text secondary | Gray | `#6b7280` |
| Positive P&L | Green | `#22c55e` |
| Negative P&L | Red | `#ef4444` |
| Card border/shadow | Light gray | `#e5e5e5` |

**Design direction:** Clean, modern dashboard style with subtle shadows, rounded cards, light background. Inspired by Zentry dashboard aesthetic.

### Other improvements
- Move to a proper React project with build step (Vite)
- Backend API to avoid CORS proxy dependency
- Sector/industry breakdown view
- Mobile responsiveness improvements
- Add fees to historical trades (backfill)

---

## Troubleshooting

### Closed position reappears in portfolio
This can happen if:
1. **Browser cache**: Clear localStorage and reload. The app will fetch fresh data from GitHub.
2. **Sync not pushed**: After closing a trade, use "Push to GitHub" in Settings to persist changes.
3. **Cron overwrote changes**: If you closed a trade but didn't push before the daily cron ran, the cron might have used stale data. Solution: Push your changes, then the next cron run will use the correct data.

**To force refresh from GitHub:**
1. Open browser DevTools (F12)
2. Go to Application > Local Storage
3. Delete `hk-portfolio-v7`
4. Reload the page

### Calendar not showing today's trade P&L
- Snapshots update automatically when you close trades
- If the calendar still shows wrong data, try "Push to GitHub" then reload
