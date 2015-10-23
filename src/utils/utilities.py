import functools
import time
import logging

from contextlib import contextmanager

class SetLogging:
    def __enter__(self):
       logging.disable(logging.CRITICAL)
    def __exit__(self, a, b, c):
       logging.disable(logging.NOTSET)

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
