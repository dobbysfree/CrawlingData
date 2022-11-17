import os
import shutil
import sys
import zipfile
import time
import re
from datetime import datetime, timedelta

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd


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


class Danawa_Automation(Automation):

    def search(self, addr):
        flag = True
        dnw_data = []
        today_date = datetime.now().strftime("%Y-%m-%d")
        # dnw_data.append(str(today_date))
        page_num = 1
        self.driver.get(addr)
        try:        # 다나와 사이트 그래픽카드 검색
            check_string = self.driver.find_element_by_css_selector("#categoryContainer > div > div:nth-child(2) > dl > dd > ul > li:nth-child(3) > label > a").text
            check_string = str(check_string).split("(")[0]
            if check_string == "그래픽카드":
                self.driver.find_element_by_css_selector("#categoryContainer > div > div:nth-child(2) > dl > dd > ul > li:nth-child(3) > label > a").click()
        except:
            pass

        while flag:     # 검색 결과 다음 페이지로 이동
            try:
                dnw_data.extend(self.get_from_page())
                page_num += 1
                self.driver.find_element_by_xpath("//*[@id=\"productListPagingContainer\"]/div/div/div/a[" + str(page_num % 10) + "]").click()
                # self.driver.get(self.driver.find_element_by_xpath("//*[@id=\"productListPagingContainer\"]/div/div/div/a[" + str(page_num % 10) + "]"))
            except:
                flag = False

        return dnw_data

    def get_from_page(self):
        one_data = []
        data = []
        flag = True
        i = 1
        today_date = datetime.now().strftime("%Y-%m-%d")
        grp_code = "00004"      # 쇼핑 코드 : 00004
        site_code = "01"        # 다나와 사이트 코드 : 01

        while flag:             # 현재 페이지 내 상품들 [상품 id, 현재 날짜, 그룹코드, 사이트 코드, 상품명, 상품 스펙, 가격] 리스트로 저장
            try:
                id = self.driver.find_element_by_css_selector("#productListContainer > div > ul > li:nth-child(" + str(i) + ")").get_attribute("id")
                id = re.findall("[0-9]+", id).pop(0)
                one_data.append(id)
                one_data.append(today_date)
                one_data.append(grp_code)
                one_data.append(site_code)
                try:
                    one_data.append(self.driver.find_element_by_css_selector("#productListContainer > div > ul > li:nth-child(" + str(i) + ") > div > div.main_info > div.head_info > a").text)
                except:
                    one_data.append("")
                try:
                    one_data.append(self.driver.find_element_by_css_selector("#productListContainer > div > ul > li:nth-child(" + str(i) + ") > div > div.main_info > dl > dd > ul").text)
                except:
                    one_data.append("")
                try:
                    one_data.append(self.driver.find_element_by_css_selector("#productListContainer > div > ul > li:nth-child(" + str(i) + ") > div > div.price_info > div > dl > dd > span").text)
                except:
                    one_data.append("")

                one_data = list(one_data)
                data.append(one_data)
                one_data = []
                i += 1
            except:
                flag = False

        return data

def main(addr):
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    option.add_argument("headless")     # 창 띄우지 않는 옵션
    option.add_argument('window-size=1920x1080')
    option.add_argument("disable-gpu")

    danawa = Danawa_Automation(option)
    result = danawa.search(addr)        # 검색된 그래픽카드 정보 가져오기
    result = list(result)
    dnw_res = pd.DataFrame(result)
    dnw_res = dnw_res.to_json(orient="values", force_ascii=False)       # json 형식으로 변환
    print(dnw_res)      # 출력

if __name__ == "__main__" :
    main_address = "http://shop.danawa.com/main/?controller=goods&methods=search&keyword=그래픽카드"
    main(main_address)