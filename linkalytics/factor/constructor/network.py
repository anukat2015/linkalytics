from elasticsearch import Elasticsearch
from functools import total_ordering, reduce

import networkx as nx

from ... environment import cfg
from ... utils import memoize

class MetaConfigInjection(type):
    """
    This metaclass implements the Singleton design pattern in order
    to perform dependency injection of pre-configured
    elasticsearch instances bound  as attributes to cls.instance
    """
    instance = None
    def __call__(cls, *args, **kwargs):

        hosts = cfg['cdr_elastic_search']['hosts']
        index = cfg['cdr_elastic_search']['index']

        if not cls.instance:
            cls.instance = super().__call__(*args, **kwargs)
            cls.es       = Elasticsearch([hosts + index],
                                         port=443,
                                         use_ssl=False,
                                         verify_certs=False,
                                         timeout=160,
            )
        return cls.instance

class propertycache:
    """
    Custom property decorator which maintiains
    intermediate results.
    """
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, obj, type=None):
        result = self.func(obj)
        self.cachevalue(obj, result)
        return result

    def cachevalue(self, obj, value):
        setattr(obj, self.name, value)

@total_ordering
class FactorNode:
    """
    Concrete implementations should be easily
    hashable, recursive data structures.

    :param url: str
        Fully qualified url to an elasticsearch instance
    """
    def __init__(self, _id):
        self._id = str(_id)
    def __repr__(self):
        return '<{clsname}({id})>'.format(
            clsname=self.__class__.__name__,
            id=self.id
        )
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        try:
            self._id = int(value)
        except ValueError as error:
            raise error
    def __hash__(self):
        return int(self.id)
    def __eq__(self, other):
        return self.id == other.id
    def __lt__(self, other):
        return self.id < other.id


class Messenger(metaclass=Singleton):

    def __init__(self, size=500):
        """
        :param url: str
            Fully qualified url to an elasticsearch instance
        :param size: int
            Size limit to set on elasticsearch query
        """
        self.size = size

    def __repr__(self):
        return '{clsname}("{url}", size={size})'.format(
            clsname=self.__class__.__name__,
            url='<Elasticsearch URL>',
            size=self.size,
        )
    @memoize
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
        return [
            i['_source'][field] for i in results['hits']['hits']
                if field in i['_source']
        ]
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

        return [
            hit['_id'] for hit in results['hits']['hits']
        ]
    def suggest(self, ad_id, field):
        """
        The suggest function suggests other ad_ids that share this
        field with the input ad_id.
        """
        suggestions = []
        field_values = self.lookup(ad_id, field)

        for value in field_values:
            ads = set(self.reverse_lookup(field, value))

            # To prevent cycles
            if ad_id in ads:
                ads.remove(ad_id)

            for ad in ads:
                suggestions.append(ad)

        return suggestions

class EdgeStruct:
    """
    Data structure applied to edges in a factor network.
    """
    def __init__(self, weight=1, **kwargs):
        self.__dict__ = kwargs
        self.weight   = weight

    def __repr__(self):
        return str(self.__dict__)

class FactorNetwork:
    """
    Factor Network Constructor
    ==========================
    Manager class for initializing and
    handling state in a factor network
    """
    def __init__(self, factor=FactorNode):
        """
        :NOTE: must be hashable
        :param factor: Node
            Node Data Primitive

        :rtype:
            <FactorNetwork>
        """
        self.messenger = Messenger()
        self.factor    = factor
        self.G         = nx.DiGraph()


    def __repr__(self):
        return '{clsname}()'.format(
                clsname=self.__class__.__name__
        )

    def register_node(self, node, factor):
        """
        Takes in a node and it's suggestions and builds
        out the directed edges.
        """
        self.G.add_node(node)
        suggestion = list(map(self.factor, self.messenger.suggest(node.id, factor)))
        for edge in suggestion:
            self.G.add_edge(node, edge)


