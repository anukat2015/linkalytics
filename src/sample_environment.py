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

prod_env = os.getenv('PRODUCTION', False)

# This contains an API key and its secret
API = collections.namedtuple('API', ('KEY', 'SECRET'))

# This contains information for databases
Database = collections.namedtuple('Database', ('HOST', 'PORT', 'DB', 'USER', 'PASS'))

# This contains configuration environments
Config = collections.namedtuple('Config', (
    'TWITTER_ACCESS',       # twitter access key and secret
    'TWITTER_CONSUMER',     # twitter consumer key and secret
    'INSTAGRAM',            # instagram access key and secret
    'YOUTUBE',              # youtube developer key
    'ELS'                   # elasticsearch instance
    # you can include your own fields here
))

# This is the twitter access API key
__twitter_access = API(KEY="k3y", SECRET="t0ps3cr3t")

# This is the twitter consumer API key
__twitter_consumer = API(KEY="k3y", SECRET="t0ps3cr3t")

# This is the common instagram API key
__instagram = API(KEY="k3y", SECRET="t0ps3cr3t")

# This is the common youtube API key, the SECRET is None since it's
# just a developer API key
__youtube = API(KEY="k3y", SECRET=None)

# This is the MEMEX ES instance, DB is the index
__memex_els = Database(HOST='localhost', PORT=9200, DB="my_index", USER="root", PASS="s3cr3t")


if prod_env:
    # Any production environments go here....
    cfg = Config(
        TWITTER_ACCESS      = __twitter_access,
        TWITTER_CONSUMER    = __twitter_consumer,
        INSTAGRAM           = __instagram,
        YOUTUBE             = __youtube,
        ELS                 = __memex_els
    )
else:
    # Any other environments go here....
    cfg = Config(
        TWITTER_ACCESS      = __twitter_access,
        TWITTER_CONSUMER    = __twitter_consumer,
        INSTAGRAM           = __instagram,
        YOUTUBE             = __youtube,
        ELS                 = __memex_els
    )
