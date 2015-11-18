import instagram
import logging
import re
import requests

from ... environment import cfg
from ... utils import sanitize, uniq_lod, push_url

logging.basicConfig()
log = logging.getLogger("linkalytics.instagram")

api = instagram.client.InstagramAPI(
	client_id	= cfg['instagram']['client_id'],
	client_secret	= cfg['instagram']['client_secret'],
	access_token	= cfg['instagram']['access_token'],
)
instagram_regex = re.compile('instagram\s*-?@?:?;?(\.com\/)?_?\.?\s*([^\s^\/]*)',re.IGNORECASE)

def get_user_id(username):
    return get_instagram('users/search', q=username)['data'][0]['id']

def get_user(uid):
    return get_instagram('users/{uid}'.format(uid=uid))['data']

def get_recent_posts(uid):
    return get_instagram('users/{uid}/media/recent'.format(uid=uid))['data']

@push_url('https://api.instagram.com/v1/')
def get_instagram(endpoint, **kwargs):
    query = {
		'url': endpoint,
		'params': {
			'access_token': cfg['instagram']['access_token']
		}
	}
    query['params'].update(kwargs)
    return query

def run(node):
    results = []
    text = sanitize(node['text'])

    for identity in re.finditer(instagram_regex, text):
        username = identity.group(2).lower()  # username is always the second group in the regex match
        uid = get_user_id(username)

        user, posts = get_user(uid), get_recent_posts(uid)
        user['posts'] = posts

        results.append(user)

    return {'instagram': uniq_lod(results, 'id')}
