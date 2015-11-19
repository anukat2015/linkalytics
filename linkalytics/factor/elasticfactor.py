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


def extend(data, url, item, factors2, degree):
    """
    extend iterates the original dictionary and adds the original based on hits; the seed refers to the input ad_id, the url is for Elastic Search, the factors1 is for the initial factors, the item is what you iterate on, and factors2 is the second list of factors for iterating
    """
    existing_data = set()
    for i in data:
        existing_data.add(i)
    print("************", "\n", existing_data)
    data[degree] = {}
    ad_ids_2 = set()
    for k1, v1 in data["original"].items():
        for k2, v2 in v1.items():
            if (k2 == item) or (item == "all"):
                for v3 in v2.values():
                    for i in v3:
                        ad_ids_2.add(i)
    for ad_id in ad_ids_2:
        addition = factor_constructor(ad_id, url, factors2)
        print(".")
        try:
            for k1 in addition:
                if k1 not in data["original"]:
                    for k2 in addition[k1]:
                        for k3 in addition[k1][k2]:
                            for j in existing_data:
                                check = {}
                                for key in data[j].keys():
                                    try:
                                        if data[j][key][k2][k3]:
                                            check.add(1)
                                    except:
                                        pass
                            if len(check) == 0:
                                pass
                            else:
                                data[degree][k1] = {}
                                data[degree][k1][k2] = {}
                                data[degree][k1][k2][k3] = addition[k1][k2][k3]
        except TypeError:
            pass

    return data


def main():
    url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
    ad_id = "63166071"
    # ad_id = "71046685"
    # ad_id = "31318107"
    # ad_id2 = "62442471"
    """
    Here's an example using the factors and the factor constructor
    """
    a = factor_constructor(ad_id, url, ["phone", "email", "text", "title"])
    x = {}
    x["original"] = a
    print(json.dumps(x))
    b = extend(x, url, "all", ["phone", "email", "text", "title"], "ext2")
    print(json.dumps(b))
    c = extend(b, url, "all", ["phone"], "ext3")
    print(json.dumps(c))

    ad_ids_extended = set()
    for k1 in b:
        for k2 in b[k1]:
            for k3 in b[k1][k2]:
                for k4 in b[k1][k2][k3]:
                    for k5 in b[k1][k2][k3][k4]:
                        ad_ids_extended.add(k5)
    print("____+_+____")
    print(ad_ids_extended)
