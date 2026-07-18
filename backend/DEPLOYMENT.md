# EcoTrace — Deployment Guide

## Architecture

```
Internet → Cloudflare (DDoS + WAF) → VPS → Nginx (HTTPS) → Docker
                                                              ├── api  (FastAPI on :8000)
                                                              └── db   (PostgreSQL)
```

Static landing files are served directly by FastAPI under `/landing/*`.

---

## 1. Server prerequisites

```bash
# On a fresh Ubuntu 22.04 / Debian 12 VPS
sudo apt update && sudo apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
sudo usermod -aG docker $USER && newgrp docker
```

---

## 2. Clone and configure

```bash
git clone https://github.com/Zwony/ecotrace.git
cd ecotrace

cp .env.example .env
nano .env          # fill in every variable
```

Generate a secure JWT secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3. OAuth App setup

**Google:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Web application)
3. Add Authorised redirect URI: `https://your-domain.com/auth/google/callback`
4. Copy Client ID and Secret into `.env`

**GitHub:**
1. Go to https://github.com/settings/developers → New OAuth App
2. Homepage URL: `https://your-domain.com`
3. Callback URL: `https://your-domain.com/auth/github/callback`
4. Copy Client ID and Secret into `.env`

---

## 4. Build and start

```bash
docker compose up -d --build

# Run database migrations
docker compose exec api alembic upgrade head

# Verify both containers are healthy
docker compose ps
```

---

## 5. Nginx + HTTPS

```nginx
# /etc/nginx/sites-available/ecotrace
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ecotrace /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. Cloudflare setup (after domain purchase)

1. Add your domain to Cloudflare (free plan works)
2. Point the A record to your VPS IP
3. Set SSL/TLS mode to **Full (strict)**
4. Enable **Bot Fight Mode** under Security
5. Add a WAF rule to block requests without a valid `User-Agent`
6. Enable **Under Attack Mode** during launch if needed

---

## 7. Firewall (ufw)

```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp    # block direct access, only Nginx should reach it
sudo ufw enable
```

---

## 8. Sending metrics from EcoTrace

A signed-in user generates a personal ingestion key from the dashboard:

```
Dashboard → "Generate dashboard key" button
```

Then configure their local project:

```python
from ecotrace import EcoTrace
from ecotrace.exporters.webhook import WebhookExporter

eco = EcoTrace(region_code="TR")
WebhookExporter(
    eco,
    url="https://your-domain.com/api/metrics/ingest",
    headers={"X-EcoTrace-Key": "ect_your_personal_key"},
)
```

Every measurement is stored under that user's account only.
