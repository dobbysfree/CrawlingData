import os
import shutil
import sys
import zipfile
import re
import time
import pandas as pd
import pickle
import datetime #임시 삽입


import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
# For Agoda page                                                        #
# -------------------------------------------------------------------------#

class agoda_automation(Automation):
    url = None  # url for the homepage
    baseUrl = None  # search_destination후의 baseUrl

    def search_destination(self, keyword):
        from datetime import datetime, timedelta

        startDate = datetime.now().strftime("%Y-%m-%d")
        endDate = (datetime.strptime(startDate, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        # 아고다 URL
        url = "https://www.agoda.com/ko-kr/pages/agoda/default/DestinationSearchResult.aspx?%s" \
              "&pagetypeid=1&origin=KR&languageFlag=kr&currencyCode=KRW&htmlLanguage=ko-krt&cultureInfoName=ko-KR&" \
              "rooms=1&adults=2&children=0&childAges=&checkIn=%s&checkOut=%s4&isUpdateAsq=true&los=1&childages=&" \
              "priceCur=KRW&tabId=1&ckuid=" % (keyword, startDate, endDate)

        self.driver.get(url)
        self.baseUrl = self.driver.current_url[:-1]
        return url

    def get_all_hotels_pagination(self, hUrl,city_code):
        data = []
        flag = True
        isSearchingFlag = 0
        isInfiniteLoop=0
        while flag:
            # print(isInfiniteLoop)
            try:
                errorPage = self.driver.find_element_by_css_selector('button.btn.btn-primary.tdBanner_actionButton')
                try:
                    errorPage.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", errorPage)
                # print("Meet Error page")
            except Exception:
                try:
                    print("검색 페이지 정상 진입")
                    try:
                        current_page = re.findall("[0-9]+", self.driver.find_element_by_class_name('page-of').text)[0]
                    except Exception:
                        current_page = re.findall("[0-9]+", self.driver.find_element_by_id('paginationPageCount').text)[0]
                    # print(current_page)
                    try:
                        final_page = re.findall("[0-9]+", self.driver.find_element_by_class_name('page-of').text)[1]
                    except Exception:
                        final_page = re.findall("[0-9]+", self.driver.find_element_by_id('paginationPageCount').text)[1]
                    # print(final_page)
                    # 검색 도중 에러페이지 발생시 리로딩 되며 화면이 처음으로 넘어가게 되면 이중검색방지 및 무한 루프 방지를 위해 Flag를 멈춘다
                    if isSearchingFlag > int(current_page):
                        # print("Click Error page button, Return to first page -- Flag False")
                        flag = False
                    else:
                        # print("데이터 추출 - 전")
                        data.extend(self.getHotels_from_searchPage(hUrl,city_code))
                        # print("데이터 추출 - 후")

                    #   마지막 페이지와 현재 페이지가 같으면 False
                    if current_page == final_page:
                        flag = False

                    #   다음 페이지로 넘기기
                    # print("페이지 버튼 - 전")
                    element = self.driver.find_element_by_css_selector('#paginationNext')
                    # print("페이지 버튼 - 후")
                    self.driver.execute_script("arguments[0].click();", element)

                    isSearchingFlag = int(current_page)
                    time.sleep(2)
                except IndexError:
                    # print("검색 페이지 - 인덱스 에러")
                    isInfiniteLoop += 1
                except NoSuchElementException:
                    # print("검색 페이지 - No Such")
                    continue

            if isInfiniteLoop > 100:
                # print("무한 루프로 돌아가는 중")
                self.driver.get(hUrl)
                isInfiniteLoop=0

        data = set(data)  # prevent duplicates
        return list(data)

    def getHotels_from_searchPage(self, hUrl,city_code):
        html = requests.get(hUrl).text
        soup = BeautifulSoup(html, "html.parser")

        # 도시, 국가 정보 가져오기
        temp = []
        hotel = self.driver.find_elements_by_class_name("ssr-search-result")
        # try:
        #     cityName = self.driver.find_element_by_xpath("// *[ @ id = 'breadcrumb'] / div / div / ul / li[9] / div / a / div").text
        #     print("cityName try")
        # except NoSuchElementException:
        #     print("cityName except")
        #     cityName = self.driver.find_element_by_class_name("availability-message__text").text
        #     cityName = cityName.split()[4]
        cityName=city_code

        countryName = self.driver.find_element_by_xpath("// *[ @ id = 'breadcrumb'] / div / div / ul / li[5] / div / a / div").text
        if countryName is None:
            try:
                print("countryName try")
                countryName = re.findall('CountryName.*', soup.text, re.MULTILINE)
                countryName = str(countryName).split('"')[2]
                if(countryName=="CountryId"):
                    countryName = ""
            except IndexError:
                print("countryName except")
                countryName=""

        if countryName =="대한민국":
            countryName = "82"
        elif countryName == "마카오":
            countryName = "853"
        else:
            countryName=""

        destinationName = (countryName,cityName)
        destinationName = tuple(destinationName)  # (도시, 국가)
        print(destinationName)
        print((len(hotel)))

        # 개별 숙소 정보 가져오기
        for h in hotel:
            #   아고다 사이트는 호텔명이 추출되지 않아 호텔 아이디값으로 명 대체함(hotelId==hName )
            hotelId=h.find_element_by_tag_name('a').get_attribute('data-hotelid')
            print(hotelId)
            hUrl = h.find_element_by_tag_name('a').get_attribute('href')  # 숙소 링크
            # print(hUrl)

            temp.append(destinationName + (hotelId, hUrl))

        return temp

    @staticmethod
    def update_hotel_details(session, hUrl):
        from datetime import datetime

        req = session.get(hUrl)
        html = req.text
        soup = BeautifulSoup(html, "html.parser")
        try:
            if re.findall('500.Internal.Server.Error', soup.text,re.MULTILINE)[0] is not None:
                # print("500 내부 에러페이지")
                hName=""
                isSoldOut=""
                rem_room=""
                hPrice=""
                clientRating=""
                address=""
                CheckIn=""
                CheckOut=""
                Room_num=""
                starRating=""
                hType=""
        except IndexError:
            #   정상진입
            print(hUrl) #########################################세부 정보 크롤링하는 중이라는 시그널 테스트후 삭제
            # 호텔 이름 추출
            hName=re.findall('name:.".*"', soup.text, re.MULTILINE)[0]
            hName =hName.split(":")[1]
            hName = hName[2:-1]
            # 호텔 명에 추가되는 경우 있어서 검사
            hName = hName.replace("\\u0026","")
            hName = hName.replace("\\u0027","")
            # 호텔 가격 추출(평균값으로 산출)
            searchFlag=True
            i = 0
            hPrice = 0
            while searchFlag:
                try:
                    hPrice_temp = re.findall('cheapestPriceValue:.*', soup.text, re.MULTILINE)[i]
                    hPrice_temp = str(hPrice_temp).split(":")[1]
                    hPrice_temp = re.findall("[0-9]+", hPrice_temp)
                    #   문자열 리스트를 숫자형으로 변환하면서 total price 산출
                    for price in range(len(hPrice_temp)):
                        hPrice_temp[price] = int(hPrice_temp[price])
                        hPrice += hPrice_temp[price]
                    i += 1
                except IndexError:
                    searchFlag = False
            if hPrice is not 0:
                hPrice //= i
            #   isSoldOut(매진여부), rem_room(남은 방 수) 추출
            isSoldOut = "Y"
            i=0
            rem_room = 0
            while isSoldOut != "N":
                try:
                    rem_room_temp = re.findall('"firstRoomAvailability":[0-9]', soup.text, re.MULTILINE)[i]
                    rem_room_temp = re.findall("[0-9]+", rem_room_temp)[0]
                    rem_room += int(rem_room_temp)
                    i += 1
                    if  rem_room_temp == "" or rem_room_temp == 0:
                        isSoldOut="N"
                except IndexError:
                    isSoldOut="N"
            if rem_room == 0:
                isSoldOut="Y"
            #   고객 평점 추출
            try:
                clientRating = re.findall('score\W*[0-9].[0-9]', soup.text, re.MULTILINE)[0]
                clientRating = re.findall('[0-9.0-9]+', clientRating)[0]
                # clientRating = soup.find('div', {'class': 'ReviewScore.ReviewScore--flipped'})
            except IndexError:
                clientRating=""
        #   아고다는 체크인, 체크아웃 시간 및 총 객실 수, 전화번호 정보 제공안함
            CheckIn = ""
            CheckOut = ""
            Room_num = ""
            #   호텔 주소 추출
            try:
                address = re.findall('full:.*\w', soup.text,re.MULTILINE)[0]
                address = str(address).split(":")[1]
                address = address[2:]
            except IndexError:
                address = ""
            #   숙소 N성급 추출
            try:
                starRating = re.findall("starRatingFontIcon.*,", soup.text, re.MULTILINE)[0]
                starRating = re.findall('[0-9]+', starRating)[0]
                if len(starRating) == 2:
                    dot = '.'
                    starRating = dot.join(starRating)
            except IndexError:
                starRating = ""
            try:
                hType = re.findall("accommodationType.*\"", soup.text,re.MULTILINE)[0]
                hType = str(hType).split(":")[1]
                hType = hType[2:-1]
            except IndexError:
                hType = ""
            if hType == "호텔":
                hType = "1"
            elif hType == "리조트":
                hType = "2"
            elif hType == "모텔":
                hType = "3"
            elif hType == "게스트하우스 / 비앤비":
                hType = "4"
            elif hType == "프라이빗 하우스":
                hType = "5"
            elif hType == "아파트먼트" or hType == "서비스 아파트먼트":
                hType = "6"
            else:
                hType = "9"

        # 생성일자, 웹사이트 코드, 그룹 코드
        createDate = datetime.now().strftime("%Y-%m-%d")
        website_code = "05"
        group_code = "00001"

        return hName, isSoldOut, rem_room, hPrice, clientRating, address, CheckIn, CheckOut, Room_num, starRating, hType, createDate, website_code, group_code


def crawl_agoda(destination,city_code):
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    option.add_argument('headless')
    option.add_argument("disable-gpu")

    hotel_data = []  ## [(도시, 국가, 숙소이름, 숙소링크), ...]

    # for keyword in destinations:
    agoda = agoda_automation(option)
    hUrl = agoda.search_destination(destination)
    result = agoda.get_all_hotels_pagination(hUrl,city_code)
    hotel_data.extend(result)
    time.sleep(1)  # time for closing webdriver

    hotel_data = set(hotel_data)  # remove duplicates

    return list(hotel_data)

def crawl_agoda_details(hotel_data):
    hotel_data_specific = []  ## [(CheckIn , CheckOut, Room_num, address, isSoldOut, starRating, reviewCount, hType), ...]

    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=10)
    sess.mount("http://", adapter)

    for hotel in hotel_data:
        if hotel[3] is not None:
            temp = agoda_automation.update_hotel_details(sess, hotel[3])
            hotel_data_specific.append(temp)
    return hotel_data_specific


def main():
    ## Crawl Hotel.com hotel list
    #	target_destinations = ["서울","부산", "인천", "대전", "대구","광주", "울산", "경기도", "청주(충복)", "충청남도", "강릉(강원)", "평창(강원)" ,"전주(전북)", "여수(전남)","경주(경북)", "거제(경남)", "제주도"]
    target_destinations = ["city=14690", "city=17172", "city=17234", "city=17233", "city=17232", "city=19042", "city=10137", "region=372", "city=21471", "region=357",
                           "city=19041", "city=17235", "city=17831", "city=213193", "city=17179", "city=212469", "city=16901"]
    city_codes = ["10", "60","40","30","70","50","68","41","36","31","20","20","56","51","71","62","69"]
    # target_destinations = ["city=17234"]
    # city_codes = ["40"]

    i = 0
    for i in range(len(target_destinations)):
        destination = target_destinations[i]
        city_code = city_codes[i]
        agoda_hotel_data = crawl_agoda(destination,city_code)

        ## For connection log
        import logging
        logging.basicConfig()
        #logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True


        ## Update Details of each hotel
        agoda_hotel_data_details_info = crawl_agoda_details(agoda_hotel_data)

        ## Merge table columnwise
        df1 = pd.DataFrame(agoda_hotel_data)
        df2 = pd.DataFrame(agoda_hotel_data_details_info)
        result = pd.concat([df1, df2], axis=1)
        result.columns = ["country", "city", "hotelID", "url", "name", "sold", "room_avail", "price", "client_rating", "address",
                                    "checkin", "checkout", "room_total", "star_rating", "Type","createDate","website","group_code"]
        t1 = result[["group_code", "website", "hotelID", "country", "city", "name", "star_rating", "Type", "address",
                     "room_total", "checkin", "checkout"]]
        t2 = result[["hotelID", "website", "country", "city", "createDate", "client_rating", "price", "room_avail", "sold"]]
        hotel_info_table = t1.to_json(orient="values", force_ascii=False)
        hotel_daily_table = t2.to_json(orient="values", force_ascii=False)

        print(hotel_info_table)
        print(hotel_daily_table)

    ## result to Json
    # return t1.to_json(orient="values", force_ascii=False), t2.to_json(orient="values", force_ascii=False)

    # ## Or Save as Json
    # with open("hotel_finals_test4.json", "w", encoding="utf-8") as file:
    #     result.to_json(file, orient="values", force_ascii=False)


############################################################################
##----------------------------------------------------------------------- ##
## CLIENT                                                                 ##
##----------------------------------------------------------------------- ##
############################################################################

if __name__ == "__main__":

    #target_destinations = ["region=372"]
    # 시작 시간
    # startTime = datetime.datetime.now()
    # print("시작시간")
    # print(startTime)

    main()

    # endTime = datetime.datetime.now()
    # print("종료시간")
    # print(endTime)
    #
    # print("구동 시간")
    # processingTime = str(endTime - startTime)
    # print(processingTime)
    # hotel_info_table : [["country", "city", "name", "Type", "address", "room_total", "checkin", "checkout"]]
    # hotel_daily_table : [["rating", "price", "room_available", "isSoldOut"]]

    # ## Or Save as Json
    # with open("hotel_info_table.json", "w", encoding="utf-8") as file:
    #     file.write(hotel_info_table)
    # with open("hotel_daily_table.json", "w", encoding="utf-8") as file:
    #     file.write(hotel_daily_table)
