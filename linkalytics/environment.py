""" This is a sample environment file.

The purpose of this file is to collect configuration and environment
variables. It checks if the `PRODUCTION` environment variable has been
set. If not, it defaults to use the development environment.

This is a Python file, so you can customize its behavior as you see fit.

To use these configurations, you can use, for instance

"""
from __future__ import print_function

import os
import logging
import sys
import pytoml as toml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('environment')

__all__ = (
    'load_config',
    'get_config',
    'cfg'
)

def load_config(name):

    base = os.path.dirname(os.path.realpath(__file__))
    fmt  = '{base}{sep}environment{sep}{name}.cfg'

    config_file_path = fmt.format(sep=os.sep, base=base, name=name)

    try:
        with open(config_file_path, 'rb') as fin:
            config = toml.load(fin)
        return config
    except:
        print("ERROR: Did you remember to generate config files with credstmpl?", file=sys.stderr)
        print("Check out credstmpl at https://github.com/qadium/credstmpl", file=sys.stderr)
        print("you'll need to run `credstmpl filename.extension.j2`", file=sys.stderr)

def get_config():
    env = os.getenv('PRODUCTION', None)
    cfg = load_config('production') if env else load_config('develop')

    cfg.update(load_config("common"))

    logger.debug("Using {env} environment.".format(env=env))

    return cfg

cfg = get_config()
