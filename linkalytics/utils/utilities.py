import functools
import time
import logging
import requests

from requests          import Request
from requests.adapters import HTTPAdapter
from contextlib        import contextmanager
from urllib.parse      import urljoin

__all__ = ['get_session', 'push_url', 'memoize', 'timer', 'SetLogging']

def get_session(proxy=None, max_retries=3):
    session = requests.session()
    session.mount('http://',  HTTPAdapter(max_retries=max_retries))
    session.mount('https://', HTTPAdapter(max_retries=max_retries))
    session.proxies = { 'https': proxy, 'http':  proxy } if proxy else {}
    return session

def push_url(resource, proxy=None):

    def wrapper(interface):

        @functools.wraps(interface)
        def connection(*args, **kwargs):
            session = get_session(proxy=proxy)

            params  = interface(*args, **kwargs)

            if resource not in params['url']:
                params['url'] = urljoin(resource, params['url'])

            request = Request(method='GET',
                              headers={'Content-Type': 'application/json'},
                              **params
                              )
            response = session.send(request.prepare(), verify=False)
            return response.json()

        return connection

    return wrapper


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