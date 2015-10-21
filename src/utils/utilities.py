import functools
import time

from contextlib import contextmanager

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

