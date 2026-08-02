# Deploying Atlas backend (ThinkPad, Fedora, DuckDNS)

This deploys the FastAPI backend as a 24/7 systemd service behind nginx with
HTTPS, reachable at `https://atlas.duckdns.org`. Postgres stays on Supabase,
Redis stays on Redis Cloud — only uvicorn runs on the ThinkPad. No dedicated
service user is needed; the service runs as your normal user.

## Before you start

1. **DuckDNS**: create the subdomain `atlas` at https://duckdns.org and copy
   your token (in the "update" link, between `token=` and `&ip=`).
2. **Router**: static IP `192.168.1.50` for the ThinkPad and two port-forward
   rules (TCP): `80 -> 192.168.1.50:80` and `443 -> 192.168.1.50:443`.
   (On the GX router: Services -> Port Forwarding, local IP = 192.168.1.50,
   remote IP = 0.0.0.0, protocol TCP, remote/local ports 80 or 443,
   interface = WAN.)
3. **.env**: copy `.env.example` from the repo root to `.env`, fill in real
   values (DATABASE_URL, REDIS_URL, SECRET_KEY). Keep `ALLOWED_ORIGINS`
   including `https://atlas.duckdns.org`.

## Install (automated)

On the ThinkPad:

```sh
git clone https://github.com/Rudraksha-007/Atlas.git ~/atlas
cd ~/atlas
sudo DUCKDNS_DOMAIN=atlas DUCKDNS_TOKEN=<your-token> \
  ./deploy/deploy.sh --env-file ./your-filled.env --domain atlas.duckdns.org
```

The script:
- installs nginx, certbot, curl and uv (Python 3.14)
- clones/pulls the repo to `~/atlas`, runs `uv sync --no-dev`
- copies your `.env` to root-only `/etc/atlas/.env` (appends `ALLOWED_ORIGINS`
  with your domain if missing)
- writes `/etc/atlas/duckdns.conf` (from the token above), installs the
  5-minute DuckDNS updater
- runs `alembic upgrade head` against the database
- renders and starts `atlas-backend.service` (uvicorn on 127.0.0.1:8000)
- sets the static IP `192.168.1.50` via nmcli
- configures nginx + lets you set up certbot HTTPS (see next section)
- masks sleep/suspend/hibernate and ignores lid-close

Run it from a local terminal on the ThinkPad, not over SSH, because the
static-IP step blips the network. Over SSH, add `--no-static-ip` and set the
IP manually (below).

If you don't want the token in shell history, let the script skip the DuckDNS
step and instead write `/etc/atlas/duckdns.conf` afterwards:

```sh
printf 'DUCKDNS_DOMAIN=atlas\nDUCKDNS_TOKEN=<your-token>\n' | sudo tee /etc/atlas/duckdns.conf
sudo chmod 600 /etc/atlas/duckdns.conf
sudo systemctl start duckdns-update.timer
```

### HTTPS (certbot)

Two ways to get the certificate:

**Path A - HTTP-01** (needs port 80 reachable from the internet): the script
tries `certbot --nginx -d <domain>` automatically; if it failed, run manually:

```sh
sudo certbot --nginx -d atlas.duckdns.org
sudo systemctl enable --now certbot-renew.timer
```

**Path B - DNS-01** (no inbound ports needed; use when the router/ISP hijacks
or blocks ports 80/443): the script obtains the cert through the DuckDNS TXT
record and configures nginx TLS on port 443:

```sh
sudo DUCKDNS_DOMAIN=atlas DUCKDNS_TOKEN=<your-token> \
  ./deploy/deploy.sh --env-file ./your-filled.env --dns01 --domain atlas.duckdns.org
```

Then the only router change needed is one forward rule (TCP):
`8443 -> 192.168.1.50:443`. The API is then reachable at
`https://atlas.duckdns.org:8443` (port 8443 because the router's own admin
interface occupies 443 on the WAN side). Renewal is automatic via
`certbot-renew.timer` (the renewal config stores the DuckDNS token).

## Manual steps the script does not cover

### Static IP (if you skipped it)
```sh
nmcli con show --active          # find your wifi connection name
nmcli con mod "<conn>" ipv4.addresses 192.168.1.50/24 \
    ipv4.gateway 192.168.1.1 ipv4.method manual \
    ipv4.dns "1.1.1.1 8.8.8.8" ipv4.ignore-auto-dns yes
nmcli con up "<conn>"
```

### BIOS / power (always-on)
- Plug in the ThinkPad and leave the lid open or closed (lid-close now does
  nothing thanks to the logind override).
- BIOS: enable "power on when AC is connected" if available.
- Optional: a small UPS to survive power blips.

## Verify

```sh
systemctl status atlas-backend        # should be active (running)
curl -s localhost:8000/               # local API
sudo certbot renew --dry-run          # cert renewal works
```

From your phone (mobile data, not home WiFi):
```sh
curl -s https://atlas.duckdns.org/
curl -s https://atlas.duckdns.org/docs
```

End-to-end: signup -> login -> refresh -> create capsule through
`https://atlas.duckdns.org`.

## Useful commands

```sh
journalctl -u atlas-backend -f        # backend logs
systemctl restart atlas-backend       # after a code update
sudo systemctl status duckdns-update.timer
```

## Updating the backend

```sh
cd ~/atlas && git pull --ff-only
sudo systemctl restart atlas-backend
```

## Troubleshooting

- **Service fails with `203/EXEC` / "Permission denied" on `.venv/bin/uvicorn`
  or `uv`**: SELinux on Fedora blocks systemd from executing binaries inside
  `$HOME` (they get `user_tmp_t`/`user_home_t` contexts). `deploy.sh` fixes this
  automatically (semanage fcontext + restorecon, chcon fallback). Manually:
  ```sh
  sudo chcon -R -t bin_t ~/atlas/Atlas/.venv/bin
  sudo systemctl restart atlas-backend
  ```
- **DuckDNS updates**: check `/etc/atlas/duckdns.conf` exists and
  `systemctl status duckdns-update.service` ran clean.
- **Certbot failed**: port 80 may be blocked/hijacked by the router or ISP.
  Re-run the deploy with `--dns01` (Path B above), which needs no inbound
  ports at all. Manual fallback:
  `pip install certbot-dns-duckdns` then
  `certbot certonly --dns-duckdns --dns-duckdns-token <TOKEN> -d atlas.duckdns.org`.
- **ISP blocked port 80 entirely**: forward `8080 -> 80` instead, use
  `https://atlas.duckdns.org:8080`... note HTTPS on non-443 needs a custom
  port in nginx; the simplest fallback then is a Cloudflare Tunnel.
