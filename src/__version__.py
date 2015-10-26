from . environment import cfg

__version__ = cfg['api']['version'].strip('v')
__build__ = 'release'
__release__ = __version__ + __build__
