import tweepy
import pyautogui
import time

"""

(api.search의 인자)
q = keyword
lang = 언어설정
since <= 원하는 날짜 < until
geocode = "latitide, logitude, radius"

(정보 추출)
.created_at : 작성시간
.text : 작성 내용
.retweet_count : 리트윗 횟수
.favorite_count : 좋아요 개수
.source : 트윗이 작성된 곳

"""

class TwitterCrawler():
    def __init__(self):
        # 인증요청 : 개인 앱 정보
        consumer_key = ""
        consumer_secret = ""
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        # access 토큰 요청
        access_token = ""
        access_token_secret = ""
        auth.set_access_token(access_token, access_token_secret)
        # twitter API 생성
        api = tweepy.API(auth, wait_on_rate_limit=True)
        return api


    ## ip 변경 매크로
    def change_ip(self):
        pyautogui.moveTo(170, 1056)
        pyautogui.click()
        pyautogui.moveTo(143, 50)
        pyautogui.click()
        time.sleep(4)
        pyautogui.moveTo(74, 1005)
        pyautogui.click()
        time.sleep(1)


    def get_count(self, api):
        with open("NASDAQ100_ENG.txt", "r", encoding="utf-16") as f:
            keywords = f.readlines()
        cnt = 0
        for key in keywords:
            for tweet in tweepy.Cursor(api.search, q=key, since="2018-05-02", until="2018-05-03").items():
                cnt += 1
                if cnt % 2000 == 0:
                    time.sleep(1)
                    print("#######ip 변경########")
                    change_ip()
                print(cnt)

            print("\n\n=====", key, " : ", cnt, " =====\n\n")
        f.close()


if __name__ == "__main__":
    crawler = TwitterCrawler()
    crawler.get_count(crawler)

