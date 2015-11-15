from unittest import TestCase

from . entropy import TermDocumentMatrix
from . entropy import ngrams

class TestLanguages(TestCase):

    document = 'hello world hello world'
    tdm      = TermDocumentMatrix()

    tdm.load_dict({0: document})

    def test_tdm(self):
        self.assertDictEqual(
            self.tdm.term2doc(), {'hello world': [0]}
        )

    def test_ngrams(self):
        self.assertEqual(
            ngrams(self.document, 2), ['hello world', 'world hello', 'hello world']
        )
