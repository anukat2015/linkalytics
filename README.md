Linkalytics
===========
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

### _OPTIONAL_: Step 2 -- Instantiate credentials from shared repository using `credstmpl`

See Qadium's [credstmpl github repository](https://github.com/qadium/credstmpl) for more installation instructions.

Also, please note this requires AWS credentials.

If you'd like to work with our data, contact one of us for the creds.

```sh
$ credstmpl /src/environment/*.j2
```


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

