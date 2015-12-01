#!/usr/bin/env python3
import redis
import csv
import argparse
import os
import datetime
import sys

# __TIME_TSV is the set of files containing time inforation. Any
# duplicates are ignored. The order these files are read is also not
# guaranteed.
__TIME_TSV = [
    "time_creation_date.tsv",
    "time_meta_creation_date.tsv",
    "time_date.tsv",
    "time_last_save_date.tsv",
    "time_meta_save_date.tsv"
]

# __MODEL_TSV is the set of files containing model information.
__MODEL_TSV = [
    "hash_model.tsv"
]

__SERIAL_TSV = [
    "hash_serial_number.tsv"
]

conn = redis.Redis(host='localhost', port=6379)

def metadata_from(filename):
    """ filename should be a valid TSV file

        rows with the first-column being NaN are ignored.
    """
    with open(filename,'r') as tsvin:
        tsvin = csv.reader(tsvin, delimiter='\t')

        for row in tsvin:
            # destructure the row
            ad_id, image_url, *fields = row
            if ad_id.lower() != "nan":
                yield int(float(ad_id)), image_url, fields

def add_to_redis(key, field, value):
    is_set = conn.hsetnx(key, field, value)
    # if we set the field, we then add it to a sorted set
    if is_set:
        if isinstance(value, float) or isinstance(value, int):
            score = float(value)
            conn.zadd(field, key, score)
        else:
            # if the value isn't a float, we pretend it's a string (and
            # raise any subsequent exceptions)
            #
            # we add the string to the key (e.g., if the value is "foo",
            # then the element name is foo:some_key). this lets us find
            # similar things by using a lexicographic sort with
            # ZRANGEBYLEX "[foo:" "[foo:\xff"
            conn.zadd(field, value + ":" + key, 0)
        sys.stdout.write('.')
    else:
        sys.stdout.write('*')

    if sys.stdout.tell() % 80 == 0:
        sys.stdout.write("\n")


def handle_time(filename):
    """ inserts timestamps into proper data structures;
        not extremely efficient since it pays for round trip
    """
    for ad_id, url, fields in metadata_from(filename):
        timestamp = datetime.datetime.strptime(fields[0],"%Y-%m-%dT%H:%M:%S")
        try:
            key = "ad:%d" % ad_id
            conn.hsetnx(key, "url", url)
            time = timestamp.timestamp()
            add_to_redis(key, "time", time)
        except OverflowError as e:
            continue

def handle_model(filename):
    for ad_id, url, fields in metadata_from(filename):
        key = "ad:%d" % ad_id
        conn.hsetnx(key, "url", url)
        add_to_redis(key, "model", fields[0])

def handle_serial(filename):
    for ad_id, url, fields in metadata_from(filename):
        key = "ad:%d" % ad_id
        conn.hsetnx(key, "url", url)
        add_to_redis(key, "serial", fields[0])

def main():
    parser = argparse.ArgumentParser(description="Populate redis from MG's cluster folder. Only includes data with a non-NaN first column.")
    parser.add_argument('path', help="Path to directory containing tsv's.")

    args = parser.parse_args()

    for tsv in __TIME_TSV:
        handle_time(os.path.join(args.path, tsv))

    for tsv in __MODEL_TSV:
        handle_model(os.path.join(args.path, tsv))

    for tsv in __SERIAL_TSV:
        handle_serial(os.path.join(args.path, tsv))

    sys.stdout.write("\n")

if __name__ == "__main__":
    main()
