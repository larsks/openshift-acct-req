#!/bin/bash

while :; do
	gunicorn -b 0.0.0.0:8080 -c config.py -e PYTHONBUFFERED=TRUE wsgi:application --log-file=-
	echo "Failed!"
	sleep 1
done

