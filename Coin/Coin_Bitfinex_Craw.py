import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

def main(addr):
    arr = []
    temp = []
    html = requests.get(addr).text
    soup = BeautifulSoup(html, 'html.parser').text
    bitfinex_data = json.loads(soup)        # json decoding
    grp_code = "00003"  # 코인 그룹코드 : 00003
    site_code = "05"  # bitfinex 사이트 코드 : 05
    today = datetime.now().strftime("%Y%m%d")  # 현재 날짜

    for data in bitfinex_data:       # [[코인명, 그룹코드, 웹 사이트 코드, 현재 날짜, 지난 가격, 저가, 고가, volume], ...]
        arr.append(data.get('pair'))
        arr.append(grp_code)
        arr.append(site_code)
        arr.append(today)
        arr.append(data.get('last_price'))
        arr.append(data.get('low'))
        arr.append(data.get('high'))
        arr.append(data.get('volume'))
        temp.append(arr)
        arr = []
    bfx_data = pd.DataFrame(temp)

    bfx_data = bfx_data.to_json(orient="values", force_ascii=False)     # bitfinex 코인 데이터 json 형식으로 변환
    print("tb_coin_daily?" + bfx_data)

if __name__ == "__main__" :
    target_address = "https://api.bitfinex.com/v1/tickers"
    main(target_address)