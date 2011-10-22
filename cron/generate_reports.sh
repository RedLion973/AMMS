#!/bin/sh

PROJECT_ROOT=/home/ludovic/AptanaWorkspace/amms/src/amms

cd $PROJECT_ROOT
python manage.py generate_reports >> $PROJECT_ROOT/logs/cron_generate_reports.log 2>&1