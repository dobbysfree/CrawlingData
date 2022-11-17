# -*- coding: utf-8 -*-
import datetime
import time
from datetime import timedelta

import pandas as pd
from dateutil.relativedelta import relativedelta

from pytrends.request import TrendReq

import pyautogui
import pymysql
from apscheduler.schedulers.blocking import BlockingScheduler



## Google Trend API
def get_py_trends(query_date, keywords, hl='en-US', tz=360, gprop='', geo=''):
    pytrends = TrendReq(hl=hl, tz=tz)

    date1, date2 = query_date.split(" ")
    date1 = datetime.datetime.strptime(date1, '%Y-%m-%d')
    date2 = datetime.datetime.strptime(date2, '%Y-%m-%d')
    time_delta = date2 - date1
    query_iter = time_delta.days // 1800 + 1
    start_date = date1
    end_date = date2

    res = None
    for i in range(query_iter):    # query_iter = 1
        end_date = start_date + timedelta(days=1800)
        if i == query_iter - 1:
            end_date = date2

        timeframe = "{}-{}-{} {}-{}-{}".format(start_date.year, start_date.month, start_date.day,
                                               end_date.year, end_date.month, end_date.day)

        print("Downloading... ", keywords, timeframe, geo, gprop)  # DEBUGgoogleamazon
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop=gprop)

        if res is not None:
            res = res.append(pytrends.interest_over_time())
        else:
            res = pytrends.interest_over_time()
        start_date = end_date + timedelta(days=1)
    res = pd.DataFrame(res.iloc[:, :-1])

    return res


def main(query_date, keywords, hl='en-US', tz=360, gprop='', geo=''):
    res = None
    gprop_list = ['', 'images', 'news', 'youtube', 'froogle']   ## 검색영역 (default : '웹검색')
    geo_list = ['', 'US', 'KR']                                 ## 검색지역 (default : '전세계')
    id_list = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010',
               '011', '012', '013', '014', '015', '016', '017', '018', '019', '020',
               '021', '022', '023', '024', '025', '026', '027', '028', '029', '030',
               '031', '032', '033', '034', '035', '036', '037', '038', '039', '040',
               '041', '042', '043', '044', '045', '046', '047', '048', '049', '050',
               '051', '052', '053', '054', '055', '056', '057', '058', '059', '060',
               '061', '062', '063', '064', '065', '066', '067', '068', '069', '070',
               '071', '072', '073', '074', '075', '076', '077', '078', '079', '080',
               '081', '082', '083', '084', '085', '086', '087', '088', '089', '090',
               '091', '092', '093', '094', '095', '096', '097', '098', '099', '100']

    # # DB 연동 및 작업 ###
    conn = pymysql.connect(host='', port=0, user='', passwd='', db='', charset='utf8')
    cur = conn.cursor()
    sql = """insert into tb_google_trend_daily(SEARCH_NAME,SITE_CODE,GRP_CODE,SEARCH_AREA,DATA_CYCLE,CREATE_DT,DATA_DT,CATEGORY,SEARCH_DOMAIN,OPP_VALUE,CHG_PSN_ID,CHG_DTTM)
     values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    for kw in keywords:
        time.sleep(1)
        kw_list = [kw]
        now = time.localtime()
        today = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

        ## IP 변경 프로그램 사용하기 위한 마우스 제어 ##
        if keywords.index(kw) % 20 == 0:
            change_ip()

        gprop_cnt = 0
        while gprop_cnt < len(gprop_list):
            geo_cnt = 0
            while geo_cnt < len(geo_list):
                res = get_py_trends(query_date=query_date, keywords=kw_list, hl=hl, tz=tz, gprop=gprop_list[gprop_cnt], geo=geo_list[geo_cnt])
                if res.empty or len(res) != 52:  # 데이터가 없을 경우 상대수치 null로 저장
                    input_empty_db(query_date, kw, id_list[keywords.index(kw)], cur, sql, geo_list, gprop_list, today, geo_cnt, gprop_cnt)
                else:  ## 데이터가 있을 경우
                    input_exist_db(query_date, kw, id_list[keywords.index(kw)], cur, sql, geo_list, gprop_list, today, geo_cnt, gprop_cnt, res)
                conn.commit()
                geo_cnt += 1
            gprop_cnt += 1

        data_cnt = keywords.index(kw) + 1
        print('[종료]', data_cnt, kw)

    conn.close()


## 데이터 결과값 없을 시
def input_empty_db(query_date, kw, id, cur, sql, geo_list, gprop_list, today, geo_cnt, gprop_cnt):
    date1, date2 = query_date.split(" ")
    date1 = datetime.datetime.strptime(date1, '%Y-%m-%d')
    date2 = datetime.datetime.strptime(date2, '%Y-%m-%d')
    time_delta = date2 - date1

    # # 검색명 / 웹사이트코드 / 그룹코드 / 검색지역 / 데이터주기 / 기준날짜 / *데이터날짜 / 카테고리 / 검색영역 / *상대수치 / 변경자ID / 변경일시
    cur.execute(sql, (
                      id, '01', '00005', geo_list.index(geo_list[geo_cnt]) + 1, '1',
                      query_date, str(date2 - datetime.timedelta(days=6))[0:10], '1',
                      gprop_list.index(gprop_list[gprop_cnt]) + 1, None, 'qraft', today))


## 데이터 결과값 있을 시
def input_exist_db(query_date, kw, id, cur, sql, geo_list, gprop_list, today, geo_cnt, gprop_cnt, res):

    # # 검색명 / 웹사이트코드 / 그룹코드 / 검색지역 / 데이터주기 / 기준날짜 / 데이터날짜 / 카테고리 / 검색영역 / 상대수치 / 변경자ID / 변경일시
    cur.execute(sql, (
                      id, '01', '00005', geo_list.index(geo_list[geo_cnt]) + 1, '1',
                      query_date, str(res[kw].index[51])[0:10], '1',
                      gprop_list.index(gprop_list[gprop_cnt]) + 1, str(res[kw][51]), 'qraft', today))


## ip 변경 매크로
def change_ip():
    pyautogui.moveTo(175, 1064)
    pyautogui.click()
    pyautogui.moveTo(144, 56)
    pyautogui.click()
    time.sleep(4)
    pyautogui.moveTo(121, 1010)
    pyautogui.click()
    time.sleep(1)


def prev_main():
    now = time.localtime()
    with open("NASDAQ100_ENG.txt", "r", encoding="utf-16") as f:
        kw_list = f.readlines()
    last_dt = datetime.date(now.tm_year, now.tm_mon, now.tm_mday - 1)
    start_dt = last_dt - relativedelta(years=1) + timedelta(days=1)
    query_str = str(start_dt) + ' ' + str(last_dt - datetime.timedelta(days=1))
    ## 검색어 / 검색지역 / 검색기간 / 카테고리 / 검색영역
    main(query_date=query_str, keywords=kw_list, hl='en-US', tz=360, gprop='', geo='')


## 스케줄링 작업 (매일 00:05 에 실행)
sched = BlockingScheduler()
@sched.scheduled_job('cron', day_of_week='mon-sun', hour=0, minute=5)
def scheduled_job():
    print("스케줄링시작")
    prev_main()


if __name__ == "__main__":
    sched.start()
    print("<<<<<<<<<<<<<<< Program 종료 >>>>>>>>>>>>>>>")