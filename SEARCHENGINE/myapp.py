import flask
import woosh
from flask import Flask, render_template, request, redirect, url_for
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, STORED, ID
from crawler import crawl
from whoosh.fields import *
from whoosh import index
from whoosh.qparser import QueryParser, OrGroup
from whoosh import scoring
from bs4 import BeautifulSoup


""" WEBSITE for the FLASK APP : http://127.0.0.1:5000/ """

app = Flask(__name__)


# Define the home route
@app.route('/')
def home():
    return render_template('search_form.html')

# first of all crawl
crawl("https://vm009.rz.uos.de/crawl/index.html")


# Define the search route
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:

        ix = index.open_dir("indexdir")
        with ix.searcher(weighting=scoring.BM25F()) as searcher:
            
            # Parse content and title
            content_parser = QueryParser("content", ix.schema, group=OrGroup)
            title_parser = QueryParser("title", ix.schema, group=OrGroup)

            # query 
            title_query = title_parser.parse(query)
            content_query = content_parser.parse(query)

            # combine both queries with a or operator 
            combined_query = title_query | content_query

            # search for results 
            final_results = searcher.search(combined_query)

            # rank the results
            search_results = [{"url": hit["url"], "title": hit["title"], "content": hit["content"], "score": hit.score} for hit in final_results]
            ranked_results = sorted(search_results, key=lambda x: (x["content"].lower().count(query.lower()) + x["title"].lower().count(query.lower())), reverse=True)

            # save url and title separately to use it in the html file
            urls = [results["url"] for results in ranked_results]
            titles = [results["title"] for results in ranked_results]
            content = []
            for results in ranked_results: 
                content.append(BeautifulSoup(results["content"][100:200], 'html.parser').get_text())
            results = zip(urls, titles, content)
            
            return render_template('test.html', query=query, urls=urls, titles=titles, results=results)

    else:
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)