from flask import Flask, request, render_template, url_for
from whoosh import index
from whoosh.qparser import QueryParser
import traceback

ix = index.open_dir("index")


app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def start():
    return render_template("start.html", title='start')

@app.route("/search")
def search():
    if not 'q' in request.args:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    else:
        search_term = request.args['q']
        result_list = []
        # Retrieving data
        
        with ix.searcher() as searcher:
            corrector = searcher.corrector("content")
            query = QueryParser("content", ix.schema).parse(search_term)
            corrected = searcher.correct_query(query, search_term)
            suggestion = None
            if corrected.query != query:
                print("Did you mean:", corrected.string)
                suggestion = corrected.string
            results = searcher.search(query)

            # get the important things from the results to use in the template
            for r in results:
                result_list.append((r["url"], r["title"], r.highlights("content")))

        return render_template("search.html", title=search_term, search_term=search_term, result=result_list, suggestion=suggestion)
    
@app.errorhandler(500)
def internal_error(exception):
   return "<pre>"+traceback.format_exc()+"</pre>"
