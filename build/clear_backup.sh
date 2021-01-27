#!/bin/sh
find /home/vaibhav_malpani/KMP_GCP/kmt/flask_backend/* -type d -name "esbackup*" -ctime +15 | xargs rm -rf