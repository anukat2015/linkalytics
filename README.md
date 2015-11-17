Linkalytics
===========

[![License][License Badge]][License] [![Version][Version Badge]][Version] [![Travis][Travis Badge]][Travis]

Analytics to link data

Getting Started with Linkalytics
--------------------------------

### Get dependencies

```sh
$ git clone https://github.com/qadium-memex/linkalytics.git
```

Move into the directory and to install requirements run

```sh
$ pip3 install -r requirements.txt
```

### Instantiate credentials from shared repository using `credstmpl`

```sh
$ credstmpl linkalytics/environment/*.j2
```

See Qadium's [credstmpl github repository](Credstmpl) for installation instructions.

> Also, please note this requires AWS credentials.


### Step 2 -- Get going

Open two terminal windows, in the first type

> Note:
> Ensure there is a local elasticsearch instance running as well as a worker queue.
> We use [disque][Disque] as our in-memory, distributed job queue.

```sh
$ python3 manage.py runserver
```

In the second, type

```sh
$ python3 -m linkalytics
```

[Documentation](https://swaggerhub.com/api/jjangsangy/linkalytics)
------------------------------------------------------------------

[![Swagger Badge][Swagger]][Swagger Badge]

Interactive documentation for the Linkalytics API can be found [here][Swagger].

For more information about generating a client or server, check out [swagger](http://swagger.io/) project


[License]:       https://github.com/qadium-memex/linkalytics/blob/master/LICENSE     "Apache 2.0 License"
[License Badge]: https://img.shields.io/pypi/l/coverage.svg                          "Apache 2.0 Badge"

[Version]:       https://badge.fury.io/gh/qadium-memex%2Flinkalytics                 "Github Version"
[Version Badge]: https://badge.fury.io/gh/qadium-memex%2Flinkalytics.svg             "Github Version Badge"

[Travis]:        https://travis-ci.org/qadium-memex/linkalytics                      "Travis-CI"
[Travis Badge]:  https://travis-ci.org/qadium-memex/linkalytics.svg?branch=master    "Travis-CI Badge"

[Swagger]:       http://online.swagger.io/validator/?url=https://raw.githubusercontent.com/qadium-memex/linkalytics/master/swagger.yaml
[Swagger Badge]: https://swaggerhub.com/api/jjangsangy/linkalytics

[Disque]:    https://github.com/antirez/disque.git
[Credstmpl]: https://github.com/qadium/credstmpl
