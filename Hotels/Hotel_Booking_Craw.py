# -*- coding:utf-8 -*-
import os
import shutil
import sys
import zipfile
import re
import time
import pandas as pd
import json
from operator import eq

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
# WebdriverWait 기능이 포함된 선택자 등등..                               #
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


class booking_automation(Automation):
    url = None  # url for the homepage
    baseUrl = None  # booking_main_search 후의 baseUrl

    def booking_main_search(self, destination):         # 메인화면에서 지역 검색
        from datetime import datetime, timedelta
        start = datetime.now().strftime("%Y.%m.%d")
        end = (datetime.strptime(start, "%Y.%m.%d") + timedelta(days=1)).strftime("%Y.%m.%d")
        startDate = start.split('.')
        endDate = end.split('.')

        # 부킹닷컴 기본 주소에 검색 지역명, 검색날짜 추가
        url = "https://www.booking.com/searchresults.ko.html?&publicholiday=0&ss=%s&checkin_year=%s&checkin_month=%s&checkin_monthday=%s&checkout_year=%s&checkout_month=%s&checkout_monthday=%s&group_adults=2&group_children=0&no_rooms=1&from_sf=1&offset=" \
               % (destination, startDate[0], startDate[1], startDate[2], endDate[0], endDate[1], endDate[2])

        url += "="
        self.driver.get(url)    # 검색된 첫 결과 화면 띄위기
        self.baseUrl = self.driver.current_url[:-1]

        return url

    def booking_hotels(self, url, stat_code):      # 페이지 이동
        data = []
        flag = True
        while flag:
            try:
                temp = self.booking_get_hotels(url, stat_code)      # 지역명으로 검색된 호텔 리스트들에서 현재 페이지의 호텔 정보들 가져오기
                data.extend(temp)
            except TimeoutException:
                return None
            try:
                self.driver.get(self.driver.find_element_by_css_selector("a.paging-next").get_attribute("href"))  # 다음 페이지 버튼이 존재한다면 다음 페이지로 이동한다
            except NoSuchElementException:      # 존재하지 않는다면,
                try:
                    if self.driver.find_element_by_class_name("paging-end") is not None:  # 해당 지역 마지막 페이지 버튼이 존재한다면 해당 지역 리스트 검색을 끝낸다
                        flag = False
                except NoSuchElementException:
                    try:        # 마지막 페이지가 아닌데 다음페이지 버튼이 존재하지 않는 경우
                        url = self.driver.find_element_by_xpath("//*[@id=\"disambBlock_region\"]/div[2]/div/div[3]/a").get_attribute("href")        # 경상북도, 남도 예외처리
                        self.driver.get(url)
                    except NoSuchElementException:
                        try:
                            url = self.driver.find_element_by_css_selector("disambBlock_city.div.cityWrapper.div.div.disname.div.a").get_attribute("href")      # 인천 예외처리
                            self.driver.get(url)
                        except NoSuchElementException:
                            try:
                                url = self.driver.find_element_by_xpath("//*[@id=\"disambBlock_city\"]/div[2]/div/div[2]/div/a").get_attribute("href")      # 세종시 예외처리
                                self.driver.get(url)
                            except NoSuchElementException:
                                break
                    except:
                        break
            except TimeoutException:        # 사이트 로딩에서 timeout exception 걸린다면, webdriver 종료
                flag = False
                self.driver.close()

        return list(data)

    def booking_get_hotels(self, url, stat_code):      # 호텔리스트에서 리스트 내 호텔별 info 가져옴
        temp = []
        hotel = self.driver.find_elements_by_css_selector("div.sr_item.sr_item_new.sr_item_default.sr_property_block.sr_flex_layout")       # 하나의 호텔을 감싸는 css 들을 찾을 것
        group_code = "00001"        # 호텔 그룹코드
        web_code = "03"             # 부킹닷컴 사이트 코드
        country_code = ""
        date = datetime.now().strftime('%Y-%m-%d')      # 현재 날짜
        try:
            try:
                response = requests.get(self.driver.find_element_by_css_selector("a.hotel_name_link.url").get_attribute("href"))        # 각 호텔들 세부 정보페이지 html 가져오기
                html = response.text
            except:
                response = requests.get(url)
                html = response.text

            soup = BeautifulSoup(html, "html.parser")       # html 파싱

            parser = re.compile('window.utag_data = ({.*?});', re.DOTALL)       # 검색된 페이지의 지역명과 국가명 찾기
            matched = parser.search(soup.text)
            if matched:
                json_string = matched.group(0)
                clean_string = json_string.split(' = ')[1].replace('\'', '\"').replace(';', "").replace(':', '\":').replace("\n", "\"").replace("\"}", "}")
                utag_data_json = json.loads(clean_string)
                country = utag_data_json.get('country_name')        # 국가명
                country = country.strip()
                if country == "대한민국":
                    country_code = "82"
                elif country == "마카오":
                    country_code = "853"
        except TypeError:
            country_code = ""
        except NoSuchElementException:
            return temp
        except:
            country_code = ""

        i = 0
        # 숙소 정보 가져오기
        for h in hotel:
            hName = ""
            hId = ""
            hUrl = ""
            try:
                hName = h.find_element_by_css_selector("span.sr-hotel__name").text  # 숙소 이름
                hUrl = h.find_element_by_css_selector("a.hotel_name_link.url").get_attribute("href")  # 숙소 링크
                try:  # 호텔 Id
                    hId = h.find_element_by_css_selector("div.sr_item_photo").get_attribute("id")
                    hId = re.findall("\d+", hId)[0]     # 호텔 아이디 값만 파싱
                except NoSuchElementException:
                    hId = "0000001"     # 부킹닷컴 내 호텔 아이디 값 없을시 0000001 설정
            except NoSuchElementException:
                pass

            try:        # 가격 정보 파싱
                hprice = re.findall("[0-9,0-9]+", h.find_element_by_css_selector("strong.price").text)[0]
            except NoSuchElementException:
                hprice = ""

            rem_room = ""  # booking.com 에서 확인하기 어려움(전체 잔여 객실 수 아님)

            # 매진 여부
            if h.find_elements_by_class_name("sold_out_property"):
                isSoldOut = "Y"
            else:
                isSoldOut = "N"

            hInfo_temp = group_code, web_code, hId, country_code, stat_code, hName, hUrl, hprice, isSoldOut, rem_room, date
            temp.append(hInfo_temp)
            i += 1

        return temp

    def booking_get_hotel_details(html):        # 호텔별 세부페이지에서 daily 정보 가져옴
        soup = BeautifulSoup(html, "html.parser")

        p = re.compile(':', re.DOTALL)

        # 체크인, 체크아웃 정보
        try:
            CheckIn = ""
            CheckOut = ""
            CheckHour = soup.find_all("span", class_="u-display-block")
            tmp_check = []
            i = -1
            for ch in CheckHour:
                try:
                    ch = ch.text.strip()
                    matched = p.search(ch)
                    if matched:
                        i += 1
                        tmp_check.insert(i, ch)
                except IndexError:
                    pass

            tmp_check = list(filter(None, tmp_check))
            CheckIn = tmp_check[0:1]
            CheckIn = CheckIn.pop(0)
            CheckOut = tmp_check[1:2]
            CheckOut = CheckOut.pop(0)
        except TypeError:
            pass
        except IndexError:
            pass

        # 주소 정보
        try:
            addr = soup.select("span.hp_address_subtitle.js-hp_address_subtitle.jq_tooltip")[0].text
            addr = addr.strip()
        except:
            addr = ""
        # 부킹닷컴 내 평점 정보
        try:
            score = soup.select("p.review_score_value")[0].text
        except NoSuchElementException:
            score = ""
        except:
            score = ""

        # 호텔 성급 정보
        try:
            starRating = soup.find("hotel_class$", soup.text)
            if starRating is None:
                starRating = ""
        except:
            starRating = ""

        # 숙소 유형
        parser = re.compile('window.utag_data = ({.*?});', re.DOTALL)
        matched = parser.search(soup.text)
        try:
            if matched:
                json_string = matched.group(0)
                clean_string = json_string.split(' = ')[1].replace('\'', '\"').replace(';', "").replace(':', '\":').replace("\n", "\"").replace("\"}", "}")
                utag_data_json = json.loads(clean_string)
                hType = utag_data_json.get('atnm')
        except:
            hType = ""

        if hType == "호텔":
            hType = "1"
        elif hType == "콘도" or hType == "리조트":
            hType = "2"
        elif hType == "모텔":
            hType = "3"
        elif hType == "게스트하우스" or hType == "게스트 하우스":
            hType = "4"
        elif hType == "펜션":
            hType = "5"
        elif hType == "레지던스":
            hType = "6"
        else:
            hType = "9"

        return score, addr, CheckIn, CheckOut, starRating, hType


