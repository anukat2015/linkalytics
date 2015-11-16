import instagram
import logging
import re
import requests

from environment import cfg
from utils import sanitize, uniq_lod

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

	# def get_profile_picture(self,instagram_id):
	# 	profile_picture_request = requests.get('https://api.instagram.com/v1/users/'+str(instagram_id)+'?access_token=' + self.INSTAGRAM_ACCESS_TOKEN)
	# 	profile_picture = profile_picture_request.json()['data']['profile_picture']
	# 	return profile_picture

	# def get_recent_media(self,instagram_id):
	# 	recent_media_request = requests.get('https://api.instagram.com/v1/users/'+str(instagram_id)+'/media/recent?access_token=' + self.INSTAGRAM_ACCESS_TOKEN)
	# 	recent_media = recent_media_request.json()
	# 	return recent_media

	# def get_likers(self,recent_media):
	# 	return [[x['username'],x['id'],x['full_name'],x['profile_picture']] for datum in recent_media['data'] for x in datum['likes']['data']]

	# def get_all_instagram_tags(self,recent_media):
	# 	return list(set(flatten([x['tags'] for x in recent_media['data']])))

	# def get_media_ids_and_posttimes(self,recent_media):
	# 	return [[x['id'],x['created_time']] for x in recent_media['data']]

	# def get_commentors(self,recent_media):
	# 	commentors = []
	# 	for media in recent_media['data']:
	# 		media_request = requests.get('https://api.instagram.com/v1/media/'+str(media['id'])+'/comments?access_token=' + self.INSTAGRAM_ACCESS_TOKEN)
	# 		media_json = media_request.json()
	# 		commentors += [
	# 			[datum['from']['username'],
	# 			datum['from']['id'],
	# 			datum['from']['full_name'],
	# 			datum['from']['profile_picture'],
	# 			datum['text']]
	# 			for datum in media_json['data']]
	# 	return commentors


# ig_id = int(self.get_instagram_id(ig_username))
#
# if ig_id != 0:
# 	recent_media = self.get_recent_media(ig_id)
# 	node['instagram_followers'] = ';'.join([str(f)for f in self.api.user_followed_by(str(ig_id))[0]])
# 	node['instagram_follows'] = ';'.join([str(f)for f in self.api.user_follows(str(ig_id))[0]])
# 	node['instagram_tags'] = self.get_all_instagram_tags(recent_media)
# 	node['instagram_profile_picture'] = self.get_profile_picture(ig_id)
#
# 	node['instagram_likers'] = ','.join(flatten(self.get_likers(recent_media)))
# 	node['get_media_ids_and_posttimes'] = ','.join(flatten(self.get_media_ids_and_posttimes(recent_media)))
# 	node['get_commentors'] = ','.join(flatten(self.get_commentors(recent_media)))

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
