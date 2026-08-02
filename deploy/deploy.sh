#!/usr/bin/env bash
# One-shot deployment of the Atlas backend on a Fedora machine.
# Runs as your own user (no dedicated service user needed).
#
# Usage:
#   sudo ./deploy.sh [--env-file /path/to/.env] [--domain atlas.duckdns.org]
#
# Optional env vars (or pass --domain):
#   DUCKDNS_DOMAIN   e.g. atlas
#   DUCKDNS_TOKEN    your DuckDNS token
#
# Before running:
#   1. Create the subdomain at https://duckdns.org and note the token
#   2. Router: ports 80/443 forwarded to the static IP (default 192.168.1.50)
#   3. A filled .env (copy .env.example, set real secrets) - pass via --env-file
#
# Flags:
#   --no-static-ip   skip nmcli static IP setup (use if running over SSH)
set -euo pipefail

DEPLOY_USER="${SUDO_USER:-$(whoami)}"
APP_DIR="${APP_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo /home/$DEPLOY_USER/atlas)}"
UV_BIN="/home/$DEPLOY_USER/.local/bin/uv"
ENV_SRC=""
DOMAIN="atlas.duckdns.org"
STATIC_IP="192.168.1.50"
GATEWAY="192.168.1.1"
REPO_URL="https://github.com/Rudraksha-007/Atlas.git"
DO_STATIC_IP=1

usage() {
    sed -n '2,20p' "$0" | sed 's/^# //; s/^#$/  /'
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file)   ENV_SRC="${2:?}"; shift 2 ;;
        --domain)     DOMAIN="${2:?}"; shift 2 ;;
        --no-static-ip) DO_STATIC_IP=0; shift ;;
        *) echo "Unknown argument: $1"; usage ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: run as root (sudo)." >&2
    exit 1
fi

if [[ "$DEPLOY_USER" == "root" ]]; then
    echo "WARN: deploying as root. Better: run 'sudo ./deploy.sh' from your normal user." >&2
fi

if [[ -z "$ENV_SRC" ]]; then
    if [[ -f /etc/atlas/.env ]]; then
        ENV_SRC=/etc/atlas/.env
    elif [[ -f ./.env ]]; then
        ENV_SRC=./.env
    else
        echo "ERROR: no .env found. Pass one with --env-file (see .env.example)." >&2
        exit 1
    fi
fi

if ! grep -q "^DATABASE_URL=." "$ENV_SRC" || ! grep -q "^REDIS_URL=." "$ENV_SRC"; then
    echo "ERROR: $ENV_SRC must contain DATABASE_URL and REDIS_URL." >&2
    exit 1
fi

if ! command -v dig >/dev/null 2>&1; then
    dnf install -y bind-utils >/dev/null 2>&1 || true
fi

echo "==> 1/10 Installing packages (nginx, certbot, curl)"
dnf install -y nginx certbot python3-certbot-nginx curl >/dev/null

echo "==> 2/10 Deploying as user '$DEPLOY_USER' (app dir: $APP_DIR)"

echo "==> 3/10 Installing uv for $DEPLOY_USER"
if [[ ! -x "$UV_BIN" ]]; then
    runuser -u "$DEPLOY_USER" -- bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh' >/dev/null 2>&1
fi
"$UV_BIN" python install 3.14 >/dev/null 2>&1 || true

echo "==> 4/10 Cloning repo to $APP_DIR"
if [[ -d "$APP_DIR/.git" ]]; then
    git -C "$APP_DIR" pull --ff-only || true
else
    git clone "$REPO_URL" "$APP_DIR"
fi
chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"

echo "==> 5/10 Installing Python deps (uv sync --no-dev)"
runuser -u "$DEPLOY_USER" -- "$UV_BIN" sync --no-dev --directory "$APP_DIR" --python 3.14

