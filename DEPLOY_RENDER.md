# Deploy no Render

Este projeto esta preparado para deploy no Render com:

- Frontend React/Vite como Static Site
- Backend FastAPI como Web Service
- PostgreSQL gerenciado
- Redis-compatible Key Value para Celery
- Celery worker
- Celery beat scheduler
- Alembic para migrations

## 1. Blueprint

O arquivo `render.yaml` fica na raiz do repositorio. No Render:

1. Crie um novo Blueprint.
2. Conecte o repositorio `brunosilvabhz-droid/sentinela`.
3. Confirme os servicos criados pelo `render.yaml`.

Servicos esperados:

```text
sentinela-api
sentinela-web
sentinela-worker
sentinela-beat
sentinela-redis
sentinela-db
```

## 2. Variaveis Obrigatorias

O `render.yaml` ja conecta automaticamente:

```text
DATABASE_URL -> sentinela-db
REDIS_URL    -> sentinela-redis
JWT_SECRET_KEY -> gerado automaticamente
```

Configure manualmente se quiser email/WhatsApp em producao:

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM_EMAIL
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM
```

## 3. URL do Frontend

O frontend usa:

```text
VITE_API_URL=https://sentinela-api.onrender.com/api/v1
```

Se o Render gerar outro subdominio para a API, ajuste `VITE_API_URL` no servico `sentinela-web` e atualize:

```text
CORS_ALLOWED_ORIGINS=https://SEU-FRONTEND.onrender.com
```

no servico `sentinela-api`.

## 4. Migrations

O backend roda automaticamente:

```bash
alembic upgrade head
```

como `preDeployCommand` do servico `sentinela-api`.

Comandos manuais uteis:

```bash
cd backend
alembic current
alembic upgrade head
alembic revision --autogenerate -m "descricao"
```

## 5. Comandos de Producao

API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Worker:

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

Scheduler:

```bash
celery -A app.workers.celery_app.celery_app beat --loglevel=INFO
```

Frontend:

```bash
npm ci && npm run build
```

Publish directory:

```text
frontend/dist
```

## 6. SQL Server e ODBC

O pacote Python `pyodbc` esta no `requirements.txt`, mas SQL Server exige o Microsoft ODBC Driver instalado no ambiente.

No Render com runtime Python nativo, conectores SQL Server podem exigir uma imagem Docker customizada com:

```text
ODBC Driver 18 for SQL Server
unixodbc
```

Oracle usa `oracledb` em modo thin para conexoes comuns e geralmente nao precisa de Instant Client.

## 7. Checklist Pos-Deploy

1. Abrir `/health` da API.
2. Abrir `/docs` da API.
3. Criar tenant e usuario admin.
4. Fazer login no frontend.
5. Criar uma fonte gerenciada.
6. Criar um collector agent.
7. Rodar o collector Python em ambiente de teste do cliente.
8. Criar e executar um alerta sobre dados ingeridos.
9. Conferir worker e beat nos logs do Render.
10. Configurar SMTP real.
11. Configurar Twilio WhatsApp.
12. Trocar para planos pagos antes de clientes reais.
