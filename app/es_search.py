from app import es, db
from elasticsearch_dsl import Search, Q
from app.models import Paste
from logging import getLogger

logger = getLogger(__name__)


def add_to_es(model_instance):
    """
    Indexes an item into the elasticsearch cluster.

    :param model_instance: The model object to be added.
    :return: Bool
    """
    try:
        json = model_instance.jsonify()
        model_name = model_instance.__class__.__name__.lower()
        result = es.index(index=model_name, doc_type=model_name, body=json)
        logger.info('Added to elasticsearch: %s', result)
        return True
    except:
        logger.error('Couldn\'t add to elasticsearch: %s', result)


def delete_from_es(model_instance):
    """
    Deletes an item/s from the elastic search index (note will get copies)

    :param model_instance: The model object to be deleted.
    :return: Bool
    """
    json = model_instance.jsonify()
    model_name = model_instance.__class__.__name__.lower()
    s = Search(using=es, index=model_name, doc_type=model_name).query('match', url=model_instance.url)
    s.execute()
    for item in s:
        result = es.delete(index=model_name, doc_type=model_name, id=item.meta.id)
        logger.info('Deleted from elasticsearch: %s', result)
        break
    return True


def delete_all_es():
    """
    Delete all indices from elasticsearch
    :return: Bool
    """
    try:
        es.indices.delete('_all')
        logger.info('All elasticsearch indices deleted')
        return True
    except:
        logger.error('Could not delete all elasticsearch indices')
        return False


def es_search_by_id(paste_id):
    """
    Simple function to get the elasticsearch database entry from the auto generated id.
    :param paste_id: String (elasticsearch - _id for db entry)
    :return: Elasticsearch Response Object
    """
    paste_id = paste_id

    if paste_id is not None:
        s = Search(using=es).query('match', _id=paste_id)
        response = s.execute()
        if len(response.hits) > 0:
            logger.info('es_search_by_id found %s documents: returning %s', len(response.hits), response.hits[0])
            return response.hits[0]
    logger.info('No hits found for %s', paste_id)
    return None


def reindex_es():
    """
    Simple function to reindex contents of the database.
    :return: Bool
    """
    all_indexed = True
    all_pastes = db.session.query(Paste).all()
    tmp = delete_all_es()
    for paste in all_pastes:
        all_indexed = all_indexed and add_to_es(paste)
    return all_indexed


class EsSearch:
    """
    A simple class to store some data about an ES search.
    """

    def __init__(self, search_string, results=None, num_results=None):
        self.search_string = search_string
        self.results = results
        self.num_results = num_results

        if self.results is None and self.num_results is None:
            qry = Q('query_string', query=search_string)
            s = Search(using=es).query(qry)
            response = s.execute()
            if response.success():
                self.results = s
                self.num_results = response.hits.total
                logger.info('%s hits found for search: %s', response.hits.total, search_string)
            else:
                logger.info('No hits for %s', search_string)


class EsPagination:
    """
    A class to mimic some of the features used in the SQLAlchemy Paginate class. This was done to allow easier
    transition from one to the other, particuarly in the case of the index.html page
    """

    def __init__(self, search, page, per_page):
        self.items = search.results[(page - 1) * per_page:(page * per_page)]
        for item in self.items:
            item.datetime = item.datetime.replace('T', '\n')
        self.page = page
        self.total_hits = search.num_results

        # Work out total number of pages
        if search.num_results % per_page == 0:
            self.total_pages = (search.num_results // per_page)
        else:
            self.total_pages = (search.num_results // per_page) + 1
        logger.info('%s pages for pagination', self.total_pages)

        # If we have a next page and what is its number
        if self.page < self.total_pages:
            self.has_next = True
            self.next_num = self.page + 1
        else:
            self.has_next = False
            self.next_num = None

        # If we have a prev page and what is its number
        if self.page > 1:
            self.has_prev = True
            self.prev_num = self.page - 1
        else:
            self.has_prev = False
            self. prev_num = None

    def iter_pages(self):
        """
        Provides an analogue to the SQLAlchemy iterpages() method for Pagination.
        This returns a list of page numbers to be displayed for pagination.
        :return: list
        """
        if self.total_pages > 1:
            mid_pages = [x + self.page for x in range(-2, 3) if self.total_pages > (x + self.page) > 1 ]
            displayed = [1] + mid_pages + [self.total_pages]
            rtn = []
            for i in range(len(displayed) - 1):
                rtn.append(displayed[i])
                if displayed[i + 1] - displayed[i] > 1:
                    rtn.append(None)
            rtn.append(displayed[-1])
            return rtn

        return [1]
