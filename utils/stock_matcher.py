import json
import os
import re


class StockMatcher:

    def __init__(self, stock_list):
        self.stock_list = stock_list
        self.aliases = self.load_stock_alias()
        self.blacklist = self.load_stock_blacklist()
        self.stock_id_map = self.build_stock_id_map()

    def load_stock_alias(self):
        alias_path = "data/stock_alias.json"

        if not os.path.exists(alias_path):
            return {}

        with open(alias_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_stock_blacklist(self):
        blacklist_path = "data/stock_blacklist.json"

        if not os.path.exists(blacklist_path):
            return []

        with open(blacklist_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def build_stock_id_map(self):
        stock_id_map = {}

        for stock in self.stock_list:
            stock_id = str(stock.get("stock_id", "")).strip()

            if stock_id:
                stock_id_map[stock_id] = stock

        return stock_id_map

    def get_news_text(self, news):
        title = news.get("title", "") or ""
        category = news.get("category", "") or ""
        summary = news.get("summary", "") or ""
        content = news.get("content", "") or ""

        return {
            "title": title,
            "category": category,
            "summary": summary,
            "content": content,
            "full_text": f"{title} {category} {summary} {content}"
        }

    def is_taiwan_stock_news(self, news):
        text_data = self.get_news_text(news)
        full_text = text_data["full_text"]

        taiwan_stock_keywords = [
            "台股",
            "個股",
            "焦點股",
            "台股盤前",
            "台股盤後",
            "股東會",
            "法說",
            "營收",
            "EPS",
            "股息",
            "股利",
            "殖利率",
            "漲停",
            "跌停",
            "上市",
            "上櫃",
            "興櫃",
            "股價",
            "每股",
            "獲利",
            "毛利率",
            "收購",
            "增資",
            "配息",
            "除息",
            "董事會",
            "AI",
            "伺服器",
            "半導體",
            "-TW",
            "-TWO",
            "Q1",
            "Q2",
            "Q3",
            "Q4"
        ]

        for keyword in taiwan_stock_keywords:
            if keyword in full_text:
                return True

        return False

    def apply_stock_alias(self, text):
        for alias, real_name in self.aliases.items():
            if alias in text:
                text += f" {real_name}"

        return text

    def extract_stock_ids_from_text(self, text):
        stock_ids = set()

        patterns = [
            r"\((\d{4})-TW\)",
            r"\((\d{4})-TWO\)",
            r"（(\d{4})-TW）",
            r"（(\d{4})-TWO）",
            r"(\d{4})-TW",
            r"(\d{4})-TWO"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)

            for stock_id in matches:
                stock_ids.add(stock_id)

        return stock_ids

    def match_by_stock_id(self, text):
        stock_ids = self.extract_stock_ids_from_text(text)

        matched_stocks = []

        for stock_id in stock_ids:
            if stock_id not in self.stock_id_map:
                continue

            stock = self.stock_id_map[stock_id]

            matched_stocks.append({
                "stock_id": stock["stock_id"],
                "stock_name": stock["stock_name"],
                "market": stock["market"],
                "match_score": 100,
                "match_type": "stock_id"
            })

        matched_stocks.sort(
            key=lambda stock: stock["stock_id"]
        )

        return matched_stocks

    def is_blacklisted(self, stock_name):
        return stock_name in self.blacklist

    def is_short_name_false_positive(self, stock_name, full_text):
        if len(stock_name) >= 3:
            return False

        for stock in self.stock_list:
            other_name = stock["stock_name"]

            if other_name == stock_name:
                continue

            if len(other_name) > len(stock_name):
                if stock_name in other_name and other_name in full_text:
                    return True

        return False

    def calculate_name_match_score(
        self,
        stock_name,
        title,
        summary,
        content
    ):
        score = 0

        if not stock_name:
            return score

        if len(stock_name) < 2:
            return score

        if self.is_blacklisted(stock_name):
            return 0

        full_text = f"{title} {summary} {content}"
        content_head = content[:300]

        if self.is_short_name_false_positive(stock_name, full_text):
            return 0

        if stock_name in title:
            score += 10

        if stock_name in summary:
            score += 5

        if stock_name in content_head:
            score += 3

        appear_count = full_text.count(stock_name)

        if appear_count >= 2:
            score += 2
        elif appear_count == 1:
            score += 1

        return score

    def match_by_stock_name(self, title, summary, content):
        scored_stocks = []

        for stock in self.stock_list:
            stock_id = stock["stock_id"]
            stock_name = stock["stock_name"]

            score = self.calculate_name_match_score(
                stock_name,
                title,
                summary,
                content
            )

            if score < 10:
                continue

            scored_stocks.append({
                "stock_id": stock_id,
                "stock_name": stock_name,
                "market": stock["market"],
                "match_score": score,
                "match_type": "stock_name"
            })

        scored_stocks.sort(
            key=lambda stock: stock["match_score"],
            reverse=True
        )

        return scored_stocks[:5]

    def remove_duplicate_stocks(self, matched_stocks):
        unique_stocks = {}

        for stock in matched_stocks:
            stock_id = stock["stock_id"]

            if stock_id not in unique_stocks:
                unique_stocks[stock_id] = stock
                continue

            if stock["match_score"] > unique_stocks[stock_id]["match_score"]:
                unique_stocks[stock_id] = stock

        return list(unique_stocks.values())

    def match(self, news):
        if not self.is_taiwan_stock_news(news):
            return []

        text_data = self.get_news_text(news)

        title = self.apply_stock_alias(text_data["title"])
        summary = self.apply_stock_alias(text_data["summary"])
        content = self.apply_stock_alias(text_data["content"])

        full_text = f"{title} {summary} {content}"

        id_matched_stocks = self.match_by_stock_id(full_text)

        if len(id_matched_stocks) > 0:
            return self.remove_duplicate_stocks(id_matched_stocks)[:5]

        name_matched_stocks = self.match_by_stock_name(
            title,
            summary,
            content
        )

        return self.remove_duplicate_stocks(name_matched_stocks)[:5]