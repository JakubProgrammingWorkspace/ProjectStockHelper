# AGENT / CLAUDE instructions

This file provides guidance to AI Agents (Antigravity, Claude Code, etc.) when working with code in this repository.

## Project Overview

StockHelper is a full-stack stock analysis platform. Django backend ingests data from multiple financial APIs (SEC, NASDAQ, Yahoo Finance, Massive, Tiingo) and exposes REST endpoints. React + TypeScript frontend renders interactive candlestick charts with financial overlays and a stock screener. 10-Q filings can be analysed by an LLM (OpenAI or Ollama) via a management command.

## Setup & Running

```bash
make up           # start all containers (Django :8000, Vite dev server :3000, Postgres :5432, Redis)
make down         # stop containers
```

## Common Commands

All commands are proxied through `make` to run inside Docker containers. See `Makefile` for a full list of targets.

- **Infrastructure**: `make initialize` (setup), `make up`, `make down`, `make sh`, `make sh-react`
- **Backend**: `make run-tests`, `make create-migrations`, `make execute-migrations`, `make uv -- <args>`
- **Frontend**: `make test-frontend`, `make build-frontend`, `make npm -- <args>`
- **Data**: `make fetch-tickers`, `make fetch-prices`, `make fetch-sec-financial`

## Architecture

### Backend (`apps/stock_data/`)

**Models** — four categories:
- *Ticker*: `SecTicker`, `MassiveTicker` — company metadata (symbol, exchange, CIK, sector, market cap)
- *Prices*: `HistoricalStockPrice` — OHLCV rows indexed by ticker + date
- *Financials*: `SecFinancialData`, `SecProcessedFinancialData` — SEC XBRL metrics (Revenue, Net Income, TTM, fiscal period)
- *Analysis*: `Sec10QLLMAnalysis` (LLM output for 10-Q filings), `StockScreenerStats` (precomputed screener metrics)

**Views / API** (`views.py`, `urls.py`):
- `GET /api/stock-data/<ticker>/` — OHLCV data with optional time-interval bundling
- `GET /api/additional-financial-data/<ticker>/` — revenue, net income
- `GET /api/tickers/` — list of active tickers
- `GET /api/stock-data/screener/` — screener results
- `GET /api/refresh-ticker-data/<ticker>/` — refresh price data on demand

**Services** (`services/`):
- API clients: `services/api_clients/` (SEC, Massive, Tiingo)
- Price fetching: `services/fetch_historical_prices/` (Tiingo, yfinance)
- SEC data pipeline: `sec_api_client.py` → `fetch_sec_financial_data_service.py` → `process_sec_financial_data_service.py` / `sec_filter_service.py`
- Screener: `screener_service.py`, `screener_stats_service.py`, `repositories/screener_stats_repository.py`
- LLM analysis: `services/document_processor/`
- Utilities: `price_bundler.py` (aggregates ticks to 1D/1W/1M)

**Management commands** (`management/commands/`): one command per data source / processing step — used by `make` targets.

### Frontend (`frontend/src/`)

**Routing** (`App.tsx`): React Router v7 — `/` redirects to `/NVDA`, `/:ticker` (chart view), `/screener`.

**Components**: `MainPanel.tsx` (chart + data visualisation), `Sidebar.tsx`, `TickerSelector.tsx`, `Screener.tsx`.

**Hooks** (one responsibility each):
- `useStockData` — fetches OHLCV from backend
- `useFinancialData` — fetches revenue/net-income overlays
- `useChart` — owns the `lightweight-charts` instance lifecycle

**Key libraries**: `lightweight-charts` 4.1.3, `react-router-dom` 7, Tailwind CSS 3, Vite, Vitest.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2, Python 3.12, `uv` package manager |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Charting | lightweight-charts 4.1.3 |
| Infra | Docker + Docker Compose + make file|

## Environment Variables

Variables live in `.env` (not accessible). Use `.env.dist` as the reference.

## Agent Configuration
Use the agent for: architecture decisions, complex debugging, refactoring planning, formatting, simple edits, boilerplate, bulk operations.