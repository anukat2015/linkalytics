#!/usr/bin/env bash

LOCKFILE='tika-server.pid'

echo "Making pid file $LOCKFILE"

touch $LOCKFILE

function handle_interrupt() {
    cleanup
    echo 'Exiting'
    exit 0
}

function cleanup() {
    rm -rf $LOCKFILE
    pkill java
    return $?
}

function loop() {
    while true; do
        read x
    done
}

java -jar $(find . -type f -name 'tika-server.jar') &

trap handle_interrupt SIGINT EXIT

loop
