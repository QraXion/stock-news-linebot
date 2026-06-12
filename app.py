from datetime import datetime
import os
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify
import json
import subprocess
import sys

from flask_cors import CORS
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction
)

from utils.stock_price_fetcher import StockPriceFetcher
from utils.technical_analyzer import TechnicalAnalyzer


load_dotenv()

app = Flask(__name__)
CORS(app)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

price_fetcher = StockPriceFetcher()
technical_analyzer = TechnicalAnalyzer()


def run_main_py_with_logs():

    print("開始執行 main.py", flush=True)

    process = subprocess.Popen(
        [sys.executable, "-u", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    for line in process.stdout:
        print(line, end="", flush=True)

    return_code = process.wait()

    if return_code != 0:
        raise Exception(f"main.py 執行失敗，return code: {return_code}")

    print("main.py 執行完成", flush=True)


def get_main_menu():

    return QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(
                    label="今日推薦",
                    text="今日推薦"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label="即時推薦",
                    text="即時推薦"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label="分數區間",
                    text="分數區間"
                )
            )
        ]
    )


def translate_sentiment(sentiment):

    mapping = {
        "positive": "正面",
        "neutral": "中性",
        "negative": "負面"
    }

    return mapping.get(sentiment, sentiment)


def calculate_technical_result(stock_id):

    price_info = price_fetcher.get_stock_price(stock_id)
    technical_info = technical_analyzer.analyze(stock_id)

    if price_info is None or technical_info is None:
        return None

    technical_score = 0
    technical_reasons = []

    latest_close = technical_info["latest_close"]
    ma5 = technical_info["ma5"]
    ma20 = technical_info["ma20"]
    volume_ratio = technical_info["volume_ratio"]
    rsi = technical_info["rsi"]

    if latest_close > ma5:
        technical_score += 1
        technical_reasons.append("股價站上 MA5，短線偏強")
    else:
        technical_reasons.append("股價未站上 MA5，短線偏弱")

    if latest_close > ma20:
        technical_score += 1
        technical_reasons.append("股價站上 MA20，中期趨勢偏多")
    else:
        technical_reasons.append("股價未站上 MA20，中期趨勢保守")

    if volume_ratio >= 1.5:
        technical_score += 1
        technical_reasons.append("成交量明顯放大，市場關注度提高")
    else:
        technical_reasons.append("成交量尚未明顯放大")

    if rsi is not None:
        if rsi > 70:
            technical_score -= 1
            technical_reasons.append("RSI 偏高，短線有過熱風險")
        elif rsi < 30:
            technical_score += 2
            technical_reasons.append("RSI 偏低，可能有低檔反彈機會")
        else:
            technical_score += 1
            technical_reasons.append("RSI 位於中性區間")
    else:
        technical_reasons.append("RSI 資料不足，暫無法判斷")

    if technical_score >= 4:
        technical_level = "強勢"
    elif technical_score == 3:
        technical_level = "偏強"
    elif technical_score == 2:
        technical_level = "平穩"
    elif technical_score == 1:
        technical_level = "偏弱"
    else:
        technical_level = "風險"

    return {
        "stock_id": stock_id,
        "technical_score": technical_score,
        "technical_level": technical_level,
        "technical_reasons": technical_reasons,
        "price_info": price_info,
        "technical_info": technical_info
    }


def build_technical_message(stock_id):

    result = calculate_technical_result(stock_id)

    if result is None:
        return f"找不到股票代號 {stock_id} 的股價或技術資料"

    price_info = result["price_info"]
    technical_info = result["technical_info"]

    lines = []

    lines.append(f"個股技術分析：{stock_id}")
    lines.append("")
    lines.append(f"技術推薦分數：{result['technical_score']}")
    lines.append(f"技術推薦等級：{result['technical_level']}")
    lines.append("")
    lines.append(f"收盤價：{price_info['close_price']}")
    lines.append(f"漲跌幅：{price_info['change_percent']}%")
    lines.append(f"成交量：{price_info['volume']}")
    lines.append("")
    lines.append(f"MA5：{technical_info['ma5']}")
    lines.append(f"MA20：{technical_info['ma20']}")
    lines.append(f"量能倍率：{technical_info['volume_ratio']}")
    lines.append(f"RSI：{technical_info['rsi']}")
    lines.append("")
    lines.append("技術面判斷：")

    for reason in result["technical_reasons"]:
        lines.append(f"- {reason}")

    return "\n".join(lines)


