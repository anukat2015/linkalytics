import logging
import re
import functools
import requests

from requests import Request
from requests.adapters import HTTPAdapter

import urllib3

urllib3.disable_warnings()

from ... environment import cfg
from ... utils       import sanitize, uniq_lod

logging.basicConfig()
log = logging.getLogger("linkalytics.twitter")

twitter_regex = re.compile('twitter\s*-*@*:*;*(\.com\/)?_*\.*\s*([^\s^\/]*)',re.IGNORECASE)

def get_session(proxy=None, max_retries=3):
    session = requests.session()
    session.mount('http://',  HTTPAdapter(max_retries=max_retries))
    session.mount('https://', HTTPAdapter(max_retries=max_retries))
    session.proxies = { 'https': proxy, 'http':  proxy } if proxy else {}
    return session

def push_url(proxy):

    def wrapper(interface):

        @functools.wraps(interface)
        def connection(*args, **kwargs):
            resource = 'api.twitter.com/1.1/'
            session = get_session(proxy=proxy)

            params  = interface(*args, **kwargs)

            if not resource in params.get('url'):
                params['url'] = resource + params['url']
            if not '://' in params.get('url'):
                params['url'] = 'https://' + params['url']

            request = Request(method='GET',
                               headers={ 'Content-Type': 'application/json' },
                               **params
            )
            response = session.send(request.prepare(), verify=False)
            return response.json()

        return connection

    return wrapper

@push_url(cfg['piscina']['proxy'])
def get_twitter(user, endpoint, **kwargs):
    query = {
        'url': endpoint,
        'params': {
            'screen_name': user
        }
    }
    query['params'].update(kwargs)
    return query


def get_friends(user, **kwargs):
    friends = get_twitter(user, 'followers/list.json', **kwargs)
    return [f.get('screen_name', None) for f in friends['users']]

def get_tweets(user, **kwargs):
    tweets = get_twitter(user, 'statuses/user_timeline.json')
    return [tweet.get('text', None) for tweet in tweets]

def get_user(user, **kwargs):
    profile = get_twitter(user, 'users/lookup.json')
    if 'errors' in profile:
        return None
    else:
        return profile[0]

def get_followers(user, **kwargs):
    followers = get_twitter(user, 'followers/list.json')
    return [follower['screen_name'] for follower in followers['users']]

def run(node):
    results = []
    text = sanitize(node['text'])
    for identity in re.finditer(twitter_regex, text):
        twitter_id = identity.group(2).lower()  # username is always the second group in the regex match
        user = get_user(twitter_id)
        if user is not None:
            output_node = {
                'id'            : twitter_id,
                'friends'       : get_friends(twitter_id, count=200),
                'followers'     : get_followers(twitter_id, count=200),
                'background_pic': user['profile_background_image_url_https'],
                'profile_pic'   : user['profile_image_url_https'],
                'description'   : user['description'],
                'name'          : user['name'],
                'profile_url'   : user['entities']['url']['urls'][0]['expanded_url'] if 'url' in user['entities'] else None,
                'tweets'        : get_tweets(twitter_id, count=200)
            }
        else:
            output_node = {
                'id'            : twitter_id,
                'friends'       : None,
                'followers'     : None,
                'background_pic': None,
                'profile_pic'   : None,
                'description'   : None,
                'name'          : None,
                'profile_url'   : None,
                'tweets'        : get_tweets(twitter_id)
            }
        results.append(output_node)
    return {'twitter': uniq_lod(results, 'id')}
