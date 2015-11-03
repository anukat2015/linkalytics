import warnings

warnings.simplefilter('ignore')

from .. utils              import with_test
from .  termdocumentmatrix import run

@with_test(run, 'termdocumentmatrix')
def data():
    yield ({'text': 'red', 'size': 5, 'ngrams': 3}, [
        {'red 8328536738 22': [70120686],
         'red 8329771287 28': [65929444],
         'red red 21': [80441298],
         'red red 22': [77093952],
         'red red 8328536738': [70120686],
         'red red 8329771287': [65929444],
         'red red red': [77093952, 80441298, 65929444, 70120686]}
    ])


