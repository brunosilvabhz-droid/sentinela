import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  Bell,
  Database,
  Eye,
  FileUp,
  History,
  LogOut,
  Play,
  Plus,
  RefreshCcw,
  Shield,
  Trash2,
  Users,
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const emptySourceForm = {
  name: "",
  source_type: "postgresql",
  connection_uri: "",
  table_name: "",
};

const databaseExamples = {
  postgresql: {
    title: "Banco PostgreSQL",
    uri: "postgresql+psycopg://user:pass@host:5432/database",
    table: "public.pedidos",
  },
  oracle: {
    title: "Banco Oracle",
    uri: "oracle+oracledb://user:pass@host:1521/?service_name=ORCLPDB1",
    table: "SCHEMA.PEDIDOS",
  },
  sqlserver: {
    title: "Banco SQL Server",
    uri: "mssql+pyodbc://user:pass@host:1433/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes",
    table: "dbo.Pedidos",
  },
};

const emptyAlertForm = {
  name: "",
  data_source_id: "",
  column_name: "",
  condition: ">",
  threshold_value: "",
  frequency: "15m",
  recipients: "financeiro@demo.com",
  channels: ["email"],
};

const emptyUserForm = {
  name: "",
  email: "",
  password: "",
  role: "user",
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("sentinela_token") || "");
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("admin1234");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [summary, setSummary] = useState(null);
  const [sources, setSources] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [users, setUsers] = useState([]);
  const [agents, setAgents] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [preview, setPreview] = useState(null);
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [sourceForm, setSourceForm] = useState(emptySourceForm);
  const [managedSourceName, setManagedSourceName] = useState("Fonte gerenciada pelo collector");
  const [agentName, setAgentName] = useState("Collector local");
  const [createdAgentToken, setCreatedAgentToken] = useState("");
  const [collectorConfig, setCollectorConfig] = useState("");
  const [uploadForm, setUploadForm] = useState({ name: "Nova fonte CSV", source_type: "csv", file: null });
  const [alertForm, setAlertForm] = useState(emptyAlertForm);
  const [userForm, setUserForm] = useState(emptyUserForm);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const activeSources = useMemo(() => sources.filter((source) => source.is_active), [sources]);
  const activeAlerts = useMemo(() => alerts.filter((alert) => alert.is_active), [alerts]);
  const isAdmin = currentUser?.role === "admin";

  useEffect(() => {
    if (token) {
      runAction(() => loadWorkspace(token), { quiet: true });
    }
  }, []);

  useEffect(() => {
    if (!alertForm.data_source_id && activeSources[0]) {
      setAlertForm((current) => ({ ...current, data_source_id: String(activeSources[0].id) }));
    }
  }, [activeSources, alertForm.data_source_id]);

  async function api(path, options = {}, authToken = token) {
    const headers = {
      Authorization: authToken ? `Bearer ${authToken}` : undefined,
      ...(options.headers || {}),
    };
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }
    const response = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(formatApiError(text));
    }
    return response.json();
  }

  async function login(event) {
    event.preventDefault();
    await runAction(async () => {
      const data = await api(
        "/auth/login",
        { method: "POST", body: JSON.stringify({ email, password }) },
        "",
      );
      localStorage.setItem("sentinela_token", data.access_token);
      setToken(data.access_token);
      await loadWorkspace(data.access_token);
      setMessage("Login realizado. Ambiente local pronto para teste.");
    });
  }

  async function loadWorkspace(authToken = token) {
    const me = await api("/users/me", {}, authToken);
    const [dashboard, sourceList, alertList, executionList] = await Promise.all([
      api("/dashboard/summary", {}, authToken),
      api("/data-sources", {}, authToken),
      api("/alerts", {}, authToken),
      api("/alerts/executions", {}, authToken),
    ]);
    const [userList, agentList] = me.role === "admin"
      ? await Promise.all([api("/users", {}, authToken), api("/ingestion/agents", {}, authToken)])
      : [[], []];
    setCurrentUser(me);
    setSummary(dashboard);
    setSources(sourceList);
    setAlerts(alertList);
    setExecutions(executionList);
    setUsers(userList);
    setAgents(agentList);
    if (me.role !== "admin" && ["sources", "users"].includes(activeTab)) {
      setActiveTab("dashboard");
    }
    if (!selectedSourceId && sourceList[0]) {
      setSelectedSourceId(String(sourceList[0].id));
    }
  }

  async function createDatabaseSource(event) {
    event.preventDefault();
    await runAction(async () => {
      await api("/data-sources", {
        method: "POST",
        body: JSON.stringify({
          name: sourceForm.name,
          source_type: sourceForm.source_type,
          connection_uri: sourceForm.connection_uri,
          table_name: sourceForm.table_name,
          config: {},
        }),
      });
      setSourceForm(emptySourceForm);
      setMessage("Fonte de banco cadastrada.");
      await loadWorkspace();
      setActiveTab("sources");
    });
  }

  async function createManagedSource(event) {
    event.preventDefault();
    await runAction(async () => {
      await api("/ingestion/sources", {
        method: "POST",
        body: JSON.stringify({ name: managedSourceName, config: {} }),
      });
      setMessage("Fonte gerenciada criada. Crie um agent e use o collector para enviar dados.");
      await loadWorkspace();
      setActiveTab("sources");
    });
  }

  async function createAgent(event) {
    event.preventDefault();
    await runAction(async () => {
      const agent = await api("/ingestion/agents", {
        method: "POST",
        body: JSON.stringify({ name: agentName }),
      });
      setCreatedAgentToken(agent.token);
      setCollectorConfig(buildCollectorConfig({ token: agent.token, sourceId: selectedManagedSourceId(activeSources) }));
      setMessage("Agent criado. Copie o token agora; ele nao sera exibido novamente.");
      await loadWorkspace();
    });
  }

  async function createUser(event) {
    event.preventDefault();
    await runAction(async () => {
      await api("/users", {
        method: "POST",
        body: JSON.stringify(userForm),
      });
      setUserForm(emptyUserForm);
      setMessage("Usuario criado.");
      await loadWorkspace();
    });
  }

  async function uploadSource(event) {
    event.preventDefault();
    await runAction(async () => {
      if (!uploadForm.file) {
        throw new Error("Selecione um arquivo CSV, TXT ou Excel.");
      }
      const formData = new FormData();
      formData.append("file", uploadForm.file);
      const query = new URLSearchParams({ name: uploadForm.name, source_type: uploadForm.source_type });
      await api(`/data-sources/upload?${query.toString()}`, { method: "POST", body: formData });
      setUploadForm({ name: "Nova fonte CSV", source_type: "csv", file: null });
      setMessage("Arquivo enviado e fonte criada.");
      await loadWorkspace();
      setActiveTab("sources");
    });
  }

  async function showPreview(sourceId) {
    await runAction(async () => {
      const data = await api(`/data-sources/${sourceId}/preview`);
      setSelectedSourceId(String(sourceId));
      setPreview(data);
      setMessage(`Preview carregado: ${data.columns.length} coluna(s).`);
    });
  }

  async function createAlert(event) {
    event.preventDefault();
    await runAction(async () => {
      await api("/alerts", {
        method: "POST",
        body: JSON.stringify({
          ...alertForm,
          data_source_id: Number(alertForm.data_source_id),
          recipients: splitList(alertForm.recipients),
        }),
      });
      setAlertForm({ ...emptyAlertForm, data_source_id: alertForm.data_source_id });
      setMessage("Alerta criado.");
      await loadWorkspace();
      setActiveTab("alerts");
    });
  }

  async function runAlert(id) {
    await runAction(async () => {
      const result = await api(`/alerts/${id}/run`, { method: "POST" });
      setMessage(`Alerta executado: ${result.status} (${result.matched_count} ${pluralize(result.matched_count, "registro encontrado", "registros encontrados")}).`);
      await loadWorkspace();
      setActiveTab("history");
    });
  }

  async function deactivateAlert(id) {
    await runAction(async () => {
      await api(`/alerts/${id}`, { method: "DELETE" });
      setMessage("Alerta desativado.");
      await loadWorkspace();
    });
  }

  async function deactivateSource(id) {
    await runAction(async () => {
      await api(`/data-sources/${id}`, { method: "DELETE" });
      setMessage("Fonte desativada.");
      await loadWorkspace();
    });
  }

  async function runAction(action, options = {}) {
    setLoading(true);
    if (!options.quiet) {
      setMessage("");
    }
    try {
      await action();
    } catch (error) {
      setMessage(`Erro: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("sentinela_token");
    setToken("");
    setSummary(null);
    setSources([]);
    setAlerts([]);
    setExecutions([]);
    setUsers([]);
    setAgents([]);
    setCurrentUser(null);
    setPreview(null);
    setMessage("Sessao encerrada.");
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Shield size={28} />
          <strong>SENTINELA</strong>
        </div>
        <nav>
          <NavItem active={activeTab === "dashboard"} icon={<Activity size={18} />} label="Dashboard" onClick={() => setActiveTab("dashboard")} />
          {isAdmin && <NavItem active={activeTab === "sources"} icon={<Database size={18} />} label="Fontes" onClick={() => setActiveTab("sources")} />}
          <NavItem active={activeTab === "alerts"} icon={<Bell size={18} />} label="Alertas" onClick={() => setActiveTab("alerts")} />
          <NavItem active={activeTab === "history"} icon={<History size={18} />} label="Relatorios" onClick={() => setActiveTab("history")} />
          {isAdmin && <NavItem active={activeTab === "users"} icon={<Users size={18} />} label="Usuarios" onClick={() => setActiveTab("users")} />}
        </nav>
      </aside>

      <section className="content">
        <header>
          <div>
            <h1>Monitoramento e alertas</h1>
            <p>Console local para operar fontes, regras, execucoes e historico.</p>
          </div>
          <div className="header-actions">
            <button onClick={() => runAction(() => loadWorkspace())} disabled={!token || loading}>
              <RefreshCcw size={16} /> Atualizar
            </button>
            {token && <button className="secondary" onClick={logout}><LogOut size={16} /> Sair</button>}
          </div>
        </header>

        {!token && (
          <form className="panel login" onSubmit={login}>
            <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
            <label>Senha<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
            <button type="submit" disabled={loading}>Entrar</button>
          </form>
        )}

        {message && <div className={message.startsWith("Erro") ? "notice error" : "notice"}>{message}</div>}

        {token && activeTab === "dashboard" && (
          <>
            <div className="metrics">
              <Metric label="Alertas enviados" value={summary?.sent_alerts ?? 0} />
              <Metric label="Alertas ativos" value={summary?.active_alerts ?? 0} />
              <Metric label="Alertas inativos" value={summary?.inactive_alerts ?? 0} />
              <Metric label="Fontes ativas" value={activeSources.length} />
            </div>
            <section className="panel two-column">
              <div>
                <h2>Ambiente local</h2>
                <p>API: {API_URL}</p>
                <p>Usuario: {currentUser?.name} ({currentUser?.role})</p>
                <p>Fontes cadastradas: {sources.length}</p>
                <p>Alertas cadastrados: {alerts.length}</p>
              </div>
              <div>
                <h2>{isAdmin ? "Fluxo admin" : "Acesso usuario"}</h2>
                <p>{isAdmin ? "Cadastre fontes, agents, usuarios e regras de alerta." : "Acompanhe alertas, execucoes e relatorios da sua empresa."}</p>
              </div>
            </section>
          </>
        )}

        {token && isAdmin && activeTab === "sources" && (
          <SourcesView
            activeSources={activeSources}
            agentName={agentName}
            agents={agents}
            collectorConfig={collectorConfig}
            createAgent={createAgent}
            createDatabaseSource={createDatabaseSource}
            createManagedSource={createManagedSource}
            createdAgentToken={createdAgentToken}
            deactivateSource={deactivateSource}
            loading={loading}
            managedSourceName={managedSourceName}
            preview={preview}
            selectedSourceId={selectedSourceId}
            setAgentName={setAgentName}
            setAlertForm={setAlertForm}
            setCollectorConfig={setCollectorConfig}
            setManagedSourceName={setManagedSourceName}
            setSourceForm={setSourceForm}
            setUploadForm={setUploadForm}
            showPreview={showPreview}
            sourceForm={sourceForm}
            uploadForm={uploadForm}
            uploadSource={uploadSource}
          />
        )}

        {token && activeTab === "alerts" && (
          <AlertsView
            activeAlerts={activeAlerts}
            activeSources={activeSources}
            alertForm={alertForm}
            createAlert={createAlert}
            deactivateAlert={deactivateAlert}
            loading={loading}
            preview={preview}
            runAlert={runAlert}
            setAlertForm={setAlertForm}
          />
        )}

        {token && activeTab === "history" && <HistoryView executions={executions} />}
        {token && isAdmin && activeTab === "users" && (
          <UsersView
            createUser={createUser}
            loading={loading}
            setUserForm={setUserForm}
            userForm={userForm}
            users={users}
          />
        )}
      </section>
    </main>
  );
}

function SourcesView({
  activeSources,
  agentName,
  agents,
  collectorConfig,
  createAgent,
  createDatabaseSource,
  createManagedSource,
  createdAgentToken,
  deactivateSource,
  loading,
  managedSourceName,
  preview,
  selectedSourceId,
  setAgentName,
  setAlertForm,
  setCollectorConfig,
  setManagedSourceName,
  setSourceForm,
  setUploadForm,
  showPreview,
  sourceForm,
  uploadForm,
  uploadSource,
}) {
  const dbExample = databaseExamples[sourceForm.source_type] || databaseExamples.postgresql;

  return (
    <>
      <section className="grid-2">
        <form className="panel form-grid" onSubmit={createManagedSource}>
          <div className="panel-title with-action">
            <h2>Fonte gerenciada</h2>
            <Shield size={18} />
          </div>
          <label>Nome<input value={managedSourceName} onChange={(event) => setManagedSourceName(event.target.value)} /></label>
          <button disabled={loading || !managedSourceName}><Plus size={16} /> Criar fonte gerenciada</button>
        </form>

        <form className="panel form-grid" onSubmit={createAgent}>
          <div className="panel-title with-action">
            <h2>Collector agent</h2>
            <Shield size={18} />
          </div>
          <label>Nome<input value={agentName} onChange={(event) => setAgentName(event.target.value)} /></label>
          <button disabled={loading || !agentName}><Plus size={16} /> Criar agent</button>
          {createdAgentToken && (
            <div className="token-box">
              <strong>Token do agent</strong>
              <code>{createdAgentToken}</code>
            </div>
          )}
          {createdAgentToken && (
            <button
              className="secondary"
              type="button"
              onClick={() => setCollectorConfig(buildCollectorConfig({ token: createdAgentToken, sourceId: selectedManagedSourceId(activeSources) }))}
            >
              Gerar config.json
            </button>
          )}
        </form>
      </section>

      {collectorConfig && (
        <section className="panel">
          <div className="panel-title"><h2>Config do collector</h2></div>
          <pre className="code-block">{collectorConfig}</pre>
        </section>
      )}

      <section className="grid-2">
        <form className="panel form-grid" onSubmit={uploadSource}>
          <div className="panel-title with-action">
            <h2>Upload de arquivo</h2>
            <FileUp size={18} />
          </div>
          <label>Nome<input value={uploadForm.name} onChange={(event) => setUploadForm((current) => ({ ...current, name: event.target.value }))} /></label>
          <label>Tipo
            <select value={uploadForm.source_type} onChange={(event) => setUploadForm((current) => ({ ...current, source_type: event.target.value }))}>
              <option value="csv">CSV</option>
              <option value="txt">TXT</option>
              <option value="excel">Excel</option>
            </select>
          </label>
          <label>Arquivo<input type="file" accept=".csv,.txt,.xlsx,.xls" onChange={(event) => setUploadForm((current) => ({ ...current, file: event.target.files?.[0] || null }))} /></label>
          <button disabled={loading || !uploadForm.name}><Plus size={16} /> Criar fonte</button>
        </form>

        <form className="panel form-grid" onSubmit={createDatabaseSource}>
          <div className="panel-title with-action">
            <h2>{dbExample.title}</h2>
            <Database size={18} />
          </div>
          <label>Tipo de banco
            <select value={sourceForm.source_type} onChange={(event) => setSourceForm((current) => ({ ...current, source_type: event.target.value }))}>
              <option value="postgresql">PostgreSQL</option>
              <option value="oracle">Oracle</option>
              <option value="sqlserver">SQL Server</option>
            </select>
          </label>
          <label>Nome<input value={sourceForm.name} onChange={(event) => setSourceForm((current) => ({ ...current, name: event.target.value }))} /></label>
          <label>Connection URI<input value={sourceForm.connection_uri} onChange={(event) => setSourceForm((current) => ({ ...current, connection_uri: event.target.value }))} placeholder={dbExample.uri} /></label>
          <label>Tabela<input value={sourceForm.table_name} onChange={(event) => setSourceForm((current) => ({ ...current, table_name: event.target.value }))} placeholder={dbExample.table} /></label>
          <button disabled={loading || !sourceForm.name || !sourceForm.connection_uri || !sourceForm.table_name}><Plus size={16} /> Criar conexao</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>Fontes ativas</h2></div>
        <div className="table">
          <div className="row source-list-head"><span>Nome</span><span>Tipo</span><span>Status</span><span>Acoes</span></div>
          {activeSources.map((source) => (
            <div className="row source-list-row" key={source.id}>
              <span>{source.name}</span>
              <span>{source.source_type}</span>
              <span>{source.is_active ? "ativa" : "inativa"}</span>
              <div className="row-actions">
                <button className="icon-button secondary" onClick={() => showPreview(source.id)} title="Preview"><Eye size={16} /></button>
                <button className="icon-button secondary" onClick={() => setAlertForm((current) => ({ ...current, data_source_id: String(source.id) }))} title="Usar em alerta"><Bell size={16} /></button>
                <button className="icon-button danger" onClick={() => deactivateSource(source.id)} title="Desativar"><Trash2 size={16} /></button>
              </div>
            </div>
          ))}
          {activeSources.length === 0 && <div className="empty">Nenhuma fonte ativa.</div>}
        </div>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>Agents cadastrados</h2></div>
        <div className="table">
          <div className="row agents-head"><span>Nome</span><span>Status</span><span>Ultima atividade</span></div>
          {agents.map((agent) => (
            <div className="row agents-row" key={agent.id}>
              <span>{agent.name}</span>
              <span>{agent.is_active ? "ativo" : "inativo"}</span>
              <span>{agent.last_seen_at ? new Date(agent.last_seen_at).toLocaleString("pt-BR") : "-"}</span>
            </div>
          ))}
          {agents.length === 0 && <div className="empty">Nenhum agent criado.</div>}
        </div>
      </section>

      <PreviewPanel preview={preview} selectedSourceId={selectedSourceId} />
    </>
  );
}

function AlertsView({ activeAlerts, activeSources, alertForm, createAlert, deactivateAlert, loading, preview, runAlert, setAlertForm }) {
  const previewColumns = preview?.columns || [];

  return (
    <>
      <section className="panel form-grid">
        <div className="panel-title with-action">
          <h2>Novo alerta</h2>
          <Bell size={18} />
        </div>
        <form className="alert-form" onSubmit={createAlert}>
          <label>Nome<input value={alertForm.name} onChange={(event) => setAlertForm((current) => ({ ...current, name: event.target.value }))} placeholder="Pedidos acima de 1000" /></label>
          <label>Fonte
            <select value={alertForm.data_source_id} onChange={(event) => setAlertForm((current) => ({ ...current, data_source_id: event.target.value }))}>
              <option value="">Selecione</option>
              {activeSources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}
            </select>
          </label>
          <label>Coluna
            <input list="columns" value={alertForm.column_name} onChange={(event) => setAlertForm((current) => ({ ...current, column_name: event.target.value }))} placeholder="valor_total" />
            <datalist id="columns">
              {previewColumns.map((column) => <option key={column} value={column} />)}
            </datalist>
          </label>
          <label>Condicao
            <select value={alertForm.condition} onChange={(event) => setAlertForm((current) => ({ ...current, condition: event.target.value }))}>
              <option value=">">&gt;</option>
              <option value="<">&lt;</option>
              <option value="=">=</option>
              <option value=">=">&gt;=</option>
              <option value="<=">&lt;=</option>
              <option value="!=">!=</option>
            </select>
          </label>
          <label>Valor<input value={alertForm.threshold_value} onChange={(event) => setAlertForm((current) => ({ ...current, threshold_value: event.target.value }))} /></label>
          <label>Frequencia<input value={alertForm.frequency} onChange={(event) => setAlertForm((current) => ({ ...current, frequency: event.target.value }))} placeholder="15m ou */15 * * * *" /></label>
          <label>Destinatarios<input value={alertForm.recipients} onChange={(event) => setAlertForm((current) => ({ ...current, recipients: event.target.value }))} /></label>
          <fieldset>
            <legend>Canais</legend>
            <label className="inline"><input type="checkbox" checked={alertForm.channels.includes("email")} onChange={(event) => toggleChannel(event, "email", setAlertForm)} /> Email</label>
            <label className="inline"><input type="checkbox" checked={alertForm.channels.includes("whatsapp")} onChange={(event) => toggleChannel(event, "whatsapp", setAlertForm)} /> WhatsApp</label>
          </fieldset>
          <button
            disabled={loading}
            type="submit"
          >
            <Plus size={16} /> Criar alerta
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>Alertas ativos</h2></div>
        <div className="table">
          <div className="row alert-list-head"><span>Nome</span><span>Regra</span><span>Canais</span><span>Acoes</span></div>
          {activeAlerts.map((alert) => (
            <div className="row alert-list-row" key={alert.id}>
              <span>{alert.name}</span>
              <span>{alert.column_name} {alert.condition} {alert.threshold_value}</span>
              <span>{alert.channels.join(", ")}</span>
              <div className="row-actions">
                <button className="icon-button" onClick={() => runAlert(alert.id)} title="Executar agora" disabled={loading}><Play size={16} /></button>
                <button className="icon-button danger" onClick={() => deactivateAlert(alert.id)} title="Desativar"><Trash2 size={16} /></button>
              </div>
            </div>
          ))}
          {activeAlerts.length === 0 && <div className="empty">Nenhum alerta ativo.</div>}
        </div>
      </section>
    </>
  );
}

function HistoryView({ executions }) {
  return (
    <section className="panel">
      <div className="panel-title"><h2>Historico de execucoes</h2></div>
      <div className="table">
        <div className="row history-head"><span>Alerta</span><span>Status</span><span>Registros</span><span>Inicio</span><span>Erro</span></div>
        {executions.map((execution) => (
          <div className="row history-row" key={execution.id}>
            <span>{execution.alert_name}</span>
            <span><StatusBadge status={execution.status} /></span>
            <span>{execution.matched_count}</span>
            <span>{new Date(execution.started_at).toLocaleString("pt-BR")}</span>
            <span>{execution.error_message || "-"}</span>
          </div>
        ))}
        {executions.length === 0 && <div className="empty">Nenhuma execucao registrada.</div>}
      </div>
    </section>
  );
}

function UsersView({ createUser, loading, setUserForm, userForm, users }) {
  return (
    <>
      <section className="panel form-grid">
        <div className="panel-title with-action">
          <h2>Novo usuario</h2>
          <Users size={18} />
        </div>
        <form className="user-form" onSubmit={createUser}>
          <label>Nome<input value={userForm.name} onChange={(event) => setUserForm((current) => ({ ...current, name: event.target.value }))} /></label>
          <label>Email<input value={userForm.email} onChange={(event) => setUserForm((current) => ({ ...current, email: event.target.value }))} /></label>
          <label>Senha<input type="password" value={userForm.password} onChange={(event) => setUserForm((current) => ({ ...current, password: event.target.value }))} /></label>
          <label>Perfil
            <select value={userForm.role} onChange={(event) => setUserForm((current) => ({ ...current, role: event.target.value }))}>
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </label>
          <button disabled={loading || !userForm.name || !userForm.email || userForm.password.length < 8}>
            <Plus size={16} /> Criar usuario
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>Usuarios</h2></div>
        <div className="table">
          <div className="row users-head"><span>Nome</span><span>Email</span><span>Perfil</span><span>Status</span></div>
          {users.map((user) => (
            <div className="row users-row" key={user.id}>
              <span>{user.name}</span>
              <span>{user.email}</span>
              <span>{user.role}</span>
              <span>{user.is_active ? "ativo" : "inativo"}</span>
            </div>
          ))}
          {users.length === 0 && <div className="empty">Nenhum usuario cadastrado.</div>}
        </div>
      </section>
    </>
  );
}

function PreviewPanel({ preview, selectedSourceId }) {
  if (!preview) {
    return (
      <section className="panel">
        <div className="panel-title"><h2>Preview</h2></div>
        <div className="empty">Selecione uma fonte para ver colunas e dados de amostra.</div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-title"><h2>Preview da fonte #{selectedSourceId}</h2></div>
      <div className="preview-meta">{preview.columns.join(" | ")}</div>
      <div className="preview-table">
        <table>
          <thead>
            <tr>{preview.columns.map((column) => <th key={column}>{column}</th>)}</tr>
          </thead>
          <tbody>
            {preview.rows.map((row, index) => (
              <tr key={index}>
                {preview.columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function NavItem({ active, icon, label, onClick }) {
  return <button className={active ? "nav-item active" : "nav-item"} onClick={onClick}>{icon} {label}</button>;
}

function StatusBadge({ status }) {
  return <span className={`badge ${status}`}>{status}</span>;
}

function splitList(value) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function toggleChannel(event, channel, setAlertForm) {
  setAlertForm((current) => {
    const channels = event.target.checked
      ? [...new Set([...current.channels, channel])]
      : current.channels.filter((item) => item !== channel);
    return { ...current, channels };
  });
}

function formatApiError(text) {
  try {
    const parsed = JSON.parse(text);
    return typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail || parsed);
  } catch {
    return text;
  }
}

function pluralize(count, singular, plural) {
  return Number(count) === 1 ? singular : plural;
}

function selectedManagedSourceId(sources) {
  return sources.find((source) => source.source_type === "managed")?.id || sources[0]?.id || 1;
}

function buildCollectorConfig({ token, sourceId }) {
  return JSON.stringify(
    {
      sentinela_api_url: API_URL,
      agent_token: token || "sentinela_agent_TOKEN_GERADO_NO_SAAS",
      data_source_id: sourceId,
      connection_uri: "postgresql+psycopg://user:pass@host:5432/database",
      query: "select pedido_id, cliente, valor_total, status from public.pedidos",
      primary_key: "pedido_id",
      batch_size: 500,
    },
    null,
    2,
  );
}

createRoot(document.getElementById("root")).render(<App />);
