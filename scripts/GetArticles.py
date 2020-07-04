import csv
import mediacloud.api
import datetime as dt
import time
import random
from newspaper import Article, ArticleException
from typing import List, Mapping


class GetArticles:
    """
    Usable text will be less than max_article_amount generally. Use a higher number than you actually want files written.

    """

    def __init__(self, max_article_amount=20000):
        self.mc = mediacloud.api.MediaCloud("MY API KEY")
        self.keywords = '(ferguson OR "michael brown" OR "mike brown" OR blacklivesmatter OR "black lives" OR blm OR alllivesmatter OR whitelivesmatter OR bluelivesmatter OR "eric garner" OR ericgarner OR "freddie gray" OR freddiegray OR "walter scott" OR walterscott OR "tamir rice" OR tamirrice OR "black lives matter" OR "john crawford" OR johncrawford OR "tony robinson" OR tonyrobinson OR "eric harris" OR ericharris OR "ezell ford" OR ezellford OR "akai gurley" OR akaigurley OR "kajieme powell" OR kajiemepowell OR "tanisha anderson" OR tanishaanderson OR "victor white" OR victorwhite OR "jordan baker" OR jordanbaker OR "jerame reid" OR jeramereid OR "yvette smith" OR yvettesmith OR "phillip white" OR philipwhite OR "dante parker" OR danteparker OR "mckenzie cochran" OR mckenziecochran OR "tyree woodson" OR tyreewoodson)'
        self.urls = []
        self.start_date = dt.date(2014, 1, 1)
        self.end_date = dt.date(2020, 6, 22)
        self.max_article_amount = max_article_amount
        self.csv_location = "../data/blm/blm-all-story-urls.csv"

    def article_count(self) -> int:
        date_range = self.mc.dates_as_query_clause(self.start_date, self.end_date)  # default is start & end inclusive
        res = self.mc.storyCount(self.keywords,
                                 date_range)  # "publish_date:[2014-01-01T00:00:00Z TO 2020-06-06T00:00:00Z]")
        return res["count"]  # Get the articles that match keywords/dates

    def get_article_data_from_api(self, max_article_amount, fetch_size=1000):
        """
        Requests data from the Mediacloud API.
        Returns a list of the data (URL, Date, Name... ETC) from each article.

        max_article_amount is number of articles to get
        fetch_size is how many articles to get with each API call

        fetch_size and max_article_amount aren't consistent with each other.
        EG: If fetch_size = 1000, and max_article_amount = 5, 1000 articles are retrieved.
        """
        article_data = []
        new_id = 0
        print("fetching article data from media cloud")
        # run until either all stories are gotten or "max_article_amount" number of articles are gotten.
        while len(article_data) < max_article_amount:
            # Make the API request
            time.sleep(.5)  # Pause script to reduce chance of us getting blacklisted for too many requests.
            fetched_stories = self.mc.storyList(self.keywords, rows=fetch_size,
                                           solr_filter="publish_date:[2014-01-01T00:00:00Z TO 2020-06-20T00:00:00Z]",
                                           last_processed_stories_id=new_id,  # continue from the last article
                                           )
            article_data.extend(fetched_stories)
            old_id = new_id  #
            new_id = article_data[-1]["processed_stories_id"]  # set a bookmark to the last article
            if new_id == old_id:  # if all articles of the given keywords have been retrieved.
                break
        return article_data

    @staticmethod
    def get_urls_from_api(article_info):
        print("getting urls")
        urls = []
        for data in article_info:
            url = data["url"]
            if url:
                urls.append(url)
        return urls

    def get_urls_from_csv(self):
        print("Getting urls from CSV file.")
        urls = []
        count = 0
        with open(self.csv_location, encoding="utf-8") as csv_file:
            reader = list(csv.reader(csv_file, delimiter=','))
            # Retrieve random file since they are stored in chronological order
            random.shuffle(reader)
            for line in reader:
                urls.append(line[3])
                count += 1
                if count == self.max_article_amount:
                    break
        print(urls)
        return urls

    # returns mapping of article url->text from url
    def url_to_newspaper_text(self, urls: List[str]) -> Mapping[str, str]:
        url_to_text = {}
        article_count = 0
        print("getting text from urls")
        for url in urls:
            time.sleep(.5)
            article = Article(url)
            if article_count % 100 == 0:
                print("{} articles retrieved so far.".format(article_count))
            if article_count == self.max_article_amount:
                print("retrieved {} article texts".format(len(url_to_text)))
                break
            print(article_count)
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
            text_directory = "./data/article-texts/text" + str(files_written)
            with open(text_directory, 'w', encoding="utf-8") as f:
                # write url followed by the text from it.
                f.write("Text retrieved from: " + url + '\n')
                f.write(text)
            files_written += 1
        print("Done. {} texts have been written to files.".format(files_written))



if __name__ == '__main__':
    fetcher = GetArticles(max_article_amount=20000)
    # article_data = fetcher.get_article_data_from_api(5)
    url_list = fetcher.get_urls_from_csv()
    # # url_list = fetcher.get_urls_from_api(article_data)
    # article_texts = fetcher.url_to_newspaper_text(url_list)
    # fetcher.write_text_to_file(article_texts)
    # # urls = (articleFetcher.get_article_urls(article_data))
