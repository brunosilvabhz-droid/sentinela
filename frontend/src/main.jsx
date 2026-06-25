import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, Bell, Database, Play, RefreshCcw, Shield, Users } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("sentinela_token") || "");
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("admin1234");
  const [summary, setSummary] = useState(null);
  const [sources, setSources] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      loadDashboard(token);
    }
  }, []);

  async function api(path, options = {}, authToken = token) {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: authToken ? `Bearer ${authToken}` : undefined,
        ...(options.headers || {}),
      },
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  async function login(event) {
    event.preventDefault();
    await runAction(async () => {
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }, "");
      localStorage.setItem("sentinela_token", data.access_token);
      setToken(data.access_token);
      setMessage("Login realizado. Dados carregados.");
      await loadDashboard(data.access_token);
    });
  }

  async function loadDashboard(authToken = token) {
    const [dashboard, sourceList, alertList] = await Promise.all([
      api("/dashboard/summary", {}, authToken),
      api("/data-sources", {}, authToken),
      api("/alerts", {}, authToken),
    ]);
    setSummary(dashboard);
    setSources(sourceList);
    setAlerts(alertList);
    if (alertList[0]) {
      await loadExecutions(alertList[0].id, authToken);
    }
  }

  async function runAlert(id) {
    await runAction(async () => {
      const result = await api(`/alerts/${id}/run`, { method: "POST" });
      setMessage(`Alerta executado: ${result.status} (${result.matched_count} registros encontrados)`);
      await loadDashboard();
    });
  }

  async function loadExecutions(alertId, authToken = token) {
    const rows = await api(`/alerts/${alertId}/executions`, {}, authToken);
    setExecutions(rows);
  }

  async function runAction(action) {
    setLoading(true);
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
    setMessage("Sessao encerrada");
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Shield size={28} />
          <strong>SENTINELA</strong>
        </div>
        <nav>
          <span><Activity size={18} /> Dashboard</span>
          <span><Database size={18} /> Fontes</span>
          <span><Bell size={18} /> Alertas</span>
          <span><Users size={18} /> Usuarios</span>
        </nav>
      </aside>

      <section className="content">
        <header>
          <div>
            <h1>Monitoramento e alertas</h1>
            <p>Console multi-tenant para acompanhar regras, execucoes e canais.</p>
          </div>
          <div className="header-actions">
            <button onClick={() => runAction(() => loadDashboard())} disabled={!token || loading}>
              <RefreshCcw size={16} /> Atualizar
            </button>
            {token && <button className="secondary" onClick={logout}>Sair</button>}
          </div>
        </header>

        {!token && (
          <form className="panel login" onSubmit={login}>
            <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
            <label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
            <button type="submit" disabled={loading}>Entrar</button>
          </form>
        )}

        {message && <div className="notice">{message}</div>}

        {summary && (
          <div className="metrics">
            <Metric label="Alertas enviados" value={summary.sent_alerts} />
            <Metric label="Ativos" value={summary.active_alerts} />
            <Metric label="Inativos" value={summary.inactive_alerts} />
            <Metric label="Status" value={Object.keys(summary.executions_by_status).length} />
          </div>
        )}

        {token && (
          <section className="panel">
            <div className="panel-title">
              <h2>Fontes de dados</h2>
            </div>
            <div className="table compact">
              <div className="row source-head"><span>Nome</span><span>Tipo</span><span>Status</span></div>
              {sources.map((source) => (
                <div className="row source-row" key={source.id}>
                  <span>{source.name}</span>
                  <span>{source.source_type}</span>
                  <span>{source.is_active ? "ativa" : "inativa"}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="panel">
          <div className="panel-title">
            <h2>Alertas cadastrados</h2>
          </div>
          <div className="table">
            <div className="row head"><span>Nome</span><span>Regra</span><span>Canais</span><span></span></div>
            {alerts.map((alert) => (
              <div className="row" key={alert.id}>
                <span>{alert.name}</span>
                <span>{alert.column_name} {alert.condition} {alert.threshold_value}</span>
                <span>{alert.channels.join(", ")}</span>
                <button className="icon-button" onClick={() => runAlert(alert.id)} title="Executar agora" disabled={loading}>
                  <Play size={16} />
                </button>
              </div>
            ))}
            {token && alerts.length === 0 && <div className="empty">Nenhum alerta cadastrado.</div>}
          </div>
        </section>

        {token && (
          <section className="panel">
            <div className="panel-title">
              <h2>Ultimas execucoes</h2>
            </div>
            <div className="table compact">
              <div className="row log-head"><span>Status</span><span>Registros</span><span>Inicio</span><span>Erro</span></div>
              {executions.map((execution) => (
                <div className="row log-row" key={execution.id}>
                  <span>{execution.status}</span>
                  <span>{execution.matched_count}</span>
                  <span>{new Date(execution.started_at).toLocaleString("pt-BR")}</span>
                  <span>{execution.error_message || "-"}</span>
                </div>
              ))}
              {executions.length === 0 && <div className="empty">Execute um alerta para gerar historico.</div>}
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function Metric({ label, value }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

createRoot(document.getElementById("root")).render(<App />);
