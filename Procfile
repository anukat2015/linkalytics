web:    gunicorn linkalytics.wsgi:app -c gunicorn.conf.py
worker: python3 -m linkalytics
disque: disque-server ${DISQUE_CONF}
redis:  redis-server  ${REDIS_CONF}
tika:   java -jar ${TIKA_JAR} -p 9998 -h 0.0.0.0
elasticsearch: elasticsearch
