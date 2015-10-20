import re
import nltk
import csv
import os

def ngram_tokenize(document, n):
    """
    Function to clean your document, remove common punctuation marks,
    split into n-grams, and return a list of n-grams that may contain
    duplicates
    """

    raw = document.lower()
    raw = re.sub("\\xbb", ' ', raw)
    raw = re.sub("\.|\,|\:|\;", ' ', raw)
    #Create your ngrams
    ngs = nltk.ngrams(raw.split(), n)
    #compute frequency distribution for all the bigrams in the text
    fdist = nltk.FreqDist(ngs)
    token = []
    for k, v in fdist.items():
        x = 1
        while x <= v:
            token.append((" ".join(k)).encode("utf-8"))
            x += 1
    return token


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


class TermDocumentMatrix(object):
    """
    ***Code adapted from https://github.com/ytmytm/python-textmining***
    Class to efficiently create a term-document matrix.

    The only initialization parameter is a tokenizer function, which should
    take in a single string representing a document and return a list of
    strings representing the n-grams in the document.

    Use the add_doc method to add a document. Use the
    write_csv method to output the current term-document matrix to a csv
    file. You can use the rows method to return the rows of the matrix if
    you wish to access the individual elements without writing directly to a
    file.

    """

    def __init__(self, tokenizer=ngram_tokenize):
        """Initialize with tokenizer to split documents into words."""
        self.tokenize = tokenizer
        self.sparse = []
        self.doc_count = {}

    def add_doc(self, document, n=2):
        """Add document to the term-document matrix."""
        words = self.tokenize(document, n)

        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        self.sparse.append(word_counts)

        for word in word_counts:
            self.doc_count[word] = self.doc_count.get(word, 0) + 1

    def rows(self, cutoff=2):
        """Helper function that returns rows of term-document matrix."""

        words = [
            word for word in
                self.doc_count if self.doc_count[word] >= cutoff
        ]
        yield words

        for row in self.sparse:
            data = [row.get(word, 0) for word in words]
            yield data

    def write_csv(self, filename, cutoff=2):
        """
        Write term-document matrix to a CSV file.

        filename is the name of the output file (e.g. 'mymatrix.csv').
        cutoff is an integer that specifies only words which appear in
        'cutoff' or more documents should be written out as columns in
        the matrix.

        """
        f = csv.writer(open(filename, 'wb'))
        for row in self.rows(cutoff=cutoff):
            f.writerow(row)

def search(search_term, size, es, phrase=True):
    match_type = 'match_phrase' if phrase else 'match'
    output     = set()
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
        output.add(hit["_source"]["text"])

    return output


def main(n, query, es):
    results  = search(query, 100, es, True)
    tdm      = TermDocumentMatrix()

    for result in results:
        tdm.add_doc(result, n)

    return tdm
