import csv
import os
import requests


class StockListCrawler:

    def fetch_twse_stock_list(self):

        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

        response = requests.get(url)
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

        response = requests.get(url)
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

    def fetch_all_stock_list(self):

        full_stock_list = []

        try:
            twse_stock_list = self.fetch_twse_stock_list()
            full_stock_list.extend(twse_stock_list)

        except Exception as e:
            print(f"上市股票清單抓取失敗：{e}")

        try:
            tpex_stock_list = self.fetch_tpex_stock_list()
            full_stock_list.extend(tpex_stock_list)

        except Exception as e:
            print(f"上櫃股票清單抓取失敗：{e}")

        return full_stock_list

    def save_stock_list_csv(
        self,
        stock_list,
        file_path="data/full_stock_list.csv"
    ):

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