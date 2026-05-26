class StockRecommender:

    def __init__(self):
        print("股票推薦器初始化成功")

        self.scoring_config = {
            "sentiment_positive": 2,
            "sentiment_negative": -2,

            "above_ma5": 1,
            "above_ma20": 1,
            "high_volume": 1,
            "rsi_oversold": 2,
            "rsi_overheated": -1,

            "event_industry": 2,
            "event_financial": 1,
            "event_chip": 1,

            "risk_keyword": -3
        }

        self.risk_keywords = [
            "全額交割",
            "淨值跌破",
            "下市",
            "處置",
            "虧損",
            "連續虧損",
            "重大訊息",
            "財務困難"
        ]

    def calculate_stock_score(self, stock_data):

        sentiment_score = 0
        technical_score = 0
        event_score = 0
        risk_score = 0

        reasons = []

        title = stock_data.get("title", "")
        content = stock_data.get("content", "")

        sentiment = stock_data.get("sentiment", {})
        sentiment_type = sentiment.get("sentiment")

        if sentiment_type == "positive":
            sentiment_score += self.scoring_config["sentiment_positive"]
            reasons.append("新聞情緒正面")

        elif sentiment_type == "negative":
            sentiment_score += self.scoring_config["sentiment_negative"]
            reasons.append("新聞情緒負面")

        elif sentiment_type == "neutral":
            sentiment_score -= 1
            reasons.append("新聞情緒中性")

        technical_info = stock_data.get("technical_info")

        if technical_info:

            latest_close = technical_info.get("latest_close", 0)
            ma5 = technical_info.get("ma5", 0)
            ma20 = technical_info.get("ma20", 0)
            volume_ratio = technical_info.get("volume_ratio", 0)
            rsi = technical_info.get("rsi")

            if latest_close > ma5:
                technical_score += self.scoring_config["above_ma5"]
                reasons.append("股價站上 MA5")

            if latest_close > ma20:
                technical_score += self.scoring_config["above_ma20"]
                reasons.append("股價站上 MA20")

            if volume_ratio > 1.2:
                technical_score += self.scoring_config["high_volume"]
                reasons.append("成交量放大")

            if rsi is not None:
                if rsi < 30:
                    technical_score += self.scoring_config["rsi_oversold"]
                    reasons.append("RSI 低檔反彈機會")

                elif rsi > 70:
                    technical_score += self.scoring_config["rsi_overheated"]
                    reasons.append("RSI 過熱")

        event_type = stock_data.get("event_type")

        for keyword in self.risk_keywords:
            if keyword in title or keyword in content:
                risk_score += self.scoring_config["risk_keyword"]
                reasons.append(f"高風險關鍵字：{keyword}")
                break

        if event_type == "產業技術":
            event_score += self.scoring_config["event_industry"]
            reasons.append("產業技術題材")

        elif event_type == "財報營收":
            event_score += self.scoring_config["event_financial"]
            reasons.append("財報題材")

        elif event_type == "股價籌碼":
            event_score += self.scoring_config["event_chip"]
            reasons.append("籌碼題材")

        recommend_score = (
            sentiment_score
            + technical_score
            + event_score
            + risk_score
        )

        if recommend_score >= 6:
            recommend_level = "強烈推薦"

        elif recommend_score >= 4:
            recommend_level = "值得關注"

        else:
            recommend_level = "觀察"

        return {
            "recommend_score": recommend_score,
            "recommend_level": recommend_level,

            "sentiment_score": sentiment_score,
            "technical_score": technical_score,
            "event_score": event_score,
            "risk_score": risk_score,

            "recommend_reasons": reasons
        }

    def summarize_stock_sentiment(self, stock_sentiment_results):

        stock_summary = {}

        for news in stock_sentiment_results:
            matched_stocks = news.get("matched_stocks", [])

            for stock in matched_stocks:
                stock_id = stock.get("stock_id")
                stock_name = stock.get("stock_name")

                if stock_id not in stock_summary:
                    stock_summary[stock_id] = {
                        "stock_id": stock_id,
                        "stock_name": stock_name,
                        "total_score": 0,
                        "news_count": 0,
                        "recommend_score": 0,
                        "recommend_level": "觀察",
                        "sentiment_score": 0,
                        "technical_score": 0,
                        "event_score": 0,
                        "risk_score": 0,
                        "recommend_reasons": [],
                        "technical_info": stock.get("technical_info", {}),
                        "news_reasons": []
                    }

                sentiment = stock.get("sentiment", {})
                sentiment_type = sentiment.get("sentiment")

                if sentiment_type == "positive":
                    stock_summary[stock_id]["total_score"] += 1

                elif sentiment_type == "negative":
                    stock_summary[stock_id]["total_score"] -= 1

                stock_summary[stock_id]["news_count"] += 1
                stock_summary[stock_id]["recommend_score"] += stock.get(
                    "recommend_score", 0
                )
                stock_summary[stock_id]["recommend_level"] = stock.get(
                    "recommend_level", "觀察"
                )
                stock_summary[stock_id]["sentiment_score"] += stock.get(
                    "sentiment_score", 0
                )
                stock_summary[stock_id]["technical_score"] += stock.get(
                    "technical_score", 0
                )
                stock_summary[stock_id]["event_score"] += stock.get(
                    "event_score", 0
                )
                stock_summary[stock_id]["risk_score"] += stock.get(
                    "risk_score", 0
                )

                for reason in stock.get("recommend_reasons", []):
                    if reason not in stock_summary[stock_id]["recommend_reasons"]:
                        stock_summary[stock_id]["recommend_reasons"].append(
                            reason
                        )

                stock_summary[stock_id]["news_reasons"].append({
                    "title": news.get("title"),
                    "sentiment": sentiment_type,
                    "event_type": news.get("event_type"),
                    "event_tags": news.get("event_tags", []),
                    "recommend_score": stock.get("recommend_score", 0),
                    "recommend_reasons": stock.get("recommend_reasons", [])
                })

        result = list(stock_summary.values())
        
        for stock in result:

            score = stock.get("recommend_score", 0)
            news_count = stock.get("news_count", 0)

            if news_count >= 2:
                stock["recommend_score"] += 1

                if "多篇新聞共同提及" not in stock["recommend_reasons"]:
                    stock["recommend_reasons"].append("多篇新聞共同提及")

            if score >= 6:
                stock["recommend_level"] = "強烈推薦"

            elif score >= 4:
                stock["recommend_level"] = "值得關注"

            else:
                stock["recommend_level"] = "觀察"

        return self.rank_stocks(result)

    def rank_stocks(self, stock_summary):

        ranked_stocks = sorted(
            stock_summary,
            key=lambda x: (
                x["recommend_score"],
                x["total_score"],
                x["news_count"]
            ),
            reverse=True
        )

        return ranked_stocks