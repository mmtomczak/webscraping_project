import selenium.common.exceptions
from flask import Flask, request, render_template, session, redirect, url_for, flash
from beautifulsoup4.bs4_scrapers import movie_or_tv, get_genres
from scrapy.crawler import CrawlerProcess
from moviescraper.moviescraper.spiders.moviespider import MoviesSpider
from database.db_filter import get_data, filter_data
from twisted.internet.error import ReactorNotRestartable

app = Flask(__name__)
app.secret_key = 'secretkey'


# Create crawl process
# define user agent, pipelines and logging format
process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
    'ITEM_PIPELINES': {'moviescraper.moviescraper.pipelines.MoviescraperPipeline': 300},
    'LOG_FORMAT': '%(levelname)s: %(message)s',
    'LOG_LEVEL': 'INFO'
})


@app.route('/', methods=['GET', 'POST'])
def type():
    types_links_dict = movie_or_tv()
    if request.method == 'POST':
        session['selected_type'] = request.form.get('type')
        return redirect(url_for('genres'))
    return render_template('type.html', types_links_dict=types_links_dict)


@app.route('/genres', methods=['GET', 'POST'])
def genres():
    selected_type = session.get('selected_type')
    genres = get_genres(selected_type)
    if request.method == 'POST':
        session['selected_genre'] = request.form.getlist('genre')
        return redirect(url_for('scraping'))
    return render_template('genres.html', genres=genres)


@app.route('/scraping', methods=['GET', 'POST'])
def scraping():
    selected_type = session.get('selected_type')
    selected_genre = session.get('selected_genre')
    category = 1 if selected_type == '/movie?language=en' else 2
    try:
        process.crawl(MoviesSpider, category=category, num_pages=4, genre=selected_genre)
        process.start()
    except ReactorNotRestartable:
        flash("Scrapy does not allow to run the spider multiple times - restart the project to scrape different data")
        return redirect(url_for('browse'))
    except selenium.common.exceptions.TimeoutException:
        flash("Page dynamic content navigation exception - restart the project")
        return redirect(url_for('browse'))
    return redirect(url_for('browse'))


@app.route('/browse', methods=['GET', 'POST'])
def browse():
    title_filter = request.args.get('title', None)
    year_filter = request.args.get('year', None)
    data = get_data()
    is_movie = session.get('selected_type') == '/movie?language=en'
    filtered_data = filter_data(data, is_movie, title_filter, year_filter)
    return render_template('browse.html', data=filtered_data, is_movie=is_movie)


if __name__ == '__main__':
    app.run(debug=True)