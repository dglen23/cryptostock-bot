# bot.py

import os
import time
import requests
import yfinance as yf

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")
BASE_URL     = f"https://api.telegram.org/bot{TOKEN}"

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
    # for prices under $1, show up to 8 decimals and strip trailing zeros
    s = f"{price:.8f}".rstrip("0").rstrip(".")
    return f"${s}"

def get_crypto_prices() -> str:
    url  = "https://api.coingecko.com/api/v3/simple/price"
    data = requests.get(url, params={"ids": ",".join(CRYPTO_IDS), "vs_currencies": "usd"}).json()
    lines = []
    for cid in CRYPTO_IDS:
        name  = cid.replace("-", " ").title()
        price = data.get(cid, {}).get("usd")
        lines.append(f"{name}: {format_price(price)}" if price is not None else f"{name}: N/A")
    return "📊 *Crypto Prices*\n" + "\n".join(lines)

def get_stock_prices() -> str:
    lines = []
    for t in STOCK_TICKERS:
        info  = yf.Ticker(t).info
        price = info.get("regularMarketPrice")
        lines.append(f"{t}: ${price:,.2f}" if price is not None else f"{t}: N/A")
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

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def main():
    offset = None
    print("🟢 Bot started, polling for updates...")
    while True:
        updates = get_updates(offset)
        for upd in updates:
            offset  = upd["update_id"] + 1
            msg     = upd.get("message", {})
            text    = msg.get("text", "").strip()
            chat_id = msg.get("chat", {}).get("id")
            if not chat_id or not text:
                continue

            if text == "/start":
                send_message(chat_id,
                    "👋 *CryptoStock Bot*\n\n"
                    "Use `/crypto` to get crypto prices.\n"
                    "Use `/stocks` to get stock prices."
                )
            elif text == "/crypto":
                send_message(chat_id, get_crypto_prices())
            elif text == "/stocks":
                send_message(chat_id, get_stock_prices())

        time.sleep(1)  # avoid hammering Telegram

if __name__ == "__main__":
    main()
