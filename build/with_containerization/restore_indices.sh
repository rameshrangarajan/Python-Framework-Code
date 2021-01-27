#!/bin/sh

cd ./../../flask_backend/
# $1 should be backup path ,
# $2 : restore_thumbnail : Value should be True or False. If this argument is not provided, it will take default value as True
python3 elasticsearch_backup_restore.py restore $1 $2