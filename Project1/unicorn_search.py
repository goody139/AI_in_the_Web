from flask import Flask, request, render_template, url_for
from whoosh import index, scoring
from whoosh.qparser import QueryParser, OrGroup
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
        
        with ix.searcher(weighting=scoring.BM25F()) as searcher:
            corrector = searcher.corrector("content")

            # Parse content and title
            content_parser = QueryParser("content", ix.schema, group=OrGroup)
            title_parser = QueryParser("title", ix.schema, group=OrGroup)

            # query 
            title_query = title_parser.parse(search_term)
            content_query = content_parser.parse(search_term)

            # combine both queries with a or operator 
            combined_query = title_query | content_query

            corrected = searcher.correct_query(combined_query, search_term)
            suggestion = None
            if corrected.query != combined_query:
                print("Did you mean:", corrected.string)
                suggestion = corrected.string

            # search for results 
            final_results = searcher.search(combined_query)
            
            # rank the results
            search_results = [{"url": hit["url"], "title": hit["title"], "content": hit["content"], "score": hit.score, "highlights": hit.highlights("content")} for hit in final_results]
            ranked_results = sorted(search_results, key=lambda x: (x["content"].lower().count(search_term.lower()) + x["title"].lower().count(search_term.lower())), reverse=True)

            # get the important things from the results to use in the template
            for r in ranked_results:
                result_list.append((r["url"], r["title"], r["highlights"]))

        return render_template("search2.html", title=search_term, search_term=search_term, result=result_list, suggestion=suggestion)
    
@app.errorhandler(500)
def internal_error(exception):
   return render_template("server_error.html", title='Server error')
