import json
import logging

import urllib3
from elasticsearch import Elasticsearch
from functools     import reduce

from . factor import FactorBase

from ... environment import cfg

es_log = logging.getLogger("elasticsearch")
es_log.setLevel(logging.CRITICAL)

urllib3_log = logging.getLogger("urllib3")
urllib3_log.setLevel(logging.CRITICAL)

urllib3.disable_warnings()

class ElasticFactor(FactorBase):

    def __init__(self, url, size=500):
        """
        :param url: str
            Fully qualified url to an elasticsearch instance
        :param size: int
            Size limit to set on elasticsearch query
        """
        self.url  = url
        self.size = size
        self.es   = Elasticsearch([url],
                                  port=443,
                                  use_ssl=False,
                                  verify_certs=False,
                                  timeout=160,
        )

    def __repr__(self):
        return '{clsname}("{url}", size={size})'.format(
            clsname=self.__class__.__name__,
            url='<Elasticsearch URL>',
            size=self.size,
        )

    def flatten(self, nested):
        """
        Recursively flatten a nested list data structure

        :param nested: list
            Nested list

        :return: flattened
        :rtype:  list
        """
        return (
            [x for l in nested for x in self.flatten(l)]
                if isinstance(nested, list) else
            [nested]
        )

    def available(self, ad_id):
        """
        Get's the available factors for a particular ad

        :param ad_id: str
            Unique ad identifier

        :return: factors
        :rtype : list
        """
        accumulator = lambda x,y: x|y
        payload = {
                "size": self.size,
                "query": {
                    "match_phrase": {
                        "_id": ad_id
                    }
                }
            }
        results = self.es.search(body=payload)
        keys    = [set(i['_source'].keys()) for i in results['hits']['hits']]

        return list(reduce(accumulator, keys, set()))

    def combine(self, ad_id, *factors):
        """
        :param ad_id: str
            Unique ad identifier
        :param factors: sequence
            Factors to merge on a particular ID

        :return: factors
        :rtype: dict
        """
        return {
            ad_id: {
                factor: dict(self.suggest(ad_id, factor)[ad_id][factor])
                    for factor in factors
            }
        }

    def reduce(self, ad_id, *factors):
        """
        Combine factors together and reduce them to a set with the same `ad_ids`

        :param ad_id: str
            Unique ad identifier
        :param factors: sequence
            Factors to merge on a particular ID

        :return: reduced
        :rtype : set
        """
        union     = lambda x,y: x|y
        intersect = lambda x,y: x&y

        combined  = self.combine(ad_id, *factors)[ad_id]

        return reduce(intersect, (reduce(union,
                    map(set, combined[factor].values()), set()) for factor in factors))

    def extend(self, ad_id, factor, extension):
        pass


    def lookup(self, ad_id, field):
        """
        Get data from ad_id

        :param ad_id: str
            String to be queried
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

        return self.flatten([
            i['_source'][field] for i in results['hits']['hits']
                    if field in i['_source']
        ])

    def reverse_lookup(self, field, field_value):
        """
        Get ad_id from a specific field and search term

        :param field_value: str
            String to be queried
        """

        payload = {
                "size": self.size,
                "query": {
                    "match_phrase": {
                        field: field_value
                    }
                }
            }
        results = self.es.search(body=payload)

        # If the Elastic Search returns 0 results,
        # then change the search field from `self.field` to all and search again.
        if not results['hits']['total']:
            payload = {
                "size": self.size,
                "query": {
                    "match_phrase": {
                        "_all": field_value
                    }
                }
            }
            results = self.es.search(body=payload)

        return [hit['_id'] for hit in results['hits']['hits']]


def combine_two_factors(original: dict, addition: dict) -> dict:
    """
    Union two dictionaries

    :param original: dict
        Dict to union
    :param addition: dict
        Dict to union
    """
    for k1 in addition:
        if k1 not in original:
            original[k1] = {}
        for k2 in addition[k1]:
            original[k1][k2] = addition[k1][k2]

    return original


def combine_multi_factors(factors: list) -> dict:
    """
    Union multiple dictionaries

    :param factors: list of dicts
        List of dicts to union
    """
    original = factors[0]
    for i in factors[1:]:
        if i:
            original = combine_two_factors(original, i)

    return original


def suggest(ad_id: str, factor_label: str, url: str):
    """
    :param ad_id: str
        Str of number
    :param factor_label: str
        Str to specify factor
    :param url: str
        Str for Elastic Search instance
    """
    try:
        factor = ElasticFactor(url)
        suggestions = factor.suggest(ad_id, factor_label)
        # print(factor_type, len(suggestions[ad_id][factor_type]))
        if len(suggestions[ad_id][factor_label]) == 0:
            return None
        else:
            return suggestions
    except TypeError:
        # print(factor_type, 0)
        return None


def factor_constructor(ad_id: str, factor_labels: list, url: str) -> dict:
    """
    :param ad_id: str
        Str of number
    :param factor_labels: list of strings
        List of strings to specify factors
    :param url: str
        Str for Elastic Search instance
    """
    suggestions = [
        suggest(ad_id, i, url) for i in factor_labels
    ]

    return combine_multi_factors(suggestions)


def flatten(data: dict, level: int) -> set:
    """
    :param data: dict
        Dict of suggestions generated by the factor_constructor
    :param level: int
        Int for the maximum levels of recursion for flattening
    """
    results = set()

    def get_ad_ids(subdict, results, depth):
        """
        :param subdict: dict
            Dict that gets iteratively smaller
        :param results: set
            Set containing the results
        :param depth: int
            Int specifying the current recursion level
        """
        if level <= depth:
            for k, v in subdict.items():
                for i in v:
                    results.add(i)
        else:
            for k, v in subdict.items():
                if isinstance(v, dict):
                    depth = depth + 1
                    get_ad_ids(v, results, depth)
                else:
                    for i in v:
                        results.add(i)

    get_ad_ids(data, results, 0)
    return results


def prune(data, keepers):
    #Remove everything that doesn't contain the keepers
    # def visit(subdict):
    #     keep = []
    #     for k, v in subdict.items():
    #         for i in keepers:
    #             if i in v:
    #                 print(k[v])
    #                 keep.append(k[v])
    #             elif isinstance(v, dict):
    #                 visit(v)
    #             else:
    #                 pass
    #     return keep
    # keep = visit(data)
    # copy = data
    # for k1 in copy:
    #     for k2 in copy[k1]:
    #         if k2 not in keep:
    #             del data[k1][k2]
    #         try:
    #             for k3 in copy[k1][k2]:
    #                 if k3 not in keep.values():
    #                     del data[k1][k2][k3]
    #         except KeyError:
    #             pass
    return {}


def extend(data: dict, url: str, factor_values: list, degree: str) -> dict:
    """
    :param data: dict
        Dict of suggestions generated by the factor_constructor
    :param url: str
        Str for Elastic Search instance
    :param factor_values: List of strings
        List of strings to specify factors
    :param degree: Str
        String to specify the extension name
    """
    field_values = set()
    for v in data.values():
        for value in flatten(v, 1):
            field_values.add(value)
    data[degree] = {}
    ad_ids_2 = flatten(data, 10)
    for ad_id in ad_ids_2:
        addition = factor_constructor(ad_id,  factor_values, url)
        print(".")
        new_field_values = list(flatten(addition, 1))
        for value in new_field_values:
            if value in field_values:
                new_field_values.remove(value)
        print("new fields:", new_field_values)
        data[degree] = prune(addition, new_field_values)
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
    x = {}
    x["original"] = factor_constructor(ad_id, ["phone", "email", "text", "title"], url)
    print(json.dumps(x))

    # print(json.dumps(x))
    # print(flatten(x, 2))
    b = extend(x, url, ["phone", "email", "text", "title"], "ext2")
    print(json.dumps(b))
    # c = extend(b, url, "all", ["phone"], "ext3")
    # print(json.dumps(c))
