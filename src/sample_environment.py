""" This is a sample environment file.

The purpose of this file is to collect configuration and environment
variables. It checks if the `PRODUCTION` environment variable has been
set. If not, it defaults to use the development environment.

This is a Python file, so you can customize its behavior as you see fit.

To use these configurations, you can use, for instance

import sample_environmnet as env
print(env.cfg.TWITTER.KEY)
"""
import os
import collections
import pytoml as toml

prod_env = os.getenv('PRODUCTION', False)

with open('/environment/common.cfg', 'rb') as fin:
    common = toml.load(fin)
with open('/environment/develop.cfg', 'rb') as fin:
    develop = toml.load(fin)
with open('/environment/production.cfg', 'rb') as fin:
    production = toml.load(fin)

# This contains configuration environments
Config = collections.namedtuple('Config', (
    'TWITTER_',             # twitter creds
    'INSTAGRAM_CONSUMER',   # instagram creds
    'YOUTUBE',              # youtube developer key
    'SQL',                  # sql instance
    'CDR_ELASTIC',          # elasticsearch instance for common data repository
    'MIRROR_ELASTIC'       # elasticsearch instance for mirrored local instance

    # you can include your own fields too!
))

if prod_env:
    # Any production environments go here....
    cfg = Config(
        TWITTER             = common["twitter"]
        INSTAGRAM           = common["instagram"],
        YOUTUBE             = common["youtube"],
        SQL                 = production["sql"],
        CDR_ELASTIC         = common["cdr_elastic_search"],
        MIRROR_ELASTIC      = production["mirror_elastic_search"]
    )
else:
    # Any other environments go here....
    cfg = Config(
        TWITTER             = common["twitter"]
        INSTAGRAM           = common["instagram"],
        YOUTUBE             = common["youtube"],
        SQL                 = develop["sql"],
        CDR_ELASTIC         = common["cdr_elastic_search"],
        MIRROR_ELASTIC      = develop["mirror_elastic_search"]
    )
