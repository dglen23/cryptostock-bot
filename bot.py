# bot.py

import time
import requests
import yfinance as yf

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TOKEN     = "7052243619:AAFpSBnVOcO6R3gje4EjwuIYJnwugdJ3gI4"
BASE_URL  = f"https://api.telegram.org/bot{TOKEN}"
CRYPTO_IDS    = [
    "bitcoin",
    "ethereum",
    "ripple",
    "hedera-hashgraph",
    "stellar",
    "quant-network",
    "ondo",
    "xdc-network",
    "pepe",         # Pepe
    "shiba-inu",    # Shiba Inu
    "solana",       # Solana
    "dogecoin",     # Dogecoin
]
STOCK_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]

# ── FETCHERS ────────────────────────────────────────────────────────────────────
def get_crypto_prices() -> str:
    url = "https://api.coingecko.com/api/v3/simple/price"
    data = requests.get(url, params={"ids": ",".join(CRYPTO_IDS), "vs_currencies": "usd"}).json()
    lines = []
    for cid in CRYPTO_IDS:
        name  = cid.replace("-", " ").title()
        price = data.get(cid, {}).get("usd")
        lines.append(f"{name}: ${price:,.2f}" if price is not None else f"{name}: N/A")
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
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def main():
    offset = None
    print("🟢 Bot started, polling for updates...")
    while True:
        updates = get_updates(offset)
        for upd in updates:
            offset = upd["update_id"] + 1
            msg = upd.get("message", {})
            text = msg.get("text", "").strip()
            chat_id = msg.get("chat", {}).get("id")
            if not chat_id or not text:
                continue

            if text == "/start":
                send_message(chat_id,
                    "👋 *CryptoStock Bot*\n\n"
                    "Use `/crypto` to get crypto prices.\n"
                    "Use `/stocks` to get stock prices.",
                )
            elif text == "/crypto":
                send_message(chat_id, get_crypto_prices())
            elif text == "/stocks":
                send_message(chat_id, get_stock_prices())

        time.sleep(1)  # avoid hammering Telegram

if __name__ == "__main__":
    main()
