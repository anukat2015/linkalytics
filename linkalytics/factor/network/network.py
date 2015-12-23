import itertools
import collections

from functools import reduce
from elasticsearch import Elasticsearch
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.search import Search
from elasticsearch_dsl.query import Q, Ids

import networkx as nx

from ... environment import cfg
from ... utils import memoize

class Messenger:
    """
    Performs transformations on data

        eg. f(x) -> y

    Decoupled from the other factor network code,
    and can be swapped with other implementations
    """

    def __init__(self, config='cdr', size=2000):
        """
        :param url: str
            Fully qualified url to an elasticsearch instance
        :param size: int|
            Size limit to set on elasticsearch query
        """
        self.conn = connections.get_connection(config)
        self.elastic = Search('cdr', extra={'size': size})

    def match(self, match_type, **kwargs):
        return self.elastic.query(match_type, **kwargs).execute()

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
        output      = self.match('match_phrase', _id=ad_id)
        keys        = [
            set(i['_source'].keys())
                for i in output.hits.hits
        ]
        return list(reduce(accumulator, keys, set()))

    def lookup(self, ad_id, field):
        """
        Get data from ad_id

        :param ad_id: str
            String to be queried
        """
        if not isinstance(ad_id, list):
            ad_id = [ad_id]

        results = self.elastic.query(Ids(values=ad_id)).execute()

        return set(flatten([
            hits['_source'][field] for hits in results.hits.hits
                if field in hits['_source']
        ]))


    def reverse_lookup(self, field, field_value):
        """
        Get ad_id from a specific field and search term

        :param field_value: str
            String to be queried
        """
        results = self.match(
            'match_phrase', **{field:field_value}).hits.hits

        if not results:
            results = self.match('match', _all=field_value).hits.hits

        return [hit['_id'] for hit in results]

    def suggest(self, ad_id, field):
        """
        The suggest function suggests other ad_ids that share this
        field with the input ad_id.
        """
        suggestions = {}
        field_values = self.lookup(ad_id, field)

        for value in field_values:
            ads = set(self.reverse_lookup(field, value))

            # To prevent cycles
            if isinstance(ad_id, list):
                ads -= set(ad_id)
            else:
                ads.discard(ad_id)
            suggestions[value] = list(ads)

        return suggestions

