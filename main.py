import ccxt
import pandas as pd
from ta.trend import ema_indicator
import asyncio
import nest_asyncio
from telegram import Bot
from config import symbols

# Binance API credentials
BINANCE_API_KEY = 'waSxjHbfTUnu9Z0swCLzUL9iBDqTtfhj1uiIByh8ROlap6G0Asyr8Fh0TzSjBeEK'
BINANCE_API_SECRET = 'F9seOIJwGEDDkiSEYDb8H54Rr5kYmMfKpBf6b8KBUguPJSata8r1wmVQUH1aiq7V'
interval = '4h'  # 1-hour candlesticks

# Telegram Bot Token and Chat ID
telegram_token = '6814496979:AAElB7IrLWtspYnA4NCg8dWeIPhMF5tJTYY'
chat_id = '1385370555'

# Initialize Binance client
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # Set the default type to futures
    }
})

# Dictionary to store the last alert messages for each symbol
last_alert_messages = {}

# Function to get historical candlestick data
def get_historical_data(symbol, interval, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, interval, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Function to check EMA cross
def check_ema_cross(df, short_period=2, long_period=25):
    df['ema_short'] = ema_indicator(df['close'], window=short_period)
    df['ema_long'] = ema_indicator(df['close'], window=long_period)

    cross_over = df['ema_short'][-2] > df['ema_long'][-2] and df['ema_short'][-3] <= df['ema_long'][-3]
    cross_under = df['ema_short'][-2] < df['ema_long'][-2] and df['ema_short'][-3] >= df['ema_long'][-3]

    return cross_over, cross_under

# Function to send Telegram message (now defined as async)
async def send_telegram_message(symbol, message):
    # Check if the current message is the same as the previous one for this symbol
    if last_alert_messages.get(symbol) != message:
        await telegram_bot.send_message(chat_id=chat_id, text=message)
        # Update the last alert message for this symbol
        last_alert_messages[symbol] = message

# Modify the main function to use symbols from the configuration file
async def main():
    while True:
        for symbol in symbols:
            try:
                historical_data = get_historical_data(symbol, interval)
                cross_over, cross_under = check_ema_cross(historical_data)

                if cross_over:
                    message = f'EMA Cross Over detected on {symbol} ({interval}).'
                    await send_telegram_message(symbol, message)

                if cross_under:
                    message = f'EMA Cross Under detected on {symbol} ({interval}).'
                    await send_telegram_message(symbol, message)

            except Exception as e:
                print(f"Error processing {symbol}: {e}")

        # Sleep for a specified interval before checking again
        await asyncio.sleep(300)  # Adjust the sleep duration as needed

# Initialize Telegram Bot
telegram_bot = Bot(token=telegram_token)

# Use nest_asyncio to allow running asyncio in Jupyter notebooks
nest_asyncio.apply()

# Create and run the event loop
asyncio.run(main())

