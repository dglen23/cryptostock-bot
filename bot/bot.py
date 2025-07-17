# bot.py

import os
import time
import json
import tempfile
import traceback
import requests
import yfinance as yf
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils import executor

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

# Initialize aiogram bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# NewsAPI.org key (set this in Railway or your environment)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

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
        url = "https://api.coingecko.com/api/v3/simple/price"
        response = requests.get(url, params={"ids": symbol, "vs_currencies": "usd"}, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            return f"{symbol.replace('-', ' ').title()}: API Error ({response.status_code})"
        
        data = response.json()
        
        # Check if the response contains the expected data structure
        if not isinstance(data, dict):
            return f"{symbol.replace('-', ' ').title()}: Invalid API response"
        
        # Check if the symbol exists in the response
        if symbol not in data:
            return f"{symbol.replace('-', ' ').title()}: Symbol not found"
        
        price = data[symbol].get("usd")
        
        # Check if price is None, 0, or negative
        if price is None:
            return f"{symbol.replace('-', ' ').title()}: Price unavailable"
        elif price <= 0:
            return f"{symbol.replace('-', ' ').title()}: Invalid price data"
        
        return f"{symbol.replace('-', ' ').title()}: {format_price(price)}"
        
    except requests.exceptions.Timeout:
        return f"{symbol.replace('-', ' ').title()}: Request timeout"
    except requests.exceptions.ConnectionError:
        return f"{symbol.replace('-', ' ').title()}: Connection error"
    except requests.exceptions.RequestException as e:
        return f"{symbol.replace('-', ' ').title()}: Network error"
    except (ValueError, KeyError, TypeError) as e:
        return f"{symbol.replace('-', ' ').title()}: Data parsing error"
    except Exception as e:
        traceback.print_exc()
        return f"{symbol.replace('-', ' ').title()}: Unexpected error"

def get_stock_price_single(ticker: str) -> str:
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = ticker_obj.info
        
        # Check if we got valid info
        if not info or not isinstance(info, dict):
            return f"{ticker.upper()}: Invalid ticker data"
        
        price = info.get("regularMarketPrice")
        
        # Check if price is None, 0, or negative
        if price is None:
            return f"{ticker.upper()}: Price unavailable"
        elif price <= 0:
            return f"{ticker.upper()}: Invalid price data"
        
        return f"{ticker.upper()}: ${price:,.2f}"
        
    except Exception as e:
        traceback.print_exc()
        return f"{ticker.upper()}: Error fetching price"

def get_crypto_prices() -> str:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        response = requests.get(url, params={"ids": ",".join(CRYPTO_IDS), "vs_currencies": "usd"}, timeout=15)
        
        # Check if the request was successful
        if response.status_code != 200:
            return f"⚠️ API Error ({response.status_code}): Unable to fetch crypto prices"
        
        data = response.json()
        
        # Check if the response contains the expected data structure
        if not isinstance(data, dict):
            return "⚠️ Invalid API response: Unable to parse crypto price data"
        
        lines = []
        successful_prices = 0
        total_cryptos = len(CRYPTO_IDS)
        
        for cid in CRYPTO_IDS:
            name = cid.replace("-", " ").title()
            
            # Check if the crypto exists in the response
            if cid not in data:
                lines.append(f"{name}: Symbol not found")
                continue
            
            price = data[cid].get("usd")
            
            # Check if price is None, 0, or negative
            if price is None:
                lines.append(f"{name}: Price unavailable")
            elif price <= 0:
                lines.append(f"{name}: Invalid price data")
            else:
                lines.append(f"{name}: {format_price(price)}")
                successful_prices += 1
        
        # Add summary if some prices failed
        summary = ""
        if successful_prices < total_cryptos:
            failed_count = total_cryptos - successful_prices
            summary = f"\n\n📊 *Summary*: {successful_prices}/{total_cryptos} prices retrieved successfully"
            if failed_count > 0:
                summary += f" ({failed_count} failed)"
        
        return "📊 *Crypto Prices*\n" + "\n".join(lines) + summary
        
    except requests.exceptions.Timeout:
        return "⚠️ Request timeout: API took too long to respond"
    except requests.exceptions.ConnectionError:
        return "⚠️ Connection error: Unable to reach the API server"
    except requests.exceptions.RequestException as e:
        return f"⚠️ Network error: {str(e)}"
    except (ValueError, KeyError, TypeError) as e:
        return f"⚠️ Data parsing error: {str(e)}"
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Unexpected error: {str(e)}"

def get_stock_prices() -> str:
    try:
        lines = []
        successful_prices = 0
        total_stocks = len(STOCK_TICKERS)
        
        for t in STOCK_TICKERS:
            try:
                ticker_obj = yf.Ticker(t)
                info = ticker_obj.info
                
                # Check if we got valid info
                if not info or not isinstance(info, dict):
                    lines.append(f"{t}: Invalid ticker data")
                    continue
                
                price = info.get("regularMarketPrice")
                
                # Check if price is None, 0, or negative
                if price is None:
                    lines.append(f"{t}: Price unavailable")
                elif price <= 0:
                    lines.append(f"{t}: Invalid price data")
                else:
                    lines.append(f"{t}: ${price:,.2f}")
                    successful_prices += 1
                    
            except Exception as e:
                lines.append(f"{t}: Error fetching price")
        
        # Add summary if some prices failed
        summary = ""
        if successful_prices < total_stocks:
            failed_count = total_stocks - successful_prices
            summary = f"\n\n📈 *Summary*: {successful_prices}/{total_stocks} prices retrieved successfully"
            if failed_count > 0:
                summary += f" ({failed_count} failed)"
        
        return "📈 *Top Stock Prices*\n" + "\n".join(lines) + summary
        
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Error fetching all stock prices: {str(e)}"

# ── NEWS FUNCTIONS ──────────────────────────────────────────────────────────────
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

def send_webapp_button(chat_id: int):
    """Send a custom keyboard with a web app button to launch the frontend."""
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 Open App",
                    "web_app": {
                        "url": "https://frontend-production-db33.up.railway.app"
                    }
                }
            ]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": "Click the button below to open the Gumball Crypto News app:",
        "reply_markup": keyboard
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json=payload
    )

