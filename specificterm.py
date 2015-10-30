from elasticsearch  import Elasticsearch
import json
import urllib3
import sys
urllib3.disable_warnings()


def search(search_term, size, es, phrase=True):
    match_type = 'match_phrase' if phrase else 'match'
    output     = dict()
    payload = {
        "size": size,
        "query" : {
            match_type : {
                "_all" : search_term
            }
        }
    }
    results = es.search(body=payload)
    print("We found " + str(results['hits']['total']) + " results for: " + search_term)

    for hit in results['hits']['hits']:
        try:
            output[hit['_id']] = hit["_source"]
        except KeyError:
            pass

    return output

def unique_features(feature, data):
    features = set()
    for v in data.values():
        try:
            if isinstance(v[feature], str):
                features.add(v[feature])
            elif isinstance(v[feature], list):
                for i in v:
                    features.add(v[feature])
        except:
            pass
    return(features)

def phone_hits(phone, size, es, phrase=True):
    match_type = 'match_phrase' if phrase else 'match'
    payload = {
        "size": size,
        "query" : {
            match_type : {
                "phone" : phone
            }
        }
    }
    results = es.search(body=payload)
    output = {}
    output["total"] = results['hits']['total']
    for hit in results['hits']['hits']:
        try:
            output[hit['_id']] = hit["_source"]
        except KeyError:
            pass
    return output

def both_hits(search_term, phone, size, es, phrase=True):
    query =  {
        "bool": {
            "must":
                [
                    {"match_phrase": { "_all": search_term }},
                    { "match": { "phone": phone }}
                ]
            }
        }

    payload = {
                "size": 500,
                "query" : query
               }
    results = es.search(body=payload)
    output = {}
    output["total"] = results['hits']['total']
    for hit in results['hits']['hits']:
        try:
            output[hit['_id']] = hit["_source"]
        except KeyError:
            pass
    return output


if __name__ == "__main__":
    es  = Elasticsearch("https://memex:3vYAZ8bSztbxmznvhD4C@els.istresearch.com:29200/memex_ht", port=443, verify_certs=False, use_ssl=False)
    query = sys.argv[1]
    results = search(query, 1000, es, True)
    phone = unique_features("phone", results)
    posttime = unique_features("posttime", results)
    print("We found " + str(len(phone)) + " phone numbers containing the phrase '" + query + "', which appear between " + str(min(posttime)) + " and " + str(max(posttime)))
    for i in phone:
        phone_res=phone_hits(i, 1000, es, True)
        both_res=both_hits(query, i, 1000, es, True)
        date_phone = set()
        for v in phone_res.values():
            try:
                date_phone.add(v["posttime"])
            except:
                pass
        print(i,"--" + str(phone_res["total"]) + " (" + str(both_res["total"]) + ") results (with " + query + ")", "date range: " + str(min(date_phone)) + "--" + str(max(date_phone)))


