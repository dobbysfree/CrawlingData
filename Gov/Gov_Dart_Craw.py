import os
import shutil
import sys
import zipfile
import time
import re
import json
import pandas as pd

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup


class Automation:
    driver = None

    def __init__(self, chrome_options=None):
        if not os.path.isfile("chromedriver.exe"):
            print("chromedriver.exe가 존재하지 않습니다. 최신 릴리즈를 최초 1회 다운로드합니다.", file=sys.stderr)

            chromedriver_latest_release = requests.get(
                "https://chromedriver.storage.googleapis.com/LATEST_RELEASE").text.strip()

            r = requests.get("https://chromedriver.storage.googleapis.com/"
                             + chromedriver_latest_release + "/chromedriver_win32.zip", stream=True)

            with open("chromedriver_win32.zip", "wb") as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)

            with zipfile.ZipFile("chromedriver_win32.zip") as zip:
                zip.extract("chromedriver.exe")

            os.remove("chromedriver_win32.zip")

        # option = webdriver.ChromeOptions()
        # option.add_argument("--user-data-dir=Foo/Bar")
        # a = Automation(option)

        self.driver = webdriver.Chrome(chrome_options=chrome_options)

    def __del__(self):
        self.driver.close()

    def click_css_selector(self, css_selector, wait=10):
        if wait != 0:
            WebDriverWait(self.driver, wait).until(
                expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
        self.driver.find_element_by_css_selector(css_selector).click()

    def find_css_selector(self, css_selector, wait=10):
        if wait != 0:
            WebDriverWait(self.driver, wait).until(
                expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
        return self.driver.find_element_by_css_selector(css_selector)

    def send_keys_css_selector(self, css_selector, keys, wait=10):
        WebDriverWait(self.driver, wait).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
        x = self.driver.find_element_by_css_selector(css_selector)
        x.clear()
        x.click()
        x.send_keys(Keys.TAB)
        x.send_keys(keys)

    def click_xpath(self, xpath, wait=10):
        if wait != 0:
            WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.XPATH, xpath)))
        self.driver.find_element_by_xpath(xpath).click()

    def find_xpath(self, xpath, wait=10):
        if wait != 0:
            WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.XPATH, xpath)))
        return self.driver.find_element_by_xpath(xpath)

    def send_keys_xpath(self, xpath, keys, wait=10):
        WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.XPATH, xpath)))
        x = self.driver.find_element_by_xpath(xpath)
        x.clear()
        x.click()
        x.send_keys(Keys.TAB)
        x.send_keys(keys)
        time.sleep(0.1)

    def is_alert(self):
        try:
            WebDriverWait(self.driver, 1).until(expected_conditions.alert_is_present(), "")
            alert = self.driver.switch_to.alert
            text = alert.text
            alert.accept()
            return True, text

        except TimeoutException:
            return False, ""

    @staticmethod
    def read_txt(filename, columns=1, sep=None):
        with open(filename, "r") as f:
            for l in f:
                if sep is not None:
                    if l.strip() == "":
                        yield [None] * columns
                    else:
                        yield l.strip().split(sep)
                else:
                    if l.strip() == "":
                        yield None
                    else:
                        yield l.strip()

    @staticmethod
    def format_time(format_string="%Y-%m-%d %H:%M:%S"):
        return time.strftime(format_string)


class dart_automation(Automation):

    def start_get(self, addr, page_no):
        addr += page_no

        session = requests.Session()
        req = session.get(addr)
        html = req.text
        soup = BeautifulSoup(html, "html.parser")

        tot_json_string = json.loads(soup.text)

        err_code = tot_json_string.get('err_code')  # 에러코드
        page_no = str(tot_json_string.get('page_no'))  # 현재 페이지 넘버
        total_page = tot_json_string.get('total_page')  # 전체 페이지 수

        match = re.search('(?<=\"list\":).+', soup.text)
        startIndex = match.start()
        endIndex = match.end()
        result = soup.text[startIndex:endIndex - 1]      # 필요한 정보 부분만 가져오기
        result = json.loads(result)

        if err_code == '000':
            # print("정상")
            if page_no == "1":
                return result, page_no, total_page  # 리스트, 현재 페이지 넘버, 전체 페이지 수
            else:
                return result
        elif err_code == '010':
            print("등록되지 않은 키입니다", file=sys.stderr)
        elif err_code == '011':
            print("사용할 수 없는 키입니다", file=sys.stderr)
        elif err_code == '020':
            print("요청 제한을 초과하였습니다", file=sys.stderr)
        elif err_code == '100':
            print("필드의 부적절한 값입니다", file=sys.stderr)
        elif err_code == '900':
            print("정의되지 않은 오류가 발생하였습니다", file=sys.stderr)
        return ""


def main(addr):
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    page = "1"

    info = dart_automation(option)
    dart_data, page_no, tot_page = info.start_get(addr, page)
    page_no = int(page_no)

    while page_no < tot_page:        # 전체 페이지 수 동안 데이터 가져오도록 호출
        page_no += 1
        temp = info.start_get(addr, str(page_no))
        dart_data.extend(temp)
        time.sleep(1)

    try:
        # 평일 공휴일 등 전날 데이터 없을 시 예외처리
        if dart_data is None or dart_data == 0:
            return ""
    except:
        df1 = pd.DataFrame(dart_data)

        t1 = df1[["crp_nm", "crp_cd", "rcp_dt", "crp_cls", "rpt_nm", "rcp_no"]]
        # crp_nm : 공시대상회사의 종목명(상장사) 또는 법인명(기타법인)
        # crp_cd : 공시대상회사의 종목코드(6자리) 또는 고유번호(8자리)
        # rcp_dt : 공시 접수일자
        # crp_cls : 법인구분(유가Y,코스닥K,코넥스N,기타E)
        # rpt_nm : 공시구분+보고서명+기타정보
        # rcp_no : 보고서 접수 번호

        # 법인구분
        return t1.to_json(orient="values", force_ascii=False)       # json 형식으로 변환


if __name__ == "__main__":
    from datetime import datetime, timedelta

    t = ['월', '화', '수', '목', '금', '토', '일']
    n = time.localtime().tm_wday

    today = datetime.now().strftime("%Y%m%d")

    if t[n] == "월":      # 현재 날짜 월요일인 경우, 금요일 데이터 가져옴
        search_date = (datetime.strptime(today, "%Y%m%d") - timedelta(days=3)).strftime("%Y%m%d")
    else:
        search_date = datetime.fromtimestamp(time.time() - 60 * 60 * 24).strftime("%Y%m%d")

    auth = "e1f50cd341bc6203806fb932918ca19685800e09"
    target_address = "http://dart.fss.or.kr/api/search.json?auth=" + auth + "&start_dt=" + search_date + "&end_dt=" + search_date + "&page_set=100&page_no="

    dart_info_table = main(target_address)

    if dart_info_table is None:     # 전날 데이터 없을 시 예외처리
        print("tb_dart_daily?" + "")
    else:       # 전날 데이터 존재할 때
        print("tb_dart_daily?" + dart_info_table)
