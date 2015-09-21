#Investigative Case Management without Pre-Processing -- Sample Code
#In a terminal window, type 'python CaseBuilderSansPP.py [indexname]' where you choose the indexname
#In a second terminal window, type 'curl -H "Content-type: application/json" -XPOST http://127.0.0.1:5000/search -d '{"search":[searchterm]}' where you choose the searchterm

import json
from elasticsearch import Elasticsearch
import pymysql
import time
from environment import cfg
from flask import Flask, request  # jsonify

app = Flask(__name__)


def query_docs(searchTerm, hostIndex, es, size, final):
    """
    Here's a function to query Elastic Search and return either all the documents or a list of ids
    """
    payload = {
        "size": size,
        "query": {
            "match": {
                "_all": searchTerm
                }
            }
        }
    res = es.search(index=hostIndex, body=payload)
    groups = set()
    for i in res['hits']['hits']:
        if final is True:
            groups.add(i)
        else:
            groups.add(str(i["_id"]))
    return set(groups)


def look_up(docIds, CDRDocIds):
    """
    Here's a function to use initially queried document ids to identify other related document ids
    """
    newIds = list(set(CDRDocIds) - set(docIds))
    if newIds:
        conn = pymysql.connect(host=cfg.SQL.HOST, port=3306, user=cfg.SQL.USER, passwd=cfg.SQL.PASS, db=cfg.SQL.DB)
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sqlStatement = ("SELECT %(docIdName)s, %(groupName)s from %(tableName)s where %(groupIdName)s in (SELECT %(groupIdName)s FROM %(tableName)s where %(docIdName)s in %(docId)s)")

        cur.execute(sqlStatement, {'docIdName': "ad_id", 'groupIdName': "phone_id", 'tableName': "phone_link", 'docId': "(" + ", ".join(newIds) + ")"})
        group = {}
        for row in cur:
            if row[1] in group:
                group[str(row[1])].append(str(row[0]))
            else:
                group[str(row[1])] = []
                group[str(row[1])].append(str(row[0]))
        conn.close()
        return group
    else:
        return None


def post_new(groups, MirrorHost, MirrorEs, CDRHost, CDREs):
    """
    Here's a function to post grouped documents to Elastic Search
    """
    for i in groups.keys():
        docIds = groups[i]
        payload = {
            "query": {
                "match": {
                    "_all": " ".join(docIds)
                    }
                }
            }
        res = CDREs.search(index=CDRHost, body=payload)
        newGroup = {}
        newGroup["docs"] = []
        for result in res['hits']['hits']:
            del result[u"_score"]
            del result[u"_type"]
            newGroup["docs"].append(result)
        res = MirrorEs.index(index=MirrorHost, doc_type="group", id=i, body=json.dumps(newGroup))


@app.route("/search", methods=['POST'])
def doc_to_group():
    """
    Here's a server that takes a search term as an input and provides a list of grouped documents as an output
    Step 1 -- Query Mirror Elastic
    Step 2 -- Query CDR Elastic
    Step 3 -- Check Lookup Table
    Step 4 -- Post to Mirror Elastic if not yet contained in Mirror Elastic
    Step 5 -- Query newly updated Mirror Elastic
    """
    data = request.get_json(force=True)["search"]
    print("You search for: " + data)
    docIds = query_docs(data, cfg.MIRROR_ELASTIC.INDEX, esMirror, 50, False)
    CDRDocIds = query_docs(data, cfg.CDR_ELASTIC.INDEX, esCDR, 50, False)
    newGroups = look_up(docIds, CDRDocIds)
    post_new(newGroups, cfg.MIRROR_ELASTIC.INDEX, esMirror, cfg.CDR_ELASTIC.INDEX, esCDR)
    results = query_docs(data, cfg.MIRROR_ELASTIC.INDEX, esMirror, 100, True)
    if results:
        return json.dumps(results)
    else:
        return "No results"


if __name__ == '__main__':
    esMirror = Elasticsearch(cfg.MIRROR_ELASTIC.URL, verify_certs=False)
    esCDR = Elasticsearch(cfg.CDR_ELASTIC.URL, verify_certs=False)
    try:
        esMirror.indices.create(index=cfg.MIRROR_ELASTIC.INDEX)
        time.sleep(1)
        print("You've created a new index")
    except:
        print("You're currently working on a pre-existing index")
    app.run()
