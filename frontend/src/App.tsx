import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowRight, Bot, Check,
  CheckCircle2, ChevronDown, CircleHelp, Clock3, Code2, FileCode2,
  FileSearch, FolderGit2, GitCompareArrows, LoaderCircle, Play, RefreshCw,
  ShieldCheck, Sparkles, Terminal, Upload, X
} from "lucide-react";
import type { Analysis, Finding, Health, PatchResult, RepoFile, TestResult } from "./types";

const api = async <T,>(url: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(url, init);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || body.message || `Request failed (${response.status})`);
  return body as T;
};

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [nemotronModels, setNemotronModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState("");
  const [repoId, setRepoId] = useState("");
  const [repoFiles, setRepoFiles] = useState<RepoFile[]>([]);
  const [repoName, setRepoName] = useState("");
  const [task, setTask] = useState("Review this repository for correctness bugs, edge cases, and missing tests. Only report issues supported by code evidence.");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [patch, setPatch] = useState<PatchResult | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeTab, setActiveTab] = useState<"findings" | "patch" | "tests">("findings");
  const [selectedFindingIds, setSelectedFindingIds] = useState<string[]>([]);
  const [showModels, setShowModels] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const selectedNemotron = useMemo(
    () => nemotronModels.find((m) => m.toLowerCase() === health?.model_id?.toLowerCase()),
    [nemotronModels, health?.model_id]
  );

  async function refreshHealth() {
    try {
      const h = await api<Health>("/api/health");
      setHealth(h);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend unavailable");
    }
  }

  useEffect(() => { void refreshHealth(); }, []);

  async function connectModel() {
    setBusy("models");
    setError("");
    setModelError("");
    try {
      const data = await api<{ models: string[]; nemotron_models: string[]; configured_model: string | null }>("/api/models");
      setModels(data.models);
      setNemotronModels(data.nemotron_models);
      setShowModels(true);
      if (data.nemotron_models.length === 0) {
        setModelError("No Nemotron model appeared in this account's live catalog. Check account access and the current catalog.");
      } else if (!data.configured_model) {
        setModelError("Catalog connected. Set NEBIUS_MODEL to one of these exact IDs in backend/.env, then restart the backend.");
      } else {
        setNotice(`Catalog verified. Configured model: ${data.configured_model}`);
      }
    } catch (e) {
      setModelError(e instanceof Error ? e.message : "Could not connect to Token Factory");
    } finally {
      setBusy("");
      await refreshHealth();
    }
  }

  async function uploadRepo(file?: File) {
    if (!file) return;
    setBusy("upload");
    setError("");
    setNotice("");
    setAnalysis(null);
    setPatch(null);
    setTestResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const data = await api<{ repo_id: string; file_count: number; files: RepoFile[] }>("/api/repositories", { method: "POST", body: form });
      setRepoId(data.repo_id);
      setRepoFiles(data.files);
      setRepoName(file.name.replace(/\.zip$/i, ""));
      setNotice(`Imported ${data.file_count} supported source files.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy("");
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function runAnalysis() {
    if (!repoId) { setError("Upload a ZIP repository first."); return; }
    setBusy("analysis"); setError(""); setNotice(""); setAnalysis(null); setPatch(null);
    try {
      const result = await api<Analysis>("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: repoId, task }),
      });
      setAnalysis(result);
      setSelectedFindingIds(result.findings.map((f) => f.id));
      setActiveTab("findings");
      setNotice("Review complete. Verify every finding against its evidence.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally { setBusy(""); }
  }

  async function generatePatch() {
    if (!repoId) return;
    setBusy("patch"); setError(""); setNotice(""); setPatch(null);
    try {
      const result = await api<PatchResult>("/api/patch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_id: repoId,
          task,
          finding_ids: selectedFindingIds,
        }),
      });
      setPatch(result);
      setActiveTab("patch");
      setNotice(result.patch ? "Patch generated. Review it before applying." : result.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Patch generation failed");
    } finally { setBusy(""); }
  }

  async function runTests() {
    if (!repoId) return;
    setBusy("tests"); setError(""); setNotice(""); setTestResult(null);
    try {
      const result = await api<TestResult>("/api/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: repoId, command: "auto" }),
      });
      setTestResult(result);
      setActiveTab("tests");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test run failed");
    } finally { setBusy(""); }
  }

  function downloadPatch() {
    if (!patch?.patch) return;
    const blob = new Blob([patch.patch], { type: "text/x-diff;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "aethercode-proposed.patch"; a.click();
    URL.revokeObjectURL(url);
  }

  function toggleFinding(f: Finding) {
    setSelectedFindingIds((prev) => prev.includes(f.id) ? prev.filter((id) => id !== f.id) : [...prev, f.id]);
  }

  const busyLabel = busy === "models" ? "Connecting…" : busy === "upload" ? "Importing…" :
    busy === "analysis" ? "Reviewing repository…" : busy === "patch" ? "Generating patch…" :
    busy === "tests" ? "Running sandbox tests…" : "";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Code2 size={21} /></div>
          <div><strong>Aether Code<span> AI</span></strong><small>SOFTWARE ENGINEERING AGENT</small></div>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <button className="side-item active"><FolderGit2 size={17} /> Repository workspace <span className="side-dot" /></button>
        <button className="side-item" onClick={() => setActiveTab("findings")}><FileSearch size={17} /> Code review</button>
        <button className="side-item" onClick={() => setActiveTab("patch")}><GitCompareArrows size={17} /> Patch review</button>
        <button className="side-item" onClick={() => setActiveTab("tests")}><Terminal size={17} /> Test runner</button>
        <div className="sidebar-bottom">
          <div className="side-note"><ShieldCheck size={17} /><div><b>Review before apply</b><p>AI output is a proposal, not proof of correctness.</p></div></div>
          <div className="user-chip"><div className="avatar">CP</div><div><b>Local workspace</b><small>Prototype · v0.1.0</small></div><ChevronDown size={15} /></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="slash">/</span><b>{repoName || "No repository selected"}</b></div>
          <div className="top-actions">
            <div className={`connection ${health?.api_key_configured ? "connected" : "disconnected"}`}><span />{health?.api_key_configured ? "Token Factory configured" : "API key missing"}</div>
            <button className="button button-secondary button-sm" onClick={connectModel} disabled={busy !== ""}><RefreshCw size={14} /> Connect model</button>
          </div>
        </header>

        <div className="content">
          <section className="welcome-row">
            <div>
              <div className="eyebrow"><Sparkles size={14} /> AGENTIC ENGINEERING WORKSPACE</div>
              <h1>Ship better code.<br /><span>With evidence.</span></h1>
              <p className="lead">Inspect a repository, find likely bugs, propose a patch, and run tests in a restricted sandbox.</p>
            </div>
            <div className="hero-visual" aria-hidden="true">
              <div className="orbit orbit-one" /><div className="orbit orbit-two" />
              <div className="hero-core"><Bot size={36} /></div>
              <div className="float-card float-a"><CheckCircle2 size={15} /> Evidence first</div>
              <div className="float-card float-b"><Terminal size={15} /> Test loop</div>
            </div>
          </section>

          <section className="stats-grid">
            <div className="stat-card"><div className="stat-top"><span>MODEL STATUS</span><Activity size={16} /></div><strong className="stat-value">{selectedNemotron ? "Verified" : health?.model_configured ? "Configured" : "Not connected"}</strong><small>{health?.model_id || "Connect and choose a Nemotron ID"}</small></div>
            <div className="stat-card"><div className="stat-top"><span>REPOSITORY</span><FolderGit2 size={16} /></div><strong className="stat-value">{repoId ? repoFiles.length : "—"} <em>{repoId ? "files" : "No upload"}</em></strong><small>{repoName || "Upload a .zip source project"}</small></div>
            <div className="stat-card"><div className="stat-top"><span>FINDINGS</span><AlertTriangle size={16} /></div><strong className="stat-value">{analysis ? analysis.findings.length : "—"}</strong><small>{analysis ? "AI-generated; verify evidence" : "No review run yet"}</small></div>
            <div className="stat-card"><div className="stat-top"><span>TAVILY RESEARCH</span><FileSearch size={16} /></div><strong className="stat-value">{health?.tavily_configured ? "Configured" : "Optional"}</strong><small>{health?.tavily_configured ? "Research sources enrich reviews and patches" : "Add TAVILY_API_KEY to backend/.env"}</small></div>
          </section>

          {error && <div className="alert alert-error"><AlertTriangle size={18} /><div><b>Something needs attention</b><p>{error}</p></div><button onClick={() => setError("")} aria-label="Dismiss"><X size={16} /></button></div>}
          {notice && <div className="alert alert-success"><CheckCircle2 size={18} /><p>{notice}</p><button onClick={() => setNotice("")} aria-label="Dismiss"><X size={16} /></button></div>}

          {showModels && <section className="panel model-panel">
            <div className="panel-heading"><div><div className="panel-kicker">LIVE CATALOG</div><h2>Token Factory model access</h2></div><button className="icon-button" onClick={() => setShowModels(false)} aria-label="Close"><X size={18} /></button></div>
            {modelError && <div className="alert alert-warn"><CircleHelp size={17} /><p>{modelError}</p></div>}
            <p className="muted">These IDs came from a live API catalog response. Set the exact ID in <code>backend/.env</code> as <code>NEBIUS_MODEL</code>, then restart the backend.</p>
            <div className="model-list">{nemotronModels.map((m) => <div className="model-row" key={m}><span className="model-dot" /><code>{m}</code><button className="button button-secondary button-sm" onClick={() => { navigator.clipboard?.writeText(m); setNotice(`Copied ${m}. Add it to backend/.env and restart the backend.`); }}>Copy ID</button></div>)}</div>
            <small className="muted">{models.length} total models listed by your account.</small>
          </section>}

          <section className="panel setup-panel">
            <div className="panel-heading"><div><div className="panel-kicker">STEP 01 · INPUT</div><h2>Bring a repository</h2><p className="muted">Upload a ZIP of source files. Secrets, dependency folders, and binary files are excluded from model context.</p></div><div className="step-number">01</div></div>
            <div className={`dropzone ${repoId ? "has-repo" : ""}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); void uploadRepo(e.dataTransfer.files?.[0]); }}>
              <input ref={fileInput} type="file" accept=".zip,application/zip" hidden onChange={(e) => void uploadRepo(e.target.files?.[0])} />
              <div className="upload-icon">{repoId ? <Check size={23} /> : <Upload size={23} />}</div>
              <div className="drop-copy"><b>{repoId ? `${repoName}.zip imported` : "Drop your repository ZIP here"}</b><span>{repoId ? `${repoFiles.length} readable source files indexed` : "or browse files · ZIP up to 25 MB"}</span></div>
              <button className="button button-secondary" onClick={() => fileInput.current?.click()} disabled={busy !== ""}><Upload size={15} /> {repoId ? "Replace repository" : "Browse ZIP"}</button>
            </div>
            {repoId && <div className="file-strip"><div className="file-strip-title"><FileCode2 size={15} /> INCLUDED FILES <span>{repoFiles.length}</span></div><div className="file-pills">{repoFiles.slice(0, 7).map((f) => <span key={f.path} title={f.path}><FileCode2 size={12} />{f.path}</span>)}{repoFiles.length > 7 && <span>+{repoFiles.length - 7} more</span>}</div></div>}
          </section>

          <section className="panel task-panel">
            <div className="panel-heading"><div><div className="panel-kicker">STEP 02 · INSTRUCTIONS</div><h2>What should Aether Code investigate?</h2></div><div className="step-number">02</div></div>
            <label className="field-label" htmlFor="task">ENGINEERING TASK</label>
            <textarea id="task" value={task} onChange={(e) => setTask(e.target.value)} maxLength={4000} placeholder="Describe the bug, feature, or code review you need..." />
            <div className="task-footer"><span>{task.length}/4000 characters · Keep requests specific</span><button className="button button-primary" onClick={runAnalysis} disabled={!repoId || !task.trim() || busy !== ""}><Sparkles size={16} /> {busy === "analysis" ? "Reviewing…" : "Analyze repository"} <ArrowRight size={15} /></button></div>
          </section>

          <section className="panel results-panel">
            <div className="panel-heading results-heading"><div><div className="panel-kicker">STEP 03 · RESULTS</div><h2>Engineering results</h2><p className="muted">Findings need human verification. Patches are reviewable proposals.</p></div><div className="results-actions"><button className="button button-secondary" onClick={generatePatch} disabled={!repoId || !task.trim() || busy !== ""}><Code2 size={15} /> {busy === "patch" ? "Working…" : "Generate patch"}</button><button className="button button-secondary" onClick={runTests} disabled={!repoId || busy !== ""}><Play size={15} /> {busy === "tests" ? "Running…" : "Run tests"}</button></div></div>
            <div className="tabs">
              <button className={activeTab === "findings" ? "tab active" : "tab"} onClick={() => setActiveTab("findings")}><AlertTriangle size={15} /> Findings <span>{analysis?.findings.length ?? 0}</span></button>
              <button className={activeTab === "patch" ? "tab active" : "tab"} onClick={() => setActiveTab("patch")}><GitCompareArrows size={15} /> Patch preview</button>
              <button className={activeTab === "tests" ? "tab active" : "tab"} onClick={() => setActiveTab("tests")}><Terminal size={15} /> Test output</button>
            </div>

            {activeTab === "findings" && <div className="results-body">
              {!analysis ? <div className="empty-state"><div className="empty-icon"><FileSearch size={24} /></div><b>No analysis yet</b><p>Upload a repository and run an analysis to see evidence-backed findings here.</p></div> :
                <>
                  <div className="summary-box"><div className="summary-icon"><Sparkles size={17} /></div><div><b>Agent summary</b><p>{analysis.summary || "The review completed without a summary."}</p><small>Model: {analysis.model} · {analysis.included_files.length} files included in context</small></div></div>
                  {analysis.findings.length === 0 ? <div className="empty-state compact"><CheckCircle2 size={25} /><b>No credible findings returned</b><p>This does not prove the repository is bug-free. Review the checks and test output.</p></div> :
                    <div className="findings-list">{analysis.findings.map((f) => <FindingCard key={f.id} finding={f} selected={selectedFindingIds.includes(f.id)} onToggle={() => toggleFinding(f)} />)}</div>}
                  <div className="checks-box"><b>Checks and limitations</b>{analysis.checks.map((c, i) => <p key={i}>• {c}</p>)}</div>
                  {!!analysis.research_sources?.length && <div className="checks-box"><b><FileSearch size={14} /> Tavily research sources</b>{analysis.research_sources.map((source, i) => <p key={source.url || i}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a> — {source.content}</p>)}</div>}
                  <div className="bottom-action"><span>{selectedFindingIds.length} findings selected for patch context</span><button className="button button-primary" onClick={generatePatch} disabled={busy !== ""}><Code2 size={15} /> Generate patch for task <ArrowRight size={15} /></button></div>
                </>}
            </div>}

            {activeTab === "patch" && <div className="results-body">
              {!patch ? <div className="empty-state"><div className="empty-icon"><GitCompareArrows size={24} /></div><b>No patch generated</b><p>Generate a patch after choosing a task. Review the diff before applying it.</p></div> :
                <><div className="summary-box"><div className="summary-icon"><GitCompareArrows size={17} /></div><div><b>Proposed change</b><p>{patch.message}</p><small>Model: {patch.model} · {patch.included_files.length} context files</small></div></div>
                  {!!patch.research_sources?.length && <div className="checks-box"><b><FileSearch size={14} /> Tavily research sources</b>{patch.research_sources.map((source, i) => <p key={source.url || i}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a> — {source.content}</p>)}</div>}
                  {patch.patch ? <><pre className="diff-view">{patch.patch.split("\n").map((line, i) => <div className={line.startsWith("+") && !line.startsWith("+++") ? "diff-add" : line.startsWith("-") && !line.startsWith("---") ? "diff-remove" : line.startsWith("@@") ? "diff-hunk" : ""} key={i}>{line || " "}</div>)}</pre><div className="bottom-action"><span>Generated code is untrusted; test before use.</span><button className="button button-primary" onClick={downloadPatch}><ArrowDownToLine size={15} /> Download .patch</button></div></> : <div className="empty-state compact"><p>{patch.message}</p></div>}
                </>}
            </div>}

            {activeTab === "tests" && <div className="results-body">
              {!testResult ? <div className="empty-state"><div className="empty-icon"><Terminal size={24} /></div><b>No test run yet</b><p>Tests run in Docker with network disabled. Docker must be installed and running.</p><button className="button button-secondary" onClick={runTests} disabled={!repoId || busy !== ""}><Play size={15} /> Run existing tests</button></div> :
                <><div className={`test-status ${testResult.status}`}><div>{testResult.status === "passed" ? <CheckCircle2 /> : testResult.status === "failed" ? <AlertTriangle /> : <Clock3 />}</div><section><b>{testResult.status.toUpperCase()}</b><p>{testResult.message}</p></section><span>{testResult.exit_code === null ? "—" : `Exit ${testResult.exit_code}`}</span></div>
                  <div className="terminal-window"><div className="terminal-bar"><span /><span /><span /><b><Terminal size={13} /> SANDBOX OUTPUT</b></div><pre>{[testResult.stdout, testResult.stderr ? `\n[stderr]\n${testResult.stderr}` : ""].join("") || "No output returned."}</pre></div>
                </>}
            </div>}
          </section>

          <footer className="footer"><span>Aether Code <b>·</b> Local prototype</span><span><ShieldCheck size={13} /> Human review required <b>·</b> Powered by your configured Nebius model</span></footer>
        </div>
      </main>
      {busy && <div className="busy-overlay"><div className="busy-card"><div className="busy-icon-wrap"><LoaderCircle className="spin" size={26} /></div><b>{busyLabel}</b><span>Keep this tab open while the request completes.</span><div className="loading-track" aria-hidden="true"><i /></div><div className="loading-dots" aria-hidden="true"><i /><i /><i /></div></div></div>}
    </div>
  );
}

function FindingCard({ finding, selected, onToggle }: { finding: Finding; selected: boolean; onToggle: () => void }) {
  return (
    <article className="finding-card">
      <div className="finding-top"><span className={`severity ${finding.severity}`}>{finding.severity}</span><span className={`confidence ${finding.confidence}`}>{finding.confidence} confidence</span><label className="select-finding"><input type="checkbox" checked={selected} onChange={onToggle} /> Include</label></div>
      <h3>{finding.title}</h3>
      <div className="finding-location"><FileCode2 size={13} />{finding.file || "File not identified"}{finding.line ? `:${finding.line}` : ""}<span>·</span>{finding.id}</div>
      <p>{finding.problem}</p>
      {finding.evidence && <div className="evidence"><b>Evidence</b><code>{finding.evidence}</code></div>}
      {finding.recommendation && <div className="recommendation"><b>Suggested direction</b><p>{finding.recommendation}</p></div>}
    </article>
  );
}

export default App;
