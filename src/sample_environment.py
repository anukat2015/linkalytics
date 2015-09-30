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
import pytoml as toml

prod_env = os.getenv('PRODUCTION', False)


def load_config(name):
    try:
        with open('/environment/' + name + '.cfg', 'rb') as fin:
            config = toml.load(fin)
        return config
    except:
        print("ERROR: Did you remember to generate config files with credstmpl?")

common = load_config("common")

if prod_env:
    production = load_config("production")
    # Common and Production Configurations Here
    cfg = common.copy()
    cfg.update(production)
else:
    develop = load_config("develop")
    # Common and Development Configurations Here
    cfg = common.copy()
    cfg.update(develop)
