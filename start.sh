#!/usr/bin/env bash

pkill disque-server

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
    printf '\nKilling Processes\n'
    kill "$linkalytics" "$server" $dq_server $tika_server
}

trap cleanup SIGKILL SIGHUP SIGINT

wait "$linkalytics" "$server" "$dq_server" "$tika_server"
