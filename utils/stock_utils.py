import csv
import json
import os


def load_stock_alias():

    alias_path = "data/stock_alias.json"

    if not os.path.exists(alias_path):
        return {}

    with open(
        alias_path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)

def load_stock_blacklist():

    blacklist_path = "data/stock_blacklist.json"

    if not os.path.exists(blacklist_path):
        return []

    with open(
        blacklist_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)

def load_stock_list(csv_path="data/full_stock_list.csv"):

    stock_list = []

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            stock_info = {
                "stock_id": str(row["stock_id"]),
                "stock_name": row["stock_name"],
                "market": row["market"]
            }

            stock_list.append(stock_info)

    return stock_list


def is_taiwan_stock_news(news):

    title = news["title"] if news.get("title") else ""
    category = news["category"] if news.get("category") else ""
    summary = news["summary"] if news.get("summary") else ""
    content = news["content"] if news.get("content") else ""

    text = f"{title} {category} {summary} {content}"

    taiwan_stock_keywords = [
        "台股",
        "焦點股",
        "台股盤前",
        "台股盤後",
        "營收",
        "法說",
        "EPS",
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
        "Q1",
        "Q2",
        "Q3",
        "Q4"
    ]

    for keyword in taiwan_stock_keywords:
        if keyword in text:
            return True

    return False


def apply_stock_alias(text):

    aliases = load_stock_alias()

    for alias, real_name in aliases.items():

        if alias in text:
            text += f" {real_name}"

    return text


def calculate_stock_match_score(stock_name, title, summary, content):

    score = 0

    if not stock_name:
        return score

    # 股票名稱太短，容易誤判
    if len(stock_name) < 2:
        return score
    
    blacklist = load_stock_blacklist()

    if stock_name in blacklist:
        return 0

    # 1. 標題命中：最重要
    if stock_name in title:
        score += 10

    # 2. 摘要命中：中等重要
    if stock_name in summary:
        score += 5

    # 3. 內文前 150 字命中：仍有參考價值
    content_head = content[:150]

    if stock_name in content_head:
        score += 3

    # 4. 全文命中：最低權重
    full_text = f"{title} {summary} {content}"
    appear_count = full_text.count(stock_name)

    if appear_count >= 2:
        score += 2
    elif appear_count == 1:
        score += 1

    return score


def find_related_stocks(title, summary, content, stock_list):

    scored_stocks = []

    for stock in stock_list:

        stock_id = stock["stock_id"]
        stock_name = stock["stock_name"]

        score = calculate_stock_match_score(
            stock_name,
            title,
            summary,
            content
        )

        if score <= 0:
            continue

        scored_stock = {
            "stock_id": stock_id,
            "stock_name": stock_name,
            "market": stock["market"],
            "match_score": score
        }

        scored_stocks.append(scored_stock)

    scored_stocks.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    # 只保留分數夠高的股票
    filtered_stocks = []

    for stock in scored_stocks:

        if stock["match_score"] >= 10:
            filtered_stocks.append(stock)

    # 最多保留 5 檔
    return filtered_stocks[:5]


def match_stocks_for_news(news, stock_list):

    if not is_taiwan_stock_news(news):
        return []

    title = news["title"] if news.get("title") else ""
    summary = news["summary"] if news.get("summary") else ""
    content = news["content"] if news.get("content") else ""

    title = apply_stock_alias(title)
    summary = apply_stock_alias(summary)
    content = apply_stock_alias(content)

    matched_stocks = find_related_stocks(
        title,
        summary,
        content,
        stock_list
    )

    return matched_stocks