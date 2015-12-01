#!/usr/bin/env bash

set -e

if [ -n "$(pgrep disque-server)" ]; then
    pkill disque-server
fi

echo "Starting Disque Server"
(
    disque-server
) &> /dev/null & dq_server=$!


echo "Starting Linkalytics Server"
(
    python3 -W ignore manage.py runserver
) &> /dev/null & server=$!


echo "Starting Workers"
(
    python3 -W ignore -m linkalytics
) &> /dev/null & linkalytics=$!

echo "Starting Tika Server"
(
    java -jar $(find . -type f -name 'tika-server.jar')
) &> /dev/null & tika_server=$!

function cleanup() {
    printf '\n%s\n' "Killing Processes"
    kill "$linkalytics" "$server" $dq_server $tika_server
}

function error() {
    echo "Error Starting Service"
}

trap cleanup SIGKILL SIGHUP SIGINT
trap error ERR

wait "$linkalytics" "$server" "$dq_server" "$tika_server" "$redis_server"
