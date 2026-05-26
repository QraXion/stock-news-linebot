class SentimentAnalyzer:

    def __init__(self):

        print("情緒分析器初始化成功")

    def analyze(self, text):

        positive_keywords = [
            "大漲",
            "創新高",
            "成長",
            "利多",
            "看好",
            "飆升",
            "漲停"
        ]

        negative_keywords = [
            "重挫",
            "衰退",
            "虧損",
            "下跌",
            "利空",
            "崩跌"
        ]

        positive_score = 0
        negative_score = 0

        for keyword in positive_keywords:

            if keyword in text:
                positive_score += 1

        for keyword in negative_keywords:

            if keyword in text:
                negative_score += 1

        if positive_score > negative_score:

            sentiment = "positive"

        elif negative_score > positive_score:

            sentiment = "negative"

        else:

            sentiment = "neutral"

        if sentiment == "positive":
            sentiment_score = 1
        elif sentiment == "negative":
            sentiment_score = -1
        else:
            sentiment_score = 0

        result = {
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "positive_score": positive_score,
            "negative_score": negative_score
        }

        return result