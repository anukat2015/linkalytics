from unittest import TestCase

from . import extract

class TestExtract(TestCase):

    def test_common_crawl(self):
        self.assertTrue(any(extract.filter_docs(extract.common_crawl('http://www.toysrus.com'))))
