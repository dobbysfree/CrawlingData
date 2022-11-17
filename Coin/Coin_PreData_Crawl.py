import json
import sys
import os
import shutil
import sys
import zipfile
import re
import time
import pandas as pd
import pickle
from datetime import datetime, timedelta
from selenium.webdriver.common.alert import Alert
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


def get_coin_name(bit_addr):
    html = requests.get(bit_addr).text
    soup = BeautifulSoup(html, 'html.parser').text         # html 파싱

    json_string = json.loads(soup)      # json decoding
    success = json_string.get('success')
    arr = []
    if success is True:
        bittrex_data = json_string.get('result')
        for data in bittrex_data:
            market = data.get('MarketCurrency')
            base = data.get('BaseCurrency')
            target_name = str(market).lower() + "-" + str(base).lower()
            arr.append(target_name)
    else:
        print("get target name 실패", file=sys.stderr)
        return None

    # print(str(arr))
    return arr


class crawl_automation(Automation):

    def get_page(self, target_addr, name):
        url = target_addr % name        # 기본 주소에 검색할 코인명 추가
        flag = True
        while flag:
            try:
                self.driver.get(url)
                try:        # 존재하지 않는 코인명, 마켓일 시
                    self.driver.find_element_by_class_name("error404")
                    return None
                except:
                    pass
                try:        # 인베스팅 사이트 팝업 제거
                    self.driver.find_element_by_xpath("//*[@id=\"PromoteSignUpPopUp\"]/div[2]/i").click()
                except:
                    pass
                self.driver.find_element_by_id("widgetField").click()       # 기간 검색을 위한 날짜 변경 버튼 클릭
            except:
                try:
                    self.driver.find_element_by_xpath("//*[@id=\"PromoteSignUpPopUp\"]/div[2]/i").click()       # 인베스팅 사이트 팝업 제거 (광고 팝업창 수시로 나타남)
                except:
                    pass
            try:
                self.driver.find_element_by_id("startDate").clear()     # 날짜 설정
                self.driver.find_element_by_id("startDate").send_keys('2012/01/01')
            except:
                pass
            """
            try:
                self.driver.find_element_by_xpath("//*[@id=\"PromoteSignUpPopUp\"]/div[2]/i").click()
            except:
                pass
            """
            try:
                self.driver.find_element_by_id("applyBtn").click()      # 지정한 기간으로 코인 과거 정보 불러오기
                flag = False
            except:
                continue
                # print("get_page failed")
                # return None
            # print("get_page finished")
        return 0

    def get_data(self, name):
        data = []
        one_day = []
        flag = True
        grp_code = "00003"
        site_code = "06"  # investing.com 가상화폐 이전 데이터
        self.find_css_selector("#curr_table > tbody")       # 정보들어있는 테이블 찾기
        # data.append(name)
        i = 1
        while flag:
            try:
                one_day.append(name)
                one_day.append(grp_code)
                one_day.append(site_code)
                data_date = self.driver.find_element_by_css_selector("#curr_table > tbody > tr:nth-child(" + str(i) + ") > td:nth-child(1)").text
                temp_date = re.findall("[0-9]+", data_date)
                data_date = temp_date[0] + temp_date[1] + temp_date[2]
                one_day.append(data_date)
                one_day.append(self.driver.find_element_by_css_selector("#curr_table > tbody > tr:nth-child(" + str(i) + ") > td:nth-child(3)").text)
                one_day.append(self.driver.find_element_by_css_selector("#curr_table > tbody > tr:nth-child(" + str(i) + ") > td:nth-child(4)").text)
                one_day.append(self.driver.find_element_by_css_selector("#curr_table > tbody > tr:nth-child(" + str(i) + ") > td:nth-child(5)").text)
                one_day.append(self.driver.find_element_by_css_selector("#curr_table > tbody > tr:nth-child(" + str(i) + ") > td:nth-child(6)").text)
                one_day = list(one_day)
                data.append(one_day)
                one_day = []
                i += 1
            except:
                flag = False

        # 코인명, 그룹코드, 사이트 코드, 날짜, 오픈가, 고가, 저가, 거래량
        return data

def get_preData(target_names, target_addr):
    # print("get_preData function")
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    """
    option.add_argument("headless")
    option.add_argument('window-size=1920x1080')
    option.add_argument("disable-gpu")
    """
    i = 0
    arr = []
    temp = []
    preData = crawl_automation(option)
    for name in target_names:
        res = preData.get_page(target_addr, name)       # 코인별 과거정보 페이지 로드해오기
        if res is None:
            continue
        data = preData.get_data(name)       # 코인별 과거정보 가져오기
        data = list(data)
        arr.append(data)
        i += 1
        data = []
        temp = pd.DataFrame(arr)
        temp = temp.to_json(orient="values", force_ascii=False)     # 임시 코인 하나 데이터 json 형식으로 변환 후 저장
        with open("temp_coin_preData.json", "w", encoding="utf-8") as file:
            file.write(temp)

    arr = pd.DataFrame(arr)
    arr = arr.to_json(orient="values", force_ascii=False)       # 전체 코인 json 형식으로 변환 후 파일에 저장
    with open("coin_preData.json", "w", encoding="utf-8") as file:
        file.write(arr)
    print(str(arr))

if __name__ == "__main__" :

    bittrex_address = "https://bittrex.com/api/v1.1/public/getmarkets"      # 코인명 받아올 비트렉스 API 주소
    investing_address = "https://kr.investing.com/currencies/%s-historical-data"        # 코인별 지난 정보 가져올 인베스팅 사이트 주소
    arr = get_coin_name(bittrex_address)
    if arr is not None:
        get_preData(arr, investing_address)
    else:       # 코인명 받아오기 실패시
        print("get_coin_name return None", file=sys.stderr)