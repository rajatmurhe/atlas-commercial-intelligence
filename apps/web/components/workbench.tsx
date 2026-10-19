"use client";
import { useEffect, useRef, useState, FormEvent } from "react";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Code2,
  Compass,
  Copy,
  Database,
  Download,
  FileText,
  LayoutDashboard,
  Loader2,
  MessageSquare,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  TrendingUp,
  X,
  Activity,
  CheckCircle2,
  AlertCircle,
  PanelLeftClose,
  Menu,
} from "lucide-react";
import { api, money, month } from "@/lib/api";
import type {
  Scope,
  Overview,
  Answer,
  Brief,
  Analysis,
  Row,
  Dataset,
} from "@/lib/types";
import { RevenueChart, GapChart, ForecastChart } from "./charts";
import {
  ReviewSummary,
  ReviewQueue,
  TherapeuticReview,
} from "./portfolio-review";

type Tab = "Overview" | "Investigate" | "Outlook" | "Briefs" | "Data & trust";
type Turn = { question: string; answer: Answer };
const navigation = [
  { name: "Overview" as Tab, icon: LayoutDashboard },
  { name: "Investigate" as Tab, icon: MessageSquare },
  { name: "Outlook" as Tab, icon: TrendingUp },
  { name: "Briefs" as Tab, icon: FileText },
];
const exampleQuestions = [
  "Which products contributed most to the target gap?",
  "Compare revenue across markets",
  "How did revenue change against the same period last year?",
];

