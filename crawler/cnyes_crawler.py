import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class CnyesCrawler:
    def __init__(self):
        self.base_url = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"

        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }

    def get_timestamp_range(self, days=1):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        return int(start_time.timestamp()), int(end_time.timestamp())
    
    def get_latest_trading_day_range(self):

        today = datetime.now()
        weekday = today.weekday()

        # Monday = 0, Sunday = 6
        if weekday == 0:
            target_day = today - timedelta(days=3)

        elif weekday == 6:
            target_day = today - timedelta(days=2)

        elif weekday == 5:
            target_day = today - timedelta(days=1)

        else:
            target_day = today - timedelta(days=1)

        start_time = target_day.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        end_time = target_day.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0
        )

        print(f"本次新聞分析日期：{start_time.strftime('%Y-%m-%d')}")

        return int(start_time.timestamp()), int(end_time.timestamp())

    def fetch_news_list(self, page=1, limit=30, days=1, mode="recent"):

        if mode == "latest_trading_day":
            start_at, end_at = self.get_latest_trading_day_range()
        else:
            start_at, end_at = self.get_timestamp_range(days)

        params = {
            "page": page,
            "limit": limit,
            "isCategoryHeadline": 1,
            "startAt": start_at,
            "endAt": end_at
        }

        response = requests.get(
            self.base_url,
            headers=self.headers,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            print(f"抓取失敗，狀態碼：{response.status_code}")
            return []

        data = response.json()

        try:
            news_items = data["items"]["data"]

        except KeyError:
            print("資料格式異常")
            return []

        results = []

        for item in news_items:

            news = {
                "news_id": item.get("newsId"),
                "title": item.get("title"),
                "summary": item.get("summary"),
                "category": item.get("categoryName"),
                "published_at": item.get("publishAt"),
                "url": f"https://news.cnyes.com/news/id/{item.get('newsId')}"
            }

            results.append(news)

        return results

    def fetch_news_content(self, url):

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"內文抓取失敗：{url}")
                return ""

            soup = BeautifulSoup(response.text, "lxml")

            content_list = []

            # 方法 1：優先抓 article 裡面的 p
            article = soup.find("article")

            if article is not None:
                paragraphs = article.find_all("p")

                for p in paragraphs:
                    text = p.get_text(strip=True)

                    if text:
                        content_list.append(text)

            # 方法 2：如果 article 抓不到，改抓所有 p
            if len(content_list) == 0:
                paragraphs = soup.find_all("p")

                for p in paragraphs:
                    text = p.get_text(strip=True)

                    if text:
                        content_list.append(text)

            content = "\n".join(content_list)

            # 清掉明顯不是新聞正文的尾巴
            content = content.replace("下一篇", "").strip()

            return content

        except Exception as e:
            print(f"抓取內文錯誤：{url}")
            print(e)

            return ""

    def fetch_multiple_pages(self, pages=2, limit=30, days=1, mode="recent"):

        all_news = []

        for page in range(1, pages + 1):

            print(f"正在抓取第 {page} 頁新聞...")

            news_list = self.fetch_news_list(
                page=page,
                limit=limit,
                days=days,
                mode=mode
            )

            for news in news_list:

                print(f"正在抓取內文：{news['title']}")

                content = self.fetch_news_content(news["url"])

                news["content"] = content

                time.sleep(1)

            all_news.extend(news_list)

            time.sleep(1)

        return all_news