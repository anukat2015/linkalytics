from . import factor
from elasticsearch import Elasticsearch
import json
import urllib3
from .. environment import cfg
import logging

es_log = logging.getLogger("elasticsearch")
es_log.setLevel(logging.CRITICAL)
urllib3_log = logging.getLogger("urllib3")
urllib3_log.setLevel(logging.CRITICAL)


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
    """
    combine the output of two factors into a single dictionary
    """
    for k1 in addition:
        if k1 not in original:
            original[k1] = {}
        for k2 in addition[k1]:
            original[k1][k2] = addition[k1][k2]
    return original


def combine_multi_factors(factors):
    """
    combine the output of multiple factors into a single dictionary
    """
    original = factors[0]
    for i in factors[1:len(factors)]:
        if i:
            original = combine_two_factors(original, i)
    return original


def generate_factor_outputs(ad_id, factor_type, url, social_media=False):
    """
    generate_factor_outputs takes an ad_id and specific factor type (e.g. phone, text, email, etc.) to output suggestions. If there are no suggestions, the function returns None. If there is a TypeError, the function returns None.
    """
    try:
        factor = ESFactor(factor_type, url)
        suggestions = factor.suggest(ad_id, social_media)
        # print(factor_type, len(suggestions[ad_id][factor_type]))
        if len(suggestions[ad_id][factor_type]) == 0:
            return None
        else:
            return suggestions
    except TypeError:
        # print(factor_type, 0)
        return None


def factor_constructor(seed, url, factors):
    """
    factor_contstructor generates multiple factor outputs and combines the outputs into a single dictionary
    """
    factor_outputs = []
    for i in factors:
        factor_outputs.append(generate_factor_outputs(seed, i, url))
    # twitter = generate_factor(seed, "text", url, True)
    combo = combine_multi_factors(factor_outputs)
    return combo


def extend(seed, url, factors1, item, factors2):
    """
    extend iterates on factor_constructor and adds data to your original dictionary based on related items
    """
    original = factor_constructor(seed, url, factors1)
    x = {}
    x["original"] = original
    x["extended"] = {}
    ad_ids_2 = set()
    for k1 in original[seed]:
        for k, v in original[seed][k1].items():
            if (k == item) or (item == "all"):
                for i in original[seed][k1][k]:
                    ad_ids_2.add(i)
    for ad_id in ad_ids_2:
        addition = factor_constructor(ad_id, url, factors2)
        print(".")
        for k1 in addition:
            if k1 not in original:
                x["extended"][k1] = {}
                for k2 in addition[k1]:
                    for k3 in addition[k1][k2]:
                        if original[seed][k2][k3]:
                            x["extended"][k1] = {}
                        else:
                            x["extended"][k1][k2] = {}
                            x["extended"][k1][k2][k3] = addition[k1][k2][k3]
    return x




def main():
    url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
    ad_id = "63166071"
    # ad_id = "71046685"
    # ad_id = "31318107"
    # ad_id2 = "62442471"
    """
    Use...
    """
    a = factor_constructor(ad_id, url, ["phone", "email", "text", "title"])
    print(json.dumps(a))
    print("_________")
    b = extend(ad_id, url, ["phone", "email", "text", "title"], "5023030050", ["phone"])
    print(json.dumps(b))
