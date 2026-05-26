import yfinance as yf


class StockPriceFetcher:
    def get_stock_price(self, stock_id: str):

        for suffix in [".TW", ".TWO"]:
            ticker = f"{stock_id}{suffix}"

            df = yf.Ticker(ticker).history(period="5d")

            if df.empty or len(df) < 2:
                continue

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            close_price = float(latest["Close"])
            previous_close = float(previous["Close"])
            volume = int(latest["Volume"])

            change_percent = ((close_price - previous_close) / previous_close) * 100

            return {
                "stock_id": stock_id,
                "ticker": ticker,
                "close_price": round(close_price, 2),
                "volume": volume,
                "change_percent": round(change_percent, 2)
            }

        return None