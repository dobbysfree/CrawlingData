import pandas as pd

from pytrends.request import TrendReq
from datetime import datetime
from datetime import timedelta

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
            US : United States of America
            KR : Republic of Korea
    
    [tz]: timezone offset, default US CST '360'
    
    [gprop]: What Google property to filter to, default to web searches
            images, news, youtube, froogle
    
    [base_path]: directory to save the csv file,
        warning! path delimiter should be "/"

    for further information, refer pytrends official document 
        https://github.com/GeneralMills/pytrends#trending_searches
"""

def get_py_trends(query_date, keywords, hl='en-US', tz=360, geo='', gprop=''):

    pytrends = TrendReq(hl=hl, tz=tz)

    date1, date2 = query_date.split(" ")
    date1 = datetime.strptime(date1, "%Y-%m-%d")
    date2 = datetime.strptime(date2, "%Y-%m-%d")
    time_delta = date2 - date1
    query_iter = time_delta.days // 1800 + 1
    start_date = date1
    end_date = date2

    res = None

    for i in range(query_iter):

        end_date = start_date + timedelta(days=1800)
        if i == query_iter-1:
            end_date = date2

        timeframe = "{}-{}-{} {}-{}-{}".format(start_date.year, start_date.month, start_date.day, end_date.year, end_date.month, end_date.day)
        print("Downloading... ", timeframe)  # DEBUG
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop=gprop)

        #
        if res is not None:
            res = res.append(pytrends.interest_over_time())
        else:
            res = pytrends.interest_over_time()

        start_date = end_date + timedelta(days=1)

    res = pd.DataFrame(res.iloc[:, :-1])

    return res

    # save


def main(query_date, keywords, hl='en-US', tz=360, geo='', gprop='', base_path="C:/"):

    res = None

    for kw in keywords:
        kw_list = [kw]
        print("Retrieving keyword: ", kw)
        if res is None:
            res = get_py_trends(query_date=query_date, keywords=kw_list, hl=hl, tz=tz, geo=geo, gprop=gprop)
        else:
            res = pd.concat([res, get_py_trends(query_date=query_date, keywords=kw_list, hl=hl, tz=tz, geo=geo, gprop=gprop)], axis=1)

    file_path = base_path + "/result.csv"
    res.to_csv(path_or_buf=file_path, index=True, index_label="date", encoding="utf-8", date_format="%m/%d/%Y")


if __name__ == "__main__":
    with open("NASDAQ100_ENG.txt", "r", encoding="utf-8") as f:
        kw_list = f.readlines()
    main(query_date="2018-03-21 2018-03-28", keywords=kw_list, hl='en-US', tz=360, geo='', gprop='', base_path="C:\\Users\\Qraft\\Documents")