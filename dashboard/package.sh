#!/bin/bash

#runtime: docker
#name: csv-dashboard
#zip -r9 csv-dashboard.zip Dockerfile app requirements.txt

rm -f csv-dashboard.zip
pushd app
zip -r9 ../csv-dashboard.zip application.py static templates
popd
zip -r9 csv-dashboard.zip requirements.txt
