# Arquitetura SENTINELA

## Decisao Principal

A SENTINELA usa uma arquitetura SaaS com **coletor Python do lado do cliente**.

O banco da aplicacao nao consulta diretamente Oracle, SQL Server, PostgreSQL ou outras fontes internas do cliente. Em vez disso:

1. O cliente instala o `sentinela_collector.py` dentro da propria rede.
2. O collector consulta as fontes internas usando credenciais locais do cliente.
3. O collector envia os dados normalizados para a API da SENTINELA via HTTPS.
4. A SENTINELA grava os registros no banco central por `tenant_id` e `data_source_id`.
5. O motor de alertas avalia regras sobre os dados ja ingeridos no banco da aplicacao.

## Fluxo

```text
Oracle / SQL Server / PostgreSQL / ERP / Arquivo
        |
        | consulta local
        v
SENTINELA Collector Python no cliente
        |
        | HTTPS outbound com X-Agent-Token
        v
SENTINELA API /ingestion/batches
        |
        v
PostgreSQL da aplicacao
        |
        v
Motor de alertas + notificacoes
```

## Vantagens

- Nao precisa abrir firewall do cliente para o SaaS.
- Credenciais Oracle/SQL Server ficam no ambiente do cliente.
- O SaaS recebe apenas os dados necessarios para monitoramento.
- Funciona com fontes legadas e bancos internos.
- Facilita vender para empresas com politicas rigidas de rede.

## Tabelas Novas

- `collector_agents`: agentes autorizados por tenant.
- `ingestion_batches`: controle de lotes recebidos, idempotencia e auditoria.
- `ingested_records`: registros normalizados em JSON.

## Segurança

- Cada agent tem um token proprio.
- A API armazena somente hash SHA-256 do token.
- O token identifica o tenant; o collector nao envia `tenant_id`.
- Toda ingestao valida se a fonte pertence ao tenant do agent.
- Batches usam `idempotency_key` para evitar duplicidade de envio.

## Fontes Diretas

O projeto ainda possui suporte direto a CSV/Excel/PostgreSQL/Oracle/SQL Server para testes, MVPs e cenarios controlados. Para produto SaaS vendido a clientes, o caminho recomendado e fonte `managed` + collector.

## Formato do Registro

Cada registro enviado:

```json
{
  "source_record_id": "123",
  "payload": {
    "pedido_id": 123,
    "cliente": "Acme",
    "valor_total": 1250.5,
    "status": "critico"
  },
  "collected_at": "2026-06-25T18:00:00Z"
}
```

As regras de alerta usam as chaves de `payload` como colunas.
