from . import factor
from elasticsearch import Elasticsearch
import json
import urllib3
from .. environment import cfg

urllib3.disable_warnings()


class ESFactor(factor.Factor):
    """
    ESFactor is a class to build exact match factors on the fly with Elastic Search. This includes: phone, e-mail, social media username, title, and text.
    """

    def __init__(self, name, url, size=500):
        super(ESFactor, self).__init__(name)
        self.size = size
        self.es = Elasticsearch(
                    [url],
                    port=443,
                    use_ssl=False,
                    verify_certs=False
                    )

    def lookup(self, ad_id):
        """
        lookup takes an ad_id and returns field values
        """
        payload = {
            "size": self.size,
            "query": {
                "ids": {
                    "values": [ad_id]
                }
            }
        }
        results = self.es.search(body=payload)
        field_vals = []
        for hit in results['hits']['hits']:
            if self.field in hit["_source"]:
                if isinstance(hit["_source"][self.field], list):
                    for item in hit["_source"][self.field]:
                        field_vals.append(item)
                else:
                    field_vals.append(hit["_source"][self.field])
        return field_vals

    def reverse_lookup(self, field_value):
        """
        reverse_lookup takes a field_value and returns ad_ids
        """
        payload = {
                "size": self.size,
                "query": {
                    "match_phrase": {
                        self.field: field_value
                    }
                }
            }
        results = self.es.search(body=payload)
        if results['hits']['total']==0: #If the Elastic Search returns 0 results, then change the search field from self.field to all and search again. This solves the problem or poor indexing where a term like missblakebanks shows up in "_all" but not in "text"
            payload = {
                "size": self.size,
                "query": {
                    "match_phrase": {
                        "_all": field_value
                    }
                }
            }
            results = self.es.search(body=payload)
        ids = []
        for hit in results['hits']['hits']:
            ids.append(hit["_id"])
        return ids


def combine_two_factors(original, addition):
    for k1 in addition:
        if k1 not in original:
            original[k1] = {}
        for k2 in addition[k1]:
            original[k1][k2] = addition[k1][k2]
    return original


def combine_multi_factors(original, additions):
    for i in additions:
        if i:
            original = combine_two_factors(original, i)
    return original


def generate_factor(ad_id, factor_type, url, social_media=False):
    try:
        factor = ESFactor(factor_type, url)
        suggestions = factor.suggest(ad_id, social_media)
        print(factor_type, len(suggestions[ad_id][factor_type]))
        return suggestions
    except TypeError:
        print(factor_type, 0)
        return None

def factor_constructor(ad_id, url):
    print(ad_id)
    phone = generate_factor(ad_id, "phone", url)
    email = generate_factor(ad_id, "email", url)
    text = generate_factor(ad_id, "text", url)
    title = generate_factor(ad_id, "title", url)
    twitter = generate_factor(ad_id, "text", url, True)
    combo = combine_multi_factors(phone, [email, text, title, twitter])
    return combo

def get_node(ad_id, url, key=True):
    combo1 = factor_constructor(ad_id, url)
    datum = set()
    for factors in combo1.values():
        for factor in factors:
            for k,v in combo1["31318107"][factor].items():
                if key is True:
                    datum.add(k)
                else:
                    for i in v:
                        datum.add(i)
    return(datum)


def main():
    url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
    # ad_id = "63166071"
    # ad_id = "71046685"
    datum = get_node("31318107", url, True)
    print(datum)
    combo1 = factor_constructor("31318107", url)
    print(json.dumps(combo1))
    # combo2 = factor_constructor("31195256", url)