# ── AIOGRAM HANDLERS ────────────────────────────────────────────────────────────
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    """Handle /start command with WebApp URL button."""
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="🚀 Launch Web App",
            url="https://frontend-production-db33.up.railway.app"
        )
    )
    await message.answer(
        "👋 *CryptoStock Bot*\n\n"
        "Use `/crypto` to get all crypto prices.\n"
        "Use `/stocks` to get all stock prices.\n"
        "Use `/chart <symbol> <period>` for a price chart:\n"
        "   `/chart bitcoin 7d` or `/chart AAPL 1d`.\n"
        "Use `/news <symbol>` for latest headlines.\n\n"
        "🌐 Or click the button below to open the web interface:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "crypto_prices")
async def crypto_prices_callback(callback_query: types.CallbackQuery):
    """Handle crypto prices button callback."""
    await callback_query.answer("Fetching crypto prices...")
    try:
        await callback_query.message.answer(get_crypto_prices(), parse_mode="Markdown")
    except Exception:
        traceback.print_exc()
        await callback_query.message.answer("⚠️ Error retrieving crypto prices.")

@dp.callback_query_handler(lambda c: c.data == "stock_prices")
async def stock_prices_callback(callback_query: types.CallbackQuery):
    """Handle stock prices button callback."""
    await callback_query.answer("Fetching stock prices...")
    try:
        await callback_query.message.answer(get_stock_prices(), parse_mode="Markdown")
    except Exception:
        traceback.print_exc()
        await callback_query.message.answer("⚠️ Error retrieving stock prices.")

@dp.callback_query_handler(lambda c: c.data == "get_news")
async def get_news_callback(callback_query: types.CallbackQuery):
    """Handle get news button callback."""
    await callback_query.answer("Fetching latest news...")
    try:
        # For general news, we can fetch news for a popular crypto or stock
        await callback_query.message.answer(
            "📰 *Latest Crypto & Stock News*\n\n"
            "Use `/news <symbol>` to get specific news.\n"
            "Examples:\n"
            "• `/news bitcoin` - Bitcoin news\n"
            "• `/news AAPL` - Apple stock news\n"
            "• `/news ethereum` - Ethereum news",
            parse_mode="Markdown"
        )
    except Exception:
        traceback.print_exc()
        await callback_query.message.answer("⚠️ Error retrieving news.")

@dp.callback_query_handler(lambda c: c.data.startswith("chart_"))
async def chart_callback(callback_query: types.CallbackQuery):
    """Handle chart button callbacks."""
    chart_data = callback_query.data[6:]  # Remove "chart_" prefix
    await callback_query.answer(f"Generating chart for {chart_data}...")
    
    try:
        parts = chart_data.split("_")
        if len(parts) >= 2:
            symbol = parts[0].lower()
            period = parts[1].lower()
            
            if symbol in CRYPTO_IDS:
                if period.endswith("d") and period[:-1].isdigit():
                    days = int(period[:-1])
                    path = plot_crypto_history(symbol, days)
                    if path:
                        with open(path, 'rb') as photo:
                            await callback_query.message.answer_photo(
                                photo,
                                caption=f"📈 {symbol.replace('-', ' ').title()} - Last {days} days"
                            )
                    else:
                        await callback_query.message.answer(f"⚠️ Could not fetch historical data for {symbol}.")
                else:
                    await callback_query.message.answer("For crypto, period must be in days (e.g. `7d`, `30d`).")
            elif symbol.upper() in STOCK_TICKERS:
                yf_period = period
                if period.endswith("d") and period[:-1].isdigit():
                    yf_period = period
                elif period not in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]:
                    await callback_query.message.answer("Invalid period for stock. Use `1d`, `5d`, `1mo`, etc.")
                    return
                path = plot_stock_history(symbol.upper(), yf_period)
                if path:
                    with open(path, 'rb') as photo:
                        await callback_query.message.answer_photo(
                            photo,
                            caption=f"📈 {symbol.upper()} - Last {yf_period}"
                        )
                else:
                    await callback_query.message.answer(f"⚠️ Could not fetch historical data for {symbol.upper()}.")
            else:
                await callback_query.message.answer("⚠️ Symbol not recognized. Use a valid crypto ID or stock ticker.")
        else:
            await callback_query.message.answer("Invalid chart format. Expected: chart_symbol_period")
    except Exception as e:
        traceback.print_exc()
        await callback_query.message.answer(f"⚠️ Error generating chart: {str(e)}")

