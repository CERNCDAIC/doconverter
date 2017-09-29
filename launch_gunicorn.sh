#!/usr/bin/bash

cd ./doconverter/api/

if [[ -z $TIMEOUTWORKERS ]]; then
    echo "TIMEOUTWORKERS variable not set. Setting to 200"
    TIMEOUTWORKERS=200
fi
if [[ -z $WORKERS ]]; then
    echo "WORKERS variable not set. Setting to 1"
    WORKERS=1
fi
gunicorn handlers:app -p handlers.pid -b 0.0.0.0:8080 --pythonpath $HOME -t $TIMEOUTWORKERS -w $WORKERS
