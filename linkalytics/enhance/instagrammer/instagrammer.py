import instagram
import logging
import re
import requests

from ... environment import cfg
from ... utils import sanitize, uniq_lod

logging.basicConfig()
log = logging.getLogger("linkalytics.instagram")

api = instagram.client.InstagramAPI(
	client_id	= cfg['instagram']['client_id'],
	client_secret	= cfg['instagram']['client_secret'],
	access_token	= cfg['instagram']['access_token'],
)
instagram_regex = re.compile('instagram\s*-?@?:?;?(\.com\/)?_?\.?\s*([^\s^\/]*)',re.IGNORECASE)

def get_instagram_id(username):
	#It seems difficult to find the id from a username using instagramAPI - figure out if this is possible later
	instagram_request = requests.get('https://api.instagram.com/v1/users/search?access_token={}&q={}'.format(cfg['instagram']['access_token'], username))
	id_num = instagram_request.json()['data'][0]['id']
	return id_num

def get_user(user_id):
	return api.user(user_id)

def run(node):
	results = []
	text = sanitize(node['text'])
	for identity in re.finditer(instagram_regex, text):
		username = identity.group(2).lower()  # username is always the second group in the regex match
		instagram_id = get_instagram_id(username)
		output_node = {
			'id'			: instagram_id,
			'username'		: username
		}
		results.append(output_node)
	return {'instagram': uniq_lod(results, 'id')}
