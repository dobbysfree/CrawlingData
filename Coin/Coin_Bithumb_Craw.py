import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
from datetime import datetime

def main(addr):
    arr = []
    temp = []
    grp_code = "00003"  # 코인 그룹코드 : 00003
    site_code = "01"  # bithumb 사이트 코드 : 01
    today = datetime.now().strftime("%Y%m%d")
    html = requests.get(addr).text
    soup = BeautifulSoup(html, 'html.parser').text
    bithumb_data = json.loads(soup)     # json decoding
    bithumb_data = bithumb_data.get('data')
    parser = re.compile('\'\w+\': {.*?}', re.DOTALL)
    matched = parser.findall(str(bithumb_data))

    # [[코인명, 그룹코드, 웹 사이트 코드, 현재날짜, 지난가격, 최저, 최고, volume], ...]
    for item in matched:
        name = item.split(':')[0].replace("\'", "")
        arr.append(name)
        clean_string = item.split('{')[1][:-1].split(',')
        for string in clean_string:
            each_data = string.split(': ')[1].replace("\'", "")
            arr.append(each_data)
        arr.append(grp_code)
        arr.append(site_code)
        arr.append(today)
        temp.append(arr)
        arr = []

    bithumb_data = pd.DataFrame(temp)

    # bithumb_data 컬럼 설정
    bithumb_data.columns = ["name", "opening_price", "closing_price", "min_price", "max_price", "average_price",
                            "units_traded", "volume_1day", "volume_7day", "buy_price", "sell_price", "grp_code",
                            "site_code", "search_date"]

    bithumb_data = bithumb_data[["name", "grp_code", "site_code", "search_date", "closing_price", "min_price", "max_price", "volume_1day"]]

    btx_data = bithumb_data.to_json(orient="values", force_ascii=False)

    print("tb_coin_daily?" + btx_data)

if __name__ == "__main__" :

    target_address = "https://api.bithumb.com/public/ticker/all"
    main(target_address)