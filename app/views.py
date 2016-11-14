from logging import getLogger
from os import getcwd
from queue import Empty
from os.path import getsize
from flask import render_template, flash, redirect, request, session, url_for, Response, jsonify
from config import database_name
from app import app, es, pastebin_handle, db_worker, db, tor_enabled
from app.forms import ScraperForm, SearchForm, DownloadPasteForm, BasicButtonForm, DateForm
from app.es_search import EsSearch, EsPagination, es_search_by_id, delete_from_es
from app.models import Paste
from app.general_functions import convert_bytes_to_size

PASTES_IN_PAGE = 10
logger = getLogger(__name__)
last_details = {
            'ps_is_alive': False,
            'ps_last_response_address': 'None',
            'ps_last_response_code': 'None',
            'ps_using_tor': 'None'
        }


@app.route('/_get_pastebin_scraper_stats')
def get_pastebin_scraper_stats():
    global last_details
    if pastebin_handle.scraper is not None and pastebin_handle.scraper.is_alive():
        if pastebin_handle.q.empty():
            pastebin_handle.q.put('request_details')
            try:
                rtn = pastebin_handle.out_q.get(timeout=0.1)
            except Empty:
                rtn = last_details
        else:
            try:
                rtn = pastebin_handle.out_q.get(timeout=0.1)
            except Empty:
                rtn = last_details
    else:
        try:
            rtn = pastebin_handle.out_q.get(timeout=0.1)
        except Empty:
            rtn = last_details
    last_details = rtn
    return jsonify(rtn)


@app.route('/scrapers', methods=['GET', 'POST'])
def scrapers():
    """
    The view for the scrapers page.
    :return: render_template
    """
    global last_details
    pastebin_form = ScraperForm()

    # Start or stop the pastebin scraper in pastebin_form
    if pastebin_form.validate_on_submit() and (pastebin_handle.action in request.form.values() or
                                               'Start and use Tor' in request.form.values()):
        if 'Start' in request.form.values() and not last_details['ps_is_alive']:
            pastebin_handle.use_tor = False
            pastebin_handle.start()
            flash("Pastebin scraper started!")
        elif 'Start' in request.form.values() and last_details['ps_is_alive']:
            flash("Please wait for the pastebin scraper to finish before restarting.")
        elif 'Start and use Tor' in request.form.values() and not last_details['ps_is_alive']:
            pastebin_handle.use_tor = True
            pastebin_handle.start()
            flash("Pastebin scraper started with Tor!")
        elif 'Start and use Tor' in request.form.values() and last_details['ps_is_alive']:
            flash("Please wait for the pastebin scraper to finish before restarting.")
        elif 'Stop' in request.form.values():
            pastebin_handle.stop()
            flash("Pastebin scraper stopped!")

    return render_template('scrapers.html',
                           title='Scrapers',
                           pastebin_handle=pastebin_handle,
                           pastebin_form=pastebin_form,
                           tor_enabled=tor_enabled
                           )


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
def index(page=1):
    """
    The view for the index page
    :return: render_template
    """

    search_form = SearchForm()
    search_term = request.args.get('search_term', None)

    if search_form.validate_on_submit():
        search_term = search_form.search_terms.data
        logger.info('search_form validated, redirecting to search results')
        return redirect(url_for('index', page=1, search_term=search_term))

    if search_term is not None:

        logger.info('index page got search_term: %s', search_term)
        # Legacy functions used when using postgres for searches.
        # found_pastes = Paste.query.filter(Paste.content.ilike('%' + search_term + '%'))
        # paged_pastes = found_pastes.paginate(page, PASTES_IN_PAGE, False)

        # Create EsSearch class and create a paginated version of it.
        found_pastes = EsSearch(search_term)
        paginated_pastes = EsPagination(found_pastes, page, PASTES_IN_PAGE)
        if paginated_pastes.total_hits > 0:
            return render_template('index.html',
                                   title='Home',
                                   form=search_form,
                                   pastes=paginated_pastes,
                                   search_term=search_term,
                                   download_paste_form=DownloadPasteForm
                                   )
        else:
            return render_template('index.html',
                                   title='Home',
                                   form=search_form,
                                   nopastes=True,
                                   search_term=search_term
                                   )

    return render_template('index.html',
                           title='Home',
                           form=search_form
                           )


@app.route('/_get_database_dicts')
def get_database_dicts():
    es_health_dict = es.cluster.health()
    es_stats_dict = es.cluster.stats()
    es_stats_dict['size'] = convert_bytes_to_size(es_stats_dict['indices']['store']['size_in_bytes'])
    es_stats_dict['available'] = convert_bytes_to_size(es_stats_dict['nodes']['fs']['available_in_bytes'])

    count = db.session.query(Paste).count()

    postgres_dict = {
        'name': database_name,
        'tables': ['paste'],
        'paste': count
    }

    rtn = {
        'es_health_dict': es_health_dict,
        'es_stats_dict': es_stats_dict,
        'postgres_dict': postgres_dict
    }
    return jsonify(rtn)


@app.route('/databases', methods=['GET', 'POST'])
def databases():
    health_dict = es.cluster.health()
    stats_dict = es.cluster.stats()
    form = BasicButtonForm()
    date_form = DateForm()
    psql_dict = {
        'name': database_name,
        'tables': ['paste'],
        'paste': db.session.query(Paste).count()
    }

    if request.method == 'POST':
        if request.form['submit'] == "Yes, reindex elasticsearch":
            db_worker.q.put(('Reindex ES', None))

        elif request.form['submit'] == 'Yes, delete everything':
            db_worker.q.put(('Delete', None))
            flash("Databases are currently being erased!")

        elif request.form['submit'] == "Delete entries older than this date":
            db_worker.q.put(("Delete Date", request.form['date']))
            # date = request.form['date'] + " 00:00:00.000000"
            # old_pastes = db.session.query(Paste).filter(Paste.datetime < date)
            # for item in old_pastes:
            #     delete_from_es(item)
            #     db.session.delete(item)
            flash("Erasing entries before " + str(request.form['date']))

    return render_template('databases.html',
                           health_dict=health_dict,
                           stats_dict=stats_dict,
                           psql_dict=psql_dict,
                           form=form,
                           date_form=date_form,
                           convert_bytes_to_size=convert_bytes_to_size)


@app.route('/download_paste.txt')
def download_paste():
    paste_id = request.args.get('paste_id')
    logger.info('Downloading paste: %s', paste_id)
    paste = es_search_by_id(paste_id)
    f = open('tmp', 'w+')
    f.write('URL\n\n' + paste.url + '\n\n\n')
    f.write('NAME\n\n' + paste.name + '\n\n\n')
    f.write('DATETIME\n\n' + paste.datetime + '\n\n\n')
    f.write('CONTENT\n\n' + paste.content)
    f.close()

    def generate(x):
        for line in x:
            yield line

    f = open('tmp', 'r')
    size = getsize(getcwd() + '/tmp')
    return Response(generate(f), mimetype='text/plain',
                    headers={"Content-Disposition": "attachment;filename=" + str(paste_id) + ".txt",
                    "Content-Length": str(size)})
