import collections
import itertools
import string
import json
import re

import pandas as pd
import numpy  as np
import scipy  as sp
import distance
import networkx as nx

from scipy import sparse
from enchant.checker import SpellChecker

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

    def add_doc(self, key, document, n=2, remove_duplicates=True):
        """
        Add document to the term-document matrix

        :param document: str
            String to be tokenized

        :param n: int
            N-Grams to split using the tokenizer

        :param remove_duplicates: bool
            Flag that sets whether to add duplicate entries
        """
        counter = collections.Counter(self.tokenizer(document, n))
        cutoff  = {
            k: 1 for k, v in counter.items()
                if v >= self.cutoff
        }
        if remove_duplicates and cutoff in self.sparse.values():
            return

        if cutoff:
            self.sparse[key] = cutoff

    def load_json(self, filepath, *args, **kwargs):
        """
        Batch load documents from a fully qualified JSON file.

        :param filepath: str
            File directory path

        Also takes any arguments allowed by

            TermDocumentMatrix.add_doc(*args, **kwargs)

        """
        loaded = json.load(open(filepath))

        if isinstance(loaded, list):
            self.load_list(loaded, *args, **kwargs)
        else:
            self.load_dict(loaded, *args, **kwargs)

    def load_dict(self, loaded, *args, **kwargs):
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
            self.add_doc(key, document, *args, **kwargs)

    def load_list(self, loaded, *args, **kwargs):
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
            }, *args, **kwargs
        )

    def to_df(self):
        """
        Convert internal TDM representation into a tabular
        Pandas DataFrame object.

        :return: df
        :rtype: pd.DataFrame

        """
        return pd.DataFrame.from_dict(self.sparse, orient='index')\
                           .fillna(value=0)\
                           .astype(np.uint16)\
                           .sort(axis=0, inplace=False)

    def to_sparse(self):
        """
        Get the SparseDataFrame representation
        """
        return sparse.csr_matrix(pd.DataFrame.as_matrix(self.to_df()), dtype=int)

    def save_sparse(self, filename):
        return sp.io.mmwrite(filename, self.to_sparse())
        
    def load_sparse(self, filename):
        return sp.io.mmread(filename)

    def term2doc(self):
        """
        For every term get the documents associated with the term.

        :return: docs
        :rtype: dict
        """
        grams = set()

        for i in self.sparse.values():
            grams.update(i.keys())

        docs = dict.fromkeys(grams)

        for k, v in self.sparse.items():
            for word in v.keys():
                if not docs[word]:
                    docs[word] = [k]
                else:
                    docs[word].append(k)

        return docs

    def sum_columns(self):
        """
        Sum up all the table columns

        :return: columns
        :rtype: pd.Series
        """
        c = collections.Counter()

        for key in self.sparse:
            c.update(self.sparse[key])

        return pd.Series(c).sort(inplace=False, ascending=False)


    def write_csv(self, filename):
        """
        Write term-document matrix to a CSV file.

        :param filename: Name of the output file (e.g. `mymatrix.csv`).
        :type  filename: str

        """
        self.to_df().to_csv(filename, chunksize=128)

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

def query_ad_ids(es, tdm, term, value="text"):
    ads = get_ad_ids(tdm, term)
    ad_ids = []
    for ad_id in ads:
        ad_ids.append({ "term" : {"_id" : int(ad_id) }})
    if value == "text":
        size = len(ad_ids)
    else:
        size = 500
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
                "size": size,
                "query" : query
               }

    results = es.search(body=payload)
    output     = dict()
    for hit in results['hits']['hits']:
        try:
            output[int(hit['_id'])] = hit["_source"][value]
        except KeyError:
            pass
    return output

def query_phones(es, phones):
    clean_phones = set()
    for i in phones.values():
        if isinstance(i,str):
            clean_phones.add(int(i))
        elif isinstance(i,list):
            for j in i:
                clean_phones.add(int(j))
    query_phones = []
    for phone in clean_phones:
        query_phones.append({ "term" : {"phone" : phone }})

    query = {
            "filtered" : {
                 "filter" : {
                    "bool" : {
                      "should" : query_phones
                        }
                    }
                }
            }

    payload = {
                "size": 500,
                "query" : query
               }

    results = es.search(body=payload)
    output     = dict()
    for hit in results['hits']['hits']:
        try:
            output[int(hit['_id'])] = hit["_source"]["text"]
        except KeyError:
            pass
    return output

def get_connected_components_jaccard_similarity(documents, jaccard_threshold=.2):
    G = nx.Graph()
    similarity = {}
    ads = list(documents)
    G.add_nodes_from(ads)

    for i in range(0,len(ads)-1):
        a = []
        for j in range(i+1,len(ads)):
            similarity[(ads[i],ads[j])] =  round(distance.jaccard(documents[ads[i]], documents[ads[j]]),3)

    for k, v in similarity.items():
        if v <= jaccard_threshold:
            G.add_edge(k[0],k[1])

    connected_components = set()

    for i in G.nodes():
        connected_components.add(str(sorted(nx.node_connected_component(G, i))))

    return connected_components

def filter_ngrams(terms, spelling=False, singletons=True, contains_numeric=False, contains_alpha=False, contains_non_alphanumeric=False):
    chkr = SpellChecker("en_US")
    print(len(terms), "n-grams before filter")
    if spelling == True:
        for k in terms.keys():
            chkr.set_text(k)
            errors = set()
            for err in chkr:
                errors.add(err.word)
            if len(errors) > 0:
                del terms[i]
    if singletons == True:
        for k,v in terms.items():
            if len(v) == 1:
                del terms[k]
    if contains_numeric == True:
        for k in terms.keys():
            if re.search("[^0-9]",k):
                del terms[k]
    if contains_alpha == True:
        for k in terms.keys():
            if re.search("[^a-z]",k):
                del terms[k]
    if contains_non_alphanumeric == True:
        for k in terms.keys():
            if re.search("[^[:alnum:]]",k):
                del terms[k]
    print(len(terms), "n-grams after filter")
    return terms

