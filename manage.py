# manage.py

from flask.ext.script import Manager

try:
    from app import app
except ImportError:
    from src import app

manager = Manager(app)

if __name__ == "__main__":
    manager.run()
