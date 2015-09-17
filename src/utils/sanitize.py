import html.parser

# strip all HTML tags from the text (except <a href="..."></a>)
# modified from http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
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
