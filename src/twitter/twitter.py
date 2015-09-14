import tweepy
import logging
import time
import urllib
import html.parser
import re
from .. environment import cfg

logging.basicConfig()
log = logging.getLogger("linkalytics.twitter")

def is_rate_limited(error):
	return isinstance(error.message, list) and \
		len(error.message) == 1 and \
		isinstance(error.message[0], dict) and \
		error.message[0]['code'] == 88

def with_retries(f, *args, **kwargs):
	attempts = 0
	num_backoff = kwargs.pop('num_backoff', 10)
	result = None
	while result is None:
		try:
			result = f(*args, **kwargs)
		except tweepy.error.TweepError as e:
			if is_rate_limited(e) and attempts < num_backoff:
				attempts += 1
				log.debug("Retrying, attempt %d out of %d" % (attempts, num_backoff))
				time.sleep(60*attempts)
			else:
				log.error(e)
				# usually, the user is deleted or we don't have access
				break
	return result

class HTMLStripper(html.parser.HTMLParser):
	def __init__(self):
		super(HTMLStripper, self).__init__(convert_charrefs=True)
		self.reset()
		self.fed = []

	def handle_starttag(self, tag, attrs):
		attrs = dict(attrs)
		if tag == 'a' and 'href' in attrs:
			self.fed.append(" " + attrs['href'] + " ")

	def handle_data(self, d):
	    self.fed.append(d)

	def get_data(self):
	    return ''.join(self.fed)

class Twitter:
	def __init__(self):
		auth = tweepy.OAuthHandler(cfg.TWITTER_CONSUMER.KEY, cfg.TWITTER_CONSUMER.SECRET)
		auth.set_access_token(cfg.TWITTER_ACCESS.KEY, cfg.TWITTER_ACCESS.SECRET)
		self.api = tweepy.API(auth)

	def get_twitter_username(self,node):
		if node['text']:

			s = HTMLStripper()
			text = node['text']
			s.feed(text)
			s.close()
			text = s.get_data()
			print(text)
			#node['escaped_text'] = text

			expression = re.compile('twitter\s*-?@?:?(\.com\/)?_?\.?\s*[^\s]*',re.IGNORECASE)
			twitter_user_name = []
			try:
				regexp_match = re.findall(expression,text)
				if len(regexp_match) > 0:
					for raw in regexp_match:
						twitter_user_name.append(re.sub("twitter\s*-?@?:?(\.com\/)?_?\.?\s*", "", raw))
			finally:
				return twitter_user_name
		else:
			return None

	def enhance(self, node, num_backoff=10):
		if 'text' in node and node['text']:
			identities = self.get_twitter_username(node)
			# make sure it's a list
			# identities = node['twitter'] if isinstance(node['twitter'], list) else [node['twitter']]
			print(identities)
			# node['twitter'] contains a *list* of possible twitter handles
			for identity in identities:
				# twitter entries look like "http://twitter.com/foobar".
				# so we split along "/" and take the last one
				identity = identity.split("/")[-1]

				# some "identities" then look like url queries, so we
				# parse them as 'urls' and only keep the path
				identity = urllib.parse.urlparse(identity).path

				print(identity)

				# some twitter handles begin with '@', so we strip them
				# this might not be a good idea since the scraper may
				# have just picked up a retweet
				if "@" == identity[0]:
					identity = identity[1::]
				log.debug(identity)

				user = with_retries(self.api.get_user, identity, num_backoff=num_backoff)
				if user is None:
					# we abort the attempt to get twitter data
					continue

				log.debug(user)

				tweets = with_retries(self.api.user_timeline, identity, num_backoff=num_backoff)
				if tweets is None:
					continue

				friends = with_retries(lambda x: [f.screen_name for f in x.friends()], user, num_backoff=num_backoff)
				if friends is None:
					continue

				followers = with_retries(lambda x: [f.screen_name for f in x.followers()], user, num_backoff=num_backoff)
				if followers is None:
					continue

				node['twitter_friends'] = friends
				node['twitter_followers'] = followers
				node['twitter_background_pic'] = user.profile_background_image_url_https
				node['twitter_profile_pic'] = user.profile_image_url_https
				node['twitter_description'] = user.description
				node['twitter_name'] = user.name
				node['twitter_profile_url'] = user.entities['url']['urls'][0]['expanded_url'] if 'url' in user.entities else None
				node['tweets'] = [f.text for f in tweets]
		return node

me = Twitter()
def run(node):
	return me.enhance(node)
