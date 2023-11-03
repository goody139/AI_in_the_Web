from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urlsplit, urljoin
from whoosh.index import create_in
from whoosh.fields import *


# [TODO] store time a page was last retrieved for checking whether it should be crawled again after some time
# [TODO] only update index instead of creating a complete new index every crawl

def crawl(start_url: str):
    # define the structure of the index entries
    schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True), url=TEXT(stored=True))

    # create index in index dir
    ix = create_in("index", schema)
    writer = ix.writer()

    # find all links in a page, store in a list and then visit each page in the list
    # depth first search

    visited_pages = []
    pages_to_visit = []

    # do not follow links to pages on other servers
    # remember the start server
    parsed_start_url = urlsplit(start_url)
    print(parsed_start_url)
    start_server = parsed_start_url.netloc

    pages_to_visit.append(start_url)

    while pages_to_visit:

        current_url = pages_to_visit.pop()
        print("\n\nloop start, visiting page:", current_url)
        print("pages to visit", pages_to_visit)
        print("visited pages", visited_pages)
        custom_headers = {'User-Agent': 'customAgent'}
        response = requests.get(current_url, headers=custom_headers, timeout=5)
        print(response.status_code)
        visited_pages.append(current_url)
        headers = response.headers

        # only process HTML responses
        if headers['Content-Type'].startswith("text/html"):
            soup = BeautifulSoup(response.content, 'html.parser')

            # add current page to index
            title = current_url
            found_title = soup.find("title")
            if found_title:
                title = found_title.text

            writer.add_document(title=u"{0}".format(title), content=u"{0}".format(soup.text), url=u"{0}".format(current_url))

            for link in soup.find_all('a'):
                # [TODO] check if the link is a valid url
                # check if it's a relative link and expand if it is
                split_url = urlparse(link.get('href'))
                if split_url.netloc == '':
                    complete_url = urljoin(start_url, link.get('href'))
                else:
                    complete_url = link.get('href')

                # check if the linked page has been visited before
                if not complete_url in visited_pages:
                    # if we haven't visited it yet
                    # only visit it if it's on the same server
                    if urlparse(complete_url).netloc == start_server:
                        # put in the list of urls to visit
                        pages_to_visit.append(complete_url)
            pages_to_visit = list(set(pages_to_visit))


    writer.commit()
    print("\n\n\ndone crawling, visited these {0} pages:".format(len(visited_pages)), visited_pages)


crawl("https://vm009.rz.uos.de/crawl/index.html")
