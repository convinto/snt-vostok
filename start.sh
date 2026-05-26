#!/bin/bash
mkdir -p /data
flask db upgrade
python app.py