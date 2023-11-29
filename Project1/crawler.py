from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urlsplit, urljoin
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.analysis import StemmingAnalyzer


def crawl(start_urls: list, stay_on_server=True):
    # define the structure of the index entries
    stem_ana = StemmingAnalyzer()
    schema = Schema(title=TEXT(analyzer=stem_ana, stored=True), content=TEXT(analyzer=stem_ana, stored=True, spelling=True), url=TEXT(stored=True))

    # create index in index dir
    ix = create_in("index", schema)
    writer = ix.writer(limitmb=1024)


    # find all links in a page, store in a list and then visit each page in the list
    # depth first search

    visited_pages = []
    pages_to_visit = []

    # do not follow links to pages on other servers
    # remember the start servers
    start_servers = [urlsplit(start_url).netloc for start_url in start_urls]

    pages_to_visit += start_urls
    pages_with_400 = []
    pages_with_500 = []
    pages_with_different_content_type = []
    pages_with_timeout = []

    pages_visited = 0

    while pages_to_visit and pages_visited < 1000:
        
        if pages_visited % 50 == 0:
            writer.commit()
            writer = ix.writer(limitmb=1024)


        current_url = pages_to_visit.pop()
        visited_pages.append(current_url)
        custom_headers = {'User-Agent': 'customAgent'}
        try:
            response = requests.get(current_url, headers=custom_headers, timeout=5)
            pages_visited += 1
        except requests.exceptions.InvalidSchema:
            continue
        except requests.exceptions.ConnectTimeout:
            # add it to the list to try again later
            pages_with_timeout.append(current_url)
            continue
        except Exception as e:
            # print("Exception occured: ", e)
            continue

        
        headers = response.headers

        if response.status_code // 100 == 4:
            pages_with_400.append(current_url)
        
        elif response.status_code // 100 == 5:
            pages_with_500.append(current_url)

        # only process HTML responses
        elif headers['Content-Type'].startswith("text/html"):
            soup = BeautifulSoup(response.content, 'html.parser')

            # add current page to index
            title = current_url
            found_title = soup.find("title")
            if found_title:
                title = found_title.text

            writer.add_document(title=u"{0}".format(title), content=u"{0}".format(soup.text), url=u"{0}".format(current_url))

            for link in soup.find_all('a'):
                # check if it's a relative link and expand if it is
                split_url = urlparse(link.get('href'))
                if split_url.netloc == '':
                    complete_url = urljoin(current_url, link.get('href'))
                else:
                    complete_url = link.get('href')

                # check if the linked page has been visited before
                if not complete_url in visited_pages:
                    # if we haven't visited it yet
                    # if we want to stay on the server, only visit it if it's on the same server
                    if stay_on_server:
                        if urlparse(complete_url).netloc in start_servers:
                            # put in the list of urls to visit
                            pages_to_visit.append(complete_url)
                    else:
                        pages_to_visit.append(complete_url)
            pages_to_visit = list(set(pages_to_visit))
        
        else:
            pages_with_different_content_type.append(current_url)

    writer.commit()

    
#     print("\n\n\ndone crawling, visited these {0} pages:".format(len(visited_pages)), visited_pages)
#     print("\n{0} pages with 400:".format(len(pages_with_400)), pages_with_400)
#     print("\n{0} pages with 500:".format(len(pages_with_500)), pages_with_500)
#     print("\n{0} pages with timeout:".format(len(pages_with_timeout)), pages_with_timeout)
#     print("\n{0} pages with non html:".format(len(pages_with_different_content_type)), pages_with_different_content_type)


# crawl(["https://vm009.rz.uos.de/crawl/index.html"], stay_on_server=True)
