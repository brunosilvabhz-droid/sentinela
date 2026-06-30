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
FRONTEND_PUBLIC_URL -> https://app.impactocg.com
```

Configure manualmente se quiser email/WhatsApp em producao:

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM_EMAIL
WHATSAPP_PROVIDER=meta
META_WHATSAPP_TOKEN
META_WHATSAPP_PHONE_NUMBER_ID
META_WHATSAPP_TEMPLATE_NAME
META_WHATSAPP_TEMPLATE_LANGUAGE=pt_BR

Opcional, se usar Twilio como alternativa:

```text
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM
```

## 3. Dominios de Producao

Mapa recomendado:

```text
impactocg.com      -> landing page institucional da IMPACTO
www.impactocg.com  -> landing page institucional da IMPACTO
app.impactocg.com  -> sistema SENTINELA
api.impactocg.com  -> API FastAPI
```

No Render:

1. Abra o servico `sentinela-web`.
2. Entre em `Settings` > `Custom Domains`.
3. Adicione `impactocg.com`.
4. Adicione `www.impactocg.com`.
5. Adicione `app.impactocg.com`.
6. Abra o servico `sentinela-api`.
7. Entre em `Settings` > `Custom Domains`.
8. Adicione `api.impactocg.com`.
9. Copie exatamente os registros DNS que o Render mostrar para cada dominio.

Na HostGator, no gerenciador de DNS do dominio `impactocg.com`, crie ou ajuste:

```text
Tipo   Nome   Destino
A      @      IP informado pelo Render para impactocg.com
CNAME  www    destino informado pelo Render para sentinela-web
CNAME  app    destino informado pelo Render para sentinela-web
CNAME  api    destino informado pelo Render para sentinela-api
```

Se existirem registros antigos de site para `@`, `www`, `app` ou `api`, remova ou substitua para evitar conflito. Como o site antigo nao sera mais usado, o dominio principal pode apontar direto para o Render.

Depois que o DNS propagar, volte no Render e aguarde o status `Verified` nos dominios. O certificado HTTPS sera emitido automaticamente.

## 4. URL do Frontend

O frontend usa:

```text
VITE_API_URL=https://api.impactocg.com/api/v1
VITE_SENTINELA_LOGIN_URL=https://app.impactocg.com/app
```

O backend deve aceitar os dominios do frontend:

```text
CORS_ALLOWED_ORIGINS=https://impactocg.com,https://www.impactocg.com,https://app.impactocg.com,https://sentinela-web.onrender.com
FRONTEND_PUBLIC_URL=https://app.impactocg.com
```

no servico `sentinela-api`.

## 5. Migrations

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

## 6. Comandos de Producao

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

## 7. SQL Server e ODBC

O pacote Python `pyodbc` esta no `requirements.txt`, mas SQL Server exige o Microsoft ODBC Driver instalado no ambiente.

No Render com runtime Python nativo, conectores SQL Server podem exigir uma imagem Docker customizada com:

```text
ODBC Driver 18 for SQL Server
unixodbc
```

Oracle usa `oracledb` em modo thin para conexoes comuns e geralmente nao precisa de Instant Client.

## 8. Checklist Pos-Deploy

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
12. Configurar os dominios customizados.
13. Testar `https://impactocg.com`.
14. Testar `https://app.impactocg.com`.
15. Testar `https://api.impactocg.com/health`.
16. Trocar para planos pagos antes de clientes reais.
