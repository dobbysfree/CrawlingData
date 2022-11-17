import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import sys
import decimal
from datetime import datetime

def main(addr):
    html = requests.get(addr).text
    soup = BeautifulSoup(html, 'html.parser').text

    json_string = json.loads(soup)      # json decoding
    success = json_string.get('success')  # json 데이터 받아오기 성공여부
    grp_code = "00003"  # 코인 그룹코드 : 00003
    site_code = "04"  # bittrex 웹사이트 코드 : 04
    today = datetime.now().strftime("%Y%m%d")
    arr = []
    temp = []

    if success is True:      # 데이터 받아오기 성공
        bittrex_data = json_string.get('result')
        for data in bittrex_data:
            arr.append(data.get('MarketName'))
            arr.append(grp_code)
            arr.append(site_code)
            arr.append(today)
            arr.append(format(data.get("Last"), '.8f'))
            arr.append(format(data.get("Low"), '.8f'))
            arr.append(format(data.get("High"), '.8f'))
            arr.append(str(data.get('Volume')))
            temp.append(arr)
            arr = []

        # [[코인명, 그룹코드, 웹사이트 코드, 현재 날짜, 지난것, 최저, 최고, volume], ...]

        bittrex_data = pd.DataFrame(temp)
        btx_data = bittrex_data.to_json(orient="values", force_ascii=False)

    else:        # 데이터 받아오기 실패
        print("실패", file=sys.stderr)

    print("tb_coin_daily?" + btx_data)

if __name__ == "__main__" :

    target_address = "https://bittrex.com/api/v1.1/public/getmarketsummaries"
    main(target_address)
