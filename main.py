import json
import os
from datetime import datetime
from crawler.cnyes_crawler import CnyesCrawler
from crawler.stock_list_crawler import StockListCrawler
from utils.stock_utils import load_stock_list, match_stocks_for_news
from models.sentiment_analyzer import SentimentAnalyzer
from models.event_classifier import EventClassifier
from recommender.stock_recommender import StockRecommender
from utils.stock_price_fetcher import StockPriceFetcher
from utils.technical_analyzer import TechnicalAnalyzer


def main():

    # 1. 抓取完整股票清單
    stock_crawler = StockListCrawler()
    full_stock_list = stock_crawler.fetch_all_stock_list()

    print(f"成功抓取 {len(full_stock_list)} 檔上市 + 上櫃股票")

    stock_crawler.save_stock_list_csv(full_stock_list)

    # 2. 載入股票清單
    stock_list = load_stock_list("data/full_stock_list.csv")

    print(f"股票清單載入成功，共 {len(stock_list)} 檔股票")

    # 3. 初始化模組
    sentiment_analyzer = SentimentAnalyzer()
    event_classifier = EventClassifier()
    price_fetcher = StockPriceFetcher()
    technical_analyzer = TechnicalAnalyzer()
    stock_recommender = StockRecommender()

    # 4. 抓取新聞
    crawler = CnyesCrawler()

    news_list = crawler.fetch_multiple_pages(
        pages=3,
        limit=30,
        days=1,
        mode="latest_trading_day"
    )

    print(f"共抓到 {len(news_list)} 篇新聞")

    # 5. 股票辨識 + 情緒分析 + 事件分類 + 股價分析 + 推薦分數
    print("\n開始進行股票辨識...\n")

    stock_sentiment_results = []

    for news in news_list:

        matched_stocks = match_stocks_for_news(
            news,
            stock_list
        )

        if len(matched_stocks) == 0:
            print(f"新聞：{news['title']}")
            print("無匹配股票，略過分析")
            print("-" * 50)
            continue

        sentiment_result = sentiment_analyzer.analyze(
            news.get("title", "")
        )

        event_result = event_classifier.classify(
            news.get("title", ""),
            news.get("content", "")
        )

        enriched_stocks = []

        for stock in matched_stocks:
            stock_id = stock.get("stock_id")
            stock_name = stock.get("stock_name")

            print(f"正在取得股價與技術指標：{stock_id} {stock_name}")

            price_info = price_fetcher.get_stock_price(stock_id)
            technical_info = technical_analyzer.analyze(stock_id)

            enriched_stock = {
                "stock_id": stock_id,
                "stock_name": stock_name,
                "title": news.get("title", ""),
                "content": news.get("content", ""),
                "price_info": price_info,
                "technical_info": technical_info,
                "sentiment": sentiment_result,
                "event_type": event_result["event_type"],
                "event_tags": event_result["event_tags"]
            }

            recommend_result = stock_recommender.calculate_stock_score(
                enriched_stock
            )

            enriched_stock["recommend_score"] = recommend_result[
                "recommend_score"
            ]

            enriched_stock["recommend_reasons"] = recommend_result[
                "recommend_reasons"
            ]

            enriched_stock["sentiment_score"] = recommend_result[
                "sentiment_score"
            ]

            enriched_stock["technical_score"] = recommend_result[
                "technical_score"
            ]

            enriched_stock["event_score"] = recommend_result[
                "event_score"
            ]
            
            enriched_stock["risk_score"] = recommend_result[
                "risk_score"
            ]

            enriched_stock["recommend_level"] = recommend_result[
                "recommend_level"
            ]

            enriched_stocks.append(enriched_stock)

        news["matched_stocks"] = enriched_stocks
        news["sentiment"] = sentiment_result
        news["event_type"] = event_result["event_type"]
        news["event_tags"] = event_result["event_tags"]

        stock_sentiment_results.append(news)

        print(f"新聞：{news['title']}")
        print(f"事件類型：{news['event_type']}")
        print(f"事件標籤：{news['event_tags']}")
        print(f"情緒分析：{sentiment_result}")
        print(f"匹配股票：{enriched_stocks}")
        print("-" * 50)

    # 6. 儲存原始新聞
    os.makedirs("data", exist_ok=True)

    with open(
        "data/news_raw.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            news_list,
            f,
            ensure_ascii=False,
            indent=4
        )

    print("新聞已儲存到 data/news_raw.json")

    # 7. 儲存個股新聞分析結果
    with open(
        "data/stock_sentiment_results.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            stock_sentiment_results,
            f,
            ensure_ascii=False,
            indent=4
        )

    print("個股情緒結果已儲存到 data/stock_sentiment_results.json")

    # 8. 建立股票摘要
    stock_summary = stock_recommender.summarize_stock_sentiment(
        stock_sentiment_results
    )

    # 9. 股票推薦排序
    ranked_stocks = stock_recommender.rank_stocks(
        stock_summary
    )

    ranked_stocks = [
        stock
        for stock in ranked_stocks
        if stock["recommend_score"] >= 4 and stock["recommend_level"] != "觀察"
    ]
    
    print(f"有效推薦股票數量：{len(ranked_stocks)}")

    analysis_date = datetime.now().strftime("%Y-%m-%d")

    for stock in ranked_stocks:
        stock["analysis_date"] = analysis_date

    if len(ranked_stocks) > 0:
        with open(
            "data/recommendation_results.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                ranked_stocks,
                f,
                ensure_ascii=False,
                indent=4
            )

        print("推薦結果已儲存到 data/recommendation_results.json")

    else:
        if os.path.exists("data/recommendation_results.json"):
            print("本次沒有符合門檻的股票，保留上一份推薦結果，不覆蓋 recommendation_results.json")
        else:
            with open(
                "data/recommendation_results.json",
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    [],
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            print("本次沒有符合門檻的股票，且沒有舊資料，因此建立空的 recommendation_results.json")
    
    top_message_lines = []

    top_message_lines.append(f"今日 Top 推薦股票（{analysis_date}）")

    if len(ranked_stocks) == 0:
        top_message_lines.append("")
        top_message_lines.append("目前沒有符合推薦門檻的股票")
        top_message_lines.append("")
        top_message_lines.append("可能原因：")
        top_message_lines.append("- 今天是週一早上，週末新聞較少")
        top_message_lines.append("- 推薦分數未達門檻")
        top_message_lines.append("- 新聞情緒偏中性或負面")
        top_message_lines.append("- 技術面條件不足")
        top_message_lines.append("")
        top_message_lines.append("建議：")
        top_message_lines.append("- 改用最近一個交易日新聞重新分析")
        top_message_lines.append("- 或於收盤後再執行即時推薦")

    else:
        for index, stock in enumerate(ranked_stocks[:5], start=1):
            top_message_lines.append(
                f"{index}. "
                f"{stock['stock_name']}（{stock['stock_id']}）"
                f"｜{stock['recommend_score']}分"
                f"｜{stock['recommend_level']}"
            )

    top_message = "\n".join(top_message_lines)

    with open(
        "data/today_top_recommendation.txt",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(top_message)

    print("今日推薦摘要已儲存到 data/today_top_recommendation.txt")

    # 10. 印出 Top 5 推薦股票
    print("\nTop 推薦股票：\n")
    if len(ranked_stocks) == 0:
        print("今日沒有符合推薦門檻的股票")
        print("原因可能是：")
        print("- 推薦分數未達門檻")
        print("- 新聞情緒偏中性或負面")
        print("- 技術面條件不足")
        print("- 出現高風險關鍵字")
        print("- 目前時間較早，新聞與成交量資料可能尚未完整")
        print("建議於收盤後重新執行分析")
        return
    
    for index, stock in enumerate(ranked_stocks[:5], start=1):

        print(
            f"{index}. "
            f"{stock['stock_name']} "
            f"（{stock['stock_id']}）"
            f"｜{stock['recommend_score']}分"
        )

    print("\n詳細分析：\n")

    for stock in ranked_stocks[:5]:

        print(
            f"{stock['stock_id']} "
            f"{stock['stock_name']}"
        )

        print(f"推薦分數：{stock['recommend_score']}")
        print(f"推薦等級：{stock['recommend_level']}")
        print(f"情緒總分：{stock['total_score']}")
        print(f"新聞數量：{stock['news_count']}")

        print("推薦依據：")

        for reason in stock.get("recommend_reasons", []):
            print(f"- {reason}")

        print("相關新聞：")

        for news in stock.get("news_reasons", [])[:3]:
            print(
                f"- [{news.get('sentiment')}] "
                f"{news.get('title')}"
            )

        print("-" * 50)


if __name__ == "__main__":
    main()