# bot.py

import os
import time
import uuid
import json
import requests
import yfinance as yf

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
    # prices under $1: show up to 8 decimals, strip trailing zeros
    s = f"{price:.8f}".rstrip("0").rstrip(".")
    return f"${s}"

def get_crypto_price_single(symbol: str) -> str:
    """Fetch a single crypto price from CoinGecko by ID (symbol matches CoinGecko ID)."""
    url  = "https://api.coingecko.com/api/v3/simple/price"
    data = requests.get(url, params={"ids": symbol, "vs_currencies": "usd"}).json()
    price = data.get(symbol, {}).get("usd")
    if price is None:
        return f"{symbol.title()}: N/A"
    return f"{symbol.replace('-', ' ').title()}: {format_price(price)}"

def get_stock_price_single(ticker: str) -> str:
    """Fetch a single stock price from yfinance."""
    info  = yf.Ticker(ticker.upper()).info
    price = info.get("regularMarketPrice")
    if price is None:
        return f"{ticker.upper()}: N/A"
    return f"{ticker.upper()}: ${price:,.2f}"

def get_crypto_prices() -> str:
    """Fetch prices for all CRYPTO_IDS."""
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
    """Fetch prices for all STOCK_TICKERS."""
    lines = []
    for t in STOCK_TICKERS:
        info  = yf.Ticker(t).info
        price = info.get("regularMarketPrice")
        if price is None:
            lines.append(f"{t}: N/A")
        else:
            lines.append(f"{t}: ${price:,.2f}")
    return "📈 *Top Stock Prices*\n" + "\n".join(lines)

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

def answer_inline_query(inline_query_id: str, results: list):
    """
    results: a list of dicts representing InlineQueryResultArticle JSON objects.
    """
    payload = {
        "inline_query_id": inline_query_id,
        "results": json.dumps(results)
    }
    requests.post(f"{BASE_URL}/answerInlineQuery", data=payload)

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def main():
    offset = None
    print("🟢 Bot started, polling for updates...")
    while True:
        updates = get_updates(offset)
        for upd in updates:
            offset = upd["update_id"] + 1

            # Handle inline queries
            if "inline_query" in upd:
                iq = upd["inline_query"]
                query_text = iq.get("query", "").strip()
                iq_id = iq.get("id")

                # Only proceed if the user typed something
                if query_text:
                    results = []
                    # Try treating the query as a crypto ID first
                    if query_text.lower() in CRYPTO_IDS:
                        price_str = get_crypto_price_single(query_text.lower())
                        results.append({
                            "type": "article",
                            "id": str(uuid.uuid4()),
                            "title": price_str,
                            "input_message_content": {
                                "message_text": price_str
                            }
                        })
                    # If not a recognized crypto, try as a stock ticker
                    elif query_text.upper() in STOCK_TICKERS:
                        price_str = get_stock_price_single(query_text.upper())
                        results.append({
                            "type": "article",
                            "id": str(uuid.uuid4()),
                            "title": price_str,
                            "input_message_content": {
                                "message_text": price_str
                            }
                        })
                    else:
                        # Provide a help entry if unrecognized
                        hint = ("Type a valid crypto ID (e.g. `bitcoin`, `dogecoin`) "
                                "or stock ticker (e.g. `AAPL`, `GOOGL`).")
                        results.append({
                            "type": "article",
                            "id": str(uuid.uuid4()),
                            "title": "No match found",
                            "input_message_content": {
                                "message_text": hint
                            }
                        })

                    answer_inline_query(iq_id, results)
                continue

            # Handle regular messages (commands)
            if "message" in upd:
                msg = upd["message"]
                text = msg.get("text", "").strip()
                chat_id = msg.get("chat", {}).get("id")
                if not chat_id or not text:
                    continue

                if text == "/start":
                    send_message(chat_id,
                        "👋 *CryptoStock Bot*\n\n"
                        "Use `/crypto` to get all crypto prices.\n"
                        "Use `/stocks` to get all stock prices.\n\n"
                        "Or, from any chat, type:\n"
                        "`@YourBotUsername <symbol>`\n"
                        "…and I’ll reply inline with the price."
                    )
                elif text == "/crypto":
                    send_message(chat_id, get_crypto_prices())
                elif text == "/stocks":
                    send_message(chat_id, get_stock_prices())

        time.sleep(1)  # avoid hammering Telegram

if __name__ == "__main__":
    main()
