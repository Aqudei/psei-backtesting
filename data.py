import os
import requests
from argparse import ArgumentParser
import json
from datetime import datetime
import csv


def download_symbol_data(symbol, company_id, scty_symbol_id):
    data = {
        "cmpy_id": company_id,
        "security_id": scty_symbol_id,
        "startDate": "06-30-1500",
        "endDate": f"{datetime.now():%m-%d-%Y}"
    }

    data_as_text = json.dumps(data)

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Accept-Language": "en-US,en;q=0.9",
        "Host": "edge.pse.com.ph",
        "Origin": "http://edge.pse.com.ph",
        "Content-Type": "application/json",
        "Referer": "http://edge.pse.com.ph/companyPage/stockData.do?cmpy_id=86",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }

    response = requests.get(url='http://edge.pse.com.ph/psei/form.do')

    url = "http://edge.pse.com.ph/common/DisclosureCht.ax"
    response = requests.post(
        url=url, headers=headers, data=data_as_text, cookies=response.cookies)

    if not response.status_code == 200:
        raise Exception("Failed to downlaod symbol data")

    output_path = os.path.abspath(os.path.join("./data", f"{symbol}.json"))
    with open(output_path, 'wt') as fp:
        fp.write(json.dumps(response.json()['chartData'], indent=1))

    print(
        f"Symbols for {symbol} was successfully written to {output_path}")

def data_to_csv():
    for file in os.listdir("./data"):
        if not file.endswith(".json"):
            continue

        symbol, ext = os.path.splitext(file)

        with open(f"./data/{file}", 'rt') as fp:
            jsn = json.loads(fp.read())

        with open(f"./data/{symbol}.csv", 'wt', newline='') as fp_o:
            writer = csv.writer(fp_o)
            writer.writerow(['OPEN', 'VALUE', 'CLOSE',
                             'CHART_DATE', 'HIGH', 'LOW'])
            for item in jsn:
                writer.writerow([
                    item['OPEN'],
                    item['VALUE'],
                    item['CLOSE'],
                    datetime.strptime(item['CHART_DATE'].replace("00:00:00","").strip(), "%b %d, %Y").date(),
                    item['HIGH'],
                    item['LOW']
                ])

        print(f"{file} was converted to csv")

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pull-all', action='store_true')
    parser.add_argument('--download-historical')
    parser.add_argument('--data-to-csv', action='store_true')

    args = parser.parse_args()

    if args.data_to_csv:
        data_to_csv()

    if args.pull_all:
        data = {
            'start': 0,
            'limit': 1000
        }

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Host": "www.pse.com.ph",
            "Origin": "https://www.pse.com.ph",
            "Referer": "https://www.pse.com.ph/stockMarket/listedCompanyDirectory.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        }
        response = requests.get("https://www.pse.com.ph")
        response = requests.post(cookies=response.cookies, headers=headers,
                                 url='https://www.pse.com.ph/stockMarket/companyInfoSecurityProfile.html?method=getListedRecords&common=yes&ajax=true', data=data)

        if not response.status_code == 200:
            exit(1)

        symbols = {r['securitySymbol']: r for r in response.json()['records']}
        with open("./symbols.json", 'wt') as fp:
            fp.write(json.dumps(symbols, indent=1))

    if args.download_historical:
        symbol = args.download_historical

        with open('./symbols.json', 'rt') as fp:
            symbols = json.loads(fp.read())

        if symbol == 'ALL':
            for stock_name, stock in symbols.items():
                try:
                    download_symbol_data(stock_name,
                                         stock['companyId'], stock['securitySymbolId'])
                except:
                    print(f"Failed to download symbol data of {stock_name}")


            data_to_csv()
            exit()

        try:
            stock = symbols[symbol]
            download_symbol_data(
                symbol, stock['companyId'], stock['securitySymbolId'])

            print(
                f"Symbols for {symbol} was successfully written to {output_path}")
        except:
            print(f"Failed to download symbol data of {symbol}")