echo "==> 6/10 Writing /etc/atlas config"
mkdir -p /etc/atlas /var/www/certbot
chmod 700 /etc/atlas
cp "$ENV_SRC" /etc/atlas/.env
if ! grep -q "^ALLOWED_ORIGINS=" /etc/atlas/.env; then
    printf '\nALLOWED_ORIGINS=http://localhost:5173,https://%s\n' "$DOMAIN" >> /etc/atlas/.env
fi
chmod 600 /etc/atlas/.env

if [[ -n "${DUCKDNS_TOKEN:-}" ]]; then
    DUCKDNS_SUBDOMAIN="${DUCKDNS_DOMAIN:-${DOMAIN%%.duckdns.org}}"
    printf 'DUCKDNS_DOMAIN=%s\nDUCKDNS_TOKEN=%s\n' \
        "$DUCKDNS_SUBDOMAIN" "$DUCKDNS_TOKEN" > /etc/atlas/duckdns.conf
    chmod 600 /etc/atlas/duckdns.conf
    install -m 0755 "$APP_DIR/deploy/duckdns-update.sh" /usr/local/sbin/duckdns-update.sh
    cp "$APP_DIR/deploy/duckdns-update.service" /etc/systemd/system/
    cp "$APP_DIR/deploy/duckdns-update.timer" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable --now duckdns-update.timer
fi

echo "==> 7/10 Running database migrations (alembic upgrade head)"
cd "$APP_DIR"
set -a
# shellcheck disable=SC1091
source /etc/atlas/.env
set +a
"$APP_DIR/.venv/bin/alembic" upgrade head

echo "==> 8/10 Installing services"
sed -e "s|@DEPLOY_USER@|$DEPLOY_USER|g" \
    -e "s|@UV_BIN@|$UV_BIN|g" \
    -e "s|@APP_DIR@|$APP_DIR|g" \
    "$APP_DIR/deploy/atlas-backend.service.in" > /etc/systemd/system/atlas-backend.service
systemctl daemon-reload
systemctl enable --now atlas-backend

if [[ "$DO_STATIC_IP" -eq 1 ]]; then
    echo "==> 9/10 Setting static IP $STATIC_IP (network will blip)"
    WIFI_CONN=$(nmcli -t -f NAME,TYPE con show --active | awk -F: '$2 ~ /wifi/ {print $1; exit}')
    if [[ -n "$WIFI_CONN" ]]; then
        nmcli con mod "$WIFI_CONN" \
            ipv4.addresses "$STATIC_IP/24" \
            ipv4.gateway "$GATEWAY" \
            ipv4.dns "1.1.1.1 8.8.8.8" \
            ipv4.ignore-auto-dns yes \
            ipv4.method manual
        nmcli con up "$WIFI_CONN" || true
    else
        echo "WARN: no active wifi connection found; set the static IP manually (see SETUP.md)."
    fi
fi

echo "==> 9/10 nginx + certbot (HTTPS for $DOMAIN)"
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/conf.d/atlas.conf
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.atlas.bak 2>/dev/null || true
cat > /etc/nginx/nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    log_format main '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';
    access_log /var/log/nginx/access.log main;
    sendfile on;
    keepalive_timeout 65;
    include /etc/nginx/conf.d/*.conf;
}
EOF
systemctl enable --now nginx

if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http --add-service=https >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
fi

certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email || true
systemctl enable --now certbot-renew.timer || true

echo "==> 10/10 Always-on hardening (sleep/lid-close)"
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target 2>/dev/null || true
mkdir -p /etc/systemd/logind.conf.d
cat > /etc/systemd/logind.conf.d/atlas-server.conf <<'EOF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
EOF
systemctl restart systemd-logind 2>/dev/null || true

echo
echo "========================================================"
echo "Done. Verify with:"
echo "  curl -s localhost:8000/          # local API"
echo "  curl -s https://$DOMAIN/  (from outside, e.g. your phone on mobile data)"
echo "  curl -s https://$DOMAIN/docs"
echo "  sudo certbot renew --dry-run"
echo "========================================================"
