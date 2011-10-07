#!/bin/sh

PROJECT_ROOT=/home/ludovic/Aptana/amms/src/amms

cd $PROJECT_ROOT
python manage.py emit_notices >> $PROJECT_ROOT/logs/cron_emit_notices.log 2>&1