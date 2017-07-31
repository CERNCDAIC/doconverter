#!/usr/bin/bash

cd ./doconverter/api/
gunicorn handlers:app -p handlers.pid -b 0.0.0.0:8080 -t 300 -w 2
