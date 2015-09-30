# linkalytics
Backend analytics to link together disparate data

##Getting Started with Linkalytics

####Step 1 -- Get dependencies

```git clone git@github.com:qadium-memex/linkalytics.git```

```pip3 install requirements.txt```

```brew install redis```

####OPTIONAL: Step 2 -- Instantiate credentials from shared repository using `credstmpl`

See Qadium's [credstmpl github repository](https://github.com/qadium/credstmpl) for more installation instructions. Also, please note this requires AWS credentials. If you'd like to work with our data, contact one of us for the creds.

```credstmpl /src/environment/common.cfg.j2```

```credstmpl /src/environment/develop.cfg.j2```

```credstmpl /src/environment/production.cfg.j2```


####Step 2 -- Get going

Open two terminal windows, in the first type

```rqworker twitter```

In the second, type

```python3 main.py```

