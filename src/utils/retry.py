import time

def retry(attempts=3, on=Exception):
    def decorator(f):
        return _func_to_retry(f, on, attempts)
    return decorator

def _func_to_retry(f, exception_cls, max_attempts):
    def g(*args, **kwargs):
        result = None
    	for attempt in range(max_attempts):
            print("Attempting {}. Attempt {}/{}".format(f.__name__, attempt+1, max_attempts))
            time.sleep((2**attempt - 1)*60)
    		try:
    			result = f(*args, **kwargs)
    		except exception_cls as e:
    			continue # try again
    	return result
    return g
