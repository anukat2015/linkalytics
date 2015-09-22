import html.parser
from nltk.corpus import stopwords

STOP = stopwords.words('english')
def sanitize(text, remove_stopwords=True):
    """ This sanitizes post text by removing all HTML tags and appending
        those in <a href="..."></a> to the end of the text.

        It also removes English stopwords.

        :param text:    a block of text we want to sanitize
        :returns:       the sanitized block of text; any anchor (<a>)
                        tags have their `href` field stored at the end,
                        delimited by the sentinel `:HREFS:`
    """
    s = HTMLStripper()
    s.feed(text)
    s.close()
    text = s.get_data()

    if remove_stopwords:
        words = (s.lower() for s in text.split() if s.lower() not in STOP)
    else:
        words = (s.lower() for s in text.split())

    return ' '.join(words)

# strip all HTML tags from the text (except <a href="..."></a>)
# modified from http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class HTMLStripper(html.parser.HTMLParser):
    def __init__(self):
        super(HTMLStripper, self).__init__(convert_charrefs=True)
        self.reset()
        self.fed = []
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.hrefs.append(attrs['href'])

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed) + " :HREFS: " + ' '.join(self.hrefs)
