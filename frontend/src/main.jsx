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
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const emptySourceForm = {
  name: "",
  source_type: "postgresql",
  connection_uri: "",
  table_name: "",
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

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("sentinela_token") || "");
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("admin1234");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [summary, setSummary] = useState(null);
  const [sources, setSources] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [preview, setPreview] = useState(null);
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [sourceForm, setSourceForm] = useState(emptySourceForm);
  const [uploadForm, setUploadForm] = useState({ name: "Nova fonte CSV", source_type: "csv", file: null });
  const [alertForm, setAlertForm] = useState(emptyAlertForm);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const activeSources = useMemo(() => sources.filter((source) => source.is_active), [sources]);
  const activeAlerts = useMemo(() => alerts.filter((alert) => alert.is_active), [alerts]);

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
    const [dashboard, sourceList, alertList, executionList] = await Promise.all([
      api("/dashboard/summary", {}, authToken),
      api("/data-sources", {}, authToken),
      api("/alerts", {}, authToken),
      api("/alerts/executions", {}, authToken),
    ]);
    setSummary(dashboard);
    setSources(sourceList);
    setAlerts(alertList);
    setExecutions(executionList);
    if (!selectedSourceId && sourceList[0]) {
      setSelectedSourceId(String(sourceList[0].id));
    }
  }

  async function createPostgresSource(event) {
    event.preventDefault();
    await runAction(async () => {
      await api("/data-sources", {
        method: "POST",
        body: JSON.stringify({
          name: sourceForm.name,
          source_type: "postgresql",
          connection_uri: sourceForm.connection_uri,
          table_name: sourceForm.table_name,
          config: {},
        }),
      });
      setSourceForm(emptySourceForm);
      setMessage("Fonte PostgreSQL cadastrada.");
      await loadWorkspace();
      setActiveTab("sources");
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
          <NavItem active={activeTab === "sources"} icon={<Database size={18} />} label="Fontes" onClick={() => setActiveTab("sources")} />
          <NavItem active={activeTab === "alerts"} icon={<Bell size={18} />} label="Alertas" onClick={() => setActiveTab("alerts")} />
          <NavItem active={activeTab === "history"} icon={<History size={18} />} label="Historico" onClick={() => setActiveTab("history")} />
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
                <p>Fontes cadastradas: {sources.length}</p>
                <p>Alertas cadastrados: {alerts.length}</p>
              </div>
              <div>
                <h2>Proximo teste</h2>
                <p>Crie uma fonte, faca preview, cadastre um alerta e execute pelo botao de play.</p>
              </div>
            </section>
          </>
        )}

        {token && activeTab === "sources" && (
          <SourcesView
            activeSources={activeSources}
            createPostgresSource={createPostgresSource}
            deactivateSource={deactivateSource}
            loading={loading}
            preview={preview}
            selectedSourceId={selectedSourceId}
            setAlertForm={setAlertForm}
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
      </section>
    </main>
  );
}

function SourcesView({
  activeSources,
  createPostgresSource,
  deactivateSource,
  loading,
  preview,
  selectedSourceId,
  setAlertForm,
  setSourceForm,
  setUploadForm,
  showPreview,
  sourceForm,
  uploadForm,
  uploadSource,
}) {
  return (
    <>
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

        <form className="panel form-grid" onSubmit={createPostgresSource}>
          <div className="panel-title with-action">
            <h2>Banco PostgreSQL</h2>
            <Database size={18} />
          </div>
          <label>Nome<input value={sourceForm.name} onChange={(event) => setSourceForm((current) => ({ ...current, name: event.target.value }))} /></label>
          <label>Connection URI<input value={sourceForm.connection_uri} onChange={(event) => setSourceForm((current) => ({ ...current, connection_uri: event.target.value }))} placeholder="postgresql+psycopg://user:pass@host:5432/db" /></label>
          <label>Tabela<input value={sourceForm.table_name} onChange={(event) => setSourceForm((current) => ({ ...current, table_name: event.target.value }))} /></label>
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

createRoot(document.getElementById("root")).render(<App />);
