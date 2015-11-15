Linkalytics
===========


[![GitHub license](https://img.shields.io/pypi/l/coverage.svg)](https://github.com/qadium-memex/linkalytics/blob/master/LICENSE) [![GitHub version](https://badge.fury.io/gh/qadium-memex%2Flinkalytics.svg)](https://badge.fury.io/gh/qadium-memex%2Flinkalytics) [![Build Status](https://travis-ci.org/qadium-memex/linkalytics.svg?branch=master)](https://travis-ci.org/qadium-memex/linkalytics)
Backend analytics to link together disparate data

Getting Started with Linkalytics
--------------------------------

### Step 1 -- Get dependencies

```sh
$ git clone git@github.com:qadium-memex/linkalytics.git
```

```sh
$ pip3 install -r requirements.txt
```

### _OPTIONAL_ --  Instantiate credentials from shared repository using `credstmpl`

```sh
$ credstmpl /src/environment/*.j2
```

See Qadium's [credstmpl github repository](https://github.com/qadium/credstmpl) for installation instructions. Also, please note this requires AWS credentials.


### Step 2 -- Get going

Open two terminal windows, in the first type

> Note:
> Ensure there is a local elasticsearch instance running as well as a worker queue.
> We use [disque](https://github.com/antirez/disque.git) as our in-memory, distributed job queue.

```sh
$ python3 src/server.py 
```

In the second, type

```sh
$ python3 dowork.py instagram twitter phone
```


[Documentation](https://swaggerhub.com/api/jjangsangy/linkalytics)
------------------------------------------------------------------

[![Swagger Badge](http://online.swagger.io/validator/?url=https://raw.githubusercontent.com/qadium-memex/linkalytics/master/swagger.yaml)](https://swaggerhub.com/api/jjangsangy/linkalytics)

Interactive documentation for the Linkalytics API can be found [here](https://swaggerhub.com/api/jjangsangy/linkalytics).

For more information about generating a client or server, check out [swagger](http://swagger.io/) project
