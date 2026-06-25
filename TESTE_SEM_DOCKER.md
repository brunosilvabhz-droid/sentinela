# Testando sem Docker

O erro `docker: O termo 'docker' nao e reconhecido` significa que o Docker Desktop nao esta instalado ou nao esta no PATH do Windows.

Para testar agora sem Docker, rode a API com SQLite local.

## 1. Abrir a pasta do backend

```powershell
cd C:\Users\bruno\Documents\Codex\2026-06-25\voc-um-arquiteto-de-software-s\outputs\sentinela\backend
```

## 2. Criar ambiente virtual

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Usar configuracao local SQLite

```powershell
Copy-Item .env.local.example .env
```

## 5. Criar banco, usuario demo, CSV demo e alerta demo

```powershell
python -m app.db.init_db
```

## 6. Rodar API

```powershell
uvicorn app.main:app --reload
```

Abra:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## 7. Login no Swagger

Em `POST /api/v1/auth/login`, use:

```json
{
  "email": "admin@demo.com",
  "password": "admin1234"
}
```

Copie o `access_token`, clique em `Authorize` no topo do Swagger e cole:

```text
Bearer SEU_TOKEN
```

## 8. Testar alerta pronto

O seed cria automaticamente:

- Fonte: `Pedidos Demo`
- CSV: `storage/uploads/1/pedidos.csv`
- Alerta: `Pedidos acima de 1000`

Teste:

1. `GET /api/v1/alerts`
2. Pegue o `id` do alerta
3. Rode `POST /api/v1/alerts/{alert_id}/run`
4. Veja o resultado em `GET /api/v1/alerts/{alert_id}/executions`

Como nao ha MailHog sem Docker, o envio SMTP pode falhar se o alerta tiver match. O log ainda sera gravado com status `error`. Para testar a regra sem erro de email, edite o alerta e deixe `channels: []`, ou instale um SMTP local.

## Opcional: instalar Docker depois

Se quiser usar o ambiente completo com PostgreSQL, Redis, Celery e MailHog, instale o Docker Desktop:

https://www.docker.com/products/docker-desktop/

Depois feche e reabra o PowerShell e rode na pasta `outputs\sentinela`:

```powershell
docker compose up --build
```
