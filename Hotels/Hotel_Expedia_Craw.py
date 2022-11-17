import os
import shutil
import sys
import zipfile
import re
import time
import pandas as pd
import pickle
from datetime import datetime, timedelta

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup


# ----------------------------------------------------------------------- #
# WebdriverWait 기능이 포함된 선택자 등등..                                  #
# https://github.com/youngminz/WebCrawling/blob/master/automation.py      #
# -------------------------------------------------------------------------#
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


# ----------------------------------------------------------------------- #
# For expedia page                                                        #
# -------------------------------------------------------------------------#

class expedia_automation(Automation):
    url = None  # url for the homepage
    baseUrl = None  # search_destination 후의 baseUrl

    # assumes self.driver is a selenium

    def search_destination(self, keyword):
        from datetime import datetime, timedelta

        startDate = datetime.now().strftime("%Y.%m.%d")     # 현재 날짜
        endDate = (datetime.strptime(startDate, "%Y.%m.%d") + timedelta(days=1)).strftime("%Y.%m.%d")
        url = "https://www.expedia.co.kr/Hotel-Search?destination=%s&startDate=%s&endDate=%s&adults=2&sort=recommended&page=1" % (
        keyword, startDate, endDate)
        self.driver.get(url)        # 날짜, 지역명을 바꾸어 사이트 띄우기
        self.baseUrl = self.driver.current_url[:-1]

    def getHotels_from_page(self, stat_code):
        self.find_css_selector("div.flex-card.flex-listing")  # 모든 호텔이 로드되면 해당 css selector가 생성된다.
        temp = []
        hotel = self.driver.find_elements_by_tag_name("article")        # article 태그를 가진 요소 찾을 것
        try:  # 국가명이 앞에 나와있는 경우
            destination = self.driver.find_element_by_id("inpSearchNear").get_attribute("value")
            destinationName = tuple(destination.split(" "))  # (도시, 국가)
            temp_destName = destinationName[0]
            temp_destName = temp_destName.replace(",", "")
            temp_destName = re.findall("\w+", temp_destName)[0]
            if temp_destName == "한국" or temp_destName == "대한민국" or destinationName[0] == "대한민국" or destinationName[0] == "한국":
                destinationName = "82"
            elif temp_destName == "마카오 특별행정구" or temp_destName == "마카오(전체)" or temp_destName == "마카오":
                destinationName = "853"
            else:
                raise Exception
            dest_string = str(stat_code + "," + destinationName)
            destinationName = tuple(dest_string.split(','))
        except:
            try:  # 국가명이 뒤에 들어가 있는 경우
                destination = self.driver.find_element_by_id("inpSearchNear").get_attribute("value")
                destinationName = tuple(destination.split(","))  # (도시, 국가)
                temp_destName = str(destinationName[1]).strip()
                if temp_destName == "한국" or temp_destName == "대한민국" or destinationName[0] == "대한민국" or destinationName[0] == "한국":
                    destinationName = "82"
                elif temp_destName == "마카오 특별행정구" or temp_destName == "마카오(전체)" or temp_destName == "마카오":
                    destinationName = "853"
                else:
                    raise Exception
                dest_string = str(stat_code + "," + destinationName)
                destinationName = tuple(dest_string.split(','))
            except:  # 국가명 없이, 지역 이름만 있는 경우
                target_destinations = ["서울특별시", "강원도", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기도", "충청북도", "충청남도",
                                       "전라북도", "전라남도", "경상북도", "경상남도", "제주도"]
                for td in target_destinations:
                    if temp_destName == td:     # 지역 이름이 대한민국 지역명 어레이에 있는 것과 일치할 때
                        destinationName = "82"
                        break
                    elif temp_destName == "마카오" or temp_destName == "마카오 특별행정구":
                        destinationName = "853"
                        break
                    else:
                        destinationName = ""
                dest_string = str(stat_code + "," + destinationName)
                destinationName = tuple(dest_string.split(','))

        # 개별 숙소 정보 가져오기
        for h in hotel:
            hName = h.find_element_by_css_selector("h3.visuallyhidden").text  # 숙소 이름
            hUrl = h.find_element_by_css_selector("a.flex-link").get_attribute("href")  # 숙소 링크
            try:
                hprice = \
                re.findall("[0-9,0-9]+", h.find_element_by_css_selector("li.price-breakdown-tooltip.price").text)[0]  # 1박 평균 가격
            except NoSuchElementException:
                hprice = ""

            rem_room = ""  # 남은 방 수 익스피디아에서 확인하기 어려움

            # 매진 여부
            if h.find_elements_by_class_name("soldOutMsg "):
                isSoldOut = "Y"
            else:
                isSoldOut = "N"

            temp.append(destinationName + (hName, hUrl, isSoldOut, rem_room, hprice))

        return temp

    def get_all_hotels(self, stat_code):
        data = []
        flag = True
        i = 1
        while flag:
            try:
                data.extend(self.getHotels_from_page(stat_code))        # 현재 페이지의 호텔들 기본 정보 가져오는 getHotels_from_page 호출
                self.driver.get(self.baseUrl + str(i + 1))              # 현재 페이지 완료시 다음 페이지로 이동
                i += 1
            except TimeoutException:
                flag = False
                # self.driver.close()
        data = set(data)  # 중복 제거
        return list(data)

    @staticmethod
    def update_hotel_details(html):
        soup = BeautifulSoup(html, "html.parser")
        grp_code = "00001"          # 호텔 그룹코드
        site_code = "01"            # 익스피디아 사이트 코드
        date = datetime.now().strftime('%Y-%m-%d')      # 현재 날짜
        try:        # 체크인 시간 정보 파싱
            CheckIn = soup.find(string=re.compile("체크인 시작 시간")).string
            if CheckIn == "체크인 시작 시간: 정오":
                CheckIn = "12:00"
            elif CheckIn == "":
                pass
            else:
                CheckIn = re.findall("[0-9:0-9]+", CheckIn)[1]
        except:
            CheckIn = ""

        try:        # 체크아웃 시간 정보 파싱
            CheckOut = soup.find(string=re.compile("체크아웃 시간")).string
            if CheckOut == "체크아웃 시간: 정오":
                CheckOut = "12:00"
            else:
                CheckOut = re.findall("[0-9:0-9]+", CheckOut)[1]
        except:
            CheckOut = ""

        try:        # 호텔의 총 객실 수 정보 파싱
            Room_num = re.findall("\\d+", soup.find("li", string=re.compile("총 객실 수")).string)[0]
        except:
            Room_num = ""
        try:        # 호텔 주소 정보와 익스피디아 내 호텔 고유 아이디값 정보 파싱
            address = soup.select("div.address")[0].text[6:-4].split("\n\n\n\n")
            addr = address[0]
            phone = re.findall("^.*infosite.hotelId.*$", soup.text, re.MULTILINE)[0]
            phone = re.findall("[0-9]+", phone).pop(0)
        except:
            phone = "0000001"       # 호텔 아이디값 없을 경우 0000001 로 설정
            addr = ""

        try:        # 익스피디아 내 호텔 사용 만족도 점수 파싱
            score = soup.select("span.rating-number")[0].text
        except IndexError:
            score = ""

        try:        # 호텔 성급 정보 파싱
            starRating = re.findall("^.*infosite.starRating.*$", soup.text, re.MULTILINE)[0]
            starRating = re.findall("[0-9.0-9]+", starRating)[1]
        except:
            starRating = ""

        try:        # 호텔 유형 정보 파싱
            hType = re.findall("^.*infosite.structureName.*$", soup.text, re.MULTILINE)[0]
            hType = re.findall("[A-Z]+", hType)[1]
            if hType == "HOTEL":
                hType = "1"
            elif hType == "RESORT":
                hType = "2"
            elif hType == "MOTEL":
                hType = "3"
            elif hType == "GUEST" or hType == "APARTMENT" or hType == "GUEST_HOUSE":
                hType = "4"
            elif hType == "PENSION":
                hType = "5"
            elif hType == "RESIDENCE":
                hType = "6"
            else:
                hType = "9"
        except:
            hType = "9"

        return score, addr, phone, CheckIn, CheckOut, Room_num, starRating, hType, grp_code, site_code, date


