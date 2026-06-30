import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bell,
  Database,
  Globe,
  Eye,
  FileUp,
  History,
  LogOut,
  Play,
  Plus,
  RefreshCcw,
  Settings,
  Shield,
  Trash2,
  Building2,
  Users,
} from "lucide-react";
import { API_URL } from "./constants";
import "./styles.css";

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
  rule_logic: "AND",
  rules: [{ column_name: "", condition: ">", threshold_value: "" }],
  template_type: "custom",
  message_template: "",
  message_variables: {},
  dynamic_email_column: "",
  dynamic_whatsapp_column: "",
  frequency: "15m",
  email_recipients: "financeiro@demo.com",
  whatsapp_recipients: "",
  channels: ["email"],
};

const alertPresets = {
  custom: {
    label: "Personalizado",
    name: "",
    rules: [{ column_name: "", condition: ">", threshold_value: "" }],
    message_template: "",
    message_variables: {},
    dynamic_email_column: "",
    dynamic_whatsapp_column: "",
  },
  birthdays: {
    label: "Aniversariantes",
    name: "Aniversariantes do dia",
    rules: [{ column_name: "data_nascimento", condition: "birthday_today", threshold_value: "hoje" }],
    message_template:
      "Ola {{nome}}, feliz aniversario! A equipe da {{empresa}} deseja um dia especial para voce.",
    message_variables: {
      nome: "nome",
      empresa: "empresa",
      data_nascimento: "data_nascimento",
    },
    dynamic_email_column: "email",
    dynamic_whatsapp_column: "whatsapp",
  },
  overdue: {
    label: "Titulo vencido",
    name: "Titulos vencidos",
    rules: [{ column_name: "dias_atraso", condition: ">", threshold_value: "0" }],
    message_template:
      "Cliente {{cliente}} possui titulo {{documento}} vencido ha {{dias_atraso}} dia(s). Valor: {{valor}}.",
    message_variables: {
      cliente: "cliente",
      documento: "documento",
      dias_atraso: "dias_atraso",
      valor: "valor",
    },
    dynamic_email_column: "email",
    dynamic_whatsapp_column: "whatsapp",
  },
};

const emptyUserForm = {
  tenant_id: "",
  name: "",
  email: "",
  password: "",
  role: "user",
};

const emptySignupForm = {
  company_name: "",
  document: "",
  plan: "free",
  max_sources: 3,
  max_alerts: 5,
  admin_name: "",
  admin_email: "",
  admin_password: "",
};

