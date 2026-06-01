import csv
import json
import os
import re


def load_stock_alias():
    alias_path = "data/stock_alias.json"

    if not os.path.exists(alias_path):
        return {}

    with open(alias_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_stock_blacklist():
    blacklist_path = "data/stock_blacklist.json"

    if not os.path.exists(blacklist_path):
        return []

    with open(blacklist_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_stock_list(csv_path="data/full_stock_list.csv"):
    stock_list = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stock_list.append({
                "stock_id": str(row["stock_id"]),
                "stock_name": row["stock_name"],
                "market": row["market"]
            })

    return stock_list


def is_taiwan_stock_news(news):
    title = news["title"] if news.get("title") else ""
    category = news["category"] if news.get("category") else ""
    summary = news["summary"] if news.get("summary") else ""
    content = news["content"] if news.get("content") else ""

    text = f"{title} {category} {summary} {content}"

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
        if keyword in text:
            return True

    return False


def apply_stock_alias(text):
    aliases = load_stock_alias()

    for alias, real_name in aliases.items():
        if alias in text:
            text += f" {real_name}"

    return text


def extract_stock_ids_from_text(text):
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


def is_short_name_false_positive(stock_name, text, stock_list):
    if len(stock_name) >= 3:
        return False

    for other_stock in stock_list:
        other_name = other_stock["stock_name"]

        if other_name == stock_name:
            continue

        if len(other_name) > len(stock_name):
            if stock_name in other_name and other_name in text:
                return True

    return False


def calculate_stock_match_score(stock_name, title, summary, content, stock_list):
    score = 0

    if not stock_name:
        return score

    if len(stock_name) < 2:
        return score

    blacklist = load_stock_blacklist()

    if stock_name in blacklist:
        return 0

    full_text = f"{title} {summary} {content}"
    content_head = content[:300]

    if is_short_name_false_positive(stock_name, full_text, stock_list):
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


def find_stocks_by_stock_id(text, stock_list):
    stock_ids = extract_stock_ids_from_text(text)

    matched_stocks = []

    for stock in stock_list:
        if stock["stock_id"] in stock_ids:
            matched_stocks.append({
                "stock_id": stock["stock_id"],
                "stock_name": stock["stock_name"],
                "market": stock["market"],
                "match_score": 100
            })

    return matched_stocks


def find_related_stocks(title, summary, content, stock_list):
    full_text = f"{title} {summary} {content}"

    id_matched_stocks = find_stocks_by_stock_id(full_text, stock_list)

    if len(id_matched_stocks) > 0:
        return id_matched_stocks[:5]

    scored_stocks = []

    for stock in stock_list:
        stock_id = stock["stock_id"]
        stock_name = stock["stock_name"]

        score = calculate_stock_match_score(
            stock_name,
            title,
            summary,
            content,
            stock_list
        )

        if score <= 0:
            continue

        scored_stocks.append({
            "stock_id": stock_id,
            "stock_name": stock_name,
            "market": stock["market"],
            "match_score": score
        })

    scored_stocks.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    filtered_stocks = []

    for stock in scored_stocks:
        if stock["match_score"] >= 10:
            filtered_stocks.append(stock)

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