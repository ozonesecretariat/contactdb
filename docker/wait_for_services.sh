#!/usr/bin/env bash

set -e

wait-for-it --timeout 60 --parallel \
  --service "${POSTGRES_HOST:-db}":"${POSTGRES_PORT:-5432}" \
  --service "${REDIS_HOST:-redis}":"${REDIS_PORT:-6379}"
