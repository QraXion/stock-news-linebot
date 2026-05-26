import yfinance as yf


class TechnicalAnalyzer:

    def calculate_rsi(self, close_prices, period=14):
        """
        計算 RSI 指標
        period 預設為 14 日
        """

        delta = close_prices.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        latest_rsi = rsi.iloc[-1]

        if latest_rsi != latest_rsi:
            return None

        return round(float(latest_rsi), 2)

    def analyze(self, stock_id: str):

        for suffix in [".TW", ".TWO"]:
            ticker = f"{stock_id}{suffix}"

            df = yf.Ticker(ticker).history(period="3mo")

            if df.empty or len(df) < 20:
                continue

            close_prices = df["Close"]
            volumes = df["Volume"]

            latest_close = close_prices.iloc[-1]
            latest_volume = volumes.iloc[-1]

            ma5 = close_prices.tail(5).mean()
            ma20 = close_prices.tail(20).mean()

            avg_volume_5 = volumes.tail(5).mean()

            if avg_volume_5 == 0:
                volume_ratio = 0
            else:
                volume_ratio = latest_volume / avg_volume_5

            rsi = self.calculate_rsi(close_prices)

            return {
                "stock_id": stock_id,
                "ticker": ticker,
                "latest_close": round(float(latest_close), 2),
                "ma5": round(float(ma5), 2),
                "ma20": round(float(ma20), 2),
                "latest_volume": int(latest_volume),
                "avg_volume_5": int(avg_volume_5),
                "volume_ratio": round(float(volume_ratio), 2),
                "rsi": rsi
            }

        return None