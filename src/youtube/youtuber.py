from apiclient.discovery import build
import re
import logging

from .. environment import cfg

logging.basicConfig()
log = logging.getLogger("linkalytics.youtube")

YOUTUBE_DEVELOPER_KEY = cfg.YOUTUBE.KEY
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube_regex = re.compile('youtube\.com\/embed\/([^\s]*)|youtu\.be\/([^\s]*)|youtube\.com\/watch\?[^\s]*v=([^\s]*)',re.IGNORECASE)
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
	developerKey=YOUTUBE_DEVELOPER_KEY)

def get_username_from_video(identity):
	# seed_html=requests.get(identity).content #identity represents embedded Youtube videos
	# seedsoup=BeautifulSoup(seed_html)
	# youtubelink=seedsoup.find_all("link")[0].get("href")
	vid_search = youtube.search().list(
		q=identity,
		part="id,snippet",
		maxResults=1
		).execute()

	user = vid_search.get("items", [])[0]["snippet"]["channelTitle"]
	return user

def run(node):
	return {
		'youtube': list({
			'video_id': next(filter(None,identity)),
			'username': get_username_from_video(identity)
		} for identity in re.finditer(youtube_regex, node['text']))
	}
