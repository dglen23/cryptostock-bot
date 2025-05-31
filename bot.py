# bot.py

import os
import time
import json
import tempfile
import traceback
import requests
import yfinance as yf

# Only import matplotlib if available; otherwise disable charting
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    print("⚠️ matplotlib not installed; /chart commands will be disabled")

from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# API keys for NewsAPI.org and Twitter API v2 (set these in Railway or your env)
NEWS_API_KEY         = os.getenv("NEWS_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

CRYPTO_IDS    = [
    "bitcoin", "ethereum", "ripple", "hedera-hashgraph",
    "stellar", "quant-network", "ondo", "xdc-network",
    "pepe", "shiba-inu", "solana", "dogecoin",
]
STOCK_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]

# ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────────
def format_price(price: float) -> str:
    if price >= 1:
        return f"${price:,.2f}"
    s = f"{price:.8f}".rstrip("0").rstrip(".")
    return f"${s}"

def get_crypto_price_single(symbol: str) -> str:
    try:
        url  = "https://api.coingecko.com/api/v3/simple/price"
        data = requests.get(url, params={"ids": symbol, "vs_currencies": "usd"}).json()
        price = data.get(symbol, {}).get("usd")
        if price is None:
            return f"{symbol.title()}: N/A"
        return f"{symbol.replace('-', ' ').title()}: {format_price(price)}"
    except Exception:
        traceback.print_exc()
        return f"{symbol.title()}: Error fetching price"

def get_stock_price_single(ticker: str) -> str:
    try:
        info  = yf.Ticker(ticker.upper()).info
        price = info.get("regularMarketPrice")
        if price is None:
            return f"{ticker.upper()}: N/A"
        return f"{ticker.upper()}: ${price:,.2f}"
    except Exception:
        traceback.print_exc()
        return f"{ticker.upper()}: Error fetching price"

def get_crypto_prices() -> str:
    try:
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
    except Exception:
        traceback.print_exc()
        return "⚠️ Error fetching all crypto prices."

def get_stock_prices() -> str:
    try:
        lines = []
        for t in STOCK_TICKERS:
            info  = yf.Ticker(t).info
            price = info.get("regularMarketPrice")
            if price is None:
                lines.append(f"{t}: N/A")
            else:
                lines.append(f"{t}: ${price:,.2f}")
        return "📈 *Top Stock Prices*\n" + "\n".join(lines)
    except Exception:
        traceback.print_exc()
        return "⚠️ Error fetching all stock prices."

# ── NEWS & TWEETS FUNCTIONS ─────────────────────────────────────────────────────
def get_news(symbol: str) -> str:
    if not NEWS_API_KEY:
        return "⚠️ NEWS_API_KEY not set in environment."
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": symbol,
            "apiKey": NEWS_API_KEY,
            "pageSize": 3,
            "sortBy": "publishedAt",
            "language": "en"
        }
        resp = requests.get(url, params=params).json()
        articles = resp.get("articles", [])
        if not articles:
            return f"📰 No recent news found for *{symbol.upper()}*."
        lines = [f"• [{a['title']}]({a['url']})" for a in articles]
        return f"📰 *News for {symbol.upper()}*\n" + "\n".join(lines)
    except Exception:
        traceback.print_exc()
        return f"⚠️ Error fetching news for {symbol.upper()}."

def get_tweets(symbol: str) -> str:
    if not TWITTER_BEARER_TOKEN:
        return "⚠️ TWITTER_BEARER_TOKEN not set in environment."
    try:
        # Build a more flexible query: symbol OR #symbol OR $SYMBOL
        query = f"{symbol} OR #{symbol} OR ${symbol.upper()}"
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        params = {
            "query": query,
            "max_results": 3,
            "tweet.fields": "text,author_id,created_at"
        }
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        # For debugging, uncomment next line and watch Railway logs:
        # print("Twitter response for", symbol, "→", data)
        tweets = data.get("data", [])
        if not tweets:
            return f"🐦 No recent tweets found for *{symbol.upper()}*."
        lines = []
        for t in tweets:
            txt = t.get("text", "").replace("\n", " ")
            created = t.get("created_at", "")
            lines.append(f"• {txt} _(at {created})_")
        return f"🐦 *Tweets for {symbol.upper()}*\n" + "\n".join(lines)
    except Exception:
        traceback.print_exc()
        return f"⚠️ Error fetching tweets for {symbol.upper()}."

