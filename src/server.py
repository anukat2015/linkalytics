"""
Investigative Case Management without Pre-Processing
====================================================

For testing, in a second terminal window, type

    curl -H "Content-type: application/json" \
         -d '{"search":[search_term]}' \
         -X POST http://127.0.0.1:5000/search

where you choose the search_term.
"""

import json
import time
import pymysql
import disq

from elasticsearch  import Elasticsearch
from environment    import cfg
from flask          import Flask, request, jsonify
from flask.ext.cors import CORS

app = Flask(__name__)

CORS(app)

disque = disq.Disque()

def query_docs(search_term, host_index, es, size, ids_only, cdr):
    """
    Here's a function to query Elastic Search and return either all the documents or a list of ids
    """
    payload = {
        "size": size,
        "query": {
            "match_phrase": {
                "_all": search_term
            }
        }
    }
    res = es.search(index=host_index, body=payload)
    groups = set()
    for i in res['hits']['hits']:
        if ids_only is True:
            if cdr is True:
                groups.add(str(i["_id"]))
            else:
                for j in i["_source"]["docs"]:
                    groups.add(str(j["_id"]))
        else:
            groups.add(json.dumps(i))
    groups = map(json.loads, groups)
    return list(groups)


def look_up(doc_ids, cdr_doc_ids):
    """
    To use initially queried document ids to identify other related document ids
    """
    new_ids = list(set(cdr_doc_ids) - set(doc_ids))
    print(new_ids)
    if new_ids:
        conn = pymysql.connect(host=cfg["sql"]["host"],
                               port=3306,
                               user=cfg["sql"]["user"],
                               passwd=cfg["sql"]["password"],
                               db=cfg["sql"]["database"]
                               )
        print(conn)
        cur = conn.cursor(pymysql.cursors.DictCursor)

        #TODO: Increase speed by adding join
        sql_statement = """SELECT `phone_id`, `ad_id`
                           FROM   `phone_link`
                           WHERE  `phone_id`
                           IN (
                               SELECT `phone_id`
                               FROM  `phone_link`
                               WHERE `ad_id`
                               IN %s
                           )
                        """
        try:
            cur.execute(sql_statement, (list(map(int, new_ids)),))
            group = {}
            for row in cur:
                print(row)
                if row['phone_id'] in group:
                    group[str(row['phone_id'])].append(str(row['ad_id']))
                else:
                    group[str(row['phone_id'])] = []
                    group[str(row['phone_id'])].append(str(row['ad_id']))

            print("Your search identified the following new groups:")
            print(group)

        except:
            print("Error")

        finally:
            conn.close()

        return group

    else:
        return None


def post_new(groups, mirror_host, mirror_es, cdr_host, cdr_es):
    """
    Here's a function to post grouped documents to Elastic Search
    """
    for i in groups.keys():
        doc_ids = groups[i]
        payload = {
            "query": {
                "match": {
                    "_all": " ".join(doc_ids)
                }
            }
        }
        scan_resp = cdr_es.search(index=cdr_host, body=payload, search_type="scan", scroll="10m")
        scroll_id = scan_resp['_scroll_id']
        res = cdr_es.scroll(scroll_id=scroll_id, scroll="10m")
        new_group = {}
        new_group["docs"] = []

        for result in res['hits']['hits']:
            del result[u"_score"]
            del result[u"_type"]
            new_group["docs"].append(result)

        #Add Instagram, Twitter, and Youtube add-ons here
        res = mirror_es.index(index=mirror_host, doc_type="group", id=i, body=json.dumps(new_group))
        print("Posted successfully")


