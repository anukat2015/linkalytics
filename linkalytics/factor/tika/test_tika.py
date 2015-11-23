import redis

from unittest import TestCase

from . import extract, tika

from ... environment import cfg

redis_instance = redis.Redis(host=cfg['redis']['host'])

class TestExtract(TestCase):

    def test_common_crawl(self):
        self.assertTrue(any(extract.filter_docs(extract.common_crawl('http://www.toysrus.com'))))


class TestTika(TestCase):

    def test_redis_save(self):
        self.assertTrue(any(tika.redis_load('http://toysrus.com', redis_instance)))

