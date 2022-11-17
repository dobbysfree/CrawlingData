# -*- coding: utf-8 -*-
import pandas as pd
import pymysql
import time
import datetime
import numpy
import pyautogui
import sys

from pytrends.request import TrendReq
from datetime import timedelta
from dateutil.relativedelta import relativedelta

"""
Variables
    [kw_list] : list of keywords to get data for



Parameters

    [query_date]: dates to search for. Form : 'YYYY-MM-DD YYYY-MM-DD'
    [keywords]: to put kw_list

    [hl]: A string specifying the ISO language code (ex.: “en-US” or “fr”). Default is “en-US”. 
            Korea is "ko-KR"
            Note that this is only influencing the data returned by related topics.

    [geo]: A two letter country abbreviation, default to “all” for global queries.

    [tz]: timezone offset, default US CST '360'

    [gprop]: What Google property to filter to, default to web searches

    [base_path]: directory to save the csv file,
        warning! path delimiter should be "/"

    for further information, refer pytrends official document 
        https://github.com/GeneralMills/pytrends#trending_searches


"""

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

    for i in range(query_iter):

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
    res         = None
    grp_code    = "00005"                                       ## 그룹코드
    site_code   = "01"                                          ## 웹사이트코드
    now         = time.localtime()                              ## 오늘날짜
    chg_id      = "qraft"                                       ## 변경자ID
    gprop_list = ['']
    #gprop_list  = ['', 'images', 'news', 'youtube', 'froogle']  ## 검색영역 (default : '웹검색')
    geo_list    = ['', 'US', 'KR']                              ## 검색지역 (default : '전세계')

    # # DB 연동 및 작업 ###
    conn = pymysql.connect(host='', port=0, user='', passwd='', db='', charset='utf8')
    cur = conn.cursor()
    sql = """insert into tb_google_trend_daily(SEARCH_NAME,SITE_CODE,GRP_CODE,SEARCH_AREA,DATA_CYCLE,DATA_DT,CATEGORY,SEARCH_DOMAIN,OPP_VALUE,CHG_PSN_ID,CHG_DTTM)
     values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    program_cnt = 0

    for kw in keywords:
        time.sleep(3)
        kw_list = [kw]
        today = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

        ## res[kw][i] - 상대수치
        ## res[kw].index[i] - 날짜
        gprop_cnt = 0
        geo_cnt = 0

        #
        ## PORT 변경 프로그램 사용하기 위한 마우스 제어 ##
        print("~~~~~~~~PORT 변경시간~~~~~~~")
        pyautogui.moveTo(659, 1067)
        pyautogui.click()
        pyautogui.moveTo(145, 50)
        pyautogui.click()
        time.sleep(4)
        pyautogui.moveTo(173, 1009)
        pyautogui.click()
        time.sleep(2)

        while gprop_cnt < len(gprop_list):
            while geo_cnt < len(geo_list):
                res = get_py_trends(query_date=query_date, keywords=kw_list, hl=hl, tz=tz, gprop=gprop_list[gprop_cnt], geo=geo_list[geo_cnt])
                i = 0


                if res.empty:  # 데이터가 없을 경우 (상대수치 null로 저장)
                    #time.sleep(1)
                    date1, date2 = query_date.split(" ")
                    date1 = datetime.datetime.strptime(date1, '%Y-%m-%d')
                    date2 = datetime.datetime.strptime(date2, '%Y-%m-%d')
                    time_delta = date2 - date1
                    while i < time_delta.days + 1:
                        # # 검색명 / 웹사이트코드 / 그룹코드 / 검색지역 / 데이터주기 / 데이터날짜 / 카테고리 / 검색영역 / 상대수치 / 변경자ID / 변경일시
                        cur.execute(sql, (kw, site_code, grp_code, geo_list.index(geo_list[geo_cnt]) + 1, '2',
                                          str(date1 + datetime.timedelta(days=i))[0:10], '1',
                                          gprop_list.index(gprop_list[gprop_cnt]) + 1, None, chg_id, today))
                        i = i + 1
                        program_cnt += 1

                else:  ## 데이터가 있을 경우
                    #time.sleep(2)
                    while i < len(res):
                        # # 검색명 / 웹사이트코드 / 그룹코드 / 검색지역 / 데이터주기 / 데이터날짜 / 카테고리 / 검색영역 / 상대수치 / 변경자ID / 변경일시
                        cur.execute(sql, (
                        kw, site_code, grp_code, geo_list.index(geo_list[geo_cnt]) + 1, '2', str(res[kw].index[i])[0:10], '1',
                        gprop_list.index(gprop_list[gprop_cnt]) + 1, str(res[kw][i]), chg_id, today))
                        i = i + 1
                        program_cnt += 1
                conn.commit()

                geo_cnt += 1
            gprop_cnt += 1
            print(kw + '==> 종료 ')
            print(program_cnt)

    conn.close()


if __name__ == "__main__":

    p_cnt = 0
    with open("NASDAQ100_ENG.txt", "r", encoding="utf-16") as f:
        kw_list = f.readlines()

    #kw_list = ['Apple Inc', 'Google']


    ## 시작날짜 마지막날짜
    ## query_str = '시작날짜' + ' ' + '마지막날짜'


    y_cnt = 2006

    while y_cnt < 2007 :
        m_cnt = 9
        while m_cnt <= 12:
            ## 검색어 / 검색지역 / 검색기간 / 카테고리 / 검색영역
            start_dt = datetime.date(y_cnt, m_cnt, 1)
            last_dt = start_dt + relativedelta(months=1)
            query_str = str(start_dt) + ' ' + str(last_dt - datetime.timedelta(days=1))
            main(query_date=query_str, keywords=kw_list, hl='en-US', tz=360, gprop='', geo='')
            m_cnt += 1
        y_cnt += 1

    print("<<<<<<< Program 종료 >>>>>>>")