def booking_hotels_detail(b_hotel_data):        # 각 호텔 세부 페이지로 이동
    b_hotel_data_detail = []
    temp = []
    for b_hotel in b_hotel_data:
        try:
            response = requests.get(b_hotel[6])     # 각 호텔별 세부 페이지 링크 통해 html 가져오기
            html = response.text
            temp = booking_automation.booking_get_hotel_details(html)       # 호텔별 정보 가져오기
            b_hotel_data_detail.append(temp)
        except:
            # 실패시 (ex. 유효하지 않는 링크) 예외처리
            temp = ["", "", "", "", "", ""]
            b_hotel_data_detail.append(temp)
    return b_hotel_data_detail


def selection_sort(temp_data):      # 부킹닷컴 검색 리스트 내 중복 호텔 제거
    for i in range(len(temp_data) - 1):
        for j in range(i + 1, len(temp_data)):
            if eq(temp_data[i][5], temp_data[j][5]) is True:  # 이름으로 비교
                if eq(temp_data[i][2], temp_data[j][2]) is True:  # 호텔 ID로 비교
                    temp_data.pop(j)
                    break
    return temp_data


def main(destinations, code):
    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")  # open as incognito mode(시크릿모드)
    hotel_data = []
    fail_arr = []
    fail_tmp = []
    booking = booking_automation(option)
    i = 0
    # each destination & hotels in page
    for keyword in destinations:
        hotel_data = []
        url = booking.booking_main_search(keyword)                      # 메인화면에서 각 지역별 검색
        res = booking.booking_hotels(url, code[i])                  # 지역별 화면의 호텔 리스트
        hotel_data.extend(res)
        time.sleep(0.1)     # time for closing web driver
        hotel_data = list(hotel_data)

        hotel_data = selection_sort(hotel_data)  # 중복 호텔 제거
        hotel_data_detail = booking_hotels_detail(hotel_data)       # 호텔별 daily 정보 가져오기
        hotel_info_file = "hotel_info_03_" + code[i] + ".json"      # 부킹닷컴 지역별 호텔 별 info정보 파일 이름
        i += 1
        try:
            # Data Frame 생성
            df1 = pd.DataFrame(hotel_data)
            df2 = pd.DataFrame(hotel_data_detail)
            result = pd.concat([df1, df2], axis=1)      # hotel_data 와 hotel_data_detail 의 데이터 프레임들을 합침
            result.columns = ["grp_code", "site_code", "hotel_code", "country_code", "stat_code", "name", "url", "price", "isSoldOut", "rem_room", "date", "score", "addr", "checkin", "checkout", "starRating", "type"]        # 데이터프레임 컬럼 이름 설정

            # DB 필드 순서에 맞게 순서 이동
            t1 = result[["grp_code", "site_code", "hotel_code", "country_code", "stat_code", "name", "starRating", "type", "addr", "rem_room", "checkin", "checkout"]]
            t2 = result[["hotel_code", "site_code", "country_code", "stat_code", "date", "score", "price", "rem_room", "isSoldOut"]]
            # json 파일 형식으로 변환
            t1 = t1.to_json(orient="values", force_ascii=False)
            t2 = t2.to_json(orient="values", force_ascii=False)

            # 지역별 Hotel Info 파일 저장 공용소에 저장함
            file_path = os.path.join("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/", hotel_info_file)
            fid = open(file_path, "w", encoding='UTF-8')
            fid.write(t1)
            fid.close()

            # 지역별 Hotel Daily 파일 출력
            print("tb_hotel_daily?" + t2)

        except Exception as e:
            # 실패할 시 다시 검색하기 위하여 검색 실패한 지역이름과 지역코드를 저장
            fail_tmp.append(keyword)
            fail_tmp.append(stat_codes[i - 1])
            fail_arr.append(fail_tmp)
            fail_tmp = []
            pass

    # 검색 실패한 지역 성공할 때까지 재검색
    i = 0
    while len(fail_arr) != 0:
        for dest in fail_arr:
            fail_stat_code = dest[1]  # 지역코드
            dest = dest[0]  # 지역명
            hotel_data = []
            url = booking.booking_main_search(dest)  # 메인화면에서 각 지역별 검색
            res = booking.booking_hotels(url, fail_stat_code)  # 지역별 화면의 호텔 리스트
            hotel_data.extend(res)
            time.sleep(0.1)  # time for closing web driver
            hotel_data = list(hotel_data)
            hotel_data = selection_sort(hotel_data)  # 중복 호텔 제거
            hotel_data_detail = booking_hotels_detail(hotel_data)  # 호텔별 daily 정보 가져오기
            hotel_info_file = "hotel_info_03_" + fail_stat_code + ".json"
            i += 1
            try:
                df1 = pd.DataFrame(hotel_data)
                df2 = pd.DataFrame(hotel_data_detail)
                result = pd.concat([df1, df2], axis=1)
                # print(str(df2))
                result.columns = ["grp_code", "site_code", "hotel_code", "country_code", "stat_code", "name", "url", "price", "isSoldOut", "rem_room", "date", "score", "addr", "checkin", "checkout", "starRating", "type"]
                t1 = result[["grp_code", "site_code", "hotel_code", "country_code", "stat_code", "name", "starRating", "type", "addr", "rem_room", "checkin", "checkout"]]
                t2 = result[["hotel_code", "site_code", "country_code", "stat_code", "date", "score", "price", "rem_room", "isSoldOut"]]

                hotel_data = t1.to_json(orient="values", force_ascii=False)
                hotel_data_details = t2.to_json(orient="values", force_ascii=False)

                file_path = os.path.join("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/", hotel_info_file)
                fid = open(file_path, "w", encoding='UTF-8')
                fid.write(hotel_data)
                fid.close()
                print("tb_hotel_daily?" + hotel_data_details)

                fail_arr.pop(0)     # 성공시 검색 실패한 목록에서 제거

            except Exception:           # 예외가 발생했다면 다시 실행
                pass

if __name__ == "__main__":
    from datetime import datetime, timedelta

    dir_name = "hotel_info_directory"
    try:         # hotel info 정보 저장할 폴더 생성
        if not (os.path.isdir("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/")):
            os.makedirs(os.path.join("D:/0. qraft_project\DataCenter\Python_Source\Hotels/" + dir_name + "/"))
    except OSError as e:
        print("Failed to create directory!!!!!")

    # 검색할 지역과 지역코드
    target_destinations = ["서울", "강원도", "부산", "대구", "인천광역시", "광주", "대전", "울산", "세종", "경기도", "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주도", "마카오"]
    target_code = ["10", "20", "60", "70", "40", "50", "30", "68", "33", "41", "36", "31", "56", "51", "71", "62", "69", ""]
    main(target_destinations, target_code)
