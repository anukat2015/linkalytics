import itertools
import string
import json
import re
import functools

import pandas as pd
import numpy as np
import distance
import networkx as nx


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
        """
        Iterating over this object will output a tuple of key, value pairs
        """
        for k, v in self.sparse.items():
            yield k, v

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

        cutoff[cutoff.index] = 1

        if not cutoff.empty:
            self.sparse[key] = cutoff

    def load_json(self, filepath, n=2):
        """
        Batch load documents from a fully qualified JSON file.

        :param filepath: str
            File directory path

        :param n: int
            N-Grams to split using the tokenizer
        """
        loaded = json.load(open(filepath))

        if isinstance(loaded, list):
            self.load_list(loaded)
        else:
            self.load_dict(loaded)

    def load_dict(self, loaded, n=2):
        """
        :param loaded: dict
            Dictionary with the following schema

        :param n: int
            N-Grams to split using the tokenizer

        Schema
        ------
        {
            “id1”: ”text1”,
            "id2": "text2"
        }
        """
        for key, document in loaded.items():
            self.add_doc(key, document, n)

    def load_list(self, loaded, n=2):
        """
        :param loaded: list
            Dictionary with the following schema

        :param n: int
            N-Grams to split using the tokenizer

        Schema
        ------
        [
            {
                "id": 2314134,
                "text": "Some Text"
            },
            {
                "id":  4324353,
                "text" "Some other text"
            }
        ]
        """
        self.load_dict(
            {
                str(item['id']): item['text']
                    for item in loaded if item.get('text', None)
            }, n
        )

    def to_df(self):
        """
        Convert internal TDM representation into a tabular
        Pandas DataFrame object.
        """
        return pd.DataFrame.from_dict(self.sparse, orient='index')\
                           .fillna(value=0)\
                           .astype(dtype=int)\
                           .sort(axis=0, inplace=False)

    def to_sparse(self):
        """
        Get the SparseDataFrame representation
        """
        return self.to_df().to_sparse(fill_value=0)

    def sum_columns(self):
        return np.sum(self.to_df()).sort(inplace=False, ascending=False).astype(int)

    def write_csv(self, filename):
        """
        Write term-document matrix to a CSV file.

        :param filename: Name of the output file (e.g. `mymatrix.csv`).
        :type  filename: str

        """
        self.to_df().to_csv(filename)

    def to_doc_id(self):
        df = self.to_df()
        return df.T > 0

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

def get_ad_ids(tdm, term):
    df = tdm.to_df()
    try:
        df.index.name = 'ad_id'
        df.reset_index(inplace=True)
    except:
        pass
    return(set(df[df[term]!=0]["ad_id"]))

def query_ad_ids(tdm, term):
    ads = get_ad_ids(tdm, term)
    ad_ids = []
    for ad_id in ads:
        ad_ids.append({ "term" : {"_id" : int(ad_id) }})

    query = {
            "filtered" : {
                 "filter" : {
                    "bool" : {
                      "should" : ad_ids
                        }
                    }
                }
            }

    payload = {
                "size": len(ad_ids),
                "query" : query
               }

    results = es.search(body=payload)
    output     = dict()
    for hit in results['hits']['hits']:
        try:
            output[hit['_id']] = hit["_source"]["text"]
        except KeyError:
            pass
    return output

def get_connected_components_jaccard_similarity(tdm, term, output, jaccard_threshold=.2):
    G = nx.Graph()
    similarity = {}
    ads = list(output)
    G.add_nodes_from(ads)
    for i in range(0,len(ads)-1):
        a = []
        for j in range(i+1,len(ads)):
            similarity[(ads[i],ads[j])] =  round(distance.jaccard(output[ads[i]], output[ads[j]]),3)
    for k, v in similarity.items():
        if v <= jaccard_threshold:
            G.add_edge(k[0],k[1])
    connected_components = nx.number_connected_components(G)
    return connected_components