# ── CHART GENERATORS ────────────────────────────────────────────────────────────
def plot_crypto_history(symbol: str, days: int) -> str:
    if plt is None:
        return None
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        resp = requests.get(url, params=params).json()
        prices = resp.get("prices", [])
        if not prices:
            return None
        times = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
        vals  = [p[1] for p in prices]
        plt.figure(figsize=(6, 3))
        plt.plot(times, vals, linewidth=1.5)
        plt.title(f"{symbol.replace('-', ' ').title()} price (last {days}d)")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.tight_layout()
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(tmp_file.name)
        plt.close()
        return tmp_file.name
    except Exception:
        traceback.print_exc()
        return None

def plot_stock_history(ticker: str, period: str) -> str:
    if plt is None:
        return None
    try:
        hist = yf.Ticker(ticker.upper()).history(period=period, interval="1h")
        if hist.empty:
            return None
        times = hist.index.to_pydatetime()
        vals  = hist["Close"].tolist()
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
    except Exception:
        traceback.print_exc()
        return None

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
                    "   `/chart bitcoin 7d` or `/chart AAPL 1d`.\n"
                    "Use `/news <symbol>` for latest headlines.\n"
                    "Use `/tweet <symbol>` for recent tweets."
                )

            elif cmd == "/crypto":
                try:
                    send_message(chat_id, get_crypto_prices())
                except Exception:
                    traceback.print_exc()
                    send_message(chat_id, "⚠️ Error retrieving crypto prices.")

            elif cmd == "/stocks":
                try:
                    send_message(chat_id, get_stock_prices())
                except Exception:
                    traceback.print_exc()
                    send_message(chat_id, "⚠️ Error retrieving stock prices.")

            elif cmd == "/chart":
                if len(parts) != 3:
                    send_message(chat_id,
                        "Usage: `/chart <symbol> <period>`\n"
                        "e.g. `/chart bitcoin 7d` or `/chart AAPL 1d`"
                    )
                    continue
                symbol = parts[1].lower()
                period = parts[2].lower()

                if symbol in CRYPTO_IDS:
                    if period.endswith("d") and period[:-1].isdigit():
                        days = int(period[:-1])
                        path = plot_crypto_history(symbol, days)
                        if path:
                            send_photo(chat_id, path, caption=f"📈 {symbol.replace('-', ' ').title()} - Last {days} days")
                        else:
                            send_message(chat_id, f"⚠️ Could not fetch historical data for {symbol}.")
                    else:
                        send_message(chat_id, "For crypto, period must be in days (e.g. `7d`, `30d`).")

                elif symbol.upper() in STOCK_TICKERS:
                    yf_period = period
                    if period.endswith("d") and period[:-1].isdigit():
                        yf_period = period
                    elif period not in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]:
                        send_message(chat_id, "Invalid period for stock. Use `1d`, `5d`, `1mo`, etc.")
                        continue
                    path = plot_stock_history(symbol.upper(), yf_period)
                    if path:
                        send_photo(chat_id, path, caption=f"📈 {symbol.upper()} - Last {yf_period}")
                    else:
                        send_message(chat_id, f"⚠️ Could not fetch historical data for {symbol.upper()}.")
                else:
                    send_message(chat_id, "⚠️ Symbol not recognized. Use a valid crypto ID or stock ticker.")

            elif cmd == "/news":
                if len(parts) != 2:
                    send_message(chat_id, "Usage: `/news <symbol>`\n(e.g. `/news bitcoin` or `/news AAPL`)")
                    continue
                symbol = parts[1].lower()
                send_message(chat_id, get_news(symbol))

            elif cmd == "/tweet":
                if len(parts) != 2:
                    send_message(chat_id, "Usage: `/tweet <symbol>`\n(e.g. `/tweet bitcoin` or `/tweet AAPL`)")
                    continue
                symbol = parts[1].lower()
                send_message(chat_id, get_tweets(symbol))

        time.sleep(1)  # avoid hammering Telegram

if __name__ == "__main__":
    main()