export default function SentinelaApp() {
  const ackToken = getAckTokenFromPath();
  const [token, setToken] = useState(() => localStorage.getItem("sentinela_token") || "");
  const [email, setEmail] = useState("superadmin@sentinela.com.br");
  const [password, setPassword] = useState("superadmin123");
  const [signupForm, setSignupForm] = useState(emptySignupForm);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [summary, setSummary] = useState(null);
  const [sources, setSources] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [occurrences, setOccurrences] = useState([]);
  const [acknowledgements, setAcknowledgements] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [agents, setAgents] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [selectedTenantId, setSelectedTenantId] = useState("");
  const [currentUser, setCurrentUser] = useState(null);
  const [preview, setPreview] = useState(null);
  const [alertSimulation, setAlertSimulation] = useState(null);
  const [sourceAttributes, setSourceAttributes] = useState([]);
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [sourceForm, setSourceForm] = useState(emptySourceForm);
  const [managedSourceName, setManagedSourceName] = useState("Fonte gerenciada pelo collector");
  const [agentName, setAgentName] = useState("Collector local");
  const [createdAgentToken, setCreatedAgentToken] = useState("");
  const [collectorConfig, setCollectorConfig] = useState("");
  const [uploadForm, setUploadForm] = useState({ name: "Nova fonte CSV", source_type: "csv", file: null });
  const [alertForm, setAlertForm] = useState(emptyAlertForm);
  const [userForm, setUserForm] = useState(emptyUserForm);
  const [appSettings, setAppSettings] = useState({ alert_copy_email: "", alert_copy_whatsapp: "" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const activeSources = useMemo(() => sources.filter((source) => source.is_active), [sources]);
  const activeAlerts = useMemo(() => alerts.filter((alert) => alert.is_active), [alerts]);
  const isPlatformAdmin = currentUser?.role === "super_admin";
  const isTenantAdmin = currentUser?.role === "admin";
  const canManageTenant = isTenantAdmin;

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

  if (ackToken) {
    return <AcknowledgementPage ackToken={ackToken} />;
  }

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

  async function signupCompany(event) {
    event.preventDefault();
    await runAction(async () => {
      await api(
        "/tenants/signup",
        {
          method: "POST",
          body: JSON.stringify({
            ...signupForm,
            document: signupForm.document || null,
          }),
        },
      );
      setSignupForm(emptySignupForm);
      setMessage("Empresa e admin criados.");
      await loadWorkspace();
    });
  }

  async function loadWorkspace(authToken = token, tenantOverride = selectedTenantId) {
    const me = await api("/users/me", {}, authToken);
    let userList = [];
    let agentList = [];
    let tenantList = [];
    let sourceList = [];
    let alertList = [];
    let executionList = [];
    let occurrenceList = [];
    let acknowledgementList = [];
    let auditLogList = [];
    let dashboard = { sent_alerts: 0, active_alerts: 0, inactive_alerts: 0, executions_by_status: {} };
    let targetTenantId = tenantOverride;
    const isSuper = me.role === "super_admin";
    if (isSuper) {
      tenantList = await api("/tenants", {}, authToken);
      targetTenantId = targetTenantId || String(tenantList.find((tenant) => tenant.document !== "SENTINELA")?.id || tenantList[0]?.id || "");
      setSelectedTenantId(targetTenantId);
    }
    const tenantQuery = isSuper && targetTenantId ? `?tenant_id=${targetTenantId}` : "";
    if (me.role !== "user" && (!isSuper || targetTenantId)) {
      sourceList = await api(`/data-sources${tenantQuery}`, {}, authToken);
    }
    if (!isSuper || targetTenantId) {
      [dashboard, alertList, executionList] = await Promise.all([
        api(`/dashboard/summary${tenantQuery}`, {}, authToken),
        me.role !== "user" ? api(`/alerts${tenantQuery}`, {}, authToken) : Promise.resolve([]),
        api(`/alerts/executions${tenantQuery}`, {}, authToken),
      ]);
      [occurrenceList, acknowledgementList] = await Promise.all([
        api(`/alerts/occurrences${tenantQuery}`, {}, authToken),
        api(`/alerts/acknowledgements${tenantQuery}`, {}, authToken),
      ]);
      if (me.role !== "user") {
        auditLogList = await api(`/alerts/audit-logs${tenantQuery}`, {}, authToken);
      }
    }
    if (me.role === "admin") {
      userList = await api("/users", {}, authToken);
    }
    if (isSuper && targetTenantId) {
      userList = await api(`/users?tenant_id=${targetTenantId}`, {}, authToken);
    }
    if (isSuper && targetTenantId) {
      agentList = await api(`/ingestion/agents?tenant_id=${targetTenantId}`, {}, authToken);
    }
    if (isSuper) {
      setAppSettings(await api("/settings/alert-copy", {}, authToken));
    }
    setCurrentUser(me);
    setSummary(dashboard);
    setSources(sourceList);
    setAlerts(alertList);
    setExecutions(executionList);
    setOccurrences(occurrenceList);
    setAcknowledgements(acknowledgementList);
    setAuditLogs(auditLogList);
    setUsers(userList);
    setAgents(agentList);
    setTenants(tenantList);
    if (me.role !== "super_admin" && activeTab === "sources") {
      setActiveTab("dashboard");
    }
    if (me.role !== "admin" && me.role !== "super_admin" && activeTab === "users") {
      setActiveTab("dashboard");
    }
    if (me.role !== "super_admin" && activeTab === "companies") {
      setActiveTab("dashboard");
    }
    if (me.role !== "super_admin" && activeTab === "settings") {
      setActiveTab("dashboard");
    }
    if (me.role === "user" && activeTab !== "dashboard" && activeTab !== "history") {
      setActiveTab("history");
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
          tenant_id: Number(selectedTenantId),
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
        body: JSON.stringify({ tenant_id: Number(selectedTenantId), name: managedSourceName, config: {} }),
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
        body: JSON.stringify({ tenant_id: Number(selectedTenantId), name: agentName }),
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
      const targetTenantId = isPlatformAdmin ? (userForm.tenant_id || selectedTenantId) : "";
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${targetTenantId}` : "";
      await api(`/users${tenantQuery}`, {
        method: "POST",
        body: JSON.stringify({
          ...userForm,
          tenant_id: isPlatformAdmin ? Number(targetTenantId) : null,
        }),
      });
      setUserForm({ ...emptyUserForm, tenant_id: targetTenantId });
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
      const query = new URLSearchParams({ tenant_id: selectedTenantId, name: uploadForm.name, source_type: uploadForm.source_type });
      await api(`/data-sources/upload?${query.toString()}`, { method: "POST", body: formData });
      setUploadForm({ name: "Nova fonte CSV", source_type: "csv", file: null });
      setMessage("Arquivo enviado e fonte criada.");
      await loadWorkspace();
      setActiveTab("sources");
    });
  }

  async function showPreview(sourceId) {
    await runAction(async () => {
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${selectedTenantId}` : "";
      const data = await api(`/data-sources/${sourceId}/preview${tenantQuery}`);
      const attributes = await api(`/data-sources/${sourceId}/attributes${tenantQuery}`);
      setSelectedSourceId(String(sourceId));
      setPreview(data);
      setSourceAttributes(attributes);
      setMessage(`Preview carregado: ${data.columns.length} coluna(s).`);
    });
  }

  async function createAlert(event) {
    event.preventDefault();
    await runAction(async () => {
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${selectedTenantId}` : "";
      const rules = alertForm.rules
        .map((rule) => ({
          column_name: rule.column_name.trim(),
          condition: rule.condition,
          threshold_value: String(rule.threshold_value).trim(),
        }))
        .filter((rule) => rule.column_name && (rule.threshold_value || rule.condition === "birthday_today"));
      if (rules.length === 0) {
        throw new Error("Informe ao menos uma condicao para o alerta.");
      }
      const emailRecipients = splitList(alertForm.email_recipients);
      const whatsappRecipients = splitList(alertForm.whatsapp_recipients);
      if (whatsappRecipients.length > 3) {
        throw new Error("Cada alerta pode ter no maximo 3 numeros de WhatsApp.");
      }
      const primaryRule = rules[0];
      await api(`/alerts${tenantQuery}`, {
        method: "POST",
        body: JSON.stringify({
          ...alertForm,
          data_source_id: Number(alertForm.data_source_id),
          column_name: primaryRule.column_name,
          condition: primaryRule.condition,
          threshold_value: primaryRule.threshold_value,
          rule_logic: alertForm.rule_logic,
          rules,
          template_type: alertForm.template_type,
          message_template: alertForm.message_template || null,
          message_variables: alertForm.message_variables,
          dynamic_email_column: alertForm.dynamic_email_column || null,
          dynamic_whatsapp_column: alertForm.dynamic_whatsapp_column || null,
          recipients: [...emailRecipients, ...whatsappRecipients],
        }),
      });
      setAlertForm({ ...emptyAlertForm, data_source_id: alertForm.data_source_id });
      setMessage("Alerta criado.");
      await loadWorkspace();
      setActiveTab("alerts");
    });
  }

  async function simulateAlert() {
    await runAction(async () => {
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${selectedTenantId}` : "";
      const rules = alertForm.rules
        .map((rule) => ({
          column_name: rule.column_name.trim(),
          condition: rule.condition,
          threshold_value: String(rule.threshold_value).trim(),
        }))
        .filter((rule) => rule.column_name && (rule.threshold_value || rule.condition === "birthday_today"));
      if (!alertForm.data_source_id || rules.length === 0) {
        throw new Error("Selecione uma fonte e informe ao menos uma condicao para simular.");
      }
      const primaryRule = rules[0];
      const simulation = await api(`/alerts/simulate${tenantQuery}`, {
        method: "POST",
        body: JSON.stringify({
          ...alertForm,
          data_source_id: Number(alertForm.data_source_id),
          column_name: primaryRule.column_name,
          condition: primaryRule.condition,
          threshold_value: primaryRule.threshold_value,
          rule_logic: alertForm.rule_logic,
          rules,
          message_template: alertForm.message_template || null,
          dynamic_email_column: alertForm.dynamic_email_column || null,
          dynamic_whatsapp_column: alertForm.dynamic_whatsapp_column || null,
          recipients: [...splitList(alertForm.email_recipients), ...splitList(alertForm.whatsapp_recipients)],
        }),
      });
      setAlertSimulation(simulation);
      setMessage(`Simulacao concluida: ${simulation.matched_count} registro(s) seriam encontrados.`);
    });
  }

  async function updateOccurrence(occurrenceId, changes) {
    await runAction(async () => {
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${selectedTenantId}` : "";
      await api(`/alerts/occurrences/${occurrenceId}${tenantQuery}`, {
        method: "PATCH",
        body: JSON.stringify(changes),
      });
      setMessage("Ocorrencia atualizada.");
      await loadWorkspace();
      setActiveTab("history");
    });
  }

  async function runAlert(id) {
    await runAction(async () => {
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${selectedTenantId}` : "";
      const result = await api(`/alerts/${id}/run${tenantQuery}`, { method: "POST" });
      setMessage(`Alerta executado: ${result.status} (${result.matched_count} ${pluralize(result.matched_count, "registro encontrado", "registros encontrados")}).`);
      await loadWorkspace();
      setActiveTab("history");
    });
  }

  async function deactivateAlert(id) {
    await runAction(async () => {
      const tenantQuery = isPlatformAdmin ? `?tenant_id=${selectedTenantId}` : "";
      await api(`/alerts/${id}${tenantQuery}`, { method: "DELETE" });
      setMessage("Alerta desativado.");
      await loadWorkspace();
    });
  }

  async function saveAppSettings(event) {
    event.preventDefault();
    await runAction(async () => {
      const updated = await api("/settings/alert-copy", {
        method: "PUT",
        body: JSON.stringify(appSettings),
      });
      setAppSettings(updated);
      setMessage("Configuracoes de copia operacional salvas.");
    });
  }

  async function deactivateSource(id) {
    await runAction(async () => {
      await api(`/data-sources/${id}?tenant_id=${selectedTenantId}`, { method: "DELETE" });
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
    setOccurrences([]);
    setAcknowledgements([]);
    setAuditLogs([]);
    setUsers([]);
    setAgents([]);
    setTenants([]);
    setSelectedTenantId("");
    setCurrentUser(null);
    setPreview(null);
    setSourceAttributes([]);
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
          {isPlatformAdmin && <NavItem active={activeTab === "companies"} icon={<Building2 size={18} />} label="Empresas" onClick={() => setActiveTab("companies")} />}
          {isPlatformAdmin && <NavItem active={activeTab === "sources"} icon={<Database size={18} />} label="Fontes" onClick={() => setActiveTab("sources")} />}
          {(isPlatformAdmin || canManageTenant) && <NavItem active={activeTab === "alerts"} icon={<Bell size={18} />} label="Alertas" onClick={() => setActiveTab("alerts")} />}
          <NavItem active={activeTab === "history"} icon={<History size={18} />} label="Relatorios" onClick={() => setActiveTab("history")} />
          {(isPlatformAdmin || canManageTenant) && <NavItem active={activeTab === "users"} icon={<Users size={18} />} label="Usuarios" onClick={() => setActiveTab("users")} />}
          {isPlatformAdmin && <NavItem active={activeTab === "settings"} icon={<Settings size={18} />} label="Configurações" onClick={() => setActiveTab("settings")} />}
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
          <AuthPanel
            email={email}
            loading={loading}
            login={login}
            password={password}
            setEmail={setEmail}
            setPassword={setPassword}
          />
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
                <h2>{isPlatformAdmin ? "Admin geral" : canManageTenant ? "Admin da empresa" : "Acesso usuario"}</h2>
                <p>{isPlatformAdmin ? "Cadastre empresas, limites comerciais, fontes de dados e agents de integracao." : canManageTenant ? "Parametrize alertas, acompanhe relatorios e gerencie usuarios da sua empresa." : "Acompanhe relatorios da sua empresa."}</p>
                {isPlatformAdmin && (
                  <a className="landing-admin-link" href="/landing-admin">
                    <Globe size={16} /> Editar landing IMPACTO
                  </a>
                )}
              </div>
            </section>
          </>
        )}

        {token && isPlatformAdmin && activeTab === "companies" && (
          <CompaniesView
            loading={loading}
            setSignupForm={setSignupForm}
            signupCompany={signupCompany}
            signupForm={signupForm}
            tenants={tenants.filter((tenant) => tenant.document !== "SENTINELA")}
          />
        )}

        {token && isPlatformAdmin && activeTab === "sources" && (
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
            selectedTenantId={selectedTenantId}
            setSelectedTenantId={(tenantId) => {
              setSelectedTenantId(tenantId);
              runAction(() => loadWorkspace(token, tenantId), { quiet: true });
            }}
            tenants={tenants.filter((tenant) => tenant.document !== "SENTINELA")}
          />
        )}

        {token && (isPlatformAdmin || canManageTenant) && activeTab === "alerts" && (
          <AlertsView
            activeAlerts={activeAlerts}
            activeSources={activeSources}
            alertForm={alertForm}
            alertSimulation={alertSimulation}
            createAlert={createAlert}
            deactivateAlert={deactivateAlert}
            loading={loading}
            preview={preview}
            runAlert={runAlert}
            setAlertForm={setAlertForm}
            showPreview={showPreview}
            simulateAlert={simulateAlert}
            sourceAttributes={sourceAttributes}
          />
        )}

        {token && isPlatformAdmin && activeTab === "settings" && (
          <SettingsView
            appSettings={appSettings}
            loading={loading}
            saveAppSettings={saveAppSettings}
            setAppSettings={setAppSettings}
          />
        )}

        {token && activeTab === "history" && (
          <HistoryView
            acknowledgements={acknowledgements}
            auditLogs={auditLogs}
            executions={executions}
            occurrences={occurrences}
            updateOccurrence={updateOccurrence}
          />
        )}
        {token && (isPlatformAdmin || canManageTenant) && activeTab === "users" && (
          <UsersView
            createUser={createUser}
            isPlatformAdmin={isPlatformAdmin}
            loading={loading}
            selectedTenantId={selectedTenantId}
            setSelectedTenantId={(tenantId) => {
              setSelectedTenantId(tenantId);
              setUserForm((current) => ({ ...current, tenant_id: tenantId }));
              runAction(() => loadWorkspace(token, tenantId), { quiet: true });
            }}
            setUserForm={setUserForm}
            tenants={tenants.filter((tenant) => tenant.document !== "SENTINELA")}
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
  selectedTenantId,
  setSourceForm,
  setSelectedTenantId,
  setUploadForm,
  showPreview,
  sourceForm,
  tenants,
  uploadForm,
  uploadSource,
}) {
  const dbExample = databaseExamples[sourceForm.source_type] || databaseExamples.postgresql;

  return (
    <>
      <section className="panel form-grid">
        <div className="panel-title with-action">
          <h2>Empresa alvo da integracao</h2>
          <Building2 size={18} />
        </div>
        <label>Empresa cliente
          <select value={selectedTenantId} onChange={(event) => setSelectedTenantId(event.target.value)}>
            <option value="">Selecione</option>
            {tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.name}</option>)}
          </select>
        </label>
      </section>

      <section className="grid-2">
        <form className="panel form-grid" onSubmit={createManagedSource}>
          <div className="panel-title with-action">
            <h2>Fonte gerenciada</h2>
            <Shield size={18} />
          </div>
          <label>Nome<input value={managedSourceName} onChange={(event) => setManagedSourceName(event.target.value)} /></label>
          <button disabled={loading || !selectedTenantId || !managedSourceName}><Plus size={16} /> Criar fonte gerenciada</button>
        </form>

        <form className="panel form-grid" onSubmit={createAgent}>
          <div className="panel-title with-action">
            <h2>Collector agent</h2>
            <Shield size={18} />
          </div>
          <label>Nome<input value={agentName} onChange={(event) => setAgentName(event.target.value)} /></label>
          <button disabled={loading || !selectedTenantId || !agentName}><Plus size={16} /> Criar agent</button>
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
          <button disabled={loading || !selectedTenantId || !uploadForm.name}><Plus size={16} /> Criar fonte</button>
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
          <button disabled={loading || !selectedTenantId || !sourceForm.name || !sourceForm.connection_uri || !sourceForm.table_name}><Plus size={16} /> Criar conexao</button>
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

function AuthPanel({
  email,
  loading,
  login,
  password,
  setEmail,
  setPassword,
}) {
  return (
    <section className="panel auth-panel">
      <div className="panel-title">
        <h2>Entrar no Sentinela</h2>
      </div>
      <form className="login" onSubmit={login}>
        <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Senha<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        <button type="submit" disabled={loading}>Entrar</button>
      </form>
    </section>
  );
}

function CompaniesView({ loading, setSignupForm, signupCompany, signupForm, tenants }) {
  return (
    <>
      <section className="panel form-grid">
        <div className="panel-title with-action">
          <h2>Nova empresa cliente</h2>
          <Building2 size={18} />
        </div>
        <form className="signup-form" onSubmit={signupCompany}>
          <label>Empresa<input value={signupForm.company_name} onChange={(event) => setSignupForm((current) => ({ ...current, company_name: event.target.value }))} /></label>
          <label>Documento<input value={signupForm.document} onChange={(event) => setSignupForm((current) => ({ ...current, document: event.target.value }))} placeholder="CNPJ opcional" /></label>
          <label>Plano
            <select value={signupForm.plan} onChange={(event) => setSignupForm((current) => ({ ...current, plan: event.target.value }))}>
              <option value="free">free</option>
              <option value="starter">starter</option>
              <option value="business">business</option>
              <option value="enterprise">enterprise</option>
            </select>
          </label>
          <label>Limite de fontes<input type="number" min="1" value={signupForm.max_sources} onChange={(event) => setSignupForm((current) => ({ ...current, max_sources: Number(event.target.value) }))} /></label>
          <label>Limite de alertas<input type="number" min="1" value={signupForm.max_alerts} onChange={(event) => setSignupForm((current) => ({ ...current, max_alerts: Number(event.target.value) }))} /></label>
          <label>Nome do admin<input value={signupForm.admin_name} onChange={(event) => setSignupForm((current) => ({ ...current, admin_name: event.target.value }))} /></label>
          <label>Email do admin<input value={signupForm.admin_email} onChange={(event) => setSignupForm((current) => ({ ...current, admin_email: event.target.value }))} /></label>
          <label>Senha do admin<input type="password" value={signupForm.admin_password} onChange={(event) => setSignupForm((current) => ({ ...current, admin_password: event.target.value }))} /></label>
          <button
            type="submit"
            disabled={loading || !signupForm.company_name || !signupForm.admin_name || !signupForm.admin_email || signupForm.admin_password.length < 8 || signupForm.max_sources < 1 || signupForm.max_alerts < 1}
          >
            <Plus size={16} /> Criar empresa e admin
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>Empresas cadastradas</h2></div>
        <div className="table">
          <div className="row companies-head"><span>Empresa</span><span>Plano</span><span>Fontes</span><span>Alertas</span><span>Status</span></div>
          {tenants.map((tenant) => (
            <div className="row companies-row" key={tenant.id}>
              <span>{tenant.name}</span>
              <span>{tenant.plan || "starter"}</span>
              <span>{tenant.max_sources}</span>
              <span>{tenant.max_alerts}</span>
              <span>{tenant.is_active ? "ativa" : "inativa"}</span>
            </div>
          ))}
          {tenants.length === 0 && <div className="empty">Nenhuma empresa cadastrada.</div>}
        </div>
      </section>
    </>
  );
}

function SettingsView({ appSettings, loading, saveAppSettings, setAppSettings }) {
  return (
    <section className="panel form-grid">
      <div className="panel-title with-action">
        <div>
          <h2>Copia operacional de alertas</h2>
          <p>Esses contatos recebem uma copia de todos os alertas disparados para validar a operacao.</p>
        </div>
        <Settings size={18} />
      </div>
      <form className="settings-form" onSubmit={saveAppSettings}>
        <label>E-mail de copia
          <input
            value={appSettings.alert_copy_email || ""}
            onChange={(event) => setAppSettings((current) => ({ ...current, alert_copy_email: event.target.value }))}
            placeholder="operacao@impactocg.com"
          />
        </label>
        <label>WhatsApp de copia
          <input
            value={appSettings.alert_copy_whatsapp || ""}
            onChange={(event) => setAppSettings((current) => ({ ...current, alert_copy_whatsapp: event.target.value }))}
            placeholder="+553191275790"
          />
        </label>
        <button type="submit" disabled={loading}>
          <Settings size={16} /> Salvar configuracoes
        </button>
      </form>
    </section>
  );
}

function AlertsView({ activeAlerts, activeSources, alertForm, alertSimulation, createAlert, deactivateAlert, loading, preview, runAlert, setAlertForm, showPreview, simulateAlert, sourceAttributes }) {
  const previewColumns = sourceAttributes.length > 0 ? sourceAttributes.map((attribute) => attribute.name) : (preview?.columns || []);
  const templateVariables = extractTemplateVariables(alertForm.message_template);

  return (
    <>
      <section className="panel form-grid">
        <div className="panel-title with-action">
          <h2>Novo alerta</h2>
          <Bell size={18} />
        </div>
        <form className="alert-form" onSubmit={createAlert}>
          <label>Nome<input value={alertForm.name} onChange={(event) => setAlertForm((current) => ({ ...current, name: event.target.value }))} placeholder="Pedidos acima de 1000" /></label>
          <label>Modelo
            <select value={alertForm.template_type} onChange={(event) => applyAlertPreset(event.target.value, setAlertForm)}>
              {Object.entries(alertPresets).map(([value, preset]) => <option key={value} value={value}>{preset.label}</option>)}
            </select>
          </label>
          <label>Fonte
            <select
              value={alertForm.data_source_id}
              onChange={(event) => {
                setAlertForm((current) => ({ ...current, data_source_id: event.target.value }));
                if (event.target.value) {
                  showPreview(event.target.value);
                }
              }}
            >
              <option value="">Selecione</option>
              {activeSources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}
            </select>
          </label>
          <div className="rule-builder">
            <div className="rule-builder-header">
              <div>
                <strong>Condicoes do alerta</strong>
                <span>Combine campos da fonte para decidir quando disparar.</span>
              </div>
              <label>Operador
                <select value={alertForm.rule_logic} onChange={(event) => setAlertForm((current) => ({ ...current, rule_logic: event.target.value }))}>
                  <option value="AND">AND - todas</option>
                  <option value="OR">OR - qualquer uma</option>
                </select>
              </label>
            </div>
            <datalist id="columns">
              {previewColumns.map((column) => <option key={column} value={column} />)}
            </datalist>
            {alertForm.rules.map((rule, index) => (
              <div className="rule-row" key={index}>
                <span className="rule-index">{index === 0 ? "SE" : alertForm.rule_logic}</span>
                <label>Coluna
                  <input list="columns" value={rule.column_name} onChange={(event) => updateAlertRule(setAlertForm, index, "column_name", event.target.value)} placeholder="valor_total" />
                </label>
                <label>Condicao
                  <select value={rule.condition} onChange={(event) => updateAlertRule(setAlertForm, index, "condition", event.target.value)}>
                    <option value=">">&gt;</option>
                    <option value="<">&lt;</option>
                    <option value="=">=</option>
                    <option value=">=">&gt;=</option>
                    <option value="<=">&lt;=</option>
                    <option value="!=">!=</option>
                    <option value="birthday_today">aniversario hoje</option>
                  </select>
                </label>
                <label>Valor
                  <input
                    disabled={rule.condition === "birthday_today"}
                    value={rule.threshold_value}
                    onChange={(event) => updateAlertRule(setAlertForm, index, "threshold_value", event.target.value)}
                    placeholder={rule.condition === "birthday_today" ? "hoje" : index === 0 ? "1000" : "3"}
                  />
                </label>
                <button className="icon-button secondary" type="button" onClick={() => removeAlertRule(setAlertForm, index)} disabled={alertForm.rules.length === 1} title="Remover condicao">
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            <button className="secondary add-rule-button" type="button" onClick={() => addAlertRule(setAlertForm)}>
            <Plus size={16} /> Adicionar condicao
            </button>
          </div>
          <div className="message-builder">
            <div className="rule-builder-header">
              <div>
                <strong>Mensagem enviada ao cliente</strong>
                <span>Use variaveis entre chaves, por exemplo: {"{{nome}}"} e {"{{valor}}"}.</span>
              </div>
            </div>
            <label>Texto da mensagem
              <textarea
                rows={5}
                value={alertForm.message_template}
                onChange={(event) => setAlertForm((current) => ({ ...current, message_template: event.target.value }))}
                placeholder="Ex.: Ola {{nome}}, identificamos o valor {{valor}} no pedido {{pedido}}."
              />
            </label>
            {templateVariables.length > 0 && (
              <div className="variable-map">
                <strong>Preenchimento das variaveis</strong>
                {templateVariables.map((variable) => (
                  <label key={variable}>{`{{${variable}}}`}
                    <input
                      list="columns"
                      value={alertForm.message_variables?.[variable] || ""}
                      onChange={(event) => updateMessageVariable(setAlertForm, variable, event.target.value)}
                      placeholder={`Coluna para ${variable}`}
                    />
                  </label>
                ))}
              </div>
            )}
            <div className="dynamic-recipient-map">
              <strong>Destinatario dinamico por linha</strong>
              <label>Coluna de e-mail
                <input
                  list="columns"
                  value={alertForm.dynamic_email_column || ""}
                  onChange={(event) => setAlertForm((current) => ({ ...current, dynamic_email_column: event.target.value }))}
                  placeholder="email"
                />
              </label>
              <label>Coluna de WhatsApp
                <input
                  list="columns"
                  value={alertForm.dynamic_whatsapp_column || ""}
                  onChange={(event) => setAlertForm((current) => ({ ...current, dynamic_whatsapp_column: event.target.value }))}
                  placeholder="whatsapp"
                />
              </label>
              <small>Quando preenchido, cada registro encontrado recebe sua propria mensagem pelo contato da linha.</small>
            </div>
          </div>
          <label>Frequencia<input value={alertForm.frequency} onChange={(event) => setAlertForm((current) => ({ ...current, frequency: event.target.value }))} placeholder="15m ou */15 * * * *" /></label>
          <label>E-mails do cliente<input value={alertForm.email_recipients} onChange={(event) => setAlertForm((current) => ({ ...current, email_recipients: event.target.value }))} placeholder="financeiro@empresa.com, gestor@empresa.com" /></label>
          <label>WhatsApps do cliente
            <input value={alertForm.whatsapp_recipients} onChange={(event) => setAlertForm((current) => ({ ...current, whatsapp_recipients: event.target.value }))} placeholder="+5531999999999, +5531888888888" />
            <small>{splitList(alertForm.whatsapp_recipients).length}/3 numeros</small>
          </label>
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
          <button className="secondary" disabled={loading} type="button" onClick={simulateAlert}>
            <Eye size={16} /> Simular
          </button>
        </form>
      </section>

      {alertSimulation && (
        <section className="panel simulation-panel">
          <div className="panel-title"><h2>Resultado da simulacao</h2></div>
          <p><strong>{alertSimulation.matched_count}</strong> registro(s) encontrados com a regra atual.</p>
          {alertSimulation.dynamic_recipients?.length > 0 && (
            <div className="simulation-block">
              <strong>Destinatarios detectados</strong>
              {alertSimulation.dynamic_recipients.map((recipient, index) => (
                <span key={index}>Email: {recipient.email || "-"} | WhatsApp: {recipient.whatsapp || "-"}</span>
              ))}
            </div>
          )}
          {alertSimulation.sample_messages?.length > 0 && (
            <div className="simulation-block">
              <strong>Mensagem de exemplo</strong>
              {alertSimulation.sample_messages.map((sample, index) => (
                <pre key={index}>{sample}</pre>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="panel">
        <div className="panel-title"><h2>Alertas ativos</h2></div>
        <div className="table">
          <div className="row alert-list-head"><span>Nome</span><span>Regra</span><span>Canais</span><span>Acoes</span></div>
          {activeAlerts.map((alert) => (
            <div className="row alert-list-row" key={alert.id}>
              <span>{alert.name}</span>
              <span>{formatAlertRules(alert)}</span>
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

function HistoryView({ acknowledgements, auditLogs, executions, occurrences, updateOccurrence }) {
  return (
    <>
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

      <section className="panel">
        <div className="panel-title"><h2>Ocorrencias de alertas</h2></div>
        <div className="table">
          <div className="row occurrences-head"><span>Alerta</span><span>Status</span><span>Responsavel</span><span>Nota</span><span>Acoes</span></div>
          {occurrences.map((occurrence) => (
            <div className="row occurrences-row" key={occurrence.id}>
              <span>{occurrence.alert_name}</span>
              <span>
                <StatusBadge status={occurrence.status} />
                <small>{occurrence.matched_count} registro(s), visto em {new Date(occurrence.last_seen_at).toLocaleString("pt-BR")}</small>
              </span>
              <input
                defaultValue={occurrence.assigned_to || ""}
                onBlur={(event) => updateOccurrence(occurrence.id, { assigned_to: event.target.value })}
                placeholder="Responsavel"
              />
              <input
                defaultValue={occurrence.resolution_note || ""}
                onBlur={(event) => updateOccurrence(occurrence.id, { resolution_note: event.target.value })}
                placeholder="Comentario"
              />
              <div className="row-actions">
                <button className="secondary" onClick={() => updateOccurrence(occurrence.id, { status: "in_progress" })}>Em analise</button>
                <button onClick={() => updateOccurrence(occurrence.id, { status: "resolved" })}>Resolver</button>
                <button className="secondary" onClick={() => updateOccurrence(occurrence.id, { status: "ignored" })}>Ignorar</button>
              </div>
            </div>
          ))}
          {occurrences.length === 0 && <div className="empty">Nenhuma ocorrencia registrada.</div>}
        </div>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>Confirmacoes de leitura</h2></div>
        <div className="table">
          <div className="row acknowledgements-head"><span>Alerta</span><span>Nome</span><span>Email</span><span>Data</span><span>Observacao</span></div>
          {acknowledgements.map((ack) => (
            <div className="row acknowledgements-row" key={ack.id}>
              <span>{ack.alert_name}</span>
              <span>{ack.acknowledged_by_name || "-"}</span>
              <span>{ack.acknowledged_by_email || "-"}</span>
              <span>{new Date(ack.acknowledged_at).toLocaleString("pt-BR")}</span>
              <span>{ack.note || "-"}</span>
            </div>
          ))}
          {acknowledgements.length === 0 && <div className="empty">Nenhuma leitura confirmada.</div>}
        </div>
      </section>

      {auditLogs.length > 0 && (
        <section className="panel">
          <div className="panel-title"><h2>Auditoria de alertas</h2></div>
          <div className="table">
            <div className="row audit-head"><span>Alerta</span><span>Acao</span><span>Usuario</span><span>Data</span></div>
            {auditLogs.map((log) => (
              <div className="row audit-row" key={log.id}>
                <span>{log.alert_name}</span>
                <span>{log.action}</span>
                <span>{log.user_id || "-"}</span>
                <span>{new Date(log.created_at).toLocaleString("pt-BR")}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function AcknowledgementPage({ ackToken }) {
  const [occurrence, setOccurrence] = useState(null);
  const [form, setForm] = useState({ acknowledged_by_name: "", acknowledged_by_email: "", note: "" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/alerts/ack/${ackToken}`)
      .then((response) => response.ok ? response.json() : Promise.reject(response))
      .then(setOccurrence)
      .catch(() => setMessage("Confirmacao nao encontrada."));
  }, [ackToken]);

  async function confirm(event) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/alerts/ack/${ackToken}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          acknowledged_by_name: form.acknowledged_by_name || null,
          acknowledged_by_email: form.acknowledged_by_email || null,
          note: form.note || null,
        }),
      });
      if (!response.ok) {
        throw new Error("Nao foi possivel confirmar a leitura.");
      }
      setMessage("Leitura confirmada. O mesmo alerta nao sera reenviado enquanto a ocorrencia nao mudar.");
      setOccurrence((current) => current ? { ...current, status: "acknowledged" } : current);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="ack-shell">
      <section className="panel auth-panel">
        <div className="panel-title"><h2>Confirmar leitura do alerta</h2></div>
        {occurrence && (
          <div className="ack-summary">
            <p><strong>{occurrence.alert_name}</strong></p>
            <p>Fonte: {occurrence.source_name}</p>
            <p>Status: {occurrence.status}</p>
            <p>Registros encontrados: {occurrence.matched_count}</p>
          </div>
        )}
        {message && <div className={message.startsWith("Confirmacao") || message.startsWith("Nao") ? "notice error" : "notice"}>{message}</div>}
        {occurrence && occurrence.status !== "acknowledged" && (
          <form className="login" onSubmit={confirm}>
            <label>Nome<input value={form.acknowledged_by_name} onChange={(event) => setForm((current) => ({ ...current, acknowledged_by_name: event.target.value }))} /></label>
            <label>Email<input value={form.acknowledged_by_email} onChange={(event) => setForm((current) => ({ ...current, acknowledged_by_email: event.target.value }))} /></label>
            <label>Observacao<input value={form.note} onChange={(event) => setForm((current) => ({ ...current, note: event.target.value }))} /></label>
            <button disabled={loading} type="submit">Confirmar leitura</button>
          </form>
        )}
      </section>
    </main>
  );
}

function UsersView({ createUser, isPlatformAdmin, loading, selectedTenantId, setSelectedTenantId, setUserForm, tenants, userForm, users }) {
  const selectedUserTenantId = userForm.tenant_id || selectedTenantId;
  return (
    <>
      {isPlatformAdmin && (
        <section className="panel">
          <div className="panel-title with-action">
            <div>
              <h2>Empresa selecionada</h2>
              <p>Escolha a empresa cliente para listar e cadastrar usuarios.</p>
            </div>
            <Building2 size={18} />
          </div>
          <label>Empresa
            <select value={selectedTenantId} onChange={(event) => setSelectedTenantId(event.target.value)}>
              <option value="">Selecione</option>
              {tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.name}</option>)}
            </select>
          </label>
        </section>
      )}
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
          <button disabled={loading || (isPlatformAdmin && !selectedUserTenantId) || !userForm.name || !userForm.email || userForm.password.length < 8}>
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

function addAlertRule(setAlertForm) {
  setAlertForm((current) => ({
    ...current,
    rules: [...current.rules, { column_name: "", condition: ">", threshold_value: "" }],
  }));
}

function removeAlertRule(setAlertForm, index) {
  setAlertForm((current) => {
    if (current.rules.length === 1) {
      return current;
    }
    return { ...current, rules: current.rules.filter((_, ruleIndex) => ruleIndex !== index) };
  });
}

function updateAlertRule(setAlertForm, index, field, value) {
  setAlertForm((current) => ({
    ...current,
    rules: current.rules.map((rule, ruleIndex) => (
      ruleIndex === index ? normalizeRuleUpdate(rule, field, value) : rule
    )),
  }));
}

function normalizeRuleUpdate(rule, field, value) {
  const updated = { ...rule, [field]: value };
  if (field === "condition" && value === "birthday_today") {
    updated.threshold_value = "hoje";
  }
  return updated;
}

function applyAlertPreset(templateType, setAlertForm) {
  const preset = alertPresets[templateType] || alertPresets.custom;
  setAlertForm((current) => ({
    ...current,
    template_type: templateType,
    name: preset.name || current.name,
    rules: preset.rules.map((rule) => ({ ...rule })),
    message_template: preset.message_template,
    message_variables: { ...preset.message_variables },
    dynamic_email_column: preset.dynamic_email_column || current.dynamic_email_column,
    dynamic_whatsapp_column: preset.dynamic_whatsapp_column || current.dynamic_whatsapp_column,
    channels: templateType === "birthdays" ? ["whatsapp"] : current.channels,
  }));
}

function extractTemplateVariables(template) {
  const matches = [...String(template || "").matchAll(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g)];
  return [...new Set(matches.map((match) => match[1].trim()))];
}

function updateMessageVariable(setAlertForm, variable, columnName) {
  setAlertForm((current) => ({
    ...current,
    message_variables: {
      ...(current.message_variables || {}),
      [variable]: columnName,
    },
  }));
}

function formatAlertRules(alert) {
  const rules = alert.rules?.length
    ? alert.rules
    : [{ column_name: alert.column_name, condition: alert.condition, threshold_value: alert.threshold_value }];
  const logic = alert.rule_logic || "AND";
  return rules
    .map((rule, index) => `${index === 0 ? "" : `${logic} `}${rule.column_name} ${rule.condition} ${rule.threshold_value}`)
    .join(" ");
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

function getAckTokenFromPath() {
  const match = window.location.pathname.match(/^\/ack\/([^/]+)$/);
  return match ? decodeURIComponent(match[1]) : "";
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
