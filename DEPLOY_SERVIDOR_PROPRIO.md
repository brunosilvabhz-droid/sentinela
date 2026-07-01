# Deploy em servidor proprio

Este roteiro sobe o SENTINELA em uma maquina propria com Docker Compose, Caddy, PostgreSQL, Redis, API, worker, beat e frontend.

## Requisitos

- Ubuntu Server 24.04 LTS ou similar
- 8 GB RAM
- 500 GB SSD
- Docker e Docker Compose
- Portas 80 e 443 liberadas no roteador/firewall
- Dominio apontando para o IP publico da maquina

## DNS

Crie ou ajuste:

| Tipo | Nome | Destino |
| --- | --- | --- |
| A | @ | IP publico da sua internet |
| CNAME | www | impactocg.com |
| CNAME | api | impactocg.com |

Se seu IP nao for fixo, use DNS dinamico ou Cloudflare Tunnel.

## Subir

```bash
git clone https://github.com/brunosilvabhz-droid/sentinela.git
cd sentinela
cp .env.server.example .env.server
nano .env.server
docker compose --env-file .env.server -f docker-compose.prod.yml up -d --build
```

Depois acesse:

```text
https://impactocg.com
https://api.impactocg.com/health
```

## Variaveis obrigatorias

No `.env.server`, troque obrigatoriamente:

- `POSTGRES_PASSWORD`
- `DATABASE_URL`, usando a mesma senha do Postgres
- `JWT_SECRET_KEY`
- `APP_DOMAIN`
- `LETSENCRYPT_EMAIL`
- `FRONTEND_PUBLIC_URL`
- `CORS_ALLOWED_ORIGINS`

## Comandos uteis

```bash
docker compose --env-file .env.server -f docker-compose.prod.yml ps
docker compose --env-file .env.server -f docker-compose.prod.yml logs -f api
docker compose --env-file .env.server -f docker-compose.prod.yml logs -f worker
docker compose --env-file .env.server -f docker-compose.prod.yml restart api worker beat
docker compose --env-file .env.server -f docker-compose.prod.yml pull
docker compose --env-file .env.server -f docker-compose.prod.yml up -d --build
```

## Backup manual do banco

```bash
mkdir -p backups
docker compose --env-file .env.server -f docker-compose.prod.yml exec postgres pg_dump -U sentinela sentinela > backups/sentinela_$(date +%Y%m%d_%H%M).sql
```

Copie a pasta `backups/` para fora da maquina, por exemplo Google Drive, OneDrive, S3 ou outro disco.

## Restaurar backup

```bash
cat backups/arquivo.sql | docker compose --env-file .env.server -f docker-compose.prod.yml exec -T postgres psql -U sentinela sentinela
```

## Atualizar app

```bash
git pull
docker compose --env-file .env.server -f docker-compose.prod.yml up -d --build
```

## Observacoes importantes

- Caddy gera HTTPS automaticamente se o dominio estiver apontando corretamente.
- Nao exponha PostgreSQL e Redis na internet.
- A API fica publica apenas por `https://api.impactocg.com` e por `/api` no dominio principal.
- Configure backup externo antes de atender cliente real.
- Use nobreak se essa maquina ficar em escritorio/casa.
