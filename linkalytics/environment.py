""" This is a sample environment file.

The purpose of this file is to collect configuration and environment
variables. It checks if the `PRODUCTION` environment variable has been
set. If not, it defaults to use the development environment.

This is a Python file, so you can customize its behavior as you see fit.

To use these configurations, you can use, for instance

>>> import environment as env
>>> print(env.cfg['twitter']['access_token'])
"""
import os
import pytoml as toml

prod_env = os.getenv('PRODUCTION', False)



def load_config(name):

    base = os.path.dirname(os.path.realpath(__file__))
    fmt  = '{base}{sep}environment{sep}{name}.cfg'

    config_file_path = fmt.format(sep=os.sep, base=base, name=name)

    try:
        with open(config_file_path, 'rb') as fin:
            config = toml.load(fin)
        return config
    except:
        print("ERROR: Did you remember to generate config files with credstmpl? Check out credstmpl at https://github.com/qadium/credstmpl -- you'll need to run `credstmpl filename.extension.j2`")

config = {}
if prod_env:
    print("Using production environment.")
    config = load_config("production")
else:
    print("Using development environment.")
    config = load_config("develop")

cfg = load_config("common")
cfg.update(config)
