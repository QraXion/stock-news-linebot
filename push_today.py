import os
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage

load_dotenv()
# =========================
# LINE BOT 設定
# =========================

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(
    LINE_CHANNEL_ACCESS_TOKEN
)

# =========================
# 讀取今日推薦
# =========================

try:
    with open(
        "data/today_top_recommendation.txt",
        "r",
        encoding="utf-8"
    ) as f:

        message = f.read()

except FileNotFoundError:

    message = "目前尚未產生今日推薦結果"

# =========================
# Push Message
# =========================

line_bot_api.push_message(
    USER_ID,
    TextSendMessage(
        text=message
    )
)

print("今日推薦已成功推播")