def crawl_expedia(destinations, stat_codes):
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    fail_arr = []
    fail_tmp = []
    i = 0
    expedia = expedia_automation(option)
    for keyword in destinations:
        expedia.search_destination(keyword)     # 기본 url에서 지역명, 날짜 검색
        result = expedia.get_all_hotels(stat_codes[i])      # 지역에 따른 전체 호텔 리스트 정보 가져오기
        hotel_data = result
        time.sleep(1)  # time for closing webdriver
        hotel_data = set(hotel_data)  # 중복제거
        hotel_data_details = crawl_expedia_details(hotel_data)      # 리스트에서 가져온 각 호텔마다의 세부 정보 가져오기
        hotel_info_file = "hotel_info_01_" + stat_codes[i] + ".json"        # 지역별 Hotel Info 파일 이름
        i += 1      # 검색 실패한 리스트 저장 위한 인덱스 i
        hotel_data = list(hotel_data)
        try:
            # Data Frame 생성
            df1 = pd.DataFrame(hotel_data)
            df2 = pd.DataFrame(hotel_data_details)
            result = pd.concat([df1, df2], axis=1)      # hotel_data 와 hotel_data_detail 의 데이터 프레임들을 합침
            result.columns = ["city", "country", "name", "url", "sold", "room_avail", "price", "score", "address", "phone", "checkin", "checkout", "room_total", "starClass", "Type", "grp_code", "site_code", "date"]      # 데이터프레임 컬럼 이름 설정

            # DB 필드 순서에 맞게 순서 이동
            t1 = result[["grp_code", "site_code", "phone", "country", "city", "name", "starClass", "Type", "address", "room_total", "checkin", "checkout"]]
            t2 = result[["phone", "site_code", "country", "city", "date", "score", "price", "room_avail", "sold"]]
            # json 파일 형식으로 변환
            hotel_data = t1.to_json(orient="values", force_ascii=False)
            hotel_data_details = t2.to_json(orient="values", force_ascii=False)

            # 지역별 Hotel Info 파일 저장 공용소에 저장함
            file_path = os.path.join("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/", hotel_info_file)
            fid = open(file_path, "w", encoding='UTF-8')
            fid.write(hotel_data)
            fid.close()
            # 지역별 Hotel Daily 파일 출력
            print("tb_hotel_daily?" + hotel_data_details)
        except:
            # 실패할 시 다시 검색하기 위하여 검색 실패한 지역이름과 지역코드를 저장
            fail_tmp.append(keyword)
            fail_tmp.append(stat_codes[i-1])
            fail_arr.append(fail_tmp)
            fail_tmp = []
            pass

    # 검색 실패한 지역 성공할 때까지 재검색
    while len(fail_arr) != 0:
        for dest in fail_arr:
            fail_stat_code = dest[1]        # 지역코드
            dest = dest[0]                  # 지역명
            try:
                expedia = expedia_automation(option)
                expedia.search_destination(dest)
                result = expedia.get_all_hotels(fail_stat_code)
                hotel_data = result
                time.sleep(1)  # time for closing webdriver
                hotel_data = set(hotel_data)  # remove duplicates
                hotel_data_details = crawl_expedia_details(hotel_data)
                hotel_info_file = "hotel_info_01_" + fail_stat_code + ".json"

                hotel_data = list(hotel_data)

                df1 = pd.DataFrame(hotel_data)
                df2 = pd.DataFrame(hotel_data_details)
                result = pd.concat([df1, df2], axis=1)
                result.columns = ["city", "country", "name", "url", "sold", "room_avail", "price", "score", "address", "phone", "checkin", "checkout", "room_total", "starClass", "Type", "grp_code",
                                  "site_code", "date"]

                t1 = result[["grp_code", "site_code", "phone", "country", "city", "name", "starClass", "Type", "address", "room_total", "checkin", "checkout"]]
                t2 = result[["phone", "site_code", "country", "city", "date", "score", "price", "room_avail", "sold"]]

                hotel_data = t1.to_json(orient="values", force_ascii=False)
                hotel_data_details = t2.to_json(orient="values", force_ascii=False)

                file_path = os.path.join("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/", hotel_info_file)
                fid = open(file_path, "w", encoding='UTF-8')
                fid.write(hotel_data)
                fid.close()

                print("tb_hotel_daily?" + hotel_data_details)

                fail_arr.pop(0)     # 성공시 검색 실패한 목록에서 제거
            except:
                pass        # 예외가 발생했다면 다시 실행


