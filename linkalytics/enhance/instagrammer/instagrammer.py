import logging
import re

from ... environment import cfg
from ... utils import sanitize, uniq_lod, push_url

logging.basicConfig()
log = logging.getLogger("linkalytics.instagram")

instagram_regex = re.compile('instagram\s*-?@?:?;?(\.com\/)?_?\.?\s*([^\s^\/]*)',re.IGNORECASE)

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

def get_user_id(username):
    return get_instagram('users/search', q=username)['data'][0]['id']

def get_user(uid):
    return get_instagram('users/{uid}'.format(uid=uid))['data']

def get_recent_posts(uid):
    posts  = get_instagram('users/{uid}/media/recent'.format(uid=uid))['data']
    output = {
        post['id']: {
            'link'       : post['link'],
            'likes'      : post['likes']['count'],
            'tags'       : post['tags'],
            'caption'    : post['caption']['text'],
            'attribution': post['attribution'],
        }  for post in posts
    }
    return output

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
