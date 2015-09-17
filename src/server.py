#Investigative Case Management without Pre-Processing -- Sample Code
#In a terminal window, type 'python CaseBuilderSansPP.py [indexname]' where you choose the indexname
#In a second terminal window, type 'curl -H "Content-type: application/json" -XPOST http://127.0.0.1:5000/search -d '{"search":[searchterm]}' where you choose the searchterm

import json
from elasticsearch import Elasticsearch
import pymysql
import os
import sys
import time
from flask import Flask, url_for, request, jsonify

app = Flask(__name__)

"""
Step 1 -- Query Internal Elastic
Step 2 -- Query External Elastic
Step 3 -- Check Lookup Table
Step 4 -- Post to Link Elastic if not contained in initial query
Step 5 -- Query newly updated Link
"""

# env variables

EXTERNAL_ELASTIC = os.getenv('EXTERNAL_ELASTIC')
EXTERNAL_INDEX = os.getenv('EXTERNAL_INDEX')

SQL_USER=os.getenv('SQL_USER', 'root')
SQL_HOST=os.getenv('SQL_HOST', '127.0.0.1')
SQL_PASS=os.getenv('SQL_PASS', '')
SQL_DB=os.getenv('SQL_DB', 'link_ht')

def queryDocIds(searchTerm, hostIndex, es):
    payload = {
                "size" : 20,
                "query" : {
                    "match" : {
                        "_all": searchTerm
                    }
                }
            }
    res = es.search(index=hostIndex, body=payload)
    docIds = []
    for i in res['hits']['hits']:
        docIds.append(str(i["_source"]["incoming_id"]))
    return list(set(docIds))


def queryExternal(searchTerm):
    url = EXTERNAL_ELASTIC
    index = EXTERNAL_INDEX
    es = Elasticsearch(url, verify_certs=False)
    payload = {
                "size" : 20,
                "query" : {
                    "match" : {
                        "_all": searchTerm
                    }
                }
            }
    res = es.search(index=index, body=payload)
    externalDocIds = []
    for i in res['hits']['hits']:
        externalDocIds.append(str(i["_source"]["incoming_id"]))
    return externalDocIds


def lookUp(docIds, externalDocIds):
    newIds = list(set(externalDocIds) - set(docIds))
    groups = {}
    conn = pymysql.connect(host=SQL_HOST, port=3306, user=SQL_USER, passwd=SQL_PASS, db=SQL_DB)
    cur = conn.cursor()
    for i in newIds:
        temp = []
        sqlStatement = ("SELECT phone_id FROM phone_link where {docIdName} = {docId} limit 10").format(docIdName="ad_id", docId=i)
        cur.execute(sqlStatement)
        groupId=[]
        for row in cur:
            groupId.append(row[0])
        if len(groupId)>0:
            sqlStatement2 = ("SELECT ad_id FROM phone_link where {groupIdName} = {groupId} limit 10").format(groupIdName="phone_id", groupId=groupId[0])
            cur.execute(sqlStatement2)
            for row in cur:
                temp.append(row[0])
            groups[i] = temp
        else:
            print(str(i) + " was not found... Is your look up table comprehensive?")
    return groups


def postNew(groups, hostIndex, es):
    externalUrl = EXTERNAL_ELASTIC
    externalIndex = EXTERNAL_INDEX
    externalEs = Elasticsearch(externalUrl, verify_certs=False)
    for i in groups.keys():
        docIds = groups[i]
        payload = {
                "size" : 20,
                "query" : {
                    "match" : {
                        "_all": " ".join(docIds)
                    }
                }
            }
        res = externalEs.search(index=externalIndex, body=payload)
        newGroup = res['hits']['hits']
        res = es.index(index=hostIndex, doc_type="group", body= json.dumps(newGroup))

def queryFinal(searchTerm, hostIndex, es):
    payload = {
                "size" : 20,
                "query" : {
                    "match" : {
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

@app.route("/search", methods = ['POST'])
def upDog():
    data = request.get_json(force=True)
    docIds = queryDocIds(data['search'], hostIndex, es)
    externalDocIds = queryExternal(data['search'])
    newGroups = lookUp(docIds, externalDocIds)
    postNew(newGroups, hostIndex, es)
    results = queryFinal(data['search'], hostIndex, es)
    if len(results)>0:
        return json.dumps(results)
    else:
        return "No results"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("Too few input parameters.  Please run as 'python CaseBuilderSansPP.py [indexname]")
    hostIndex = sys.argv[1]
    #Create an Elastic instance named after the input parameter
    url = 'http://localhost:9200/'
    es = Elasticsearch(url, verify_certs=False)
    try:
        es.indices.create(index=hostIndex)
        time.sleep(1)
        print("You've created a new index")
    except:
        print("You're working on a pre-existing index")
    app.run()