def crawl_expedia_details(hotel_data):
    hotel_data_specific = []

    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=10)
    sess.mount("http://", adapter)
    agent = {"User-Agent": 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}     # 사이트 여러번 접근하기 위해, headers 추가
    for hotel in hotel_data:
        try:
            response = requests.get(hotel[3], headers=agent)        # 각 호텔의 링크로 requests
            html = response.text
            if html is None:
                raise Exception     # get 의 결과가 없다면 예외처리
            temp = expedia_automation.update_hotel_details(html)        # get의 결과를 파싱하여 필요한 정보 가져오기
            hotel_data_specific.append(temp)        # 어레이에 저장
        except:
            # 예외 발생시 null 값으로 어레이에 저장
            temp = ["", "", "", "", "", "", "", "", "", "", ""]
            hotel_data_specific.append(temp)

    return hotel_data_specific

def main(destinations, stat_codes):

    crawl_expedia(destinations, stat_codes)

############################################################################
##----------------------------------------------------------------------- ##
## CLIENT                                                                 ##
##----------------------------------------------------------------------- ##
############################################################################

if __name__ == "__main__":

    dir_name = "hotel_info_directory"
    try:        # hotel info 정보 저장할 폴더 생성
        if not (os.path.isdir("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/")):
            os.makedirs(os.path.join("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/"))
    except OSError as e:
        print("Failed to create directory!!!!!")

    # 검색할 지역과 지역코드
    target_destinations = ["강원도", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기도", "충청북도", "충청남도", "전라북도", "전라남도",
                           "경상북도", "경상남도", "제주도", "서울", "마카오"]
    target_code = ["20", "60", "70", "40", "50", "30", "68", "33", "41", "36", "31", "56", "51", "71", "62", "69",
                   "10", ""]

    main(target_destinations, target_code)