@app.route("/search", methods=['POST'])
def doc_to_group():
    """
    Here's a server that takes a search term as an input
    and provides a list of grouped documents as an output

    Step 1 -- Query Mirror Elastic
    Step 2 -- Query CDR Elastic
    Step 3 -- Check Lookup Table
    Step 4 -- Post to Mirror Elastic if not yet contained in Mirror Elastic
    Step 5 -- Query newly updated Mirror Elastic
    """
    # search_term = search["text"]
    search_term = request.get_json(force=True)["search"]
    # print("You searched for: " + search_term)
    # doc_ids = query_docs(search_term, cfg["mirror_elastic_search"]["index"], es_mirror, 50, True, False)

    # print("# of Results from Mirror: " + str(len(doc_ids)))
    # cdr_doc_ids = query_docs(search_term, cfg["cdr_elastic_search"]["index"], es_cdr, 50, True, True)

    # print("# of Results from CDR: {}".format(len(cdr_doc_ids)))
    # new_groups = look_up(doc_ids, cdr_doc_ids)

    # if new_groups:
    #     print("# of New Groups: {}".format(len(new_groups)))
    #     post_new(new_groups, cfg["mirror_elastic_search"]["index"], es_mirror, cfg["cdr_elastic_search"]["index"], es_cdr)
    #     time.sleep(2)

    # else:
    #     print("No new groups")
    results = query_docs(search_term, cfg["cdr_elastic_search"]["index"], es_cdr, 100, False, True)
    print("Results: " + str(len(results)))

    if results:
        return jsonify(results=results)
    else:
        return jsonify({'message': 'no results'})

def process_job(record):
    job_id = disque.addjob('worker', json.dumps(record))
    print('submitted job {}'.format(job_id))
    # wait for result
    result = get_result(job_id)
    return json.dumps(result)

def get_result(job_id):
    qname, result_id, result = disque.getjob(job_id)[0]
    disque.fastack(result_id)
    return (qname, result_id, json.loads(result.decode('utf8')))

@app.route('/enhance/<path:endpoint>', methods=['POST'])
def enhance(endpoint):
    record = request.get_json()
    results = process_job(record)
    return jsonify(results=results, endpoint=endpoint, **record)

def test_doc_to_group(search):
    """
    Here's a server that takes a search term as an input
    Provides a list of grouped documents as an output

    Step 1 -- Query Mirror Elastic
    Step 2 -- Query CDR Elastic
    Step 3 -- Check Lookup Table
    Step 4 -- Post to Mirror Elastic if not yet contained in Mirror Elastic
    Step 5 -- Query newly updated Mirror Elastic
    """
    search_term = search["text"]

    print("You searched for: {}".format(search_term))
    doc_ids = query_docs(search_term, mirror_elastic_index, es_mirror, 50, True, False)

    print("# of Results from Mirror: {}".format(len(doc_ids)))
    cdr_doc_ids = query_docs(search_term, cdr_elastic_index, es_cdr, 50, True, True)

    print("# of Results from CDR: {}".format(cdr_doc_ids))
    new_groups = look_up(doc_ids, cdr_doc_ids)

    if new_groups:
        print("# of New Groups: {}".format(len(new_groups)))
        post_new(new_groups, mirror_elastic_index, es_mirror, cdr_elastic_index, es_cdr)
        time.sleep(1.2)

    else:
        print("No new groups")
    results = query_docs(search_term, mirror_elastic_index, es_mirror, 100, False, True)
    print("Results: " + str(len(results)))

    if results:
        return jsonify(results=results)
    else:
        return jsonify({'message': 'no results'})


if __name__ == '__main__':
    es_mirror = Elasticsearch(cfg["mirror_elastic_search"]["hosts"], verify_certs=False)
    es_cdr    = Elasticsearch(cfg["cdr_elastic_search"]["hosts"],    verify_certs=False)

    mirror_elastic_index = cfg["mirror_elastic_search"]["index"]
    cdr_elastic_index    = cfg["cdr_elastic_search"]["index"]

    try:
        es_mirror.indices.create(index=cfg.MIRROR_ELS.DB)
        time.sleep(1)
        print("You've created a new index")

    except:
        print("You're currently working on a pre-existing index")

    app.run(debug=True, host="0.0.0.0", port=8080)
