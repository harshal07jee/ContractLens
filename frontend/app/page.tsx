"use client";

import { ChangeEvent, FormEvent, useMemo, useRef, useState } from "react";
import { askContract, getSource, uploadContract } from "../lib/api";
import type { ChatAnswer, ContractAnalysis, Evidence, SourceChunk } from "../lib/types";

const nav = ["Dashboard", "Contracts", "Obligations", "Timeline", "AI Assistant"];

const samplePrompts = [
  "When does this contract expire?",
  "What obligations should I track?",
  "Who are the parties to this agreement?",
  "What are the payment terms?",
  "How can the contract be terminated?",
  "What is the renewal policy?",
];

type ChatEntry = {
  question: string;
  answer: ChatAnswer;
};

function labelDate(value?: string | null) {
  if (!value) return "Not found";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("Dashboard");
  const [contract, setContract] = useState<ContractAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [source, setSource] = useState<SourceChunk | null>(null);
  const [obligationFilter, setObligationFilter] = useState<string>("All");
  const inputRef = useRef<HTMLInputElement>(null);

  const parties = useMemo(
    () => contract?.overview.parties.map((party) => party.value).join(" × ") || "Upload a contract to begin",
    [contract]
  );

  const uniqueParties = useMemo(() => {
    if (!contract) return ["All"];
    const set = new Set<string>();
    contract.obligations.forEach((o) => {
      if (o.party) set.add(o.party);
    });
    return ["All", ...Array.from(set)];
  }, [contract]);

  const filteredObligations = useMemo(() => {
    if (!contract) return [];
    if (obligationFilter === "All") return contract.obligations;
    return contract.obligations.filter((o) => o.party === obligationFilter);
  }, [contract, obligationFilter]);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    setChat([]);
    setSource(null);
    try {
      const res = await uploadContract(file);
      setContract(res);
      setActiveTab("Dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to process the contract.");
    } finally {
      setLoading(false);
      event.target.value = "";
    }
  }

  async function sendQuestion(text: string) {
    const q = text.trim();
    if (!contract || !q || chatLoading) return;
    setChatLoading(true);
    try {
      const answer = await askContract(contract.id, q);
      setChat((current) => [...current, { question: q, answer }]);
      setQuestion("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to answer that question.");
    } finally {
      setChatLoading(false);
    }
  }

  async function submitQuestion(event: FormEvent) {
    event.preventDefault();
    await sendQuestion(question);
  }

  async function viewSource(citation: Evidence) {
    if (!contract || !citation.source_id) return;
    try {
      setSource(await getSource(contract.id, citation.source_id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to open the source.");
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">◒</span>
          <span>ContractLens</span>
        </div>
        <nav>
          {nav.map((item, index) => (
            <button
              className={activeTab === item ? "nav-item active" : "nav-item"}
              key={item}
              onClick={() => setActiveTab(item)}
            >
              <span>{["▦", "▱", "✓", "◷", "✦"][index]}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-dot">CL</div>
          <div>
            <strong>Workspace</strong>
            <small>Contract intelligence</small>
          </div>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">CONTRACT INTELLIGENCE</p>
            <h1>{activeTab}</h1>
          </div>
          <button className="upload-button" onClick={() => inputRef.current?.click()} disabled={loading}>
            {loading ? "Analyzing contract…" : "+ Upload contract"}
          </button>
          <input ref={inputRef} type="file" accept="application/pdf" onChange={handleFile} hidden />
        </header>

        {error && (
          <div className="error">
            <span>!</span>
            {error}
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {!contract && !loading && (
          <section className="empty-state">
            <div className="empty-icon">↥</div>
            <h2>Turn a contract into an action plan.</h2>
            <p>Upload a text-readable PDF to extract key terms, obligations, deadlines, and evidence-backed answers.</p>
            <button className="upload-button" onClick={() => inputRef.current?.click()}>
              Upload a PDF
            </button>
            <small>PDF files up to 25 MB · Your contract stays in your workspace</small>
          </section>
        )}

        {loading && (
          <section className="empty-state">
            <div className="loader" />
            <h2>Reading the agreement</h2>
            <p>Extracting pages, obligations, dates, and source evidence.</p>
          </section>
        )}

        {contract && (
          <>
            <section className="contract-heading">
              <div>
                <div className="status">
                  <span /> Processed
                </div>
                <h2>{contract.filename.replace(/\.pdf$/i, "")}</h2>
                <p>
                  {parties} <b>·</b> {contract.page_count} page{contract.page_count === 1 ? "" : "s"}
                </p>
              </div>
              <button className="ghost-button" onClick={() => inputRef.current?.click()}>
                Replace file
              </button>
            </section>

            {/* View 1: DASHBOARD */}
            {activeTab === "Dashboard" && (
              <>
                <section className="metrics">
                  <Metric
                    label="Expires"
                    value={labelDate(contract.overview.expiration_date?.value)}
                    tone="blue"
                    citation={contract.overview.expiration_date?.evidence}
                    onSource={viewSource}
                  />
                  <Metric
                    label="Renewal"
                    value={contract.overview.renewal_terms[0]?.value ?? "No renewal term found"}
                    tone="purple"
                    citation={contract.overview.renewal_terms[0]?.evidence}
                    onSource={viewSource}
                  />
                  <Metric
                    label="Obligations"
                    value={`${contract.obligations.length} detected`}
                    tone="amber"
                    onClick={() => setActiveTab("Obligations")}
                  />
                </section>
                <div className="dashboard-grid">
                  <section className="panel overview">
                    <div className="panel-title">
                      <div>
                        <p className="eyebrow">AT A GLANCE</p>
                        <h3>Key information</h3>
                      </div>
                      <button className="ghost-button" onClick={() => setActiveTab("Contracts")}>
                        View all ›
                      </button>
                    </div>
                    <InfoRow label="Parties" value={parties} evidence={contract.overview.parties[0]?.evidence} onSource={viewSource} />
                    <InfoRow label="Payment terms" value={contract.overview.payment_terms[0]?.value ?? "Not found"} evidence={contract.overview.payment_terms[0]?.evidence} onSource={viewSource} />
                    <InfoRow label="Termination" value={contract.overview.termination_terms[0]?.value ?? "Not found"} evidence={contract.overview.termination_terms[0]?.evidence} onSource={viewSource} />
                  </section>

                  <section className="panel timeline">
                    <div className="panel-title">
                      <div>
                        <p className="eyebrow">KEY DATES</p>
                        <h3>Timeline</h3>
                      </div>
                      <button className="count" onClick={() => setActiveTab("Timeline")}>
                        {contract.timeline.length} ›
                      </button>
                    </div>
                    {contract.timeline.length ? (
                      contract.timeline.slice(0, 4).map((event, index) => (
                        <button className="timeline-item" onClick={() => viewSource(event.evidence)} key={`${event.title}-${index}`}>
                          <span className={`timeline-dot dot-${index % 3}`} />
                          <div>
                            <strong>{event.title}</strong>
                            <p>{event.date ? labelDate(event.date) : event.relative_deadline}</p>
                            <small>{event.description}</small>
                          </div>
                          <span className="arrow">›</span>
                        </button>
                      ))
                    ) : (
                      <p className="muted">No actionable dates found.</p>
                    )}
                  </section>

                  <section className="panel obligations">
                    <div className="panel-title">
                      <div>
                        <p className="eyebrow">RESPONSIBILITIES</p>
                        <h3>Upcoming obligations</h3>
                      </div>
                      <button className="count" onClick={() => setActiveTab("Obligations")}>
                        {contract.obligations.length} ›
                      </button>
                    </div>
                    {contract.obligations.length ? (
                      contract.obligations.slice(0, 4).map((obligation, index) => (
                        <button className="obligation" onClick={() => viewSource(obligation.evidence)} key={`${obligation.description}-${index}`}>
                          <span className="avatar">{(obligation.party ?? "?").slice(0, 1)}</span>
                          <div>
                            <strong>{obligation.party ?? "Contract party"}</strong>
                            <p>{obligation.description}</p>
                          </div>
                          <span className="frequency">{obligation.frequency ?? obligation.deadline ?? "View source"}</span>
                        </button>
                      ))
                    ) : (
                      <p className="muted">No explicit obligations found.</p>
                    )}
                  </section>

                  <section className="panel assistant">
                    <div className="panel-title">
                      <div>
                        <p className="eyebrow">ASK THE CONTRACT</p>
                        <h3>AI Assistant</h3>
                      </div>
                      <button className="ghost-button" onClick={() => setActiveTab("AI Assistant")}>
                        Expand ✦
                      </button>
                    </div>
                    <div className="chat-history">
                      {chat.length === 0 ? (
                        <div>
                          <p className="muted">Try asking a question or choose a prompt:</p>
                          <div className="suggestion-chips">
                            {samplePrompts.slice(0, 3).map((prompt) => (
                              <button className="chip" key={prompt} onClick={() => sendQuestion(prompt)}>
                                {prompt}
                              </button>
                            ))}
                          </div>
                        </div>
                      ) : (
                        chat.map((item, index) => (
                          <div key={index} style={{ marginBottom: 12 }}>
                            <div className="chat-q">Q: {item.question}</div>
                            <article className="answer">
                              <p>{item.answer.answer}</p>
                              {item.answer.citations.map((citation, citationIndex) => (
                                <button className="citation" onClick={() => viewSource(citation)} key={`${citation.source_id}-${citationIndex}`}>
                                  Page {citation.page}
                                  {citation.section ? ` · ${citation.section}` : ""} ↗
                                </button>
                              ))}
                            </article>
                          </div>
                        ))
                      )}
                    </div>
                    <form onSubmit={submitQuestion}>
                      <input
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        disabled={chatLoading}
                        placeholder="Ask about this contract…"
                      />
                      <button disabled={!question.trim() || chatLoading}>{chatLoading ? "…" : "↑"}</button>
                    </form>
                  </section>
                </div>
              </>
            )}

            {/* View 2: CONTRACTS (Full Terms & Provisions) */}
            {activeTab === "Contracts" && (
              <section className="full-panel">
                <div className="panel-title">
                  <div>
                    <p className="eyebrow">CONTRACT STRUCTURE</p>
                    <h3>Key Terms and Provisions</h3>
                  </div>
                </div>
                <InfoRow label="Parties" value={parties} evidence={contract.overview.parties[0]?.evidence} onSource={viewSource} />
                <InfoRow
                  label="Effective date"
                  value={labelDate(contract.overview.effective_date?.value)}
                  evidence={contract.overview.effective_date?.evidence}
                  onSource={viewSource}
                />
                <InfoRow
                  label="Expiration date"
                  value={labelDate(contract.overview.expiration_date?.value)}
                  evidence={contract.overview.expiration_date?.evidence}
                  onSource={viewSource}
                />

                <h4 style={{ margin: "24px 0 10px", fontSize: 14 }}>Payment Terms</h4>
                {contract.overview.payment_terms.map((term, i) => (
                  <InfoRow label={`Term ${i + 1}`} value={term.value} evidence={term.evidence} onSource={viewSource} key={i} />
                ))}

                <h4 style={{ margin: "24px 0 10px", fontSize: 14 }}>Renewal Terms</h4>
                {contract.overview.renewal_terms.map((term, i) => (
                  <InfoRow label={`Term ${i + 1}`} value={term.value} evidence={term.evidence} onSource={viewSource} key={i} />
                ))}

                <h4 style={{ margin: "24px 0 10px", fontSize: 14 }}>Termination Terms</h4>
                {contract.overview.termination_terms.map((term, i) => (
                  <InfoRow label={`Clause ${i + 1}`} value={term.value} evidence={term.evidence} onSource={viewSource} key={i} />
                ))}

                <h4 style={{ margin: "24px 0 10px", fontSize: 14 }}>Important Terms & Protections</h4>
                {contract.overview.important_terms.map((term, i) => (
                  <InfoRow label={`Clause ${i + 1}`} value={term.value} evidence={term.evidence} onSource={viewSource} key={i} />
                ))}
              </section>
            )}

            {/* View 3: OBLIGATIONS (Full List with Filters) */}
            {activeTab === "Obligations" && (
              <section className="full-panel">
                <div className="panel-title">
                  <div>
                    <p className="eyebrow">RESPONSIBILITIES</p>
                    <h3>All Obligations ({filteredObligations.length})</h3>
                  </div>
                  <span className="count">{contract.obligations.length} total</span>
                </div>

                <div className="filter-pills">
                  {uniqueParties.map((p) => (
                    <button
                      className={obligationFilter === p ? "pill active" : "pill"}
                      key={p}
                      onClick={() => setObligationFilter(p)}
                    >
                      {p}
                    </button>
                  ))}
                </div>

                {filteredObligations.length ? (
                  filteredObligations.map((obligation, index) => (
                    <button className="obligation" onClick={() => viewSource(obligation.evidence)} key={`${obligation.description}-${index}`}>
                      <span className="avatar">{(obligation.party ?? "?").slice(0, 1)}</span>
                      <div>
                        <strong>{obligation.party ?? "Contract party"}</strong>
                        <p>{obligation.description}</p>
                      </div>
                      <span className="frequency">{obligation.frequency ?? obligation.deadline ?? "View source ›"}</span>
                    </button>
                  ))
                ) : (
                  <p className="muted">No obligations found matching this filter.</p>
                )}
              </section>
            )}

            {/* View 4: TIMELINE (Full Chronological Events) */}
            {activeTab === "Timeline" && (
              <section className="full-panel">
                <div className="panel-title">
                  <div>
                    <p className="eyebrow">CHRONOLOGICAL SCHEDULE</p>
                    <h3>Contract Timeline ({contract.timeline.length})</h3>
                  </div>
                  <span className="count">{contract.timeline.length} events</span>
                </div>

                {contract.timeline.map((event, index) => (
                  <button className="timeline-item" onClick={() => viewSource(event.evidence)} key={`${event.title}-${index}`}>
                    <span className={`timeline-dot dot-${index % 3}`} />
                    <div>
                      <strong>{event.title}</strong>
                      <p>{event.date ? labelDate(event.date) : event.relative_deadline}</p>
                      <small>{event.description}</small>
                    </div>
                    <span className="arrow">›</span>
                  </button>
                ))}
              </section>
            )}

            {/* View 5: AI ASSISTANT (Expanded Interactive View) */}
            {activeTab === "AI Assistant" && (
              <section className="full-panel">
                <div className="panel-title">
                  <div>
                    <p className="eyebrow">CONTRACT COPILOT</p>
                    <h3>AI Assistant</h3>
                  </div>
                  <span className="sparkle">✦ Grounded Answers</span>
                </div>

                <p className="muted" style={{ marginBottom: 12 }}>
                  Ask questions to get answers cited directly from the contract chunks.
                </p>

                <div className="suggestion-chips">
                  {samplePrompts.map((prompt) => (
                    <button className="chip" key={prompt} onClick={() => sendQuestion(prompt)}>
                      {prompt}
                    </button>
                  ))}
                </div>

                <div className="chat-history" style={{ minHeight: 280, maxHeight: 480 }}>
                  {chat.length === 0 ? (
                    <p className="muted" style={{ textAlign: "center", padding: "40px 0" }}>
                      No messages yet. Click any suggestion above or type your question below.
                    </p>
                  ) : (
                    chat.map((item, index) => (
                      <div key={index} style={{ marginBottom: 18 }}>
                        <div className="chat-q">Q: {item.question}</div>
                        <article className="answer">
                          <p>{item.answer.answer}</p>
                          <div style={{ marginTop: 8 }}>
                            {item.answer.citations.map((citation, citationIndex) => (
                              <button className="citation" onClick={() => viewSource(citation)} key={`${citation.source_id}-${citationIndex}`}>
                                Page {citation.page}
                                {citation.section ? ` · ${citation.section}` : ""} ↗
                              </button>
                            ))}
                          </div>
                        </article>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={submitQuestion} style={{ display: "flex", gap: 8, marginTop: 16 }}>
                  <input
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    disabled={chatLoading}
                    placeholder="Ask about this contract…"
                    style={{
                      flex: 1,
                      border: "1px solid #dce3ed",
                      borderRadius: 8,
                      padding: "12px 14px",
                      font: "500 13px Manrope",
                    }}
                  />
                  <button
                    disabled={!question.trim() || chatLoading}
                    style={{
                      padding: "0 22px",
                      border: 0,
                      borderRadius: 8,
                      background: "var(--navy)",
                      color: "white",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    {chatLoading ? "Asking…" : "Ask"}
                  </button>
                </form>
              </section>
            )}
          </>
        )}
      </section>

      {source && (
        <div className="drawer-backdrop" onClick={() => setSource(null)}>
          <aside className="source-drawer" onClick={(event) => event.stopPropagation()}>
            <button className="drawer-close" onClick={() => setSource(null)}>
              ×
            </button>
            <p className="eyebrow">SOURCE EVIDENCE</p>
            <h3>{source.section ?? "Contract excerpt"}</h3>
            <p className="source-meta">
              Page {source.page} · Chunk {source.chunk_id}
            </p>
            <blockquote>{source.text}</blockquote>
            <p className="source-note">This excerpt comes directly from the uploaded contract.</p>
          </aside>
        </div>
      )}
    </main>
  );
}

function Metric({
  label,
  value,
  tone,
  citation,
  onSource,
  onClick,
}: {
  label: string;
  value: string;
  tone: string;
  citation?: Evidence;
  onSource?: (evidence: Evidence) => void;
  onClick?: () => void;
}) {
  return (
    <button
      className={`metric ${tone}`}
      onClick={() => {
        if (citation && onSource) {
          onSource(citation);
        } else if (onClick) {
          onClick();
        }
      }}
    >
      <p>{label}</p>
      <strong>{value}</strong>
      {citation ? <small>View source ›</small> : onClick ? <small>View details ›</small> : null}
    </button>
  );
}

function InfoRow({
  label,
  value,
  evidence,
  onSource,
}: {
  label: string;
  value: string;
  evidence?: Evidence;
  onSource: (evidence: Evidence) => void;
}) {
  return (
    <button className="info-row" onClick={() => evidence && onSource(evidence)}>
      <span>{label}</span>
      <strong>{value}</strong>
      {evidence && <i>Page {evidence.page} ›</i>}
    </button>
  );
}
