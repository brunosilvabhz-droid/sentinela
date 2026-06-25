import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, Bell, Database, Play, Shield, Users } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

function App() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("admin1234");
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [message, setMessage] = useState("");

  async function api(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: token ? `Bearer ${token}` : undefined,
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
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    setMessage("Login realizado");
  }

  async function loadDashboard() {
    const [dashboard, alertList] = await Promise.all([api("/dashboard/summary"), api("/alerts")]);
    setSummary(dashboard);
    setAlerts(alertList);
  }

  async function runAlert(id) {
    const result = await api(`/alerts/${id}/run`, { method: "POST" });
    setMessage(`Alerta executado: ${result.status} (${result.matched_count} registros)`);
    loadDashboard();
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
          <button onClick={loadDashboard} disabled={!token}>Atualizar</button>
        </header>

        {!token && (
          <form className="panel login" onSubmit={login}>
            <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
            <label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
            <button type="submit">Entrar</button>
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
                <button className="icon-button" onClick={() => runAlert(alert.id)} title="Executar agora">
                  <Play size={16} />
                </button>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

createRoot(document.getElementById("root")).render(<App />);
