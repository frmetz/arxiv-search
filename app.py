from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re

import datetime

app = Flask(__name__)

CATEGORIES = ["quant-ph", "cond-mat.quant-gas", "cond-mat.dis-nn", "cond-mat.other", "cond-mat.stat-mech"] # make this also determinable in browser

#TODO
# also search in cross-listings
# allow categories to be determined as well
# check whether it's actually doing the right stuff

def fetch_papers(fromdate, todate, search_term):
    print()
    print()
    search_query = '+OR+'.join([f'"{term.replace(" ", "+")}"' for term in search_term])

    # search_query_ti = 'ti:' + '+OR+ti:'.join([f'"{term.replace(" ", "+")}"' for term in search_term])
    # search_query_abs = '+OR+abs:' + '+OR+abs:'.join([f'"{term.replace(" ", "+")}"' for term in search_term])
    # search_query = search_query_ti + search_query_abs
    
    # print(search_query)
    results_per_iteration = 500
    i = 0
    from_date = datetime.datetime(int(fromdate[:4]), int(fromdate[5:7]), int(fromdate[8:10]))
    to_date = datetime.datetime(int(todate[:4]), int(todate[5:7]), int(todate[8:10]))
    paper_date = datetime.datetime(int(todate[:4]), int(todate[5:7]), int(todate[8:10]))
    papers = []
    print("from_date: ", from_date)
    k = 0 
    l = 0
    while (paper_date >= from_date):
        url = f"http://export.arxiv.org/api/query?search_query={search_query}&start={i}&max_results={results_per_iteration}&sortBy=submittedDate&sortOrder=descending"
        print(url)
        # i += results_per_iteration

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        entries = soup.find_all('entry')

        print("number of results ", len(entries))
        i += len(entries)

        for entry in entries:
            title = entry.find('title').text
            summary = entry.find('summary').text
            link = entry.find('link', {'type': 'text/html'})['href']
            authors = [{'name': author.find('name').text, 'affiliation': author.find('arxiv:affiliation', {'xmlns:arxiv': 'http://arxiv.org/schemas/atom'}).text if author.find('arxiv:affiliation', {'xmlns:arxiv': 'http://arxiv.org/schemas/atom'}) else ''} for author in entry.find_all('author')]
            category = entry.find('arxiv:primary_category', {'xmlns:arxiv': 'http://arxiv.org/schemas/atom'})['term']
            published = entry.find('published')
            revised = entry.find('updated')

            published_date = published.get_text()
            paper_date = datetime.datetime(int(published_date[:4]), int(published_date[5:7]), int(published_date[8:10]))

            # print("paper_date: ", paper_date)
            if from_date <= paper_date and paper_date <= to_date:
                k += 1
                # print("yes")
                if any(ele in category for ele in CATEGORIES):
                    l += 1
                    # print(category)
                    papers.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'authors': authors,
                        'category': category,
                        'published': published,
                        'revised': revised
                    })
    print("number of correct dates: ", k)
    print("number of correct cates: ", l)

    return papers



def highlight_keywords(text, keywords):
    colors = ['#F08080', '#7FFFD4', '#D8BFD8', '#DDA0DD', '#F0E68C', '#FFDAB9', '#AFEEEE', '#B0C4DE', '#B0E0E6', '#98FB98']
    highlighted_text = text
    for index, keyword in enumerate(keywords):
        regex = re.compile(f'({keyword})', re.IGNORECASE)
        highlighted_text = regex.sub(f'<span style="background-color: {colors[index % len(colors)]}">\\1</span>', highlighted_text)
    return highlighted_text



@app.route('/')
@app.route('/papers', methods=['GET', 'POST'])
def papers():
    from_date = request.form.get('from_date', None) or request.args.get('from_date', None)
    to_date = request.form.get('to_date', None) or request.args.get('to_date', None)
    search_term = request.form.get('search_term', None) or request.args.get('search_term', None)

    if from_date is None:
        today = date.today()
        day_shift = 2
        if today.weekday() == 6: # Saturday
            day_shift = 3
        elif today.weekday() == 7: # Sunday
            day_shift = 4
        elif today.weekday() == 0: # Monday
            day_shift = 4
        from_date = (today - timedelta(days = day_shift)).strftime('%Y-%m-%d')
    if to_date is None:
        to_date = date.today().strftime('%Y-%m-%d')

    if search_term and from_date and to_date:
        search_terms = [term.strip() for term in request.form['search_term'].split(',')]
        papers = fetch_papers(from_date, to_date, search_terms)
        papers = fetch_papers(from_date, to_date, search_terms)
        for paper in papers:
            paper['title'] = highlight_keywords(paper['title'], search_terms)
            paper['summary'] = highlight_keywords(paper['summary'], search_terms)
    else:
        papers = []
    return render_template('index.html', papers=papers, from_date=from_date, to_date=to_date, search_term=search_term)

if __name__ == '__main__':
    app.run(debug=True)
