import factor
from elasticsearch import Elasticsearch
import json
import urllib3
urllib3.disable_warnings()


class ESFactor(factor.Factor):
    def __init__(self, name, url, username, password, size=100):
        super(ESFactor, self).__init__(name)
        self.size = size
        self.es = Elasticsearch(
                    [url],
                    http_auth=(username, password),
                    port=443,
                    use_ssl=False,
                    verify_certs=False
                    )

    def lookup(self, ad_id):
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
                field_vals.append(hit["_source"][self.field])
        return field_vals

    def reverse_lookup(self, field_value):

        payload = {
                "size": self.size,
                "query": {
                    "match_phrase": {
                        self.field: field_value
                    }
                }
            }
        results = self.es.search(body=payload)
        ids = []
        for hit in results['hits']['hits']:
            ids.append(hit["_id"])
        return ids

foo = ESFactor("phone"...)
a = foo.lookup("56514908")
b = foo.reverse_lookup(a[0])

bar = ESFactor()

# print(a)
# print(b)
# 6025825900    queenkasey33@gmail.com      31318107
a = foo.suggest("31318107")
b = bar.suggest("31318107")

z = a
for k1 in b:
    if k1 not in a:
        a[k1] = {}
    for k2 in b[k1]:
        a[k1][k2] = b[k1][k2]

print(json.dumps(a))
