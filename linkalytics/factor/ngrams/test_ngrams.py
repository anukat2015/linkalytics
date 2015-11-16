from unittest import TestCase

from . entropy import TermDocumentMatrix
from . entropy import ngrams


document = 'hello world hello world'
tdm      = TermDocumentMatrix()

tdm.load_dict({0: document})


class TestTDM(TestCase):

    def test_term2doc(self):
        self.assertDictEqual(
            tdm.term2doc(), {'hello world': [0]}
        )

    def test_ngrams(self):
        self.assertEqual(
            ngrams(document, 2), [
                'hello world', 'world hello', 'hello world'
            ]
        )