#Investigative Case Management without Pre-Processing -- Sample Code
#In a terminal window, type 'python CaseBuilderSansPP.py [indexname]' where you choose the indexname
#In a second terminal window, type 'curl -H "Content-type: application/json" -XPOST http://127.0.0.1:5000/search -d '{"search":[searchterm]}' where you choose the searchterm

import json
from elasticsearch import Elasticsearch
import pymysql
import time
from environment import cfg
from flask import Flask, request, jsonify

app = Flask(__name__)

"""
Step 1 -- Query Internal Elastic
Step 2 -- Query External Elastic
Step 3 -- Check Lookup Table
Step 4 -- Post to Link Elastic if not contained in initial query
Step 5 -- Query newly updated Link
"""


def query_doc_ids(searchTerm, hostIndex, es):
    payload = {
        "size": 50,
        "fields": ["*incoming_id*"],
        "query": {
            "match": {
                "_all": searchTerm
                }
            }
        }
    res = es.search(index=hostIndex, body=payload)
    docIds = {}
    for i in res['hits']['hits']:
        docIds.add(str(i["_source"]["incoming_id"]))
    return list(set(docIds))


def look_up(docIds, externalDocIds):
    newIds = list(set(externalDocIds) - set(docIds))
    conn = pymysql.connect(host=cfg.SQL.HOST, port=3306, user=cfg.SQL.USER, passwd=cfg.SQL.PASS, db=cfg.SQL.DB)
    cur = conn.cursor()
    sqlStatement = ("SELECT {docIdName} from {tableName} where {groupIdName} in (SELECT {groupIdName} FROM {tableName} where {docIdName} in {docId})").format(docIdName="ad_id", groupIdName="phone_id", tableName="phone_link", docId="(" + ", ".join(newIds) + ")")
    cur.execute(sqlStatement)
    group = {}
    for row in cur:
        if row[1] in group:
            group[row[1]].append(str(row[0]))
        else:
            group[row[1]] = str([row[0]])
    return group


def post_new(groups, internalHost, internalEs, externalHost, externalEs):
    for i in groups.keys():
        docIds = groups[i]
        payload = {
            "query": {
                "match": {
                    "_all": " ".join(docIds)
                    }
                }
            }
        res = externalEs.search(index=externalHost, body=payload)
        newGroup = {}
        newGroup["_id"] = i
        newGroup["docs"] = []
        for result in res['hits']['hits']:
            del result[u"_score"]
            del result[u"_type"]
            newGroup["docs"].append(result)
        res = internalEs.index(index=internalHost, doc_type="group", body=json.dumps(newGroup))


def query_final(searchTerm, hostIndex, es):
    payload = {
        "query": {
            "match": {
                "_all": searchTerm
                }
            }
        }
    res = es.search(index=hostIndex, body=payload)
    groups = []
    for i in res['hits']['hits']:
        groups.append(i)
    return groups


@app.route("/search", methods=['POST'])
def doc_2_group():
    data = request.get_json(force=True)["search"]
    docIds = query_doc_ids(data, cfg.INT_ELASTIC.INDEX, esInternal)
    externalDocIds = query_doc_ids(data, cfg.EXT_ELASTIC.INDEX, esExternal)
    newGroups = look_up(docIds, externalDocIds)
    post_new(newGroups, cfg.INT_ELASTIC.INDEX, esInternal, cfg.EXT_ELASTIC.INDEX, esExternal)
    results = query_final(data, cfg.INT_ELASTIC.INDEX, esInternal)
    if results:
        return jsonify(results)
    else:
        return "No results"


if __name__ == '__main__':
    print("Getting Started")
    esInternal = Elasticsearch(cfg.INT_ELASTIC.URL, verify_certs=False)
    esExternal = Elasticsearch(cfg.EXT_ELASTIC.URL, verify_certs=False)
    try:
        esInternal.indices.create(index=cfg.INT_ELASTIC.INDEX)
        time.sleep(1)
        print("You've created a new index")
    except:
        print("You're currently working on a pre-existing index")
    app.run()
