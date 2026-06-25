# SENTINELA

SENTINELA e uma plataforma SaaS multi-tenant para monitoramento de dados, regras de alerta e notificacoes automaticas por email e WhatsApp.

## Arquitetura

```text
sentinela/
  backend/
    app/
      api/
        deps.py
        router.py
        routes/
          auth.py
          tenants.py
          users.py
          data_sources.py
          alerts.py
          dashboard.py
      core/
        config.py
        security.py
      db/
        base.py
        init_db.py
        session.py
      models/
        tenant.py
        user.py
        data_source.py
        alert.py
      schemas/
        auth.py
        tenant.py
        user.py
        data_source.py
        alert.py
      services/
        auth_service.py
        data_loader.py
        notification_service.py
        rule_engine.py
        tenant_limits.py
      workers/
        celery_app.py
        tasks.py
    Dockerfile
    requirements.txt
  frontend/
    src/
      main.jsx
      styles.css
  docker-compose.yml
```

## Modelo Multi-Tenant

O isolamento do MVP usa `tenant_id` em todas as tabelas de negocio. Toda rota autenticada le o usuario atual pelo JWT e filtra queries por `current_user.tenant_id`.

Tabelas:

- `tenants`: empresas/clientes. Campos principais: `id`, `name`, `document`, `plan`, `max_alerts`, `is_active`, `created_at`.
- `users`: usuarios vinculados ao tenant. Campos: `id`, `tenant_id`, `name`, `email`, `hashed_password`, `role`, `is_active`, `created_at`.
- `data_sources`: fontes CSV/TXT/Excel/PostgreSQL/Oracle/SQL Server. Campos: `id`, `tenant_id`, `name`, `source_type`, `file_path`, `connection_uri`, `table_name`, `config`, `is_active`, `created_at`.
- `alerts`: regras. Campos: `id`, `tenant_id`, `data_source_id`, `name`, `column_name`, `condition`, `threshold_value`, `frequency`, `recipients`, `channels`, `is_active`, `last_run_at`, `created_at`.
- `alert_executions`: logs. Campos: `id`, `tenant_id`, `alert_id`, `status`, `matched_count`, `sample_records`, `channels`, `error_message`, `started_at`, `finished_at`, `duration_ms`.

Para producao, uma evolucao forte e ativar Row Level Security no PostgreSQL alem do filtro na aplicacao.

## Como Rodar

```bash
docker compose up --build
```

Inicialize as tabelas e um usuario demo:

```bash
docker compose exec api python -m app.db.init_db
```

Acesse:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- MailHog: `http://localhost:8025`
- Frontend: rode em outro terminal dentro de `frontend`: `npm install && npm run dev`

Login demo:

```text
admin@demo.com
admin1234
```

## Fluxo Principal

1. Criar tenant em `POST /api/v1/tenants`.
2. Criar usuario admin em `POST /api/v1/tenants/{tenant_id}/users`.
3. Fazer login em `POST /api/v1/auth/login`.
4. Criar fonte em `POST /api/v1/data-sources` ou enviar arquivo em `POST /api/v1/data-sources/upload`.
5. Criar alerta em `POST /api/v1/alerts`.
6. Executar manualmente em `POST /api/v1/alerts/{alert_id}/run` ou deixar o Celery Beat disparar.
7. Consultar logs em `GET /api/v1/alerts/{alert_id}/executions`.
8. Consultar indicadores em `GET /api/v1/dashboard/summary`.

## Exemplo de Alerta

```json
{
  "data_source_id": 1,
  "name": "Pedidos acima de 1000",
  "column_name": "valor_total",
  "condition": ">",
  "threshold_value": "1000",
  "frequency": "*/15 * * * *",
  "recipients": ["financeiro@empresa.com", "whatsapp:+5511999999999"],
  "channels": ["email", "whatsapp"]
}
```

O motor carrega a fonte, avalia a coluna e grava uma linha em `alert_executions` com status `sent`, `no_match` ou `error`.

## Notificacoes

Email usa SMTP configurado por env vars. Em desenvolvimento, o compose usa MailHog.

WhatsApp usa Twilio. Configure:

```text
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Se Twilio nao estiver configurado, a chamada de WhatsApp e ignorada para facilitar desenvolvimento local.

## Fontes Oracle e SQL Server

A SENTINELA aceita fontes relacionais via SQLAlchemy:

```text
PostgreSQL: postgresql+psycopg://user:pass@host:5432/database
Oracle:     oracle+oracledb://user:pass@host:1521/?service_name=ORCLPDB1
SQL Server: mssql+pyodbc://user:pass@host:1433/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

Exemplos de tabelas:

```text
PostgreSQL: public.pedidos
Oracle:     SCHEMA.PEDIDOS
SQL Server: dbo.Pedidos
```

Observacoes:

- Oracle usa o pacote Python `oracledb`.
- SQL Server usa `pyodbc` e precisa do Microsoft ODBC Driver instalado no servidor.
- Em deploy Linux, instale o ODBC Driver 18 no container ou use uma imagem base customizada.
- O preview limita a leitura a 10.000 linhas para evitar cargas grandes.
- O isolamento por cliente continua sendo feito por `tenant_id` nas configuracoes da SENTINELA; a tabela externa deve ser controlada por credenciais de leitura.

## SaaS, Planos e Limites

O campo `tenants.max_alerts` limita alertas ativos. O MVP ja bloqueia criacao acima do limite com HTTP 402.

Sugestao de planos:

- Free: 5 alertas, execucao a cada 60 min, 1 usuario.
- Starter: 25 alertas, execucao a cada 15 min, 5 usuarios.
- Pro: 100 alertas, execucao a cada 5 min, WhatsApp habilitado.
- Enterprise: limites customizados, SSO, RLS obrigatorio, auditoria avancada.

Billing pode ser integrado com Stripe: `tenant.plan`, `tenant.max_alerts` e uma futura tabela `subscriptions` sincronizada por webhooks.

## Deploy

Opcoes praticas:

- Render: Postgres gerenciado, Redis, Web Service para API, Worker para Celery e Cron/Background Worker para Beat.
- Azure: Azure Container Apps, Azure Database for PostgreSQL, Azure Cache for Redis, Key Vault para segredos.

Este repositorio ja inclui `render.yaml`, Alembic e comandos de producao. Veja [DEPLOY_RENDER.md](DEPLOY_RENDER.md).

Checklist de producao:

- Trocar `JWT_SECRET_KEY`.
- Usar HTTPS.
- Configurar SMTP real.
- Configurar Twilio.
- Migrar `Base.metadata.create_all` para Alembic.
- Sanitizar politicas de upload, antivirus e storage S3/Azure Blob.
- Ativar logs estruturados e tracing.
- Aplicar RLS no PostgreSQL se houver exigencia forte de isolamento.
