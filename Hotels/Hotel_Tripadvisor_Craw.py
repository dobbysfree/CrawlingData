import os
import shutil
import sys
import zipfile
import re
import time
import pandas as pd
import datetime  # 임시 삽입

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
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

        self.driver = webdriver.Chrome(chrome_options=chrome_options)

    def __del__(self):
        self.driver.close()

    def click_css_selector(self, css_selector, wait=10):
        if wait != 0:
            WebDriverWait(self.driver, wait).until(
                expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
        self.driver.find_element_by_css_selector(css_selector).click()

    def find_css_selector(self, css_selector, wait=5):
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
# For tripAdvisor page                                                        #
# -------------------------------------------------------------------------#

class tripAdvisor_automation(Automation):
    url = None  # url for the homepage
    baseUrl = None  # search_destination후의 baseUrl

    def search_destination(self, keyword):

        url = "https://www.tripadvisor.co.kr/"
        self.driver.get(url)
        self.baseUrl = self.driver.current_url[:-1]
        #   여행지 값 전송
        destination = self.driver.find_element_by_class_name('typeahead_input')
        destination.clear()
        destination.send_keys(keyword)
        #   CheckIn 날짜 선택
        checkIn_blank = self.driver.find_element_by_xpath(
            '//*[@id="taplc_trip_search_home_default_0"]/div[2]/div[2]/div/span[1]/span[2]/span')
        checkIn_blank.click()
        checkIn_cal = self.find_css_selector(
            'div.dsdc-months-holder.showBorder > div > span > span.dsdc-cell.dsdc-day.dsdc-today')
        try:
            self.driver.execute_script("arguments[0].click();", checkIn_cal)
        except Exception:
            checkIn_cal.click()

        # CheckOut 날짜 선택
        checkOut_cal = self.find_css_selector(
            'div.dsdc-months-holder.showBorder > div > span > span.dsdc-cell.dsdc-day.dsdc-endrange')
        try:
            self.driver.execute_script("arguments[0].click();", checkOut_cal)
        except Exception:
            checkOut_cal.click()
        time.sleep(0.5)
        #   검색 버튼 클릭
        element = self.driver.find_element_by_xpath('// *[ @ id = "SUBMIT_HOTELS"]')
        element.click()

    def get_all_hotels_pagination(self, city_code):
        data = []
        flag = True
        loadingWhiteBox = True
        tooManyReloading = 0
        while flag:
            try:
                # 정상 로딩 박스 출현 시 검사
                waitFlag = self.driver.find_element_by_id('taplc_hotels_loading_box_0').get_attribute('style')
                # 로딩 창이 안 뜨면 페이지 재로딩
                if waitFlag == '':
                    link = self.driver.find_element_by_css_selector('head > link[hreflang=ko]').get_attribute('href')
                    self.driver.get(link)
                    waitFlag = "URL Reloading"
                    if (tooManyReloading == 10):
                        time.sleep(10)
                        waitFlag = "display: none;"
                    tooManyReloading += 1
            except Exception:
                # 정상 로딩 박스가 출현하지 않았을 때
                try:
                    self.driver.find_element_by_css_selector('div.hacLoadingBox')
                    # self.driver.find_element_by_css_selector('div.loadingWhiteBox')
                    waitFlag = "another loadingBox Exist"
                    loadingWhiteBox = False
                except TimeoutException:
                    waitFlag = "another loadingBox - TimeEX"
                except NoSuchElementException:
                    waitFlag = "another loadingBox - NoSuch"
                    if loadingWhiteBox is False:
                        time.sleep(5)
                        waitFlag = "display: none;"
            try:
                self.driver.find_element_by_css_selector('div.metaListingWrapper')
                self.find_css_selector('div.metaListingWrapper > div > div.listing')

                # print("sponsoredHeadingTag")
                time.sleep(3)
                waitFlag = "display: none;"
            except TimeoutException:
                pass
            except NoSuchElementException:
                pass
            # print(waitFlag)

            if waitFlag == "display: none;":
                time.sleep(5)
                data.extend(self.getHotels_from_searchPage(city_code))
                #   다음 페이지로 넘기기
                try:
                    try:
                        nextButton = self.driver.find_element_by_css_selector('span.nav.next.taLnk.ui_button.primary')
                    except NoSuchElementException:
                        try:
                            self.driver.find_element_by_css_selector('span.nav.next.ui_button.disabled')
                            flag = False
                        except NoSuchElementException:
                            nextButton = self.driver.find_element_by_css_selector('a.nav.next.taLnk.ui_button.primary')
                        # 클릭시 오류 나는 거 두개 코드로 해결
                    try:
                        self.driver.execute_script("arguments[0].click();", nextButton)
                    except Exception:
                        try:
                            nextButton.click()
                        except Exception:
                            pass
                except NoSuchElementException:
                    flag = False

        data = set(data)  # prevent duplicates
        return list(data)

    def getHotels_from_searchPage(self, city_code):
        # 도시, 국가 정보 가져오기
        temp = []
        hotel = self.driver.find_elements_by_class_name("listing")

        # cityName = self.driver.find_element_by_css_selector("#taplc_trip_planner_breadcrumbs_0 > ul > li:nth-child(2) > a > span").text
        # countryName = self.driver.find_element_by_css_selector("#taplc_trip_planner_breadcrumbs_0 > ul > li:nth-child(3) > a > span").text
        destinationName = self.driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").get_attribute("value")
        countryName = destinationName.split(",")[1].lstrip()  # (도시, 국가)
        if countryName == "대한민국":
            countryName = "82"
        elif countryName == "중국":  # 마카오는 (중국, 마카오)로 되어있어서 임의로 삽입함
            countryName = "853"
        destinationName = (countryName, city_code)
        destinationName = tuple(destinationName)  # (도시, 국가)

        # print(destinationName)
        # print((len(hotel)))

        # 개별 숙소 정보 가져오기
        i = 0
        for i in range(len(hotel)):
            h = hotel[i]
            try:
                try:
                    hName = h.find_element_by_css_selector('div.ui_column.is-narrow.title_wrap').text  # 스폰서 태그
                except Exception:
                    hName = h.find_element_by_css_selector('div.listing_title').text  # 숙소 이름
            except Exception:
                hName = ""
            # print(hName)
            try:
                try:
                    hUrl = h.find_element_by_css_selector('div.ui_column.is-narrow.title_wrap > a').get_attribute(
                        'href')  # 숙소 링크(스폰서 태그)
                except Exception:
                    hUrl = h.find_element_by_css_selector('div.listing_title > a').get_attribute("href")  # 숙소 링크
            except Exception:
                hUrl = ""
            # print(hUrl)
            #   isSoldOut(매진여부), 가격 추출
            isSoldOut ="N"
            try:
                try:
                    hotelPrice = re.findall("[0-9,0-9]+", h.find_element(By.CSS_SELECTOR, "div.price> span").text)[0]  # 1박 최저 가격
                except NoSuchElementException:
                    hotelPrice = re.findall("[0-9,0-9]+", h.find_element(By.CSS_SELECTOR, "div.price-wrap > div").text)[0]  # 1박 최저 가격
            except Exception:
                hotelPrice = ""
                isSoldOut="Y"
            # print(hotelPrice)
            if hUrl != "":
                temp.append(destinationName + (hName, hUrl, hotelPrice, isSoldOut))

        return temp

    @staticmethod
    def update_hotel_details(session, hUrl):
        from datetime import datetime

        req = session.get(hUrl)
        html = req.text
        soup = BeautifulSoup(html, "html.parser")
        print(hUrl)  ######################################### Hotel 세부정보 크롤링되는 여부(임시 삽입 -> 확인하고 삭제)
        #   고객 평점 추출
        try:
            clientRating = re.findall('ratingValue".*:.*"\d.\d"', soup.text, re.MULTILINE)[0]
            clientRating = str(clientRating).split('"')[2]
        except IndexError:
            clientRating = ""
        #   호텔 주소 추출
        try:
            address = re.findall('streetAddress".*:.*"[^s]*"', soup.text, re.MULTILINE)[0]
            address = str(address).split('"')[2]
            # address = address[1:-1]
        except IndexError:
            address = ""
        #   총 객실 수 추출
        try:
            Room_num = re.findall('객실 수\d*', soup.text, re.MULTILINE)[0]
            Room_num = Room_num[4:]
        except AttributeError:
            Room_num = ""
        except IndexError:
            Room_num = ""
        #   숙소 N성급 추출
        try:
            try:
                starRating = re.findall("'HotelRating',.'\d.\d'", soup.text, re.MULTILINE)[0]
                starRating = str(starRating).split(",")[1].lstrip()
                starRating = starRating[1:-1]
            except IndexError:
                starRating = re.findall('star.*"[0-9]"', soup.text, re.MULTILINE)[0]
                starRating = re.findall('[0-9]+', starRating)[0]
        except IndexError:
            starRating = ""
        #   숙소 유형
        try:
            try:
                hType = re.findall("'HotelType',\s*'[A-Z][a-z]*", soup.text, re.MULTILINE)[0]
                hType = str(hType).split(",")[1].lstrip()
                hType = hType[1:]
            except IndexError:
                hType = re.findall("HotelType\W*\w*\W*\w*\s*\w*\W", soup.text, re.MULTILINE)[0]
                hType = str(hType).split("\n")[2]
                hType = hType[4:-1]
        except IndexError:
            hType = ""

        if hType == "Hotel" or hType == "Boutique" or hType == "Small" or hType == "Small Hotel" or hType == "Boutique Hotel":
            hType = "1"  # 호텔
        elif hType == "Resort":
            hType = "2"  # 리조트
        elif hType == "Motel":
            hType = "3"  # 모텔
        elif hType == "Guest" or hType == "Guest house":
            hType = "4"  # 게스트 하우스
        elif hType == "Apartment" or "Apartment Hotel":
            hType = "6"  # 레지던스
        # elif hType == "Hostel" or hType == "Condominium" or  hType == "Specialty Hotel" or  hType == "Lodge" or hType == "Onsen" or \
        #     hType == "Onsen Hotel" or hType == "Spa" or hType == "Specialty"or hType == "Specialty Hotel":
        #     hType = "9"
        else:
            hType = "9"

        hotelId = soup.find('div', {'class': 'blRow'})
        hotelId = hotelId.get('data-locid')

        # 트립어드바이저에서는 남는 방수, 체크인, 체크아웃시간, 연락처 정보 제공 안함
        rem_room = ""
        CheckIn = ""
        CheckOut = ""

        # 생성일자, 웹사이트 코드, 그룹 코드
        createDate = datetime.now().strftime("%Y-%m-%d")
        website_code = "05"
        group_code = "00001"

        return rem_room, clientRating, address, hotelId, CheckIn, CheckOut, Room_num, starRating, hType, createDate, website_code, group_code


def crawl_tripAdvisor(destination, city_code):
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    option.add_argument('headless')
    option.add_argument("disable-gpu")

    option.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")

    hotel_data = []  ## [(도시, 국가, 숙소이름, 숙소링크), ...]
    # for keyword in destinations:
    tripAdvisor = tripAdvisor_automation(option)
    tripAdvisor.search_destination(destination)
    result = tripAdvisor.get_all_hotels_pagination(city_code)
    hotel_data.extend(result)
    time.sleep(1)  # time for closing webdriver
    hotel_data = set(hotel_data)  # remove duplicates

    return list(hotel_data)


def crawl_tripAdvisor_details(hotel_data):
    hotel_data_specific = []  ## [(CheckIn , CheckOut, Room_num, address, isSoldOut, starRating, reviewCount, hType), ...]

    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=10)
    sess.mount("http://", adapter)
    for hotel in hotel_data:
        if hotel[3] is not '':
            temp = tripAdvisor_automation.update_hotel_details(sess, hotel[3])
            hotel_data_specific.append(temp)

    return hotel_data_specific


