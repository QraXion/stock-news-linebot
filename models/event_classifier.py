class EventClassifier:

    def __init__(self):

        self.category_keywords = {
            "財報營收": [
                "營收", "獲利", "財報", "EPS", "每股純益",
                "毛利率", "淨利", "年增", "月增", "季增",
                "稅前盈餘", "每股稅前", "雙位數成長"
            ],
            "產業技術": [
                "人工智慧", "AI PC", "主權AI", "生成式AI",
                "AI需求", "AI散熱", "AI伺服器",
                "半導體", "晶片", "製程", "晶圓", "封測",
                "伺服器", "資料中心", "超算", "GPU", "ASIC",
                "CoWoS", "電動車", "記憶體", "液冷"
            ],
            "股價籌碼": [
                "焦點股", "漲停", "跌停", "跳空", "創新高",
                "重挫", "大漲", "大跌", "外資", "投信",
                "法人", "買超", "賣超", "成交量", "三大法人",
                "爆出天量", "亮燈","ETF", "成分股", "換血", "入列", "剔除"
            ],
            "併購投資": [
                "收購", "併購", "入股", "增資", "投資",
                "股權", "合併", "策略聯盟", "出售"
            ],
            "總經政策": [
                "關稅", "政策", "Fed", "央行", "匯率",
                "台幣", "美中", "川習會", "通膨", "利率",
                "國務卿"
            ]
        }

        self.tag_keywords = {
            "AI": [
                "人工智慧", "AI PC", "主權AI", "生成式AI",
                "AI需求", "AI散熱", "AI伺服器", "AI晶片",
                "AI應用", "AI獲利", "AI藍圖"
            ],
            "半導體": [
                "半導體", "晶片", "製程", "晶圓", "封測",
                "ASIC", "VCORE", "CoWoS"
            ],
            "金融": [
                "金控", "銀行", "保險", "壽險", "證券",
                "公股", "臺企銀", "華南金", "兆豐金",
                "第一金", "合庫金", "富邦金", "國泰金"
            ],
            "航運": [
                "航運", "運價", "貨櫃", "出貨量"
            ],
            "財報": [
                "Q1", "Q2", "Q3", "Q4", "EPS", "獲利",
                "每股純益", "營收", "年增", "月增", "季增",
                "稅前盈餘", "每股稅前"
            ],
            "股價異動": [
                "漲停", "跌停", "跳空", "創新高", "重挫",
                "大漲", "大跌", "亮燈"
            ],
            "併購": [
                "收購", "併購", "合併", "股權", "出售", "增資"
            ],
            "總經": [
                "Fed", "央行", "匯率", "台幣", "美中",
                "關稅", "國務卿"
            ]
        }

    def classify(self, title: str, content: str = ""):

        text = f"{title} {content}"
        text_upper = text.upper()

        category_scores = {}

        for category, keywords in self.category_keywords.items():
            score = 0

            for keyword in keywords:

                if self._keyword_match(keyword, text, text_upper):
                    score += 1

            category_scores[category] = score

        best_category = max(category_scores, key=category_scores.get)

        if category_scores[best_category] == 0:
            best_category = "其他"

        tags = []

        for tag, keywords in self.tag_keywords.items():

            for keyword in keywords:

                if self._keyword_match(keyword, text, text_upper):
                    tags.append(tag)
                    break

        return {
            "event_type": best_category,
            "event_tags": tags
        }

    def _keyword_match(self, keyword: str, text: str, text_upper: str):

        # 避免單獨 AI 造成大量誤判
        if keyword == "AI":
            return False

        # 英文關鍵字統一用大寫比對
        english_keywords = [
            "AI PC", "GPU", "ASIC", "VCORE", "COWOS",
            "EPS", "Q1", "Q2", "Q3", "Q4", "FED"
        ]

        if keyword.upper() in english_keywords:
            return keyword.upper() in text_upper

        return keyword in text