@dp.callback_query_handler(lambda c: c.data.startswith("news_"))
async def news_callback(callback_query: types.CallbackQuery):
    """Handle news button callbacks."""
    symbol = callback_query.data[5:]  # Remove "news_" prefix
    await callback_query.answer(f"Fetching news for {symbol.upper()}...")
    
    try:
        await callback_query.message.answer(get_news(symbol), parse_mode="Markdown")
    except Exception as e:
        traceback.print_exc()
        await callback_query.message.answer(f"⚠️ Error fetching news for {symbol.upper()}: {str(e)}")

@dp.message_handler(content_types=['web_app_data'])
async def handle_webapp_data(message: types.Message):
    """Handle data received from the Telegram Web App."""
    try:
        data = message.web_app_data.data
        
        if data == "crypto":
            await message.answer("📊 Fetching crypto prices...")
            await message.answer(get_crypto_prices(), parse_mode="Markdown")
        elif data == "stocks":
            await message.answer("📈 Fetching stock prices...")
            await message.answer(get_stock_prices(), parse_mode="Markdown")
        elif data.startswith("chart:"):
            # Handle chart requests from WebApp
            chart_data = data[6:]  # Remove "chart:" prefix
            parts = chart_data.split()
            if len(parts) >= 2:
                symbol = parts[0].lower()
                period = parts[1].lower()
                
                if symbol in CRYPTO_IDS:
                    if period.endswith("d") and period[:-1].isdigit():
                        days = int(period[:-1])
                        path = plot_crypto_history(symbol, days)
                        if path:
                            with open(path, 'rb') as photo:
                                await message.answer_photo(
                                    photo,
                                    caption=f"📈 {symbol.replace('-', ' ').title()} - Last {days} days"
                                )
                        else:
                            await message.answer(f"⚠️ Could not fetch historical data for {symbol}.")
                    else:
                        await message.answer("For crypto, period must be in days (e.g. `7d`, `30d`).")
                elif symbol.upper() in STOCK_TICKERS:
                    yf_period = period
                    if period.endswith("d") and period[:-1].isdigit():
                        yf_period = period
                    elif period not in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]:
                        await message.answer("Invalid period for stock. Use `1d`, `5d`, `1mo`, etc.")
                        return
                    path = plot_stock_history(symbol.upper(), yf_period)
                    if path:
                        with open(path, 'rb') as photo:
                            await message.answer_photo(
                                photo,
                                caption=f"📈 {symbol.upper()} - Last {yf_period}"
                            )
                    else:
                        await message.answer(f"⚠️ Could not fetch historical data for {symbol.upper()}.")
                else:
                    await message.answer("⚠️ Symbol not recognized. Use a valid crypto ID or stock ticker.")
            else:
                await message.answer("Invalid chart format. Expected: chart:symbol period")
        elif data.startswith("news:"):
            # Handle news requests from WebApp
            symbol = data[5:]  # Remove "news:" prefix
            await message.answer(f"📰 Fetching news for {symbol.upper()}...")
            await message.answer(get_news(symbol), parse_mode="Markdown")
        else:
            await message.answer(f"❓ Unknown WebApp data: {data}")
    except Exception as e:
        traceback.print_exc()
        await message.answer(f"⚠️ Error processing WebApp data: {str(e)}")