def main():
    ## Crawl Hotel.com hotel list
    target_destinations = ["서울", "부산", "인천", "대전", "대구", "광주", "울산", "경기도", "충청북도", "충청남도", "강원도", "전라북도", "전라남도",
                           "경상북도", "경상남도", "제주도", "마카오"]
    city_codes = ["10", "60", "40", "30", "70", "50", "68", "41", "36", "31", "20", "56", "51", "71", "62", "69", ""]
    # target_destinations = ["경기도"]
    # city_codes = ["40"]

    i = 0
    for i in range(len(target_destinations)):
        destination = target_destinations[i]
        city_code = city_codes[i]
        tripAdvisor_hotel_data = crawl_tripAdvisor(destination, city_code)

        ## For connection log
        import logging
        logging.basicConfig()
        # logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        ## Update Details of each hotel
        tripAdvisor_hotel_data_details_info = crawl_tripAdvisor_details(tripAdvisor_hotel_data)

        ## Merge table columnwise
        df1 = pd.DataFrame(tripAdvisor_hotel_data)
        df2 = pd.DataFrame(tripAdvisor_hotel_data_details_info)
        result = pd.concat([df1, df2], axis=1)
        result.columns = ["country", "city", "name", "url", "price", "sold", "room_avail", "client_rating", "address",
                          "hotelID", "checkin", "checkout", "room_total", "star_rating", "Type", "createDate",
                          "website", "group_code"]
        t1 = result[["group_code", "website", "hotelID", "country", "city", "name", "star_rating", "Type", "address",
                     "room_total", "checkin", "checkout"]]
        t2 = result[
            ["hotelID", "website", "country", "city", "createDate", "client_rating", "price", "room_avail", "sold"]]

        hotel_info_table = t1.to_json(orient="values", force_ascii=False)
        hotel_daily_table = t2.to_json(orient="values", force_ascii=False)

        hotel_info_file = "hotel_info_04_" + city_code + ".json"
        with open(hotel_info_file, "w", encoding="utf-8") as file:
            file.write(hotel_info_table)

        # print(hotel_info_table)
        print("tb_hotel_daily?" + hotel_daily_table)

    ## result to Json
    # return t1.to_json(orient="values", force_ascii=False), t2.to_json(orient="values", force_ascii=False)

    # ## Or Save as Json
    # with open(hotel_info_file, "w", encoding="utf-8") as file:
    #     result.to_json(file, orient="values", force_ascii=False)


