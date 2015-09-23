import nose
from utils import with_test
from server import run


@with_test(doc_to_group, 'server')
def data():
    yield ({"text": "1356728"}, [
    	{"_id": "17149483596", "_type": "group"}
    	])
