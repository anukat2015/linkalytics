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

    def __repr__(self):
        return '{classname}{arguments}'.format(
            classname=self.__class__.__name__,
            arguments=str(tuple(([i[0] for i in self.__dict__.values()])))
        )

class NGramArguments(Arguments):

    def __init__(self, query, size, ngrams):
        self.ngrams = [ngrams]
        super().__init__(query, size)