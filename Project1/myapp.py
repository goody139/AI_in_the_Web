from flask import Flask, request, render_template, url_for
from whoosh import index
ix = index.open_dir("index")


app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def start():
    return render_template("start.html", title='start')

@app.route("/search")
def search():
    if not 'q' in request.args:
        return "No search term provided, go back to the <a href=\"/\">home page</a>"
    else:
        search_term = request.args['q']
        result_list = []
        # Retrieving data
        from whoosh.qparser import QueryParser
        with ix.searcher() as searcher:
            # find entries with the words 'first' AND 'last'
            query = QueryParser("content", ix.schema).parse(search_term)
            results = searcher.search(query)

            # get the important things from the results to use in the template
            for r in results:
                result_list.append((r["url"], r["title"], r.highlights("content")))

        return render_template("search.html", title=search_term, search_term=search_term, result=result_list)
    