############################################################################
##----------------------------------------------------------------------- ##
## CLIENT                                                                 ##
##----------------------------------------------------------------------- ##
############################################################################

if __name__ == "__main__":
    # target_destinations = ["서울","부산", "인천", "대전", "대구","광주", "울산", "경기도", "충청북도", "충청남도","강원도" ,"전라북도", "전라남도","경상북도", "경상남도", "제주도"]
    # 시작 시간
    # startTime = datetime.datetime.now()
    # print("시작시간")
    # print(startTime)

    main()

    # endTime = datetime.datetime.now()
    # print("종료시간")
    # print(endTime)
    # #
    # print("구동 시간")
    # processingTime = str(endTime - startTime)
    # print(processingTime)

    # hotel_info_table, hotel_daily_table = main(target_destinations)

    # target_destinations = ["g294197", "g297884", "g297889", "g297887", "g297886", "g304129", "g297893", "g1072089", "g2023524", "g1072096",
    #                        "g1072105", "g2023520", "g1072086", "g2023521", "g1072104", "g983296"]

    # target_destinations = ["경기도","충청북도"]

    # hotel_info_table : [["country", "city", "name", "Type", "address", "room_total", "checkin", "checkout"]]
    # hotel_daily_table : [["rating", "price", "room_available", "isSoldOut"]]

    # # ## Or Save as Json
    # with open("hotel_info_table.json", "w", encoding="utf-8") as file:
    #     file.write(hotel_info_table)
    # with open("hotel_daily_table.json", "w", encoding="utf-8") as file:
    #     file.write(hotel_daily_table)
    # 종료 시간
