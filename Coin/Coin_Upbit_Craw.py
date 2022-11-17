import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime

def main(addr, name_list):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    arr = []
    temp = []
    grp_code = "00003"
    site_code = "03"
    today = datetime.now().strftime("%Y%m%d")
    for name in name_list:
        full_addr = addr % name  # 기본주소에 검색할 코인명 추가
        html = requests.get(full_addr, headers=headers).text  # name_list 목록 모두 지속적으로 requests 하기 위한 헤더 추가
        soup = BeautifulSoup(html, 'html.parser').text[1:-1]
        upbit_data = json.loads(soup)
        arr.append(str(upbit_data.get('code')[11:]))
        arr.append(grp_code)
        arr.append(site_code)
        arr.append(today)
        arr.append(str(upbit_data.get('tradePrice')))
        arr.append(str(upbit_data.get('lowPrice')))
        arr.append(str(upbit_data.get('highPrice')))
        arr.append(str(upbit_data.get('candleAccTradeVolume')))
        temp.append(arr)
        arr = []

    # [[마켓별 코인명, 그룹코드, 웹사이트 코드, 현재날짜, 거래가격, 최저, 최고, volume], ...]
    upbit_data = pd.DataFrame(temp)
    upb_data = upbit_data.to_json(orient="values", force_ascii=False)       # json 형식으로 변환
    print("tb_coin_daily?" + upb_data)

if __name__ == "__main__":
    target_address = "https://crix-api-endpoint.upbit.com/v1/crix/candles/days?code=CRIX.UPBIT.%s"
    # name_list : 마켓별 코인명
    name_list = ["KRW-BTC", "KRW-DASH", "KRW-ETH", "KRW-NEO", "KRW-BCC", "KRW-MTL", "KRW-LTC", "KRW-STRAT", "KRW-XRP", "KRW-ETC", "KRW-OMG", "KRW-SNT", "KRW-WAVES", "KRW-PIVX", "KRW-XEM", "KRW-ZEC", "KRW-XMR", "KRW-QTUM", "KRW-LSK", "KRW-STEEM", "KRW-XLM", "KRW-ARDR", "KRW-KMD",
                 "KRW-ARK", "KRW-STORJ", "KRW-GRS", "KRW-VTC", "KRW-REP", "KRW-EMC2", "KRW-ADA", "KRW-SBD", "KRW-TIX", "KRW-POWR", "KRW-MER", "KRW-BTG",
                 "BTC-NEO", "BTC-BCC", "BTC-ETH", "BTC-LTC", "BTC-STRAT", "BTC-XRP", "BTC-ETC", "BTC-OMG", "BTC-CVC", "BTC-DGB", "BTC-PAY", "BTC-SC", "BTC-SNT", "BTC-DASH", "BTC-XVG", "BTC-WAVES", "BTC-NMR", "BTC-SYNX", "BTC-PIVX", "BTC-GBYTE", "BTC-XEM", "BTC-FUN", "BTC-ZEC",
                 "BTC-XMR", "BTC-LBC", "BTC-QTUM", "BTC-GNT", "BTC-NXT", "BTC-BAT", "BTC-XEL", "BTC-EDG", "BTC-LSK", "BTC-RDD", "BTC-DCT", "BTC-STEEM", "BTC-GAME", "BTC-FCT", "BTC-PTOY", "BTC-DCR", "BTC-DOGE", "BTC-BNT", "BTC-XLM", "BTC-PART", "BTC-MCO", "BTC-UBQ", "BTC-ARDR",
                  "BTC-KMD", "BTC-ARK", "BTC-ADX", "BTC-SYS", "BTC-ANT", "BTC-MUE", "BTC-XDN", "BTC-STORJ", "BTC-QRL", "BTC-NXS", "BTC-GRS", "BTC-VOX", "BTC-VTC", "BTC-CLOAK", "BTC-SIB", "BTC-REP", "BTC-VIA", "BTC-WINGS", "BTC-CFI", "BTC-1ST", "BTC-UNB", "BTC-NBT", "BTC-SWT",
                 "BTC-MAID", "BTC-SLS", "BTC-AGRS", "BTC-MONA", "BTC-AMP", "BTC-HMQ", "BTC-TX", "BTC-RLC", "BTC-BLOCK", "BTC-DYN", "BTC-GUP", "BTC-MEME", "BTC-OK", "BTC-XZC", "BTC-ADT", "BTC-FTC", "BTC-ION", "BTC-BSD", "BTC-GNO", "BTC-EMC2", "BTC-EXCL", "BTC-SPHR", "BTC-EXP",
                 "BTC-BITB", "BTC-BAY", "BTC-VRC", "BTC-BURST", "BTC-SHIFT", "BTC-BLK", "BTC-ZEN", "BTC-KORE", "BTC-RADS", "BTC-IOP", "BTC-RISE", "BTC-NAV", "BTC-ADA", "BTC-MANA", "BTC-SALT", "BTC-SBD", "BTC-TIX", "BTC-RCN", "BTC-VIB", "BTC-POWR", "BTC-MER", "BTC-BTG", "BTC-ENG",
                 "BTC-UKG", "BTC-DNT", "BTC-IGNIS",
                 "ETH-NEO", "ETH-BCC", "ETH-LTC", "ETH-STRAT", "ETH-XRP", "ETH-ETC", "ETH-OMG", "ETH-CVC", "ETH-DGB", "ETH-PAY", "ETH-SC", "ETH-SNT", "ETH-DASH", "ETH-WAVES", "ETH-NMR", "ETH-XEM", "ETH-FUN", "ETH-ZEC", "ETH-XMR", "ETH-QTUM", "ETH-GNT", "ETH-BAT", "ETH-FCT",
                 "ETH-PTOY", "ETH-BNT", "ETH-XLM", "ETH-MCO", "ETH-ADX", "ETH-ANT", "ETH-STORJ", "ETH-QRL", "ETH-REP", "ETH-WINGS", "ETH-CFI", "ETH-1ST", "ETH-HMQ", "ETH-RLC", "ETH-GUP", "ETH-ADT", "ETH-GNO", "ETH-MANA", "ETH-SALT", "ETH-TIX", "ETH-RCN", "ETH-VIB", "ETH-POWR",
                 "ETH-BTG",
                 "USDT-BTC", "USDT-NEO", "USDT-BCC", "USDT-ETH", "USDT-LTC", "USDT-XRP", "USDT-ETC", "USDT-DASH", "USDT-ZEC", "USDT-XMR", "USDT-OMG", "USDT-XVG", "USDT-ADA", "USDT-BTG", "USDT-NXT"]
    main(target_address, name_list)
