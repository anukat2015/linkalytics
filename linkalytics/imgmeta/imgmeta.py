import redis
import datetime

from .. environment import cfg

conn = redis.Redis(host=cfg['redis']['host'])

def bytes_to_timestamp(b):
    timestamp = float(b)
    return datetime.datetime.utcfromtimestamp(timestamp).isoformat()

def _decode_list(l):
    return map(lambda x: x.decode('utf-8'), l)

def _time_range(lb_ad_id, ub_ad_id, limit):
    ub_time = conn.hget(ub_ad_id, "time")
    lb_time = conn.hget(lb_ad_id, "time")
    if ub_time and lb_time:
        ub_time = float(ub_time)
        lb_time = float(lb_time)
        ads = list(conn.zrangebyscore("time", "%f" % (lb_time - limit), "%f" % (ub_time + limit), withscores=True, score_cast_func=bytes_to_timestamp))
        new_lb = ads[0][0].decode('utf-8')
        new_ub = ads[-1][0].decode('utf-8')
        if new_lb == lb_ad_id and new_ub == ub_ad_id:
            return ads
        else:
            return _time_range(new_lb, new_ub, limit)
    else:
        return []

def suggest_one(ad_id, with_model, time_window, with_serial):
    result = {
        "model": {},
        "serial_no": {},
        "times": {}
    }
    if with_model:
        model = conn.hget("ad:%s" % ad_id, "model")
        if model:
            model = model.decode('utf-8')
            models = _decode_list(conn.zrangebylex("model", "[%s:ad:" % model, "[%s:ad:\xff" % model))
            result["model"] = {ad_id.split(":")[-1] : model for ad_id in models}
    if with_serial:
        serial_no = conn.hget("ad:%s" % ad_id, "serial")
        if serial_no:
            serial_no = serial_no.decode('utf-8')
            serials = _decode_list(conn.zrangebylex("serial", "[%s:ad:" % serial_no, "[%s:ad:\xff" % serial_no))
            result["serial_no"] = {ad_id.split(":")[-1] : serial_no for ad_id in serials}
    if time_window:
        times = _time_range("ad:%s" % ad_id, "ad:%s" % ad_id, time_window)
        if times:
            result["times"] = {ad[0].decode('utf-8').lstrip("ad:") : ad[1] for ad in times}
    return result

def suggest_related(ad_ids, with_model, time_window, with_serial, with_intersection):
    suggestions = {}
    for ad_id in ad_ids:
        result = suggest_one(ad_id, with_model, time_window, with_serial)
        suggestions[ad_id] = result
        model_suggestions = set(result["model"].keys())
        serial_suggestions = set(result["serial_no"].keys())
        time_suggestions = set(result["times"].keys())
        suggested = set()
        if with_intersection:
            if with_model:
                suggested &= model_suggestions
            if with_serial:
                suggested &= serial_suggestions
            if time_window:
                suggested &= time_suggestions
        else:
            if with_model:
                suggested |= model_suggestions
            if with_serial:
                suggested |= serial_suggestions
            if time_window:
                suggested |= time_suggestions
    return suggestions, suggested

def suggest_to_depth(ad_ids, depth, model, time, serial, intersect):
    """ Suggest_to_depth takes a list of ad_ids (as str) and runs
        suggest_related to a specific depth. It returns a tuple of
        suggestions.
    """
    suggestions = {}
    queried_ads = set(map(str,ad_ids))
    ads_to_query = set(map(str,ad_ids))
    for _ in range(depth):
        result, suggested = suggest_related(ads_to_query, model, time, serial, intersect)
        suggestions.update(result)
        # now add the suggested ads to the query
        ads_to_query = set()
        for key in result:
            ads_to_query.update(suggested)
        # remove any ads we've already queried
        ads_to_query = ads_to_query.difference(queried_ads)
        if not ads_to_query:    # if there are no more ads to query, quit early
            break
        # track the ads we will have queried
        queried_ads.update(ads_to_query)

    return suggestions

def run(node):
    result = suggest_to_depth([node['id']], 1, True, 1200, True, False)
    for k in result:
        result[k].update({"id": k})
    return {"imgmeta": [result[k] for k in result]}
