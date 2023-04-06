#!/usr/bin/env bash

set -e

wait_for_services.sh

if [ "$DJANGO_MIGRATE" = "yes" ]; then
    ./manage.py migrate --noinput
    ./manage.py collectstatic --noinput
fi

exec "$@"

