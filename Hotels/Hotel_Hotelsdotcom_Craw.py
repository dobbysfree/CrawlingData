#-*- coding: utf-8 -*-
import os
from wheel.signatures import keys
import shutil
import zipfile
import re
import time
import sys
import datetime #임시 삽입
import pandas as pd
import pickle

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------- #
# WebdriverWait 기능이 포함된 선택자 등등..                               #
# https://github.com/youngminz/WebCrawling/blob/master/automation.py      #
#-------------------------------------------------------------------------#
class Automation:
    driver = None
    def __init__(self, chrome_options=None):
        if not os.path.isfile("chromedriver.exe"):
            print("chromedriver.exe가 존재하지 않습니다. 최신 릴리즈를 최초 1회 다운로드합니다.", file=sys.stderr)

            chromedriver_latest_release = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE").text.strip()

            r = requests.get("https://chromedriver.storage.googleapis.com/" + chromedriver_latest_release + "/chromedriver_win32.zip", stream=True)

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
# For hotelsDotCom page                                                        #
#-------------------------------------------------------------------------#

class hotelsDotCom_automation(Automation):
    url = None # url for the homepage
    baseUrl = None # search_destination후의 baseUrl
    
    def search_destination(self, keyword):
        from datetime import datetime, timedelta

        startDate = datetime.now().strftime("%Y-%m-%d")
        endDate = (datetime.strptime(startDate, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        #호텔스 닷컴 URL
        #url = "https://kr.hotels.com/search.do?q-triptype=work&r&q-destination=%s&q-check-in=%s&q-check-out=%s&q-rooms=1&q-room-0-adults=2&q-room-0-children=0"%(keyword,startDate, endDate)
        url = "https://kr.hotels.com/search.do?q-triptype=work&destination-id=%s&q-check-in=%s&q-check-out=%s&q-rooms=1&q-room-0-adults=2&q-room-0-children=0"%(keyword, startDate, endDate)

        self.driver.get(url)
        self.baseUrl = self.driver.current_url[:-1]

    def getHotels_from_searchPage(self,city_code):
            # 도시, 국가 정보 가져오기
            temp = []
            hotel = self.driver.find_elements_by_tag_name("article")
            destinationName = self.driver.find_element_by_id("q-destination").get_attribute("value")
            countryName = destinationName.split(",")[1].lstrip()
            # print(countryName)
            if countryName == '한국':
                country_code = "82"
            elif countryName == '마카오':
                country_code = "853"
            else:
                country_code = ""

            #destinationName = tuple(destinationName.split(",")) # (도시, 국가)
            destinationName = (country_code, city_code) # (도시, 국가)
            destinationName = tuple(destinationName)  # (도시, 국가)

            # print(destinationName);
            # print(len(hotel))
            # 개별 숙소 정보 가져오기
            for i in range(len(hotel)):
                h = hotel[i]
                hName = h.find_element_by_class_name('p-name').text # 숙소 이름
                hUrl = h.find_element_by_css_selector('h3.p-name > a').get_attribute("href")  # 숙소 링크
                # print(hName)
                try:
                    try:
                        hotelPrice = re.findall("[0-9,0-9]+",h.find_element_by_css_selector("span.old-price-cont > ins").text)[0]  # 1박 평균 가격(할인Yes)
                    except NoSuchElementException:
                        hotelPrice = re.findall("[0-9,0-9]+",h.find_element_by_css_selector("div.price > a >  b").text)[0]  # 1박 평균 가격(할인No)
                except NoSuchElementException:
                    hotelPrice = ""

                # sold-out 태그 있으면 남은 방 0, 없으면 남은 방 숫자 추척
                # 추적이 되지 않으면 방이 몇개 남았는지 알수없으므로 Null값 삽입
                try:
                    try:
                        if h.find_element_by_css_selector("p.sold-out-message") is not None:
                            rem_room=0
                    except NoSuchElementException:
                        rem_room = re.findall("[0-9]+", h.find_element_by_css_selector("div.scarcity-message").text)[0]
                except NoSuchElementException:
                    rem_room = ""
                if rem_room == 0:
                    isSoldOut = "Y"
                else:
                    isSoldOut = "N"
                # 고객 평점 추출
                try:
                    clientRating=re.findall("[0-9.0-9]+",h.find_element_by_css_selector("span.guest-rating-value").text)[0]
                except NoSuchElementException:
                    clientRating=""

                temp.append(destinationName + (hName, hUrl, isSoldOut, rem_room, hotelPrice,clientRating))
            return temp

    def get_all_hotels_scrollDown(self,city_code):
        data = []
        isScrollDone=True   #스크롤 다운이 끝까지 다 됐으면 False로 변경

        while isScrollDone:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")    # Scroll down to bottom
            time.sleep(0.5)   # Wait to load page
            try:
                try:
                    # 인근 숙소 태그 만나면 스크롤 종료
                    if self.driver.find_element_by_class_name('expanded-area-message') is not None:
                        # print("인근 숙소 태그")
                        isScrollDone=False
                except:
                    # 마지막 태그를 찾아서 있으면 Flag값 변경
                    if self.driver.find_element_by_xpath("//*[@id='result-info-container']/div") is not None:
                        # print("마지막 태그")
                        isScrollDone = False
                    elif self.driver.find_element_by_css_selector("div.info info-highlight").get_attribute('style') is not "display: none;":
                        # print("마지막 태그")
                        isScrollDone = False
            except NoSuchElementException:
                continue
            except TimeoutException:
                self.driver.close()

        data.extend(self.getHotels_from_searchPage(city_code))
        data = set(data)  # prevent duplicates
        return list(data)

    @staticmethod
    def update_hotel_details(session, hUrl):
        from datetime import datetime
        req = session.get(hUrl)
        html = req.text
        soup = BeautifulSoup(html, "html.parser")
        #print(hUrl)
        #체크인 시간 추출
        try:
            try:
                CheckIn = soup.find(string=re.compile("체크인 시작 시간:")).string
            except AttributeError:
                CheckIn = soup.find(string=re.compile("체크인 시간:")).string
            if CheckIn == "체크인 시작 시간: 정오" or CheckIn == "체크인 시간: 정오":
                CheckIn = "12:00"
            elif CheckIn == "":
                pass
            else:
                CheckIn = re.findall("[0-9:0-9]+",CheckIn)[1]
        except AttributeError:
            CheckIn = ""
        except IndexError:
            CheckIn = ""
        # 체크아웃 시간 추출
        try:
            CheckOut = soup.find(string=re.compile("체크아웃 시간:")).string
            if CheckOut == "체크아웃 시간: 정오" or CheckOut == "체크아웃 시간: 자정":
                CheckOut = "12:00"
            else:
                CheckOut = re.findall("[0-9:0-9]+", CheckOut)[1]
        except AttributeError:
            CheckOut = ""
        except IndexError:
            CheckOut = ""
       # 총 객실 수 추출
        try:
            Room_num = re.findall("[0-9,0-9]+", soup.find(string=re.compile("객실 보유")).string)[0]
        except AttributeError:
            Room_num = ""
        # 숙소 주소 추출
        try:
            address = soup.find('span', {'class': 'postal-addr'}).text
        except AttributeError:
            address=""
        # 숙소 연락처(호텔 아이디 값) 추출
        try:
            hotelId = soup.find('span', {'id': 'hd_property_info_tfn'}).text
        except AttributeError:
            # 숙소 연락처가 없다면 ID값 추출
            try:
                hotelId = soup.find('input', {'id': 'totpq-destination'})
                hotelId = hotelId.get('data-destination-id')
            except AttributeError:
                hotelId = ""
        # 숙소 별점 추출
        try:
            starRating = re.findall("[0-9.0-9]+", soup.find(string=re.compile("성급")).string)[0]
        except AttributeError:
            starRating = ""
        # 숙소 유형 추출
        try:
            hType = re.findall("accommodationTypeIds.*]", soup.text)
            hType = str(hType).split(",")[0]
            hType = re.findall("[0-9]+", hType)[0]
        except IndexError:
            hType=""
        if hType == "1":
            hType = "1" #   호텔
        elif hType == "3" or hType == "4":
            hType="2" #   리조트
        elif hType == "7":
            hType = "3" #   모텔
        elif hType == "30"or hType == "8":
            hType = "4" #   게스트 하우스
        elif hType == "25" or hType == "21" or hType == "20"or hType == "14" or hType == "11" or hType == "5":
            hType = "5" #   펜션
        elif hType == "15":
            hType = "6" #   레지던스
        else:
            hType = "9" #   기타

        # 생성일자, 웹사이트 코드, 그룹 코드
        createDate = datetime.now().strftime("%Y-%m-%d")
        website_code = "02"
        group_code = "00001"

        return address, CheckIn, CheckOut, Room_num, starRating, hotelId,hType,createDate,website_code,group_code

def crawl_hotelsDotCom(destination, city_code):

    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    option.add_argument('headless')
    option.add_argument("disable-gpu")

    hotel_data = []  ## [(도시, 국가, 숙소이름, 숙소링크), ...]

    # for keyword in destinations:
    hotelsDotCom = hotelsDotCom_automation(option)
    hotelsDotCom.search_destination(destination)
    result = hotelsDotCom.get_all_hotels_scrollDown(city_code)
    hotel_data.extend(result)
    time.sleep(1)  # time for closing webdriver
    hotel_data = set(hotel_data)    # remove duplicates

    return list(hotel_data)

def crawl_hotelDotCom_details(hotel_data):
    hotel_data_specific = []  ## [(CheckIn , CheckOut, Room_num, address, isSoldOut, starRating, reviewCount, hType), ...]

    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=10)
    sess.mount("http://", adapter)

    for hotel in hotel_data:
        temp = hotelsDotCom_automation.update_hotel_details(sess,hotel[3])
        hotel_data_specific.append(temp)
    return hotel_data_specific

def main():
    ## Crawl Hotel.com hotel list
    #	target_destinations = ["서울", "강원도", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기도", "충청북도", "충청남도", "전라북도","전라남도","경상북도", "경상남도", "제주도", "마카오"]
    target_destinations = ["759818","10235260", "1639028", "1639042", "757364", "759560", "754647", "761311", "1753973",
                             "10235259", "10235261", "10395901", "10405232", "10235264","10235265", "10235266", "1644457", "806258"]
    city_codes = ["10", "20", "60","70","40","50","30","68","33","41","36","31","56","51","71","62","69",""]
    #target_destinations = ["1753973"]
    #city_codes = ["33"]

    i=0
    for i in range(len(target_destinations)):
        destination=target_destinations[i]
        city_code = city_codes[i]
        hotelsDotcom_hotel_data = crawl_hotelsDotCom(destination,city_code)

        

        ## For connection log
        import logging
        logging.basicConfig()
        #logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        ## Update Details of each hotel
        hotelsDotcom_hotel_data_details_info = crawl_hotelDotCom_details(hotelsDotcom_hotel_data)
                
        ## Merge table columnwise
        df1 = pd.DataFrame(hotelsDotcom_hotel_data)
        df2 = pd.DataFrame(hotelsDotcom_hotel_data_details_info)
        result = pd.concat([df1,df2], axis=1)
        result.columns = [ "country", "city", "name", "url", "sold", "room_avail", "price","client_rating" , "address", "checkin",
                          "checkout", "room_total", "star_rating", "hotelID","Type","createDate","website","group_code"]
        
        t1 = result[["group_code", "website", "hotelID", "country", "city", u"name", "star_rating", "Type", u"address", "room_total", "checkin", "checkout"]]
        t2 = result[["hotelID","website", "country", "city", "createDate", "client_rating", "price", "room_avail", "sold"]]
        

        hotel_info_table    = t1.to_json(orient="values", force_ascii=False)
        hotel_daily_table   = t2.to_json(orient="values", force_ascii=False)
        

        hotel_info_file = "hotel_info_02_" + city_code + ".json"
        with open(hotel_info_file, "w", encoding="utf-8") as file:
            file.write(hotel_info_table)

        #print("tb_hotel_info?" + hotel_info_table)
        print("tb_hotel_daily?" + hotel_daily_table)

 

    # ## result to Json
    # return t1.to_json(orient="values", force_ascii=False), t2.to_json(orient="values", force_ascii=False)

    # ## Or Save as Json
    #with open(hotel_info_file, "w", encoding="utf-8") as file:
    #     result.to_json(file, orient="values", force_ascii=False)


############################################################################
##----------------------------------------------------------------------- ##
## CLIENT                                                                 ##
##----------------------------------------------------------------------- ##
############################################################################

if __name__ == "__main__":
    #	target_destinations = ["서울", "강원도", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기도", "충청북도", "충청남도", "전라북도","전라남도","경상북도", "경상남도", "제주도", "마카오"]
    # target_destinations = ["806258"]  #   마카오 destination-id값

    #시작 시간
    # startTime = datetime.datetime.now()
    # print("시작시간")
    # print(startTime)                
    
    main()
    
    # endTime = datetime.datetime.now()
    # print("종료시간")
    # print(endTime)

    # print("구동 시간")
    # processingTime = str(endTime - startTime)
    # print(processingTime)

    # hotel_info_table : [["country", "city", "name", "Type", "address", "room_total", "checkin", "checkout"]]
    # hotel_daily_table : [["rating", "price", "room_available", "isSoldOut"]]


    # ## Or Save as Json
    #with open("hotel_info_table.json", "w", encoding="utf-8") as file:
    #     file.write(hotel_info_table)
    #with open("hotel_daily_table.json", "w", encoding="utf-8") as file:
    #     file.write(hotel_daily_table)
