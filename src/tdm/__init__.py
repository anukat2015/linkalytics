from . entropy  import TermDocumentMatrix
from . entropy  import n_grams
from . __main__ import get_results
from . __main__ import lsh
from . __main__ import unique_features
from . __main__ import phone_hits
from . __main__ import both_hits

class Arguments:

    def __init__(self, query, size):
        self.query = [query]
        self.size  = [size]