def build_score_range_message():

    return (
        "分數區間說明\n\n"
        "新聞推薦分數：\n"
        "8分以上：強烈推薦\n"
        "5~7.9分：值得關注\n"
        "5分以下：觀察\n\n"
        "技術推薦分數：\n"
        "4分以上：強勢\n"
        "3分：偏強\n"
        "2分：平穩\n"
        "1分：偏弱\n"
        "0分以下：風險"
    )


def read_today_recommendation_message():

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(
            "data/today_top_recommendation.txt",
            "r",
            encoding="utf-8"
        ) as f:
            message = f.read()

    except FileNotFoundError:
        return (
            "目前尚未產生今日推薦結果。\n"
            "請先使用「即時推薦」功能。"
        )

    if today not in message:
        return (
            "目前尚未產生今日推薦結果。\n"
            "系統偵測到目前資料不是今日最新分析。\n\n"
            "請先使用「即時推薦」功能。"
        )

    return message


def load_recommendation_results():

    try:
        with open(
            "data/recommendation_results.json",
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except FileNotFoundError:
        return []


def find_recommendation_stock(stock_id):

    stocks = load_recommendation_results()

    for stock in stocks:
        if str(stock.get("stock_id")) == str(stock_id):
            return stock

    return None


@app.route("/")
def home():
    return "Stock News Line Bot Running!"


@app.route("/today")
def today_recommendation():

    message = read_today_recommendation_message()

    return message.replace("\n", "<br>")


@app.route("/stock/<stock_id>")
def stock_detail(stock_id):

    found_stock = find_recommendation_stock(stock_id)

    if found_stock is None:
        return (
            f"本次推薦結果中沒有找到 {stock_id} 的相關新聞。<br><br>"
            "以下提供技術面分析：<br><br>"
            + build_technical_message(stock_id).replace("\n", "<br>")
        )

    lines = [
        f"{found_stock.get('stock_name')}（{found_stock.get('stock_id')}）",
        f"推薦分數：{found_stock.get('recommend_score')}",
        f"推薦等級：{found_stock.get('recommend_level')}",
        f"新聞數量：{found_stock.get('news_count')}",
        "",
        "推薦依據："
    ]

    for reason in found_stock.get("recommend_reasons", []):
        lines.append(f"- {reason}")

    lines.append("")
    lines.append("相關新聞：")

    for news in found_stock.get("news_reasons", [])[:3]:
        lines.append(
            f"- [{translate_sentiment(news.get('sentiment'))}] {news.get('title')}"
        )

    lines.append("")
    lines.append("技術面補充：")
    lines.append(build_technical_message(stock_id))

    return "<br>".join(lines)


@app.route("/api/recommendations/today", methods=["GET"])
def api_today_recommendations():

    try:
        recommendations = load_recommendation_results()

        return jsonify({
            "status": "success",
            "data": recommendations
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": []
        }), 500


@app.route("/api/stocks/<stock_id>", methods=["GET"])
def api_stock_detail(stock_id):

    try:
        found_stock = find_recommendation_stock(stock_id)
        technical_result = calculate_technical_result(stock_id)

        if found_stock is not None:
            data = {
                "stock_id": found_stock.get("stock_id"),
                "stock_name": found_stock.get("stock_name"),
                "data_source": (
                    "recommendation_with_technical"
                    if technical_result is not None
                    else "recommendation_only"
                ),
                "recommend_score": found_stock.get("recommend_score"),
                "recommend_level": found_stock.get("recommend_level"),
                "news_count": found_stock.get("news_count"),
                "sentiment_score": found_stock.get("sentiment_score"),
                "technical_score": found_stock.get("technical_score"),
                "event_score": found_stock.get("event_score"),
                "risk_score": found_stock.get("risk_score"),
                "recommend_reasons": found_stock.get("recommend_reasons", []),
                "news_reasons": found_stock.get("news_reasons", []),
                "analysis_date": found_stock.get("analysis_date"),
                "technical_analysis": technical_result
            }

            return jsonify({
                "status": "success",
                "data": data
            })

        if technical_result is not None:
            data = {
                "stock_id": stock_id,
                "stock_name": stock_id,
                "data_source": "technical_only",
                "recommend_score": technical_result["technical_score"],
                "recommend_level": technical_result["technical_level"],
                "news_count": 0,
                "sentiment_score": 0,
                "technical_score": technical_result["technical_score"],
                "event_score": 0,
                "risk_score": 0,
                "recommend_reasons": technical_result["technical_reasons"],
                "news_reasons": [],
                "analysis_date": None,
                "technical_analysis": technical_result
            }

            return jsonify({
                "status": "success",
                "data": data
            })

        return jsonify({
            "status": "error",
            "message": f"找不到股票代號 {stock_id} 的推薦資料、股價或技術資料",
            "data": None
        }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": None
        }), 500


