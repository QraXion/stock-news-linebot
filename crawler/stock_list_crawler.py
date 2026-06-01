import csv
import os
import requests


class StockListCrawler:

    def fetch_twse_stock_list(self):

        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        stock_list = []

        for item in data:

            stock_id = item.get("Code")
            stock_name = item.get("Name")

            if not stock_id or not stock_name:
                continue

            stock_info = {
                "stock_id": str(stock_id),
                "stock_name": stock_name,
                "market": "上市"
            }

            stock_list.append(stock_info)

        return stock_list

    def fetch_tpex_stock_list(self):

        url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        stock_list = []

        for item in data:

            stock_id = item.get("SecuritiesCompanyCode")
            stock_name = item.get("CompanyName")

            if not stock_id or not stock_name:
                continue

            stock_info = {
                "stock_id": str(stock_id),
                "stock_name": stock_name,
                "market": "上櫃"
            }

            stock_list.append(stock_info)

        return stock_list

    def load_existing_stock_list_csv(self, file_path="data/full_stock_list.csv"):

        if not os.path.exists(file_path):
            print("找不到舊股票清單 CSV，無法使用備援股票清單")
            return []

        stock_list = []

        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:
                stock_list.append({
                    "stock_id": str(row["stock_id"]),
                    "stock_name": row["stock_name"],
                    "market": row["market"]
                })

        print(f"已使用舊股票清單備援，共 {len(stock_list)} 檔股票")

        return stock_list

    def fetch_all_stock_list(self):

        full_stock_list = []

        try:
            twse_stock_list = self.fetch_twse_stock_list()
            full_stock_list.extend(twse_stock_list)
            print(f"上市股票清單抓取成功，共 {len(twse_stock_list)} 檔")

        except Exception as e:
            print(f"上市股票清單抓取失敗：{e}")

        try:
            tpex_stock_list = self.fetch_tpex_stock_list()
            full_stock_list.extend(tpex_stock_list)
            print(f"上櫃股票清單抓取成功，共 {len(tpex_stock_list)} 檔")

        except Exception as e:
            print(f"上櫃股票清單抓取失敗：{e}")

        if len(full_stock_list) == 0:
            print("本次上市與上櫃股票清單皆抓取失敗，改用舊 CSV 備援")
            return self.load_existing_stock_list_csv()

        if len(full_stock_list) < 1500:
            old_stock_list = self.load_existing_stock_list_csv()

            if len(old_stock_list) > len(full_stock_list):
                print("本次股票清單數量偏少，改用舊 CSV 備援，避免股票匹配率下降")
                return old_stock_list

        return full_stock_list

    def save_stock_list_csv(
        self,
        stock_list,
        file_path="data/full_stock_list.csv"
    ):

        if len(stock_list) == 0:
            print("股票清單為空，不覆蓋 data/full_stock_list.csv")
            return

        os.makedirs("data", exist_ok=True)

        with open(
            file_path,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "stock_id",
                    "stock_name",
                    "market"
                ]
            )

            writer.writeheader()

            for stock in stock_list:
                writer.writerow(stock)

        print(f"股票清單已儲存：{file_path}")