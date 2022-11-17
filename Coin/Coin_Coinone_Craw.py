import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
from datetime import datetime

def main(addr):
    arr = []
    temp = []
    grp_code = "00003"
    site_code = "02"
    today = datetime.now().strftime("%Y%m%d")

    html = requests.get(addr).text
    soup = BeautifulSoup(html, 'html.parser').text
    coinone_data = json.loads(soup)      # json decoding

    coinone_data.pop('errorCode')
    result = coinone_data.pop('result')     # 데이터 받아오기 결과
    if result == "success":                  # 위 결과가 성공일 시
        coinone_data = str(coinone_data)[1:-1]
        parser = re.compile('\'\w+\': {.*?}', re.DOTALL)
        matched = parser.findall(str(coinone_data))          # 각 코인별 정보 추출
        for item in matched:
            clean_string = item.split('{')[1][:-1].split(',')
            for string in clean_string:                     # 코인별 정보 저장
                each_data = string.split(': ')[1].replace("\'", "")
                arr.append(each_data)
            arr.append(grp_code)
            arr.append(site_code)
            arr.append(today)
            temp.append(arr)
            arr = []
        coinone_data = pd.DataFrame(temp)
        coinone_data.columns = ["volume", "last", "yesterday_last", "yesterday_low", "high", "currency", "low", "yesterday_first", "yesterday_volume", "yesterday_high", "first", "grp_code", "site_code", "search_date"]
        # coinone_data = coinone_data[["currency", "volume", "last", "yesterday_last", "yesterday_low", "high", "low", "yesterday_first", "yesterday_volume", "yesterday_high", "first"]]
        coinone_data = coinone_data[["currency", "grp_code", "site_code", "search_date", "last", "low", "high", "volume"]]
        cone_data = coinone_data.to_json(orient="values", force_ascii=False)         # json 형식으로 변환
        print("tb_coin_daily?" + cone_data)

    else:
        print("Coinone site " + result)

if __name__ == "__main__" :

    target_address = "https://api.coinone.co.kr/ticker/?format=json&currency=all"
    main(target_address)