@app.route("/api/analysis/run", methods=["POST"])
def api_run_analysis():

    print("收到 Web /api/analysis/run 請求，開始重新執行 main.py", flush=True)

    try:
        run_main_py_with_logs()
        recommendations = load_recommendation_results()

        return jsonify({
            "status": "success",
            "message": "即時分析完成",
            "data": recommendations
        })

    except Exception as e:
        print("Web 即時分析失敗", flush=True)
        print(e, flush=True)

        return jsonify({
            "status": "error",
            "message": str(e),
            "data": []
        }), 500


@app.route("/rerun")
def rerun_analysis():

    print("收到 /rerun 請求，開始重新執行 main.py", flush=True)

    try:
        run_main_py_with_logs()

        return "分析已重新執行完成，請回到 /today 查看最新推薦"

    except Exception as e:
        print("main.py 執行失敗", flush=True)
        print(e, flush=True)

        return "重新執行分析失敗，請檢查 Render Logs 錯誤訊息"


@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    user_message = event.message.text.strip()

    print(f"使用者 ID：{event.source.user_id}", flush=True)

    if user_message == "今日推薦":

        message = read_today_recommendation_message()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=get_main_menu()
            )
        )

    elif user_message == "即時推薦":

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=
                "即時推薦已開始執行。\n"
                "系統正在抓取新聞、進行情緒分析與技術分析，請稍候約 1~5 分鐘。"
            )
        )

        try:
            run_main_py_with_logs()

            with open(
                "data/today_top_recommendation.txt",
                "r",
                encoding="utf-8"
            ) as f:
                latest_message = f.read()

            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(
                    text="即時推薦分析完成\n\n" + latest_message,
                    quick_reply=get_main_menu()
                )
            )

        except Exception as e:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(
                    text="即時推薦分析失敗\n" + str(e)
                )
            )

    elif user_message == "分數區間":

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=build_score_range_message(),
                quick_reply=get_main_menu()
            )
        )

    elif user_message.isdigit() and len(user_message) == 4:

        stock_id = user_message.strip()
        found_stock = find_recommendation_stock(stock_id)

        if found_stock is not None:
            lines = [
                f"{found_stock.get('stock_name')}（{found_stock.get('stock_id')}）",
                f"推薦分數：{found_stock.get('recommend_score')}",
                f"推薦等級：{found_stock.get('recommend_level')}",
                f"新聞數量：{found_stock.get('news_count')}",
                "",
                "推薦依據："
            ]

            for reason in found_stock.get("recommend_reasons", []):
                lines.append(f"- {reason}")

            lines.append("")
            lines.append("相關新聞：")

            for news in found_stock.get("news_reasons", [])[:3]:
                lines.append(
                    f"- [{translate_sentiment(news.get('sentiment'))}] {news.get('title')}"
                )

            lines.append("")
            lines.append("技術面補充：")
            lines.append(build_technical_message(stock_id))

            message = "\n".join(lines)

        else:
            message = (
                f"本次推薦結果中沒有找到 {stock_id} 的相關新聞。\n\n"
                "以下提供技術面分析：\n\n"
                + build_technical_message(stock_id)
            )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=message,
                quick_reply=get_main_menu()
            )
        )

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=
                "系統已啟動完成。\n\n"
                "請選擇功能，或直接輸入股票代號，例如：\n"
                "2330\n\n"
                "可使用功能：\n"
                "今日推薦\n"
                "即時推薦\n"
                "分數區間",
                quick_reply=get_main_menu()
            )
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)