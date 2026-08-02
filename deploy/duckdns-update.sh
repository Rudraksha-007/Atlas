#!/usr/bin/env bash
# Updates the DuckDNS A record with the current public IP.
# Reads DUCKDNS_DOMAIN and DUCKDNS_TOKEN from /etc/atlas/duckdns.conf
set -euo pipefail

source /etc/atlas/duckdns.conf

curl -fsS -o /dev/null --max-time 20 \
    "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip="
