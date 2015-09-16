import tweepy
import logging
import time
import urllib
import html.parser
import re
from .. environment import cfg
from .. utils import retry

logging.basicConfig()
log = logging.getLogger("linkalytics.twitter")

auth = tweepy.OAuthHandler(cfg.TWITTER_CONSUMER.KEY, cfg.TWITTER_CONSUMER.SECRET)
auth.set_access_token(cfg.TWITTER_ACCESS.KEY, cfg.TWITTER_ACCESS.SECRET)
api = tweepy.API(auth)

twitter_regex = re.compile('twitter\s*-*@*:*(\.com\/)?_*\.*\s*([^\s]*)',re.IGNORECASE)

@retry(on=tweepy.error.TweepError)
def get_user(twitter_id):
	return api.get_user(twitter_id)

@retry(on=tweepy.error.TweepError)
def get_tweets(twitter_id):
	return [tweet.text for tweet in api.user_timeline(twitter_id)]

@retry(on=tweepy.error.TweepError)
def get_friends(user):
	if user is not None:
		return [f.screen_name for f in user.friends()]
	return None

@retry(on=tweepy.error.TweepError)
def get_followers(user):
	if user is not None:
		return [f.screen_name for f in user.followers()]
	return None

def run(node):
	results = []
	for identity in re.finditer(twitter_regex, node['text']):
		twitter_id = identity.group(2)  # username is always the second group in the regex match
		user = get_user(twitter_id)
		if user is not None:
			output_node = {
				'id'			: twitter_id,
				'friends'		: get_friends(user),
				'followers'		: get_followers(user),
				'background_pic': user.profile_background_image_url_https,
				'profile_pic'	: user.profile_image_url_https,
				'description'	: user.description,
				'name'			: user.name,
				'profile_url'	: user.entities['url']['urls'][0]['expanded_url'] if 'url' in user.entities else None,
				'tweets'		: get_tweets(twitter_id)
			}
		else:
			output_node = {
				'id'			: twitter_id,
				'friends'		: None,
				'followers'		: None,
				'background_pic': None,
				'profile_pic'	: None,
				'description'	: None,
				'name'			: None,
				'profile_url'	: None,
				'tweets'		: get_tweets(twitter_id)
			}
		results.append(output_node)
	return {'twitter': results}
