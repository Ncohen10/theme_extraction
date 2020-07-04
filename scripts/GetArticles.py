import csv
import mediacloud.api
import datetime as dt
import time
import random
from newspaper import Article, ArticleException
from typing import List, Mapping


class GetText:

    """
    Usable text will be less than max_article_amount generally. Use a higher number than you actually want files written.

    """

    def __init__(self):
        self.mc = mediacloud.api.MediaCloud("1f0bd16c9099d90e518ef4d5616a44c93c46330f8065d3c2e1f9cdefe0b093fb")
        # self.keywords = '(ferguson OR "michael brown" OR "mike brown" OR blacklivesmatter OR "black lives" OR blm OR alllivesmatter OR whitelivesmatter OR bluelivesmatter OR "eric garner" OR ericgarner OR "freddie gray" OR freddiegray OR "walter scott" OR walterscott OR "tamir rice" OR tamirrice OR "black lives matter" OR "john crawford" OR johncrawford OR "tony robinson" OR tonyrobinson OR "eric harris" OR ericharris OR "ezell ford" OR ezellford OR "akai gurley" OR akaigurley OR "kajieme powell" OR kajiemepowell OR "tanisha anderson" OR tanishaanderson OR "victor white" OR victorwhite OR "jordan baker" OR jordanbaker OR "jerame reid" OR jeramereid OR "yvette smith" OR yvettesmith OR "phillip white" OR philipwhite OR "dante parker" OR danteparker OR "mckenzie cochran" OR mckenziecochran OR "tyree woodson" OR tyreewoodson)'
        self.keywords = '"black lives matter"'
        self.urls = []
        self.start_date = dt.date(2014, 1, 1)  # for API
        self.end_date = dt.date(2020, 6, 22)   # for API
        self.csv_location = "../data/blm/blm-all-story-urls.csv"


    # NOT USED - API
    def article_count(self) -> int:
        date_range = self.mc.dates_as_query_clause(self.start_date, self.end_date)  # default is start & end inclusive
        res = self.mc.storyCount(self.keywords,
                                 date_range)  # "publish_date:[2014-01-01T00:00:00Z TO 2020-06-06T00:00:00Z]")
        return res["count"]  # Get the articles that match keywords/dates

    # NOT USED - API
    def get_article_data_from_api(self, max_article_amount, fetch_size=1000):
        # most amount of articles per query is 1000
        article_data = []
        new_id = 0
        print("fetching article data from media cloud")
        # run until either all stories are gotten or "max_articles" number of articles are found
        while len(article_data) < max_article_amount:
            # Make the API request
            time.sleep(.5)
            old_id = new_id
            fetched_stories = self.mc.storyList(self.keywords, rows=fetch_size,
                                                solr_filter="publish_date:[2014-01-01T00:00:00Z TO 2020-06-20T00:00:00Z]",
                                                last_processed_stories_id=new_id,  # continue from the last article
                                                )
            article_data.extend(fetched_stories)
            new_id = article_data[-1]["processed_stories_id"]  # set the last article
            if new_id == old_id:
                break
        return article_data

    # NOT USED - API
    @staticmethod
    def get_urls_from_api_data(article_info):
        print("getting urls")
        urls = []
        for data in article_info:
            url = data["url"]
            if url:
                urls.append(url)
        return urls

    def get_urls_from_csv(self, max_urls_to_get):
        print("Getting urls from CSV file.")
        urls = []
        url_count = 0
        with open(self.csv_location, encoding="utf-8") as csv_file:
            reader = list(csv.reader(csv_file, delimiter=','))
            # Get files randomly since they are stored in chronological order
            random.shuffle(reader)
            for line in reader:
                urls.append(line[3])
                url_count += 1
                if url_count == max_urls_to_get:
                    break
        print("{} urls were retrieved".format(len(urls)))
        return urls

    # returns mapping of article url->text from url
    def url_to_newspaper_text(self, urls: List[str], max_article_amount) -> Mapping[str, str]:
        url_to_text = {}
        article_count = 0
        print("getting text from urls")
        for url in urls:
            time.sleep(.5)
            article = Article(url)
            if article_count % 100 == 0:
                print("{} articles retrieved so far.".format(article_count))
            if article_count == max_article_amount:
                print("retrieved {} article texts".format(len(url_to_text)))
                break
            try:
                # get and parse article using newspaper
                article.download()
                article.parse()
                article_text = article.text
                # map each url to the text that comes from it.
                # lowers chance of duplicate articles occurring as well perhaps?
                url_to_text[url] = article_text
                article_count += 1
            # if error with newspaper library or unable to access article from url, continue with iteration.
            # UnicodeError is thrown with a few of the URLs as well.
            # I think UnicodeError happens when the hostname part of the url is greater 64 characters.
            except (ArticleException, AttributeError, UnicodeError) as e:
                # print(e)
                continue
        print("retrieved {} article texts".format(len(url_to_text)))
        return url_to_text

    # writes each text to a separate file.
    @staticmethod
    def write_text_to_file(url_text_mapping: Mapping[str, str], max_file_amount=10000) -> None:
        print("writing text to file")
        files_written = 0
        # url_text_mapping is mapping of url->text from url
        for url in url_text_mapping:
            text = url_text_mapping[url]
            # ignore blank/small text or pages that require signing in to google
            if len(text) < 61:
                continue
            if max_file_amount == files_written:
                break
            # files are written in format (text0, text1, ... , textn)
            text_directory = "../data/article_texts/text" + str(files_written)
            with open(text_directory, 'w', encoding="utf-8") as f:
                # write url followed by the text from it.
                f.write("Text retrieved from: " + url + '\n')
                f.write(text)
            files_written += 1
        print("Done. {} texts have been written to files.".format(files_written))

if __name__ == '__main__':
    fetcher = GetText()
    url_list = fetcher.get_urls_from_csv(max_urls_to_get=5)
    article_texts = fetcher.url_to_newspaper_text(url_list, max_article_amount=5)
    fetcher.write_text_to_file(article_texts)
