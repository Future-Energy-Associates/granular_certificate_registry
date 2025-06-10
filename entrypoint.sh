#!/bin/bash

cron

touch /var/log/cron.log
tail -f /var/log/cron.log &

# Start your FastAPI app
exec uvicorn gc_registry.main:app --host 0.0.0.0 --port 8000