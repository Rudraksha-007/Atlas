# Deploying Atlas backend (ThinkPad, Fedora, nginx + Cloudflare Tunnel)

This deploys the FastAPI backend as a 24/7 systemd service behind nginx,
exposed to the internet through a Cloudflare Tunnel at
`https://atlas.<you>.pp.ua`. Postgres stays on Supabase, Redis stays on
Redis Cloud — only uvicorn, nginx and cloudflared run on the ThinkPad.

No inbound ports, no static IP, no certbot: the tunnel connects **out** to
Cloudflare, and Cloudflare's edge terminates HTTPS for free.

## Architecture

```
[phone/internet] --HTTPS--> Cloudflare edge <--tunnel(outbound)--> cloudflared
                                   ^                                  |
                                   |                     nginx :80 (ThinkPad)
                                   |                                  v
                                   +---------- uvicorn 127.0.0.1:8000
```

## Before you start

1. **Free domain (pp.ua)**: register at https://pp.ua (free; approval usually
   within hours). Pick something like `atlas.<yourname>.pp.ua`.
2. **Cloudflare**: add the domain as a site (free plan). It gives you two
   nameservers (e.g. `xxx.ns.cloudflare.com`) — set them in the pp.ua control
   panel. Wait for propagation: `dig +short atlas.<you>.pp.ua ns` should show
   `*.ns.cloudflare.com`.
3. **Tunnel**: Cloudflare Zero Trust (free) -> Networks -> Tunnels -> Create a
   tunnel (Cloudflared, named). Add a public hostname:
   `atlas.<you>.pp.ua` -> service `http://localhost` (nginx on :80).
   Copy the tunnel token (used with `--cf-token`).
4. **.env**: copy `.env.example` from the repo root to `.env`, fill in real
   values (DATABASE_URL, REDIS_URL, SECRET_KEY). Keep `ALLOWED_ORIGINS`
   containing `https://atlas.<you>.pp.ua`.

## Install (automated)

On the ThinkPad (works over SSH — no network blips anymore):

```sh
git clone https://github.com/Rudraksha-007/Atlas.git ~/atlas
cd ~/atlas
cp /path/to/your-filled.env ./env.tmp        # scp it from your dev machine
```

The real command:

```sh
sudo ./deploy/deploy.sh --env-file ./env.tmp \
     --domain atlas.<you>.pp.ua --cf-token <TUNNEL_TOKEN>
```

Prefer not to have the token in shell history? Skip `--cf-token` and write it
afterwards (the script will warn you):

```sh
printf 'CF_TOKEN=<TUNNEL_TOKEN>\n' | sudo tee /etc/atlas/cloudflared.conf
sudo chmod 600 /etc/atlas/cloudflared.conf
sudo cloudflared service install "<TUNNEL_TOKEN>"
sudo systemctl enable --now cloudflared
```

The script:
- installs nginx and cloudflared (Cloudflare RPM repo)
- installs uv + Python 3.14, clones/pulls the repo to `~/atlas`,
  runs `uv sync --no-dev`
- copies your `.env` to root-only `/etc/atlas/.env` (appends your domain to
  `ALLOWED_ORIGINS` if missing)
- runs `alembic upgrade head` against the database
- installs and starts `atlas-backend.service` (uvicorn on 127.0.0.1:8000)
- installs the tunnel token and starts `cloudflared`
- writes the nginx vhost (HTTP-only, proxy to uvicorn) and starts nginx
- masks sleep/suspend/hibernate and ignores lid-close (24/7 operation)

## Verify

On the ThinkPad:

```sh
systemctl status atlas-backend nginx cloudflared   # all active (running)
curl -s localhost:8000/                            # local API
journalctl -u cloudflared -f                       # tunnel connected
```

From your phone (mobile data, not home WiFi):

```sh
curl -s https://atlas.<you>.pp.ua/
curl -s https://atlas.<you>.pp.ua/docs
```

End-to-end: signup -> login -> refresh -> create capsule through
`https://atlas.<you>.pp.ua`.

## Useful commands

```sh
journalctl -u atlas-backend -f        # backend logs
systemctl restart atlas-backend       # after a code update
systemctl restart cloudflared         # if the tunnel drops
```

## Updating the backend

```sh
cd ~/atlas && git pull --ff-only
sudo systemctl restart atlas-backend
```

## Troubleshooting

- **502/521 from the tunnel**: nginx is probably not seeing uvicorn.
  `curl -s localhost:8000/` locally; check `journalctl -u atlas-backend -u nginx`.
- **Tunnel shows "HEALTHY" but site is down**: public hostname in Zero Trust
  must point to `http://localhost` (port 80, nginx) — not to port 8000.
- **cloudflared missing**: the script installs it from the Cloudflare RPM
  repo; on failure do it manually:
  `sudo dnf install -y cloudflared` (after writing /etc/yum.repos.d/cloudflared.repo).
- **AVC denials in `journalctl -u nginx`** (SELinux): proxying to 127.0.0.1:8000
  works out of the box (port 8000 is in `http_port_t`). If you still see
  denials: `sudo setsebool -P nginx_can_network_connect 1`.
- **Service fails with `203/EXEC` / "Permission denied" on `.venv/bin/uvicorn`
  or `uv`**: SELinux on Fedora blocks systemd from executing binaries inside
  `$HOME`. `deploy.sh` fixes this automatically. Manually:
  ```sh
  sudo chcon -R -t bin_t ~/atlas/.venv/bin
  sudo systemctl restart atlas-backend
  ```
- **CORS errors from the frontend**: make sure `ALLOWED_ORIGINS` in
  `/etc/atlas/.env` includes `https://atlas.<you>.pp.ua`, then
  `sudo systemctl restart atlas-backend`.
