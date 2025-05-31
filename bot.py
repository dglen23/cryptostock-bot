# bot.py

import os
import time
import json
import tempfile
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import InputFile

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

CRYPTO_IDS   = [
    "bitcoin",
    "ethereum",
    "ripple",
    "hedera-hashgraph",
    "stellar",
    "quant-network",
    "ondo",
    "xdc-network",
    "pepe",
    "shiba-inu",
    "solana",
    "dogecoin",
]
STOCK_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]

# ── FETCHERS ────────────────────────────────────────────────────────────────────
def format_price(price: float) -> str:
    if price >= 1:
        return f"${price:,.2f}"
    s = f"{price:.8f}".rstrip("0").rstrip(".")
    return f"${s}"

def get_crypto_price_single(symbol: str) -> str:
    url  = "https://api.coingecko.com/api/v3/simple/price"
    data = requests.get(url, params={"ids": symbol, "vs_currencies": "usd"}).json()
    price = data.get(symbol, {}).get("usd")
    if price is None:
        return f"{symbol.title()}: N/A"
    return f"{symbol.replace('-', ' ').title()}: {format_price(price)}"

def get_stock_price_single(ticker: str) -> str:
    info  = yf.Ticker(ticker.upper()).info
    price = info.get("regularMarketPrice")
    if price is None:
        return f"{ticker.upper()}: N/A"
    return f"{ticker.upper()}: ${price:,.2f}"

def get_crypto_prices() -> str:
    url  = "https://api.coingecko.com/api/v3/simple/price"
    data = requests.get(url, params={"ids": ",".join(CRYPTO_IDS), "vs_currencies": "usd"}).json()
    lines = []
    for cid in CRYPTO_IDS:
        name  = cid.replace("-", " ").title()
        price = data.get(cid, {}).get("usd")
        if price is None:
            lines.append(f"{name}: N/A")
        else:
            lines.append(f"{name}: {format_price(price)}")
    return "📊 *Crypto Prices*\n" + "\n".join(lines)

def get_stock_prices() -> str:
    lines = []
    for t in STOCK_TICKERS:
        info  = yf.Ticker(t).info
        price = info.get("regularMarketPrice")
        if price is None:
            lines.append(f"{t}: N/A")
        else:
            lines.append(f"{t}: ${price:,.2f}")
    return "📈 *Top Stock Prices*\n" + "\n".join(lines)

# ── CHART GENERATORS ────────────────────────────────────────────────────────────
def plot_crypto_history(symbol: str, days: int) -> str:
    """
    Fetch historical price data for a crypto from CoinGecko and plot.
    Returns the file path to the saved PNG.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    resp = requests.get(url, params=params).json()
    prices = resp.get("prices", [])
    if not prices:
        return None

    # Convert to lists of datetime and price
    times = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    vals = [p[1] for p in prices]

    # Plot
    plt.figure(figsize=(6, 3))
    plt.plot(times, vals, linewidth=1.5)
    plt.title(f"{symbol.replace('-', ' ').title()} price (last {days}d)")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.tight_layout()

    # Save to a temporary file
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name)
    plt.close()
    return tmp_file.name

def plot_stock_history(ticker: str, period: str) -> str:
    """
    Fetch historical price data for a stock from yfinance and plot.
    `period` can be '1d', '7d', '30d', etc. Returns file path to PNG.
    """
    hist = yf.Ticker(ticker.upper()).history(period=period, interval="1h")
    if hist.empty:
        return None

    times = hist.index.to_pydatetime()
    vals = hist["Close"].tolist()

    plt.figure(figsize=(6, 3))
    plt.plot(times, vals, linewidth=1.5)
    plt.title(f"{ticker.upper()} price (last {period})")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.tight_layout()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name)
    plt.close()
    return tmp_file.name

# ── TELEGRAM API ────────────────────────────────────────────────────────────────
def get_updates(offset=None, timeout=30):
    resp = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": timeout})
    return resp.json().get("result", [])

def send_message(chat_id: int, text: str):
    requests.post(f"{BASE_URL}/sendMessage", data={
        "chat_id":    chat_id,
        "text":       text,
        "parse_mode": "Markdown"
    })

def send_photo(chat_id: int, photo_path: str, caption: str = None):
    with open(photo_path, "rb") as f:
        files = {"photo": (os.path.basename(photo_path), f, "image/png")}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "Markdown"
        requests.post(f"{BASE_URL}/sendPhoto", data=data, files=files)

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def main():
    offset = None
    print("🟢 Bot started, polling for updates...")
    while True:
        updates = get_updates(offset)
        for upd in updates:
            offset = upd["update_id"] + 1
            msg    = upd.get("message", {})
            text   = msg.get("text", "").strip()
            chat_id = msg.get("chat", {}).get("id")
            if not chat_id or not text:
                continue

            parts = text.split()
            cmd = parts[0].lower()

            if cmd == "/start":
                send_message(chat_id,
                    "👋 *CryptoStock Bot*\n\n"
                    "Use `/crypto` to get all crypto prices.\n"
                    "Use `/stocks` to get all stock prices.\n"
                    "Use `/chart <symbol> <period>` for a price chart:\n"
                    "`/chart bitcoin 7d` or `/chart AAPL 1d`."
                )

            elif cmd == "/crypto":
                send_message(chat_id, get_crypto_prices())

            elif cmd == "/stocks":
                send_message(chat_id, get_stock_prices())

            elif cmd == "/chart":
                # Expecting: /chart <symbol> <period>
                if len(parts) != 3:
                    send_message(chat_id, "Usage: `/chart <symbol> <period>`\n"
                                          "e.g. `/chart bitcoin 7d` or `/chart AAPL 1d`")
                    continue

                symbol = parts[1].lower()
                period = parts[2].lower()

                # Determine if crypto or stock
                if symbol in CRYPTO_IDS:
                    # Period should end with 'd' (days) or 'h' (hours)
                    if period.endswith("d") and period[:-1].isdigit():
                        days = int(period[:-1])
                        path = plot_crypto_history(symbol, days)
                        if path:
                            send_photo(chat_id, path, caption=f"📈 {symbol.replace('-', ' ').title()} - Last {days} days")
                        else:
                            send_message(chat_id, f"Could not fetch historical data for {symbol}.")
                    else:
                        send_message(chat_id, "For crypto, period must be in days, e.g. `7d`, `30d`.")
                elif symbol.upper() in STOCK_TICKERS:
                    # Period can be '1d', '7d', '30d', '1mo', etc.
                    # yfinance supports '1d', '5d', '1mo', '3mo', '6mo', '1y', etc.
                    # If user says '7d', translate to '7d'
                    yf_period = period
                    # For '7d', '30d', etc., yfinance uses '7d' or '30d'
                    if period.endswith("d") and period[:-1].isdigit():
                        yf_period = period
                    elif period in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]:
                        yf_period = period
                    else:
                        send_message(chat_id, "Invalid period for stock. Use `1d`, `5d`, `1mo`, `3mo`, etc.")
                        continue

                    path = plot_stock_history(symbol.upper(), yf_period)
                    if path:
                        send_photo(chat_id, path, caption=f"📈 {symbol.upper()} - Last {yf_period}")
                    else:
                        send_message(chat_id, f"Could not fetch historical data for {symbol.upper()}.")
                else:
                    send_message(chat_id, "Symbol not recognized. Use a valid crypto ID or stock ticker.")

        time.sleep(1)  # avoid hammering Telegram

if __name__ == "__main__":
    main()
