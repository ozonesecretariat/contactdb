#!/usr/bin/env bash

set -e

wait-for-it "$POSTGRES_HOST":"${POSTGRES_PORT:-5432}" --timeout=60
