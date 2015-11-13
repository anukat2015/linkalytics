import functools
import warnings

from elasticsearch  import Elasticsearch

from . environment import cfg

warnings.simplefilter('ignore')

url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
es  = Elasticsearch(url, port=443, verify_certs=False, use_ssl=False, request_timeout=160, timeout=160)

def run(node):
    search_term, size = node.get('search', 'cali'), int(node.get('size', 100))
    return get_results(search_term, size)

def search(es, total=True):
    """
    Elasticsearch Decorator
    -----------------------
    Wraps a function which becomes the payload for a query to an elasticsearch.

    :param es: Elasticsearch instance

    :return: Elasticsearch results
    :rtype:  dict

    Usage:
    ------
    from elasticsearch import Elasticsearch

    es = Elasticsearch("https://elasticsearch.com/index")

    @search()
    def get_results(search_term, size):
        return {
            "size": size,
            "query" : {
                "match": {
                    "_all": search_term
                }
            }
        }

    results = get_results('foo', 1000)
    """
    def wrap(func):
        """
        :param func: Decorated Function
        """
        @functools.wraps(func)
        def _wrap(*args, **kwargs):
            output, payload = dict(), func(*args, **kwargs)

            results = es.search(body=payload)

            if total:
                output["total"] = results['hits']['total']

            for hit in results['hits']['hits']:
                try:
                    output[hit['_id']] = hit["_source"]
                except KeyError:
                    pass

            return output

        return _wrap

    return wrap

@search(es, total=False)
def get_results(search_term, size, phrase=True):
    match_type = 'match_phrase' if phrase else 'match'
    payload = {
        "size": size,
        "query" : {
            match_type : {
                "_all" : search_term
            }
        }
    }
    return payload

@search(es, total=False)
def query_ads(k, v, value='text'):

    ad_ids = []
    for ad_id in v:
        ad_ids.append({ "term" : {"_id" : int(ad_id) }})

    size    = len(ad_ids) if value == 'text' else 500
    query   = { "filtered" : { "filter" : { "bool" : { "should" : ad_ids } } } }
    payload = { "size": size, "query" : query }

    return payload

@search(es, total=True)
def phone_hits(phone, size):
    payload = {
        "size": size,
        "query" : {
            "match_phrase": {
                "phone" : phone
            }
        }
    }
    return payload

@search(es, total=True)
def both_hits(search_term, phone):
    query =  {
        "bool": {
            "must": [
                { "match_phrase": { "_all": search_term } },
                { "match": { "phone": phone } }
            ]
        }
    }
    return { "size": 500, "query" : query }
