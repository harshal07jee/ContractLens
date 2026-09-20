"use client";

import { ChangeEvent, FormEvent, useMemo, useRef, useState } from "react";
import { askContract, getSource, uploadContract } from "../lib/api";
import type { ChatAnswer, ContractAnalysis, Evidence, SourceChunk } from "../lib/types";

const nav = ["Dashboard", "Contracts", "Obligations", "Timeline", "AI Assistant"];

function labelDate(value?: string | null) {
  if (!value) return "Not found";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export default function Home() {
  const [contract, setContract] = useState<ContractAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatAnswer[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [source, setSource] = useState<SourceChunk | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const parties = useMemo(() => contract?.overview.parties.map((party) => party.value).join(" × ") || "Upload a contract to begin", [contract]);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading(true); setError(null); setChat([]); setSource(null);
    try { setContract(await uploadContract(file)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to process the contract."); }
    finally { setLoading(false); event.target.value = ""; }
  }

  async function submitQuestion(event: FormEvent) {
    event.preventDefault();
    if (!contract || !question.trim() || chatLoading) return;
    setChatLoading(true);
    try {
      const answer = await askContract(contract.id, question.trim());
      setChat((current) => [...current, answer]);
      setQuestion("");
    }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to answer that question."); }
    finally { setChatLoading(false); }
  }

  async function viewSource(citation: Evidence) {
    if (!contract || !citation.source_id) return;
    try { setSource(await getSource(contract.id, citation.source_id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to open the source."); }
  }

  return <main className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">◒</span><span>ContractLens</span></div>
      <nav>{nav.map((item, index) => <button className={index === 0 ? "nav-item active" : "nav-item"} key={item}><span>{["▦", "▱", "✓", "◷", "✦"][index]}</span>{item}</button>)}</nav>
      <div className="sidebar-bottom"><div className="profile-dot">CL</div><div><strong>Workspace</strong><small>Contract intelligence</small></div></div>
    </aside>
    <section className="content">
      <header className="topbar"><div><p className="eyebrow">CONTRACT INTELLIGENCE</p><h1>Dashboard</h1></div><button className="upload-button" onClick={() => inputRef.current?.click()} disabled={loading}>{loading ? "Analyzing contract…" : "+ Upload contract"}</button><input ref={inputRef} type="file" accept="application/pdf" onChange={handleFile} hidden /></header>
      {error && <div className="error"><span>!</span>{error}<button onClick={() => setError(null)}>Dismiss</button></div>}
      {!contract && !loading && <section className="empty-state"><div className="empty-icon">↥</div><h2>Turn a contract into an action plan.</h2><p>Upload a text-readable PDF to extract key terms, obligations, deadlines, and evidence-backed answers.</p><button className="upload-button" onClick={() => inputRef.current?.click()}>Upload a PDF</button><small>PDF files up to 25 MB · Your contract stays in your workspace</small></section>}
      {loading && <section className="empty-state"><div className="loader" /><h2>Reading the agreement</h2><p>Extracting pages, obligations, dates, and source evidence.</p></section>}
      {contract && <>
        <section className="contract-heading"><div><div className="status"><span /> Processed</div><h2>{contract.filename.replace(/\.pdf$/i, "")}</h2><p>{parties} <b>·</b> {contract.page_count} page{contract.page_count === 1 ? "" : "s"}</p></div><button className="ghost-button" onClick={() => inputRef.current?.click()}>Replace file</button></section>
        <section className="metrics">
          <Metric label="Expires" value={labelDate(contract.overview.expiration_date?.value)} tone="blue" citation={contract.overview.expiration_date?.evidence} onSource={viewSource} />
          <Metric label="Renewal" value={contract.overview.renewal_terms[0]?.value ?? "No renewal term found"} tone="purple" citation={contract.overview.renewal_terms[0]?.evidence} onSource={viewSource} />
          <Metric label="Obligations" value={`${contract.obligations.length} detected`} tone="amber" />
        </section>
        <div className="dashboard-grid">
          <section className="panel overview"><div className="panel-title"><div><p className="eyebrow">AT A GLANCE</p><h3>Key information</h3></div></div><InfoRow label="Parties" value={parties} evidence={contract.overview.parties[0]?.evidence} onSource={viewSource}/><InfoRow label="Payment terms" value={contract.overview.payment_terms[0]?.value ?? "Not found"} evidence={contract.overview.payment_terms[0]?.evidence} onSource={viewSource}/><InfoRow label="Termination" value={contract.overview.termination_terms[0]?.value ?? "Not found"} evidence={contract.overview.termination_terms[0]?.evidence} onSource={viewSource}/></section>
          <section className="panel timeline"><div className="panel-title"><div><p className="eyebrow">KEY DATES</p><h3>Timeline</h3></div><span className="count">{contract.timeline.length}</span></div>{contract.timeline.length ? contract.timeline.slice(0, 4).map((event, index) => <button className="timeline-item" onClick={() => viewSource(event.evidence)} key={`${event.title}-${index}`}><span className={`timeline-dot dot-${index % 3}`} /><div><strong>{event.title}</strong><p>{event.date ? labelDate(event.date) : event.relative_deadline}</p><small>{event.description}</small></div><span className="arrow">›</span></button>) : <p className="muted">No actionable dates found.</p>}</section>
          <section className="panel obligations"><div className="panel-title"><div><p className="eyebrow">RESPONSIBILITIES</p><h3>Upcoming obligations</h3></div><span className="count">{contract.obligations.length}</span></div>{contract.obligations.length ? contract.obligations.slice(0, 4).map((obligation, index) => <button className="obligation" onClick={() => viewSource(obligation.evidence)} key={`${obligation.description}-${index}`}><span className="avatar">{(obligation.party ?? "?").slice(0, 1)}</span><div><strong>{obligation.party ?? "Contract party"}</strong><p>{obligation.description}</p></div><span className="frequency">{obligation.frequency ?? obligation.deadline ?? "View source"}</span></button>) : <p className="muted">No explicit obligations found.</p>}</section>
          <section className="panel assistant"><div className="panel-title"><div><p className="eyebrow">ASK THE CONTRACT</p><h3>AI Assistant</h3></div><span className="sparkle">✦</span></div><div className="chat-history">{chat.length === 0 ? <p className="muted">Try “When does this contract expire?” or “What obligations should I track?”</p> : chat.map((answer, index) => <article className="answer" key={index}><p>{answer.answer}</p>{answer.citations.map((citation, citationIndex) => <button className="citation" onClick={() => viewSource(citation)} key={`${citation.source_id}-${citationIndex}`}>Page {citation.page}{citation.section ? ` · ${citation.section}` : ""} ↗</button>)}</article>)}</div><form onSubmit={submitQuestion}><input value={question} onChange={(event) => setQuestion(event.target.value)} disabled={chatLoading} placeholder="Ask about this contract…" /><button disabled={!question.trim() || chatLoading}>{chatLoading ? "…" : "↑"}</button></form></section>
        </div>
      </>}
    </section>
    {source && <div className="drawer-backdrop" onClick={() => setSource(null)}><aside className="source-drawer" onClick={(event) => event.stopPropagation()}><button className="drawer-close" onClick={() => setSource(null)}>×</button><p className="eyebrow">SOURCE EVIDENCE</p><h3>{source.section ?? "Contract excerpt"}</h3><p className="source-meta">Page {source.page} · Chunk {source.chunk_id}</p><blockquote>{source.text}</blockquote><p className="source-note">This excerpt comes directly from the uploaded contract.</p></aside></div>}
  </main>;
}

function Metric({ label, value, tone, citation, onSource }: { label: string; value: string; tone: string; citation?: Evidence; onSource?: (evidence: Evidence) => void }) {
  return <button className={`metric ${tone}`} onClick={() => citation && onSource?.(citation)}><p>{label}</p><strong>{value}</strong>{citation && <small>View source ›</small>}</button>;
}

function InfoRow({ label, value, evidence, onSource }: { label: string; value: string; evidence?: Evidence; onSource: (evidence: Evidence) => void }) {
  return <button className="info-row" onClick={() => evidence && onSource(evidence)}><span>{label}</span><strong>{value}</strong>{evidence && <i>Page {evidence.page} ›</i>}</button>;
}
