#!/usr/bin/env bash
# One-shot deployment of the Atlas backend on a Fedora machine.
# Exposed to the internet via nginx + a Cloudflare Tunnel (no inbound ports,
# no static IP, no certbot - Cloudflare terminates TLS).
#
# Usage:
#   sudo ./deploy.sh [--env-file /path/to/.env] [--domain atlas.you.pp.ua] [--cf-token <TUNNEL_TOKEN>]
#
# Flags:
#   --env-file   path to the filled .env
#   --domain     public hostname for the tunnel/nginx (default: atlas.you.pp.ua)
#   --cf-token   cloudflared tunnel token (or write it afterwards to
#                /etc/atlas/cloudflared.conf as CF_TOKEN=... to avoid shell history)
#
# Before running:
#   1. Register a free pp.ua (or eu.org) subdomain and put it on Cloudflare DNS
#   2. Cloudflare Zero Trust -> Networks -> Tunnels: create a named tunnel
#      with public hostname atlas.you.pp.ua -> http://localhost (nginx :80)
#   3. A filled .env (copy .env.example, set real secrets) - pass via --env-file
set -euo pipefail

DEPLOY_USER="${SUDO_USER:-$(whoami)}"
APP_DIR="${APP_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo /home/$DEPLOY_USER/atlas)}"
UV_BIN="/home/$DEPLOY_USER/.local/bin/uv"
ENV_SRC=""
DOMAIN="atlas.you.pp.ua"
CF_TOKEN=""
REPO_URL="https://github.com/Rudraksha-007/Atlas.git"

usage() {
    sed -n '2,20p' "$0" | sed 's/^# //; s/^#$/  /'
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file)   ENV_SRC="${2:?}"; shift 2 ;;
        --domain)     DOMAIN="${2:?}"; shift 2 ;;
        --cf-token)   CF_TOKEN="${2:?}"; shift 2 ;;
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

echo "==> 1/10 Installing packages (nginx)"
dnf install -y nginx curl >/dev/null

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

echo "==> 5b/10 Fixing SELinux contexts for executables (Fedora Enforcing)"
if command -v semanage >/dev/null 2>&1; then
    semanage fcontext -a -t bin_t "$APP_DIR/.venv/bin(/.*)?" 2>/dev/null || true
    semanage fcontext -a -t bin_t "$UV_BIN" 2>/dev/null || true
    restorecon -R "$APP_DIR/.venv/bin" 2>/dev/null || true
    restorecon "$UV_BIN" 2>/dev/null || true
else
    chcon -R -t bin_t "$APP_DIR/.venv/bin" 2>/dev/null || true
    chcon -t bin_t "$UV_BIN" 2>/dev/null || true
fi

echo "==> 6/10 Writing /etc/atlas config"
mkdir -p /etc/atlas
chmod 700 /etc/atlas
if [[ "$ENV_SRC" != "/etc/atlas/.env" ]]; then
    cp "$ENV_SRC" /etc/atlas/.env
fi
sed -i -E 's/^([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$/\1=\2/' /etc/atlas/.env
if ! grep -q "^ALLOWED_ORIGINS=" /etc/atlas/.env; then
    printf '\nALLOWED_ORIGINS=http://localhost:5173,https://%s\n' "$DOMAIN" >> /etc/atlas/.env
elif ! grep -q "^ALLOWED_ORIGINS=.*$DOMAIN" /etc/atlas/.env; then
    sed -i "s|^ALLOWED_ORIGINS=|&http://localhost:5173,https://$DOMAIN,|" /etc/atlas/.env
fi
chmod 600 /etc/atlas/.env

echo "==> 7/10 Running database migrations (alembic upgrade head)"
cd "$APP_DIR"
set -a
# shellcheck disable=SC1091
source /etc/atlas/.env
set +a
"$APP_DIR/.venv/bin/alembic" upgrade head

echo "==> 8/10 Installing atlas-backend service (uvicorn on 127.0.0.1:8000)"
sed -e "s|@DEPLOY_USER@|$DEPLOY_USER|g" \
    -e "s|@APP_DIR@|$APP_DIR|g" \
    "$APP_DIR/deploy/atlas-backend.service.in" > /etc/systemd/system/atlas-backend.service
systemctl daemon-reload
systemctl enable --now atlas-backend

echo "==> 9/10 Installing cloudflared tunnel"
if [[ -z "$CF_TOKEN" && -f /etc/atlas/cloudflared.conf ]]; then
    CF_TOKEN=$(awk -F= '/^CF_TOKEN=/{print $2; exit}' /etc/atlas/cloudflared.conf)
fi
if [[ -z "$CF_TOKEN" ]]; then
    echo "WARN: no CF_TOKEN given (--cf-token / CF_TOKEN / /etc/atlas/cloudflared.conf)." >&2
    echo "      The tunnel will NOT be exposed until you set it:" >&2
    echo "        printf 'CF_TOKEN=<token>\\n' | sudo tee /etc/atlas/cloudflared.conf && sudo chmod 600 /etc/atlas/cloudflared.conf" >&2
    echo "        sudo cloudflared service install \"\$CF_TOKEN\" && sudo systemctl enable --now cloudflared" >&2
else
    if ! command -v cloudflared >/dev/null 2>&1; then
        cat > /etc/yum.repos.d/cloudflared.repo <<'EOF'
[cloudflared]
name=cloudflared
baseurl=https://pkg.cloudflare.com/cloudflared/rpm/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://pkg.cloudflare.com/cloudflared-repo.key
EOF
        dnf install -y cloudflared >/dev/null
    fi
    printf 'CF_TOKEN=%s\n' "$CF_TOKEN" > /etc/atlas/cloudflared.conf
    chmod 600 /etc/atlas/cloudflared.conf
    cloudflared service install "$CF_TOKEN" >/dev/null 2>&1 || true
    systemctl daemon-reload
    systemctl enable --now cloudflared
fi

echo "==> 10/10 nginx reverse proxy for $DOMAIN"
sed "s|@DOMAIN@|$DOMAIN|g" "$APP_DIR/deploy/nginx.conf" > /etc/nginx/conf.d/atlas.conf
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
nginx -t
systemctl enable --now nginx

if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
fi

echo "==> 11/11 Always-on hardening (sleep/lid-close)"
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
echo "  systemctl status cloudflared     # tunnel up?"
echo "  journalctl -u cloudflared -f     # tunnel logs"
echo "  curl -s https://$DOMAIN/         # from outside (e.g. your phone on mobile data)"
echo "========================================================"
