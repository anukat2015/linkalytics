from . import create_app

from . environment import cfg

app = create_app(cfg)