@dp.message_handler(commands=["crypto", "cryptocurrency", "coins", "crypto_prices"])
async def crypto_command(message: types.Message):
    """Handle crypto price commands."""
    try:
        await message.answer(get_crypto_prices(), parse_mode="Markdown")
    except Exception:
        traceback.print_exc()
        await message.answer("⚠️ Error retrieving crypto prices.")

@dp.message_handler(commands=["stocks", "equities", "shares", "stock_prices"])
async def stocks_command(message: types.Message):
    """Handle stock price commands."""
    try:
        await message.answer(get_stock_prices(), parse_mode="Markdown")
    except Exception:
        traceback.print_exc()
        await message.answer("⚠️ Error retrieving stock prices.")

@dp.message_handler(commands=["chart", "graph", "price_chart", "chart_price"])
async def chart_command(message: types.Message):
    """Handle chart commands."""
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(
            "Usage: `/chart <symbol> <period>`\n"
            "e.g. `/chart bitcoin 7d` or `/chart AAPL 1d`",
            parse_mode="Markdown"
        )
        return
    
    symbol = parts[1].lower()
    period = parts[2].lower()

    if symbol in CRYPTO_IDS:
        if period.endswith("d") and period[:-1].isdigit():
            days = int(period[:-1])
            path = plot_crypto_history(symbol, days)
            if path:
                with open(path, 'rb') as photo:
                    await message.answer_photo(
                        photo,
                        caption=f"📈 {symbol.replace('-', ' ').title()} - Last {days} days"
                    )
            else:
                await message.answer(f"⚠️ Could not fetch historical data for {symbol}.")
        else:
            await message.answer("For crypto, period must be in days (e.g. `7d`, `30d`).")
    elif symbol.upper() in STOCK_TICKERS:
        yf_period = period
        if period.endswith("d") and period[:-1].isdigit():
            yf_period = period
        elif period not in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]:
            await message.answer("Invalid period for stock. Use `1d`, `5d`, `1mo`, etc.")
            return
        path = plot_stock_history(symbol.upper(), yf_period)
        if path:
            with open(path, 'rb') as photo:
                await message.answer_photo(
                    photo,
                    caption=f"📈 {symbol.upper()} - Last {yf_period}"
                )
        else:
            await message.answer(f"⚠️ Could not fetch historical data for {symbol.upper()}.")
    else:
        await message.answer("⚠️ Symbol not recognized. Use a valid crypto ID or stock ticker.")

@dp.message_handler(commands=["news", "headlines", "latest_news", "news_articles"])
async def news_command(message: types.Message):
    """Handle news commands."""
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer(
            "Usage: `/news <symbol>`\n(e.g. `/news bitcoin` or `/news AAPL`)",
            parse_mode="Markdown"
        )
        return
    
    symbol = parts[1].lower()
    await message.answer(get_news(symbol), parse_mode="Markdown")

# ── MAIN FUNCTION ────────────────────────────────────────────────────────────────
async def main():
    """Start the bot."""
    print("🟢 Bot started with aiogram...")
    await dp.start_polling()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
