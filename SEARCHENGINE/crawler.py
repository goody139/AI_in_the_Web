import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse, urljoin
import os
from whoosh.index import create_in
from whoosh.fields import *
from whoosh import index
from whoosh.qparser import QueryParser


# Search results : ranking?! 


def create_index(): 
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")

    schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True), url=TEXT(stored=True))
    ix = create_in("indexdir", schema)
    return ix


def is_same_domain(base_url, url):
    base_domain = urlparse(base_url).netloc
    current_domain = urlparse(url).netloc
    return base_domain == current_domain

def crawl(start_url):
    # Initialize the stack with the start URL
    stack = deque([start_url])
    visited = set()
    ix = create_index()

    # While the stack is not empty
    while stack:
        # Pop the first URL
        url = stack.popleft()

        # If not visited recently
        if url not in visited:
            try:
                # Get the content
                response = requests.get(url)
                if response.status_code == 200:
                    content = response.text

                    # Analyze it, find links to other websites, and add links to the stack (push)
                    soup = BeautifulSoup(content, 'html.parser')
                    # Extract the title of the page
                    title = soup.title.text if soup.title else "No title found"

                    # update index
                    writer = ix.writer()
                    writer.add_document(title=title, content=content, url=url)
                    writer.commit()
                    
                    
                    for link in soup.find_all('a'):
                        new_url = urljoin(url, link['href'])
                        if new_url and new_url.startswith('https') & is_same_domain(url, new_url):
                            stack.append(new_url)
                    

                    # Update visited list
                    visited.add(url)

            except Exception as e:
                print(f"An error occurred while processing {url}: {str(e)}")


def search_index(search_item): 
    ix = index.open_dir("indexdir")
    # Retrieving data
    with ix.searcher() as searcher:
        # find entries with search item
        query = QueryParser("content", ix.schema).parse(search_item)
        results = searcher.search(query)

        # print all results
        if results: 
            print("Here are the results listed")
            for r in results:
                print(r)
                return r
        else: 
            print("No proper results found.")

def main(): 
    # crawl 
    crawl("https://vm009.rz.uos.de/crawl/index.html")
    print("Type in a search item.")
    x = input()
    search_index(x)


     
if __name__=="__main__": 
    main() 