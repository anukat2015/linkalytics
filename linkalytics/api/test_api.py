from unittest import TestCase
from flask    import current_app

from .. import create_app

from .. environment import cfg

class APITest(TestCase):

    def setUp(self):
        self.app = create_app(cfg)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)
