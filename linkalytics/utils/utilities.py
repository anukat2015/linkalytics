import functools

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