class FactorNetwork:
    """
    Factor Network Constructor
    ==========================
    Maintains an internal representation of the factor network as a
    graph and provides functionality to manipulate state.
    """
    def __init__(self, Messenger=Messenger, **kwargs):
        """
        :param Messenger:
            A class constructor following the suggestion
            interface
        :param kwargs:
            Keyword arguments fed into constructor
            to initialize local network object
        """
        self.messenger = Messenger()
        self.G         = nx.DiGraph(**kwargs)

    def __repr__(self):
        nodes  = nx.number_of_nodes(self.G)
        edges  = nx.number_of_edges(self.G)
        return '{nm}(nodes={nodes}, edges={edges})'.format(
            nm=self.__class__.__name__,
            nodes=nodes,
            edges=edges,
        )

    def get_graph(self, node, factor, **kwargs):
        """
        Create the networkx graph representation

        :param node: str
            Document ID of the root node
        :param factor: str
            A type of factor to query
        :param kwargs:
            Keyword arguments fed into constructor
            to initialize local network object
        """
        G, node = nx.DiGraph(**kwargs), str(node)
        G.add_node(node, {'type': 'doc'})

        self.messenger.lookup(node, factor)
        message = self.messenger.suggest(node, factor)

        for value, keys in message.items():
            edgelist = itertools.zip_longest([node], keys, fillvalue=node)
            metadata = {'value': value, 'factor': factor}
            G.add_edges_from(edgelist, **metadata)

        return G

    def register_node(self, node, factor):
        node = str(node)
        self.G = nx.compose(self.G, self.get_graph(node, factor))

    def to_dict(self):
        """
        Serialize graph edges back into JSON
        """
        d = collections.defaultdict(list)
        for leaf, node in nx.edges(self.G):
            d[node].append(leaf)

        return dict(d)

    def show(self):
        nx.draw_networkx(self.G,
                         pos=nx.layout.fruchterman_reingold_layout(self.G),
                         with_labels=False,
                         node_size=100,
        )

    def commit(self, index_name, user_name):
        """
        Commit the current state of factor network to a local Elastic instance

        The index_name should remain constant for an organization. The user_name refers to the specific user and provides the functionality to maintain the user provenance by making it the Elastic document type.

        Specifically, split the state into 3 components (1) root (the datum with which you started) (2) extension (the data you've confirmed based on factor network suggestions) (3) suggestions (the suggested extensions to your data)

        We index a factor network by taking the root and appending a _x to it. We loop through get requests on that particular lead to get based on the most recently committed root_x and we add 1 to x.

        The results of the commit will look as follows in Elastic:

        {
            "_index": "Your_Index_Name",
            "_type": "adam",
            "_id": "rootid_x",
            "_score": 1,
            "_source": {
                "root": [[0,1],[0,7],...],
                "extension": {[[1,2],[2,3],...]},
                "suggestions": {[[3,4],[...],...]}
            }
        }
        """
        es = Elasticsearch()
        source = set()
        target = set()
        edges = self.G.edges()
        for edge in edges:
            source.add(edge[0])
            target.add(edge[1])

        def split(intersection, edges):
            result = []
            for i in intersection:
                for edge in edges:
                    if i in edge:
                        result.append(edge)
            return result

        state = {}
        state["root"] = split(source.difference(target), edges)
        state["extension"] = split(target.intersection(source), edges)
        state["suggestions"] = split(target.difference(source), edges)

        i = 1
        preexisting = True
        while preexisting:
            try:
                index_id = state["root"][0][0] + "_" + str(i)
                es.get(index=index_name, id=index_id, doc_type=user_name)
                i = i + 1
            except:
                preexisting = False

        res = es.index(index=index_name, id=index_id, doc_type=user_name, body=state)
        current_state = es.get(index=index_name, id=index_id, doc_type=user_name)
        return current_state

    def unpack_state_to_graph(self, index_name, user_name, index_id):
        """
        Get request to Elastic to return the graph without the lead/extension/suggestions differentiator
        """
        es = Elasticsearch()
        edges = []
        current_state = es.get(index=index_name, id=index_id, doc_type=user_name)
        for k, v in current_state["_source"].items():
            for edge in v:
                edges.append(edge)

        G = nx.DiGraph()
        G.add_edges_from(edges)
        return G

    def merge(self, index_name, user_name_a, index_id_a, user_name_b, index_id_b):
        """
        Merge two factor states
        """
        # state_a = es.get(index=index_name, index_id_a, doc_type=user_name_a)
        # state_b = es.get(index=index_name, index_id_b, doc_type=user_name_b)
        G_a = set(self.unpack_state_to_graph(index_name, user_name_a, index_id_a).edges())
        G_b = set(self.unpack_state_to_graph(index_name, user_name_b, index_id_a).edges())
        network = {}
        network["intersection"] = G_a.intersection(G_b)
        network["workflow_a"] = G_a.difference(G_b)
        network["workflow_b"] = G_b.difference(G_a)
        n_edges = len(network["intersection"]) + len(network["workflow_a"]) + len(network["workflow_b"])
        network["merge_stats"] = {}
        network["merge_stats"]["intersection"] = round(len(network["intersection"])/n_edges, 2)
        network["merge_stats"]["workflow_a"] = round(len(network["workflow_a"])/n_edges, 2)
        network["merge_stats"]["workflow_b"] = round(len(network["workflow_b"])/n_edges, 2)
        return(network)

def flatten(nested):
    return (
        [x for l in nested for x in flatten(l)]
        if isinstance(nested, list) else
        [nested]
    )

def run(node):
    _id, factor = node.get('id'), node.get('factor')
    network = FactorNetwork()
    network.register_node(_id, factor)
    network.commit("factor_state2016", "adam")
    return network.to_dict()
