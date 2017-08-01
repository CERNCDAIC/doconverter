#!/usr/bin/bash

cd ./doconverter/api/

WORKERS=1
TIMEOUT=30
while test $# -gt 0; do
        case "$1" in
                -h|--help)
                        echo "Invoke gunicorn passing working nodes and timeout"
                        echo " "
                        echo "options:"
                        echo "-h, --help                show brief help"
                        echo "-w XX     number of workers"
                        echo "-t XX     timeout for inactivity, default 30 secs"
                        exit 0
                        ;;
                -w)
                        shift
                        if test $# -gt 0; then
                                WORKERS=$1
                        else
                                echo "no process specified"
                                exit 1
                        fi
                        shift
                        ;;
                -t)
                        shift
                        if test $# -gt 0; then
                                TIMEOUT=$1
                        else
                                echo "no output dir specified"
                                exit 1
                        fi
                        shift
                        ;;
                *)
                        break
                        ;;
        esac
done

gunicorn handlers:app -p handlers.pid -b 0.0.0.0:8080 -t $TIMEOUT -w $WORKERS
