import functools
import time
import logging

from contextlib import contextmanager

def search(es):
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

            output["total"] = results['hits']['total']
            for hit in results['hits']['hits']:
                try:
                    output[int(hit['_id'])] = hit["_source"]
                except KeyError:
                    pass

            return output

        return _wrap

    return wrap


def memoize(func):
    """
    Memoizing decorator for functions, methods, or classes, exposing
    the cache publicly.
    Currently only works on positional arguments.
    """
    cache = func.cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        if args not in cache:
            cache[args] = func(*args, **kwargs)

        return cache[args]

    return wrapper

@contextmanager
def timer(label):
    output = '{label}: {time:03.3f} sec'
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
    print(output.format(label=label, time=end-start))


class SetLogging:
    """
    ContextManager for setting logging until block completes.
    By default will disable logging.

    Example Use
    -----------
    # Sets logging to INFO
    with SetLogging(logging.INFO):
        do_something()
    """
    def __init__(self, setpoint=logging.CRITICAL):
        self.setpoint = setpoint
        self.endpoint = logging.NOTSET

    def __enter__(self):
        logging.disable(self.setpoint)

    def __exit__(self, type, value, traceback):
        logging.disable(self.endpoint)