export default function Workbench() {
  const [tab, setTab] = useState<Tab>("Overview");
  const [scope, setScope] = useState<Scope>({
    country: "All markets",
    period: "Q3 2026",
  });
  const [data, setData] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [selected, setSelected] = useState<Answer | null>(null);
  const [showSQL, setShowSQL] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [quality, setQuality] = useState<{
    metadata: Dataset;
    agent_mode: string;
    tracing: string;
    limitations: string[];
    runs: { status: string; started_at: string; accepted: number }[];
  } | null>(null);
  const [votes, setVotes] = useState<Record<string, number>>({});
  const [sidebar, setSidebar] = useState(false);
  const [help, setHelp] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api<Overview>(`overview?${new URLSearchParams(scope)}`)
      .then((d) => {
        if (active) setData(d);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [scope]);
  useEffect(() => {
    let active = true;
    if (tab === "Briefs")
      api<Brief[]>("briefs")
        .then((d) => {
          if (active) setBriefs(d);
        })
        .catch((e) => setError(e.message));
    if (tab === "Outlook") {
      setAnalysis(null);
      api<Analysis>(`analysis?country=${encodeURIComponent(scope.country)}`)
        .then((d) => {
          if (active) setAnalysis(d);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    }
    if (tab === "Data & trust" || tab === "Investigate")
      api<typeof quality>("quality")
        .then((d) => {
          if (active) setQuality(d);
        })
        .catch((e) => setError(e.message));
    return () => {
      active = false;
    };
  }, [tab, scope.country]);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [turns, busy]);
  useEffect(() => {
    if (!help) return;
    const previous = document.activeElement as HTMLElement | null;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setHelp(false);
        return;
      }
      if (event.key === "Tab") {
        const items = Array.from(
          document.querySelectorAll<HTMLElement>(
            ".about-modal button, .about-modal a[href]",
          ),
        );
        const first = items[0],
          last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, [help]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  async function ask(text: string, override?: Scope) {
    if (busy || !text.trim()) return;
    setBusy(true);
    setError("");
    setTab("Investigate");
    setQuestion("");
    try {
      const answer = await api<Answer>("chat", {
        question: text,
        scope: override || scope,
      });
      setTurns((t) => [...t, { question: text, answer }]);
      setSelected(answer);
      setShowSQL(false);
      if (answer.status === "answered") setScope(answer.scope);
    } catch (e) {
      setError((e as Error).message);
      setQuestion(text);
    } finally {
      setBusy(false);
    }
  }
  async function saveBrief() {
    if (busy) return;
    setBusy(true);
    try {
      const b = await api<Brief>("briefs", scope);
      setBriefs((bs) => [b, ...bs]);
      setTab("Briefs");
      setToast("Review brief saved");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function vote(answer: Answer, value: number) {
    try {
      await api("feedback", { run_id: answer.run_id, vote: value });
      setVotes((v) => ({ ...v, [answer.run_id]: value }));
      setToast("Feedback recorded");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function navigate(next: Tab) {
    setTab(next);
    setSidebar(false);
    setError("");
  }
  function exportBrief(b: Brief) {
    const c = b.content;
    const text = `# ${b.title}\n\n${c.summary}\n\n${c.findings.map((f) => "- " + f).join("\n")}\n\n${c.next_step}\n\n${c.disclosure}\nData version: ${c.data_version}\n`;
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/markdown" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "commercial-review.md";
    a.click();
    URL.revokeObjectURL(url);
  }
  const worstMarket = data?.markets[0];
  const gap = data?.summary.gap || 0;

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebar ? "open" : ""}`}>
        <a className="brand" href="/" aria-label="Atlas home">
          <span className="brand-mark">
            <Compass size={25} strokeWidth={1.4} />
          </span>
          <span>
            atlas<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="workspace">
          <div className="workspace-icon">CI</div>
          <div>
            <strong>Commercial intelligence</strong>
            <span>Gulf markets / Human health</span>
          </div>
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {navigation.map(({ name, icon: Icon }) => (
            <button
              key={name}
              aria-current={tab === name ? "page" : undefined}
              className={`nav-item ${tab === name ? "active" : ""}`}
              onClick={() => navigate(name)}
            >
              <Icon size={17} />
              <span>{name}</span>
              {tab === name && <span className="active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sandbox-note">
            <span className="live-dot" />
            <span>Synthetic portfolio</span>
            <small>
              48 months · 4 Gulf markets
              <br />
              Synthetic pharmaceutical data
            </small>
          </div>
          <button
            className={`nav-item ${tab === "Data & trust" ? "active" : ""}`}
            onClick={() => navigate("Data & trust")}
          >
            <ShieldCheck size={17} />
            Data & trust
          </button>
          <button className="nav-item" onClick={() => setHelp(true)}>
            <CircleHelp size={17} />
            About this workspace
          </button>
          <div className="profile">
            <span className="avatar">RM</span>
            <div>
              <strong>Commercial operations</strong>
              <small>Independent portfolio demo</small>
            </div>
          </div>
        </div>
      </aside>
      {sidebar && (
        <button
          className="sidebar-scrim"
          aria-label="Close navigation"
          onClick={() => setSidebar(false)}
        />
      )}
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setSidebar(true)}
            >
              <Menu size={19} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>{tab}</strong>
          </div>
          <div className="topbar-right">
            <span className="synthetic-badge">
              <span />
              Synthetic data
            </span>
            <div className="topbar-divider" />
            <button
              className="icon-button"
              aria-label="About this workspace"
              onClick={() => setHelp(true)}
            >
              <CircleHelp size={18} />
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                ATLAS / INTELLIGENCE <span>/</span>{" "}
                {tab === "Overview" ? "PERFORMANCE REVIEW" : tab.toUpperCase()}
              </div>
              <h1>
                {tab === "Overview"
                  ? "Commercial performance"
                  : tab === "Investigate"
                    ? "Performance investigation"
                    : tab === "Outlook"
                      ? "Forecast & statistical evidence"
                      : tab === "Briefs"
                        ? "Commercial review briefs"
                        : "Data assurance"}
              </h1>
              <p>
                {tab === "Overview"
                  ? "Human health portfolio · Gulf markets · Quarterly business review"
                  : tab === "Investigate"
                    ? "Ask a business question. Inspect the numbers behind the answer."
                    : tab === "Outlook"
                      ? "Forecasts, baselines, and the uncertainty between them."
                      : tab === "Briefs"
                        ? "Concise commercial reviews, ready for a human perspective."
                        : "Traceable metrics and explicit limits, by design."}
              </p>
            </div>
            {tab !== "Investigate" && (
              <button
                className="button primary"
                disabled={busy || !data || loading}
                onClick={saveBrief}
              >
                <FileText size={15} />
                {busy ? "Preparing…" : "Create review brief"}
                <ArrowUpRight size={15} />
              </button>
            )}
          </div>
          <div className="filterbar">
            <div className="filter-controls">
              <label>
                <span>Market</span>
                <select
                  aria-label="Market"
                  disabled={busy}
                  value={scope.country}
                  onChange={(e) =>
                    setScope((s) => ({ ...s, country: e.target.value }))
                  }
                >
                  {["All markets", "UAE", "Kuwait", "Qatar", "Oman"].map(
                    (v) => (
                      <option key={v}>{v}</option>
                    ),
                  )}
                </select>
                <ChevronDown size={13} />
              </label>
              {tab !== "Outlook" && (
                <label>
                  <span>Period</span>
                  <select
                    aria-label="Period"
                    disabled={busy}
                    value={scope.period}
                    onChange={(e) =>
                      setScope((s) => ({ ...s, period: e.target.value }))
                    }
                  >
                    {["Q3 2026", "Q2 2026", "YTD 2026", "FY 2025"].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                  <ChevronDown size={13} />
                </label>
              )}
            </div>
            <span className="data-date">
              <span className="live-dot" />
              Data through 30 Sep 2026 <span className="muted">· USD</span>
            </span>
          </div>
          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={17} />
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Dismiss error"
                onClick={() => setError("")}
              >
                <X size={15} />
              </button>
            </div>
          )}

          {tab === "Overview" &&
            (loading ? (
              <Skeleton />
            ) : (
              data && (
                <>
                  <ReviewSummary data={data} onInvestigate={ask} />
                  <div className="kpi-grid">
                    <KPI
                      label="Portfolio revenue"
                      value={money(data.summary.revenue)}
                      subtitle="vs. same period last year"
                      change={data.summary.growth}
                      series={data.trend.map((r) => r.revenue)}
                    />
                    <KPI
                      label="Target attainment"
                      value={`${data.summary.attainment.toFixed(1)}%`}
                      subtitle={`${money(data.summary.target)} revenue target`}
                      change={null}
                      series={data.trend.map((r) => r.revenue / r.target)}
                      progress={data.summary.attainment}
                    />
                    <KPI
                      label="Gap to target"
                      value={`${gap < 0 ? "−" : "+"}${money(Math.abs(gap))}`}
                      subtitle={
                        gap < 0
                          ? "Below the reporting-period plan"
                          : "Above the reporting-period plan"
                      }
                      change={null}
                      series={data.trend.map((r) => r.revenue - r.target)}
                      negative={gap < 0}
                    />
                    <KPI
                      label="Markets below target"
                      value={`${data.markets.filter((r) => r.attainment < 100).length}`}
                      suffix={`/ ${data.markets.length}`}
                      subtitle="Markets to review this period"
                      change={null}
                      series={[]}
                      markets={data.markets}
                    />
                  </div>
                  <div className="overview-primary">
                    <section className="panel revenue-panel">
                      <div className="panel-heading">
                        <div>
                          <h2>Revenue trajectory</h2>
                          <p>
                            Reporting year through{" "}
                            {scope.period === "FY 2025"
                              ? "Dec 2025"
                              : scope.period === "Q2 2026"
                                ? "Jun 2026"
                                : "Sep 2026"}
                          </p>
                        </div>
                        <div className="segment">
                          <button
                            className={!showTable ? "selected" : ""}
                            onClick={() => setShowTable(false)}
                          >
                            Chart
                          </button>
                          <button
                            className={showTable ? "selected" : ""}
                            onClick={() => setShowTable(true)}
                          >
                            Table
                          </button>
                        </div>
                      </div>
                      <div className="chart-legend">
                        <span>
                          <i className="legend-actual" />
                          Revenue
                        </span>
                        <span>
                          <i className="legend-target" />
                          Target
                        </span>
                        <span>
                          <i className="legend-prior" />
                          Prior year
                        </span>
                      </div>
                      {showTable ? (
                        <EvidenceTable rows={data.trend} compact />
                      ) : (
                        <RevenueChart rows={data.trend} />
                      )}
                      <div className="panel-foot">
                        <ShieldCheck size={13} />
                        Actuals and targets share one metric definition.
                        <button onClick={() => navigate("Data & trust")}>
                          View methodology
                          <ArrowRight size={12} />
                        </button>
                      </div>
                    </section>
                    <ReviewQueue data={data} onInvestigate={ask} />
                  </div>
                  <div className="overview-secondary">
                    <section className="panel">
                      <div className="panel-heading">
                        <div>
                          <h2>Market performance</h2>
                          <p>Revenue against the reporting-period plan</p>
                        </div>
                        <span className="quiet-badge">
                          {data.markets.length} markets
                        </span>
                      </div>
                      <div className="market-table">
                        <div className="market-row table-labels">
                          <span>MARKET</span>
                          <span>REVENUE</span>
                          <span>ATTAINMENT</span>
                          <span />
                        </div>
                        {data.markets.map((r) => (
                          <button
                            className="market-row"
                            key={r.country}
                            onClick={() =>
                              ask(`Show the target gap in ${r.country}`, {
                                ...scope,
                                country: r.country!,
                              })
                            }
                          >
                            <span className="market-name">
                              <span className="country-code">
                                {r.country?.slice(0, 2).toUpperCase()}
                              </span>
                              {r.country}
                            </span>
                            <strong>{money(r.revenue)}</strong>
                            <span className="attainment-cell">
                              <span className="mini-track">
                                <i
                                  style={{
                                    width: `${Math.min(100, r.attainment)}%`,
                                  }}
                                />
                              </span>
                              <span>{r.attainment.toFixed(1)}%</span>
                            </span>
                            <ArrowUpRight size={15} />
                          </button>
                        ))}
                      </div>
                      <div className="panel-foot">
                        Select a market to open an investigation.
                        <span />
                      </div>
                    </section>
                    <section className="panel">
                      <div className="panel-heading">
                        <div>
                          <h2>Product contribution</h2>
                          <p>Signed revenue gap to target</p>
                        </div>
                        <button
                          className="icon-button"
                          aria-label="Investigate product contribution"
                          onClick={() => ask(exampleQuestions[0])}
                        >
                          <ArrowUpRight size={18} />
                        </button>
                      </div>
                      <GapChart rows={data.products} />
                    </section>
                  </div>
                  <TherapeuticReview data={data} />
                  <section className="ask-strip">
                    <div className="ask-icon">
                      <Sparkles size={19} />
                    </div>
                    <div>
                      <strong>Open a performance investigation</strong>
                      <p>
                        Resolve the question, compare contributions, and inspect
                        the source calculation.
                      </p>
                    </div>
                    <button
                      className="button secondary"
                      onClick={() => navigate("Investigate")}
                    >
                      Start investigating
                      <ArrowRight size={15} />
                    </button>
                  </section>
                </>
              )
            ))}

          {tab === "Investigate" && (
            <div className="investigation-grid">
              <section className="panel conversation">
                <div className="panel-heading">
                  <h2>
                    <MessageSquare size={16} />
                    Investigation
                  </h2>
                  <span className="quiet-badge">
                    {quality?.agent_mode === "live" || selected?.mode === "live"
                      ? "Live model"
                      : "Guided mode"}
                  </span>
                </div>
                <div className="turn-list">
                  {turns.length === 0 ? (
                    <div className="chat-welcome">
                      <span className="assistant-mark">
                        <Compass size={24} />
                      </span>
                      <h3>
                        What would you like
                        <br />
                        to understand?
                      </h3>
                      <p>
                        Start with a question about revenue, growth, or the gap
                        to plan.
                      </p>
                      <div className="suggestions">
                        {exampleQuestions.map((q) => (
                          <button
                            disabled={busy}
                            key={q}
                            onClick={() => ask(q)}
                          >
                            {q}
                            <ArrowUpRight size={14} />
                          </button>
                        ))}
                      </div>
                      <small>
                        {quality?.agent_mode === "live"
                          ? "Live mode resolves your question into an approved analytical plan. Inspect the SQL and evidence behind each answer."
                          : "Guided mode uses a transparent rules-based planner. No live LLM credentials are required."}
                      </small>
                    </div>
                  ) : (
                    turns.map(({ question: q, answer: a }) => (
                      <div className="turn" key={a.run_id}>
                        <div className="user-question">{q}</div>
                        <button
                          className={`answer-preview ${selected?.run_id === a.run_id ? "current" : ""}`}
                          onClick={() => setSelected(a)}
                        >
                          <span className="answer-status">
                            <Compass size={14} />
                            {a.status === "answered"
                              ? "Evidence ready"
                              : a.status === "clarification"
                                ? "Clarification needed"
                                : "Scope boundary"}
                          </span>
                          <strong>{a.title}</strong>
                          <p>{a.text}</p>
                          {a.status === "answered" && (
                            <span className="evidence-link">
                              Inspect evidence
                              <ArrowRight size={12} />
                            </span>
                          )}
                        </button>
                      </div>
                    ))
                  )}
                  {busy && (
                    <div className="thinking" role="status">
                      <Loader2 size={15} className="spin" />
                      Resolving scope and checking the data…
                    </div>
                  )}
                  <div ref={bottom} />
                </div>
                <form
                  className="composer"
                  onSubmit={(e: FormEvent) => {
                    e.preventDefault();
                    ask(question);
                  }}
                >
                  <textarea
                    aria-label="Your business question"
                    placeholder={
                      turns.length
                        ? "Ask a follow-up…"
                        : "Ask about commercial performance…"
                    }
                    value={question}
                    maxLength={1500}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        ask(question);
                      }
                    }}
                  />
                  <div>
                    <small>
                      {scope.country} · {scope.period}
                    </small>
                    <button
                      className="send-button"
                      aria-label="Send question"
                      disabled={busy || !question.trim()}
                    >
                      <Send size={16} />
                    </button>
                  </div>
                </form>
              </section>
              <section className="panel evidence-panel">
                {selected ? (
                  <>
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">INVESTIGATION EVIDENCE</span>
                        <h2>
                          {selected.scope.country}{" "}
                          <span className="muted">
                            / {selected.scope.period}
                          </span>
                        </h2>
                      </div>
                      {selected.status === "answered" && (
                        <span className="verified">
                          <CheckCircle2 size={14} />
                          Query verified
                        </span>
                      )}
                    </div>
                    <div className="finding">
                      <h3>{selected.title}</h3>
                      <p>{selected.text}</p>
                    </div>
                    {selected.rows.length > 0 && (
                      <>
                        <div className="evidence-chart">
                          {selected.intent === "products" ? (
                            <GapChart rows={selected.rows} />
                          ) : selected.chart === "line" ? (
                            <RevenueChart rows={selected.rows} />
                          ) : null}
                        </div>
                        <EvidenceTable rows={selected.rows} />
                      </>
                    )}
                    {selected.next_check && (
                      <div className="next-check">
                        <span>
                          <ArrowUpRight size={16} />
                          Suggested next check
                        </span>
                        <p>{selected.next_check}</p>
                      </div>
                    )}
                    {selected.sql && (
                      <div className="sql-box">
                        <button
                          className="sql-toggle"
                          aria-expanded={showSQL}
                          onClick={() => setShowSQL(!showSQL)}
                        >
                          <Code2 size={15} />
                          Show SQL
                          <ChevronDown
                            size={14}
                            style={{
                              transform: showSQL ? "rotate(180deg)" : "",
                            }}
                          />
                        </button>
                        {showSQL && (
                          <>
                            <pre>{selected.sql}</pre>
                            <button
                              className="text-button"
                              onClick={async () => {
                                try {
                                  await navigator.clipboard.writeText(
                                    selected.sql!,
                                  );
                                  setToast("SQL copied");
                                } catch {
                                  setToast("Select the SQL text to copy it");
                                }
                              }}
                            >
                              <Copy size={13} />
                              Copy SQL
                            </button>
                          </>
                        )}
                      </div>
                    )}
                    <div className="evidence-footer">
                      <small>
                        {selected.data_version}
                        <br />
                        {selected.latency_ms} ms · {selected.mode} planner ·{" "}
                        {selected.usage.input_tokens +
                          selected.usage.output_tokens}{" "}
                        model tokens
                      </small>
                      <div>
                        <span>Useful?</span>
                        <button
                          className={`icon-button ${votes[selected.run_id] === 1 ? "voted" : ""}`}
                          aria-label="Helpful answer"
                          onClick={() => vote(selected, 1)}
                        >
                          <ThumbsUp size={15} />
                        </button>
                        <button
                          className={`icon-button ${votes[selected.run_id] === -1 ? "voted" : ""}`}
                          aria-label="Unhelpful answer"
                          onClick={() => vote(selected, -1)}
                        >
                          <ThumbsDown size={15} />
                        </button>
                      </div>
                    </div>
                    <p className="disclaimer">{selected.limitation}</p>
                  </>
                ) : (
                  <div className="empty-evidence">
                    <div className="evidence-grid-art">
                      <div />
                      <div />
                      <div />
                      <div />
                      <span>
                        <Search size={27} strokeWidth={1.3} />
                      </span>
                    </div>
                    <h3>Your investigation evidence</h3>
                    <p>
                      Your charts, calculations, and SQL will appear here.
                      <br />
                      Start an investigation to follow the evidence.
                    </p>
                    <div className="evidence-principles">
                      <span>
                        <Database size={14} />
                        Approved data
                      </span>
                      <span>
                        <ShieldCheck size={14} />
                        Read-only queries
                      </span>
                      <span>
                        <Code2 size={14} />
                        Visible SQL
                      </span>
                    </div>
                  </div>
                )}
              </section>
            </div>
          )}

          {tab === "Outlook" &&
            (analysis ? (
              <>
                <div className="outlook-grid">
                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <h2>Revenue outlook</h2>
                        <p>{scope.country} · October–December 2026</p>
                      </div>
                      <span className="quiet-badge">
                        {analysis.selected_model === "ets"
                          ? "ETS"
                          : "Seasonal naïve"}{" "}
                        selected
                      </span>
                    </div>
                    <ForecastChart data={analysis} />
                    <div className="panel-foot">
                      Historical actuals <span>Exploratory forecast · USD</span>
                    </div>
                  </section>
                  <section className="panel model-card">
                    <span className="eyebrow">BASELINE COMPARISON</span>
                    <h2>Out-of-sample accuracy</h2>
                    <p>
                      Held-out test: {analysis.test_period}. Lower error is
                      better.
                    </p>
                    {Object.entries(analysis.test).map(([key, v]) => (
                      <div className="model-result" key={key}>
                        <div>
                          <strong>
                            {key === "ets"
                              ? "Exponential smoothing"
                              : "Seasonal naïve"}
                          </strong>
                          <small>MAPE / WAPE</small>
                        </div>
                        <span>
                          {v.mape.toFixed(1)}%
                          <small>{v.wape.toFixed(1)}% WAPE</small>
                        </span>
                      </div>
                    ))}
                    <p className="method-note">{analysis.method}</p>
                  </section>
                </div>
                <div className="overview-secondary">
                  <section className="panel analysis-card">
                    <span className="eyebrow">SALES-DROP SCREEN</span>
                    <h2>
                      {analysis.anomaly.flagged
                        ? "A deviation to investigate."
                        : "No threshold breach this month."}
                    </h2>
                    <div className="large-stat">
                      {analysis.anomaly.robust_score?.toFixed(2) ?? "N/A"}
                      <small>robust score</small>
                    </div>
                    <p>{analysis.anomaly.method}</p>
                  </section>
                  <section className="panel analysis-card">
                    <span className="eyebrow">
                      RANDOMIZED SYNTHETIC CAMPAIGN · ALL MARKETS
                    </span>
                    <h2>Promotion experiment</h2>
                    <div className="large-stat">
                      {analysis.promotion.effect_pp.toFixed(1)}
                      <small>percentage-point growth difference</small>
                    </div>
                    <p>
                      Approximate 95% interval:{" "}
                      {analysis.promotion.ci_low_pp.toFixed(1)} to{" "}
                      {analysis.promotion.ci_high_pp.toFixed(1)} pp. Exact test
                      p = {analysis.promotion.p_value.toFixed(4)}.
                    </p>
                    <p className="method-note">
                      {analysis.promotion.limitation}
                    </p>
                  </section>
                </div>
                <div className="note-banner">
                  <CircleHelp size={17} />
                  {analysis.interval_note} Forecast values are not business
                  commitments.
                </div>
              </>
            ) : (
              <Skeleton />
            ))}

          {tab === "Briefs" && (
            <div className="briefs-grid">
              {briefs.length === 0 ? (
                <section className="panel empty-brief">
                  <FileText size={32} strokeWidth={1.3} />
                  <h2>Prepare the commercial review.</h2>
                  <p>
                    Create a review from your selected market and reporting
                    period.
                    <br />
                    It will include the numbers, the biggest gaps, and a
                    proposed next check.
                  </p>
                  <button
                    className="button primary"
                    disabled={busy || !data}
                    onClick={saveBrief}
                  >
                    <Plus size={15} />
                    Create your first brief
                  </button>
                </section>
              ) : (
                briefs.map((b) => (
                  <article className="panel brief" key={b.brief_id}>
                    <div className="brief-top">
                      <span className="quiet-badge">DRAFT · FOR REVIEW</span>
                      <FileText size={19} />
                    </div>
                    <h2>{b.title}</h2>
                    <p>{b.content.summary}</p>
                    <ul>
                      {b.content.findings.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                    <div className="brief-next">
                      <strong>Next conversation</strong>
                      <p>{b.content.next_step}</p>
                    </div>
                    <div className="brief-bottom">
                      <small>{b.content.disclosure}</small>
                      <button
                        className="button secondary"
                        onClick={() => exportBrief(b)}
                      >
                        <Download size={14} />
                        Markdown
                      </button>
                    </div>
                  </article>
                ))
              )}
            </div>
          )}

          {tab === "Data & trust" &&
            (quality ? (
              <>
                <div className="trust-intro">
                  <ShieldCheck size={25} />
                  <div>
                    <h2>Every number comes from a reproducible simulation.</h2>
                    <p>
                      This independent portfolio project contains no MSD
                      records, real product data, or patient information.
                      Product and rep names are fictional.
                    </p>
                  </div>
                </div>
                <div className="overview-secondary">
                  <section className="panel analysis-card">
                    <span className="eyebrow">DATA CONTRACT</span>
                    <h2>
                      {quality.metadata.rows.toLocaleString()} sales records
                    </h2>
                    <dl className="definition-list">
                      <div>
                        <dt>History</dt>
                        <dd>Oct 2022 – Sep 2026</dd>
                      </div>
                      <div>
                        <dt>Sales grain</dt>
                        <dd>Month × product × territory × rep × channel</dd>
                      </div>
                      <div>
                        <dt>Reporting currency</dt>
                        <dd>USD · synthetic prices</dd>
                      </div>
                      <div>
                        <dt>Generator seed</dt>
                        <dd>422804</dd>
                      </div>
                      <div>
                        <dt>Data version</dt>
                        <dd className="mono">
                          {quality.metadata.data_version}
                        </dd>
                      </div>
                    </dl>
                  </section>
                  <section className="panel analysis-card">
                    <span className="eyebrow">PIPELINE CHECKS</span>
                    <h2>Quality is checked before loading.</h2>
                    <div className="check-list">
                      {Object.entries(quality.metadata.quality_checks).map(
                        ([name, passed]) => (
                          <div key={name}>
                            {passed ? (
                              <CheckCircle2 size={15} />
                            ) : (
                              <AlertCircle size={15} />
                            )}
                            <span>{name.replaceAll("_", " ")}</span>
                            <small>{passed ? "Passed" : "Failed"}</small>
                          </div>
                        ),
                      )}
                    </div>
                  </section>
                </div>
                <section className="panel analysis-card">
                  <div className="panel-heading flush">
                    <div>
                      <span className="eyebrow">METRIC DICTIONARY</span>
                      <h2>Shared definitions across every view.</h2>
                    </div>
                    <Database size={20} />
                  </div>
                  <div className="metric-definitions">
                    <div>
                      <strong>Revenue</strong>
                      <p>Sum of recorded sales revenue in reporting USD.</p>
                    </div>
                    <div>
                      <strong>Target attainment</strong>
                      <p>
                        Total actual ÷ total target × 100. Sales are aggregated
                        before the target join.
                      </p>
                    </div>
                    <div>
                      <strong>Year-over-year growth</strong>
                      <p>
                        Change against the same calendar months in the prior
                        year.
                      </p>
                    </div>
                    <div>
                      <strong>Portfolio share</strong>
                      <p>
                        Product revenue ÷ selected portfolio revenue. This is
                        not market share.
                      </p>
                    </div>
                  </div>
                </section>
                <section className="panel analysis-card">
                  <span className="eyebrow">OPERATIONAL TRANSPARENCY</span>
                  <h2>Runtime & known limitations</h2>
                  <p>
                    Planner: <strong>{quality.agent_mode}</strong> · Tracing:{" "}
                    <strong>{quality.tracing}</strong>
                  </p>
                  <ul className="limitations">
                    {quality.limitations.map((l) => (
                      <li key={l}>{l}</li>
                    ))}
                  </ul>
                </section>
              </>
            ) : (
              <Skeleton />
            ))}
          <footer className="page-footer">
            <span>
              ATLAS <span className="footer-dot">·</span> COMMERCIAL
              INTELLIGENCE
            </span>
            <span>
              Independent portfolio project{" "}
              <span className="footer-dot">·</span> Synthetic data, real
              calculations
            </span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={16} />
          {toast}
        </div>
      )}
      {help && (
        <div className="modal-backdrop" onClick={() => setHelp(false)}>
          <section
            className="about-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="about-title"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="icon-button modal-close"
              aria-label="Close about"
              onClick={() => setHelp(false)}
              autoFocus
            >
              <X size={20} />
            </button>
            <Compass size={34} strokeWidth={1.4} />
            <span className="eyebrow">AN INDEPENDENT RESEARCH PROJECT</span>
            <h2 id="about-title">
              Commercial clarity,
              <br />
              with evidence attached.
            </h2>
            <p>
              Atlas explores how an analytics agent can help commercial teams
              investigate performance using a fictional pharmaceutical
              portfolio.
            </p>
            <p>
              The data is seeded and synthetic. Calculations run against
              PostgreSQL. Guided mode uses a deterministic planner; live model
              mode requires separate configuration.
            </p>
            <div className="note-banner">
              This project is not affiliated with or endorsed by MSD.
            </div>
            <button
              className="button primary"
              onClick={() => {
                setHelp(false);
                navigate("Data & trust");
              }}
            >
              Explore data & trust
              <ArrowRight size={15} />
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

function KPI({
  label,
  value,
  subtitle,
  change,
  series,
  negative,
  progress,
  suffix,
  markets,
}: {
  label: string;
  value: string;
  subtitle: string;
  change: number | null;
  series: number[];
  negative?: boolean;
  progress?: number;
  suffix?: string;
  markets?: Row[];
}) {
  const low = Math.min(...series),
    high = Math.max(...series);
  const points = series
    .map(
      (v, i) =>
        `${(i * 90) / Math.max(series.length - 1, 1)},${26 - ((v - low) / Math.max(high - low, 1)) * 22}`,
    )
    .join(" ");
  return (
    <article className="kpi">
      <div className="kpi-label">
        {label}
        <span className="kpi-indicator" />
      </div>
      <div className="kpi-value">
        <span className={negative ? "negative-value" : ""}>{value}</span>
        {suffix && <small>{suffix}</small>}
        {series.length > 0 && progress === undefined && (
          <svg
            className="sparkline"
            width="94"
            height="30"
            viewBox="0 0 94 30"
            aria-hidden="true"
          >
            <polyline
              points={points}
              fill="none"
              stroke={negative ? "#dba178" : "#65c9bb"}
              strokeWidth="1.6"
            />
          </svg>
        )}
      </div>
      {progress !== undefined && (
        <div className="kpi-progress">
          <i style={{ width: `${Math.min(100, progress)}%` }} />
          <span />
        </div>
      )}
      {markets && (
        <div className="market-dots">
          {markets.map((r) => (
            <span key={r.country} className={r.attainment < 100 ? "below" : ""}>
              {r.country}
            </span>
          ))}
        </div>
      )}
      <div className="kpi-caption">
        {change !== null && (
          <span className={`change ${change < 0 ? "down" : ""}`}>
            {change < 0 ? (
              <ArrowDownRight size={12} />
            ) : (
              <ArrowUpRight size={12} />
            )}{" "}
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
        {subtitle}
      </div>
    </article>
  );
}
function EvidenceTable({
  rows,
  compact = false,
}: {
  rows: Row[];
  compact?: boolean;
}) {
  if (!rows.length) return null;
  const columns = Object.keys(rows[0]).filter(
    (k) => !["prior_year_revenue", "share"].includes(k),
  );
  return (
    <div className={`evidence-table ${compact ? "compact" : ""}`}>
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>
                  {r[c] === null
                    ? "—"
                    : typeof r[c] === "number"
                      ? c === "attainment"
                        ? `${Number(r[c]).toFixed(1)}%`
                        : money(Number(r[c]), false)
                      : c === "month"
                        ? month(String(r[c]))
                        : r[c]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function Skeleton() {
  return (
    <div
      className="skeleton-state"
      role="status"
      aria-label="Loading commercial data"
    >
      <div className="kpi-grid">
        {[1, 2, 3, 4].map((i) => (
          <div className="skeleton-card" key={i}>
            <span />
            <strong />
            <span />
          </div>
        ))}
      </div>
      <div className="skeleton-large" />
      <p>
        <Loader2 size={15} className="spin" />
        Loading verified data…
      </p>
    </div>
  );
}
