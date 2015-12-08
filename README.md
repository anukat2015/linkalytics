Linkalytics
===========

[![License][License Badge]][License] [![Version][Version Badge]][Version] [![Travis][Travis Badge]][Travis]

Backend analytics to link together disparate data

Support
--------

Here’s a list of Python platforms that are officially supported.

- Python 3.5 (Latest)
- Python 3.4

Quickstart
==========

Clone Repository
----------------

```sh
$ git clone https://github.com/qadium-memex/linkalytics.git
```

### \*_Optional_ `Git LFS`

This repository contains some large filed stored using [Git (Large File System) LFS][LFS Blog].

Git Large File Storage (LFS) replaces large files such as audio samples, videos, datasets,
and graphics with text pointers inside Git, while storing the file contents on a remote server.

[Instructions for installing Git LFS][LFS]

After installing LFS, to retrieve the text pointers with the actual files runha.

```sh
$ git lfs pull
```

Install Python Dependencies
---------------------------

```sh
$ pip3 install -r requirements.txt
```

Also it is necessary to install the dependencies `pandas` and `scipy`

```sh
$ pip3 install scipy pandas
```

Install Disque
--------------
Currently we utilize [Disque][Disque] as a distributed work queue.

To install disque, ensure that you have a proper C Compiler installed and grab the repository

```sh
$ git clone https://github.com/antirez/disque.git
```

Make and install binaries

```sh
make && make install
```

Or use `sudo` if necessary

```sh
make && sudo make install
```


Instantiate credentials from shared repository using `credstmpl`
----------------------------------------------------------------
See Qadium's [credstmpl github repository](Credstmpl) for installation instructions.

> Also, please note this requires AWS credentials.


```sh
$ credstmpl linkalytics/environment/*.j2
```

Run Services (Short Version)
----------------------------

There is a quick and dirty start script that should run all the necessary services required to run linkalytics.

To run in from the root project directory

```sh
$ ./start.sh
```

If this doesn't work try the longer version and start each service manually


Run Services (Long Version)
---------------------------

Each of these services should run in it's own terminal window

### Run the disque server

```sh
$ disque-server
```

### Start Redis Server

```sh
$ redis-server infrastructure/ansible/redis/templates/redis.conf
```

### Start Linkalytics API Server

```sh
$ python3 manage.py runserver
```

### Start Workers

```sh
$ python3 -m linkalytics
```

### _[Optional]_ Start Tika Metadata Extraction Server

* _Requires Java Runtime Environment 7+_

```sh
$ java -jar $(find . -type f -name 'tika-server.jar')
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

[LFS]: https://git-lfs.github.com
[LFS Blog]: https://github.com/blog/1986-announcing-git-large-file-storage-lfs
