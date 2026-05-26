from utils.stock_price_fetcher import StockPriceFetcher

fetcher = StockPriceFetcher()

result = fetcher.get_stock_price("2330")

print(result)