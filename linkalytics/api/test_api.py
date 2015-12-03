from unittest import TestCase
from base64   import b64encode
from flask    import current_app

from .. import create_app

from .. environment import cfg

class APITest(TestCase):

    def setUp(self):
        self.app = create_app(cfg)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def get_api_headers(self, username, password):
        auth = b64encode('{username}:{password}'.format(username=username, password=password).encode('utf-8')).decode('utf-8')
        return {
            'Authorization': 'Basic {auth}'.format(auth=auth)

        }

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_page_not_found(self):
        response = self.client.post(
            '/wrong_path',
            content_type='application/json',
            headers=self.get_api_headers(cfg['api']['username'], cfg['api']['password'])
        )
        self.assertTrue(response.status_code == 404)

