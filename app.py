from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from datetime import date
import re

import datetime

app = Flask(__name__)
# app.jinja_env.variable_start_string = '%%'
# app.jinja_env.variable_end_string = '%%'


#TODO
# allow date range
# by default it should check for the current (or previous) date
# also search in cross-listings
# allow categories to be determined as well
# check whether it's actually doing the right stuff
# ------>highlighting of search terms

def fetch_papers(date, search_term): # allow composable search terms
    search_query = '+OR+'.join([f'"{term.replace(" ", "+")}"' for term in search_term])
    results_per_iteration = 100
    i = 0
    to_date = datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10])) # allow date range; by default it should check the current date
    paper_date = datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10]))
    papers = []
    while (paper_date >= to_date):
        url = f"http://export.arxiv.org/api/query?search_query={search_query}&start={i}&max_results={results_per_iteration}&sortBy=submittedDate&sortOrder=descending"
        print(url)
        i += results_per_iteration

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        entries = soup.find_all('entry')

        for entry in entries:
            title = entry.find('title').text
            summary = entry.find('summary').text
            link = entry.find('link', {'type': 'text/html'})['href']
            authors = [{'name': author.find('name').text, 'affiliation': author.find('arxiv:affiliation', {'xmlns:arxiv': 'http://arxiv.org/schemas/atom'}).text if author.find('arxiv:affiliation', {'xmlns:arxiv': 'http://arxiv.org/schemas/atom'}) else ''} for author in entry.find_all('author')]
            category = entry.find('arxiv:primary_category', {'xmlns:arxiv': 'http://arxiv.org/schemas/atom'})['term']
            published = entry.find('published')
            revised = entry.find('updated')

            categories = ["quant-ph", "cond-mat.quant-gas", "cond-mat.dis-nn"] # make this also determinable in browser

            if date in published.get_text():
                if any(ele in category for ele in categories):
                    print(category)
                    papers.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'authors': authors,
                        'category': category,
                        'published': published,
                        'revised': revised
                    })

        published_date = published.get_text()
        paper_date = datetime.datetime(int(published_date[:4]), int(published_date[5:7]), int(published_date[8:10]))

    return papers


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         search_term = request.form.get('search_term', '').lower()
#         print("search_term ", search_term)
#         today = date.today().strftime('%Y-%m-%d')
#         papers = fetch_papers(today)
#         filtered_papers = [paper for paper in papers if search_term in paper['title'].lower() or search_term in paper['summary'].lower()]

#         return render_template('index.html', papers=filtered_papers)

#     return render_template('index.html')

# @app.route('/papers', methods=['POST'])
# def papers():
#     date = request.form['date']
#     search_terms = [term.strip() for term in request.form['search_term'].split(',')]
#     papers = fetch_papers(date, search_terms)
#     return render_template('index.html', papers=papers, date=date, search_term=', '.join(search_terms))


def highlight_keywords(text, keywords):
    colors = ['#F08080', '#7FFFD4', '#D8BFD8', '#DDA0DD', '#F0E68C', '#FFDAB9', '#AFEEEE', '#B0C4DE', '#B0E0E6', '#98FB98']
    highlighted_text = text
    for index, keyword in enumerate(keywords):
        regex = re.compile(f'({keyword})', re.IGNORECASE)
        highlighted_text = regex.sub(f'<span style="background-color: {colors[index % len(colors)]}">\\1</span>', highlighted_text)
    return highlighted_text



    try:
        # learning,control,network
        search_term = [term.strip() for term in request.form['search_term'].split(',')] # ['learning', 'control', 'network']
        date = request.form['date']
        # today = date.today().strftime('%Y-%m-%d')
        papers = fetch_papers(date, search_term)
        # filtered_papers = [paper for paper in papers if search_term in paper['title'].lower() or search_term in paper['summary'].lower()]
        # return render_template('index.html', papers=papers)

        for paper in papers:
            paper['title'] = highlight_keywords(paper['title'], search_term)
            paper['summary'] = highlight_keywords(paper['summary'], search_term)

        return render_template('index.html', papers=papers, search_term=', '.join(search_term)) # learning, control, network
    except Exception as e:
        return f"An error occurred: {str(e)}"



@app.route('/')
@app.route('/papers', methods=['GET', 'POST'])
def papers():
    print("hello")
    date = request.form.get('date', None) or request.args.get('date', None)
    search_term = request.form.get('search_term', None) or request.args.get('search_term', None)
    print(search_term)
    if date and search_term:
        search_terms = [term.strip() for term in request.form['search_term'].split(',')]
        papers = fetch_papers(date, search_terms)
        print(papers)
        for paper in papers:
            paper['title'] = highlight_keywords(paper['title'], search_terms)
            paper['summary'] = highlight_keywords(paper['summary'], search_terms)
    else:
        papers = []
    return render_template('index.html', papers=papers, date=date, search_term=search_term)

if __name__ == '__main__':
    app.run(debug=True)
