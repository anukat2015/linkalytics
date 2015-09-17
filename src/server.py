#Investigative Case Management without Pre-Processing -- Sample Code
#In a terminal window, type 'python CaseBuilderSansPP.py [indexname]' where you choose the indexname
#In a second terminal window, type 'curl -H "Content-type: application/json" -XPOST http://127.0.0.1:5000/search -d '{"search":[searchterm]}' where you choose the searchterm

import json
from elasticsearch import Elasticsearch
import pymysql
import sys
import time
from .. environment import cfg
from flask import Flask, request, jsonify

app = Flask(__name__)

"""
Step 1 -- Query Internal Elastic
Step 2 -- Query External Elastic
Step 3 -- Check Lookup Table
Step 4 -- Post to Link Elastic if not contained in initial query
Step 5 -- Query newly updated Link
"""


def queryDocIds(searchTerm, hostIndex, es):
    payload = {
        "query": {
            "match": {
                "_all": searchTerm
                }
            }
        }
    res = es.search(index=hostIndex, body=payload)
    docIds = []
    for i in res['hits']['hits']:
        docIds.append(str(i["_source"]["incoming_id"]))
    return list(set(docIds))


def lookUp(docIds, externalDocIds):
    newIds = list(set(externalDocIds) - set(docIds))
    groups = {}
    conn = pymysql.connect(host=cfg.SQL.HOST, port=3306, user=cfg.SQL.USER, passwd=cfg.SQL.PASS, db=cfg.SQL.DB)
    cur = conn.cursor()
    sqlStatement = ("SELECT phone_id FROM phone_link where {docIdName} in {docId} limit 10").format(docIdName="ad_id", docId="(" + ",".join(newIds) + ")")
    cur.execute(sqlStatement)
    ###WORK IN PROGRESS...    groupId = []
        for row in cur:
            groupId.append(row[0])
        if groupId:
            sqlStatement2 = ("SELECT ad_id FROM phone_link where {groupIdName} = {groupId} limit 10").format(groupIdName="phone_id", groupId=groupId[0])
            cur.execute(sqlStatement2)
            for row in cur:
                temp.append(row[0])
            groups[i] = temp
        else:
            print(str(i) + " was not found... Is your look up table comprehensive?")
    return groups


def postNew(groups, hostIndex, es):
    externalEs = Elasticsearch(cfg.EXT_ELASTIC.URL, verify_certs=False)
    for i in groups.keys():
        docIds = groups[i]
        payload = {
            "query": {
                "match": {
                    "_all": " ".join(docIds)
                    }
                }
            }
        res = externalEs.search(index=cfg.EXT_ELASTIC.INDEX, body=payload)
        newGroup = res['hits']['hits']
        res = es.index(index=hostIndex, doc_type="group", body=json.dumps(newGroup))


def queryFinal(searchTerm, hostIndex, es):
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
    print("There are " + str(len(groups)) + " results")
    print(groups[0])
    return groups


@app.route("/search", methods=['POST'])
def upDog():
    data = request.get_json(force=True)
    docIds = queryDocIds(data['search'], cfg.INT_ELASTIC.INDEX, esInternal)
    externalDocIds = queryDocIds(data['search'], cfg.EXT_ELASTIC.INDEX, esExternal)
    newGroups = lookUp(docIds, externalDocIds)
    postNew(newGroups, cfg.INT_ELASTIC.INDEX, esInternal)
    results = queryFinal(data['search'], cfg.INT_ELASTIC.INDEX, esInternal)
    if len(results) > 0:
        return json.dumps(results)
    else:
        return "No results"

if __name__ == '__main__':
    esInternal = Elasticsearch(cfg.INT_ELASTIC.URL, verify_certs=False)
    esExternal = Elasticsearch(cfg.EXT_ELASTIC.URL, verify_certs=False)
    try:
        es.indices.create(index=cfg.INT_ELASTIC.INDEX)
        time.sleep(1)
        print("You've created a new index")
    except:
        print("You're working on a pre-existing index")
    app.run()
