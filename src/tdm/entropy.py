import itertools
import string
import re

import pandas as pd
import numpy as np

def n_grams(document, n):
    table = dict((ord(char), None) for char in string.punctuation)
    raw   = re.sub('<[^<]+?>', '', document).lower().translate(table)
    grams = [
        itertools.islice(raw.split(), i, None) for i in range(n)
    ]
    return [' '.join(i) for i in zip(*grams)]

def high_entropy_featurizing(document):
    """
    Function to identify attributes of a string to determine whether it may
    be a unique identifier... WORK IN PROGRESS
    """

    words = document.split()
    unique = set()
    for word in words:
        n_character = len(word)
        n_numeric = sum(1 for c in word if c.isnumeric())
        # n_alpha = sum(1 for c in word if c.isalpha())
        # n_uppercase = sum(1 for c in word if c.isupper())
        # n_lowercase = sum(1 for c in word if c.isupper())
        if (n_character > 8) & (n_character == n_numeric):
            unique.add(word)
        # if (...)
    print(unique)


class TermDocumentMatrix:
    """
    Efficiently create a term-document matrix.
    """

    def __init__(self, cutoff=2, tokenizer=n_grams):
        """
        :param cutoff: int
            Specifies only words which appear in minimum documents to be
            written out as columns in the matrix.
        :param tokenizer: function
            Function that takes a single string representing a document
            and return a list of strings representing the n-grams in the document.
        """
        self.cutoff    = cutoff
        self.tokenizer = tokenizer
        self.sparse    = {}

    def __repr__(self):
        return '{classname}(cutoff={cutoff}, tokenizer={tokenizer})'.format(
            classname=self.__class__.__name__,
            tokenizer=self.tokenizer.__name__,
            cutoff=self.cutoff,
        )

    def __len__(self):
        return len(self.sparse)

    def __iter__(self):
        for k, v in self.sparse.items():
            yield {k: v}

    def add_doc(self, key, document, ngs=2):
        """
        Add document to the term-document matrix

        :param document: str
            String to be tokenized
        :param ngs: int
            n-grams
        """
        words  = self.tokenizer(document, ngs)
        counts = pd.Series(words).value_counts()
        cutoff = counts[counts >= self.cutoff]

        if not cutoff.empty:
            self.sparse[key] = cutoff

    def to_df(self):
        return pd.DataFrame.from_dict(self.sparse, orient='index')\
                           .fillna(value=0)\
                           .astype(dtype=np.uint32)\
                           .sort_index(inplace=False)

    def to_sparse(self):
        return self.to_df().to_sparse(fill_value=0)

    def sum_columns(self):
        return np.sum(self.to_df()).sort_values(inplace=False, ascending=False).astype(np.uint32)

    def write_csv(self, filename):
        """
        Write term-document matrix to a CSV file.

        :param filename: Name of the output file (e.g. `mymatrix.csv`).
        :type  filename: str

        """
        self.to_df().to_csv(filename)

def search(search_term, size, es, phrase=True):
    match_type = 'match_phrase' if phrase else 'match'
    output     = dict()
    payload = {
        "size": size,
        "query" : {
            match_type : {
                "_all" : search_term
            }
        }
    }
    results = es.search(body=payload)

    for hit in results['hits']['hits']:
        try:
            output[hit['_id']] = hit["_source"]["text"]
        except KeyError:
            pass

    return output


def main(n, query, es):
    results  = search(query, 1000, es, True)
    tdm      = TermDocumentMatrix(cutoff=2)

    for key, document in results.items():
        tdm.add_doc(key, document)

    return tdm
