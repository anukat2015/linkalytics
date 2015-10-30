# encoding: utf-8

import collections
import unicodedata
import itertools
import string
import json
import re
import os

import pandas as pd
import numpy  as np
import scipy  as sp
import distance
import networkx as nx

from scipy import sparse
from enchant.checker import SpellChecker

def n_grams(document, n, normalize=True, numbers=True):
    numbers = 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'
    table   = dict((ord(char), None) for char in string.punctuation)
    raw     = re.sub('<[^<]+?>', '', document).lower().translate(table)

    # Replace spelled out numbers with actual numbers
    if numbers:
        for word, num in list(zip(numbers, range(10))):
            raw = raw.replace(word, str(num))
    if normalize:
        raw     = ''.join(c for c in raw if not unicodedata.combining(c))

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
            if isinstance(document, dict) and 'text' in document:
                self.add_doc(key, document.get('text', None), *args, **kwargs)
            elif isinstance(document, str):
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
        df = self.to_df()
        return sparse.csr_matrix(pd.DataFrame.as_matrix(df), dtype=int), df.index, df.columns

    def save_sparse(self, filename):
        matrix, index, columns = self.to_sparse()
        name, _ = filename.rsplit('.')

        sp.io.mmwrite(filename, matrix)

        index.to_series().to_csv('.'.join([name, 'index']))
        columns.to_series().to_csv('.'.join([name, 'columns']))

    @classmethod
    def load_sparse(cls, filename):
        matrix  = sp.io.mmread(filename)
        name, _ = filename.rsplit('.')

        index   = pd.Series.from_csv('.'.join([name, 'index']))
        columns = pd.Series.from_csv('.'.join([name, 'columns']))

        return pd.DataFrame(matrix.todense(), index=index, columns=columns).to_sparse(fill_value=0)

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

        sums = pd.Series(c).sort(inplace=False, ascending=False)

        return sums[sums > self.cutoff]


    def write_csv(self, filename):
        """
        Write term-document matrix to a CSV file.

        :param filename: Name of the output file (e.g. `mymatrix.csv`).
        :type  filename: str

        """
        self.to_df().to_csv(filename, chunksize=128)


def query_phones(es, phones):
    clean_phones = set()
    for i in phones.values():
        if isinstance(i,str):
            clean_phones.add(int(i))
        elif isinstance(i,list):
            for j in i:
                clean_phones.add(int(j))
    query_phones_list = []
    for phone in clean_phones:
        query_phones_list.append({ "term" : {"phone" : phone }})

    query = {
            "filtered" : {
                 "filter" : {
                    "bool" : {
                      "should" : query_phones_list
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
        output[int(hit['_id'])] = {}
        try:
            output[int(hit['_id'])]["text"] = hit["_source"]["text"]
        except KeyError:
            pass
    return output

def get_connected_components_jaccard_similarity(documents, jaccard_threshold=.2, field_type="text"):
    """
        Find the connected components of documents sharing the same n-gram based on a threshold for Jaccard similarity.
    """
    document_text = {}
    for k,v in documents.items():
        try:
            document_text[k] = v[field_type]
        except:
            pass
    G = nx.Graph()
    similarity = {}
    ads = list(document_text)
    G.add_nodes_from(ads)

    for i in range(0,len(ads)-1):
        a = []
        for j in range(i+1,len(ads)):
            similarity[(ads[i],ads[j])] =  round(distance.jaccard(document_text[ads[i]], document_text[ads[j]]),3)

    for k, v in similarity.items():
        if v <= jaccard_threshold:
            G.add_edge(k[0],k[1])

    connected_components = set()

    for i in G.nodes():
        connected_components.add(str(sorted(nx.node_connected_component(G, i))))

    return connected_components

def list_features(documents, field_type="text"):
    feature = set()
    for v in documents.values():
        try:
            if feature.add(str(v[field_type]))
        except:
            pass
    return feature


def similarity_to_csv(output):
    print(output)
    with open(os.getcwd() + '/results.tsv', 'w') as g:
        cc_text = {}
        cc_phone = {}
        g.write("phrase\ttext_connected_components\ttext_ad_ids\tphone_connected_components\tphone_ad_ids\n")
        for k, v in output.items():
                    print("_______")
                    print(k)
                    print(v)
                    cc_text[k] = get_connected_components_jaccard_similarity(v, .1, "text")
                    g.write(k + "\t")
                    g.write(str(len(cc_text[k])) + "\t")
                    g.write(",".join(str(x) for x in list(cc_text[k])) + "\t")
                    cc_phone[k] = list_features(v, "phone")
                    g.write(str(len(cc_phone[k])) + "\t")
                    g.write(", ".join(cc_phone[k]) + "\n")

    g.close()

def filter_ngrams(terms, spelling=False, singletons=True, contains_numeric=False, contains_alpha=False, contains_non_alphanumeric=False):
    """
        Filter n-grams by a variety of features
    """
    chkr = SpellChecker("en_US")
    print(len(terms), "n-grams before filter")
    if spelling:
        for k in list(terms.keys()):
            chkr.set_text(k)
            errors = set()
            for err in chkr:
                errors.add(err.word)
            if len(errors) > 0:
                del terms[k]
    if singletons:
        for k,v in list(terms.items()):
            if len(v) == 1:
                del terms[k]
    if contains_numeric:
        for k in list(terms.keys()):
            if re.search("[^0-9]",k):
                del terms[k]
    if contains_alpha:
        for k in list(terms.keys()):
            if re.search("[^a-z]",k):
                del terms[k]
    if contains_non_alphanumeric:
        for k in list(terms.keys()):
            if re.search("[^[:alnum:]]",k):
                del terms[k]
    print(len(terms), "n-grams after filter")
    return terms
