bind = "0.0.0.0:8080"

workers = 4
worker_class = 'tornado'

max_requests = 1000
timeout = 30
keep_alive = 2

preload = True