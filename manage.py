# manage.py

from flask.ext.script import Manager, Server

from linkalytics import create_app
from linkalytics.environment import cfg

app = create_app(cfg)

server  = Server(host="0.0.0.0", port=8080)
manager = Manager(app)

manager.add_command('runserver', server)

if __name__ == "__main__":
    manager.run()
