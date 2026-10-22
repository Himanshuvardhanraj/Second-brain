import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "";
const TOKEN_KEY = "second_brain_token";

async function api(path, options = {}, token = localStorage.getItem(TOKEN_KEY)) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
  } catch {
    throw new Error("The backend is temporarily unavailable. Please try again.");
  }

  async function streamChat(question, token, onEvent) {
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
    let response;
    try {
      response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST", headers, credentials: "include",
        body: JSON.stringify({ question, top_k: 8 }),
      });
    } catch {
      throw new Error("The backend is temporarily unavailable. Please try again.");
    }
    if (!response.ok || !response.body) throw new Error("The answer could not be generated. Please try again later.");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";
      for (const event of events) {
        const line = event.split("\n").find((part) => part.startsWith("data: "));
        if (line) onEvent(JSON.parse(line.slice(6)));
      }
      if (done) break;
    }
  }
  const text = await response.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
  if (!response.ok) {
    const detail = typeof data.detail === "object" ? data.detail.message : data.detail;
    throw new Error(detail || "Something went wrong. Please try again.");
  }
  return data;
}

function Login({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
      window.history.replaceState({}, "", "/");
      onAuthenticated(token);
    }
  }, [onAuthenticated]);

  const continueAsGuest = async () => {
    setBusy(true); setError("");
    try {
      const data = await api("/api/auth/guest", { method: "POST" }, null);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      onAuthenticated(data.access_token);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const submitCredentials = async (event) => {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/signup";
      const data = await api(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name: mode === "signup" ? name : undefined }),
      }, null);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      onAuthenticated(data.access_token);
    } catch (err) { setError(err.message); setBusy(false); }
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="brand brand--dark"><span className="brand-mark">⌘</span><span className="brand-name">Second Brain</span></div>
        <p className="eyebrow">PERSONAL KNOWLEDGE, ORGANIZED</p>
        <h1>Your notes, in conversation.</h1>
        <p className="login-copy">Create a free account to keep your saved chats across devices. Supabase Auth securely manages your credentials.</p>
        <div className="auth-tabs">
          <button className={mode === "login" ? "auth-tab auth-tab--active" : "auth-tab"} onClick={() => { setMode("login"); setError(""); }}>Log in</button>
          <button className={mode === "signup" ? "auth-tab auth-tab--active" : "auth-tab"} onClick={() => { setMode("signup"); setError(""); }}>Sign up</button>
        </div>
        <form onSubmit={submitCredentials} className="auth-form">
          {mode === "signup" && <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Display name" maxLength={100} />}
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email address" maxLength={254} required />
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password (8+ characters)" minLength={8} maxLength={128} required />
          <button className="google-button" type="submit" disabled={busy}>{mode === "login" ? "Log in" : "Create account"}</button>
        </form>
        <button className="guest-button" onClick={continueAsGuest} disabled={busy}>Skip for now</button>
        {error && <p className="form-error">{error}</p>}
      </section>
    </main>
  );
}

function SourceList({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources?.length) return null;
  return <div className="sources">
    <button className="sources-toggle" onClick={() => setOpen((value) => !value)}>{open ? "⌄" : "›"} {sources.length} source{sources.length !== 1 ? "s" : ""}</button>
    {open && <ol className="sources-list">{sources.map((source, index) => <li key={index}><span className="source-num">{index + 1}</span><span className="source-name">{source.source?.split("/").pop() || "unknown"}</span><span className="source-meta">p.{source.page} · {Number(source.score || 0).toFixed(3)}</span></li>)}</ol>}
  </div>;
}

function AdminPanel({ token, onNotice }) {
  const [tab, setTab] = useState("logs");
  const [logs, setLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async (nextTab = tab) => {
    setLoading(true);
    try {
      const data = await api(nextTab === "logs" ? "/admin/search-logs" : "/admin/users", {}, token);
      if (nextTab === "logs") setLogs(data.logs || []);
      else setUsers(data.users || []);
    } catch (err) { onNotice(err.message); } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [tab]);

  const removeUser = async (item) => {
    const confirmation = window.prompt(`Type ${item.email} to permanently delete this user and all data.`);
    if (confirmation !== item.email) return;
    try {
      await api(`/admin/users/${item.id}?confirm_email=${encodeURIComponent(item.email)}${item.role === "admin" ? "&confirm_admin=true" : ""}`, { method: "DELETE" }, token);
      setUsers((current) => current.filter((user) => user.id !== item.id));
      onNotice("User and associated data deleted.");
    } catch (err) { onNotice(err.message); }
  };

  return <div className="notes-page admin-page">
    <p className="eyebrow">ADMINISTRATION</p><h1>Admin console</h1>
    <div className="admin-tabs"><button className={tab === "logs" ? "admin-tab admin-tab--active" : "admin-tab"} onClick={() => setTab("logs")}>Search Logs</button><button className={tab === "users" ? "admin-tab admin-tab--active" : "admin-tab"} onClick={() => setTab("users")}>Users</button></div>
    {loading ? <p className="empty-sub">Loading…</p> : tab === "logs" ? <div className="admin-table">{logs.length === 0 ? <p className="empty-sub">No search logs yet.</p> : logs.map((log) => <article className="admin-row" key={log.id}><strong>{log.query_text}</strong><small>{log.user_id || "Guest"} · {new Date(log.created_at).toLocaleString()} · {log.latency_ms ?? "—"} ms</small></article>)}</div> : <div className="admin-table">{users.map((item) => <article className="admin-row" key={item.id}><div><strong>{item.email || item.id}</strong><small>{item.role}</small></div><button className="document-delete" onClick={() => removeUser(item)}>Delete</button></article>)}</div>}
    <p className="admin-retention">Search queries are logged for service improvement and retained for 30 days.</p>
  </div>;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [notes, setNotes] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [showNotes, setShowNotes] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const loadAccount = async (activeToken) => {
    try {
      const [account, saved, library] = await Promise.all([api("/api/auth/me", {}, activeToken), api("/api/notes", {}, activeToken), api("/api/documents", {}, activeToken)]);
      setUser(account.user); setNotes(saved.notes || []); setDocuments(library.documents || []);
    } catch {
      try {
        const renewed = await api("/api/auth/refresh", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }, null);
        localStorage.setItem(TOKEN_KEY, renewed.access_token);
        setToken(renewed.access_token);
      } catch {
        localStorage.removeItem(TOKEN_KEY); setToken(null);
      }
    }
  };

  useEffect(() => { if (token) loadAccount(token); }, [token]);
  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages, loading]);

  if (!token) return <Login onAuthenticated={setToken} />;

  const signOut = () => {
    api("/api/auth/logout", { method: "POST" }, token).catch(() => {});
    localStorage.removeItem(TOKEN_KEY); setToken(null);
  };
  const saveChat = async (messageIndex) => {
    const answer = messages[messageIndex];
    const previous = messages[messageIndex - 1];
    if (answer.saved) return;
    const question = previous?.text || "Saved conversation";
    const alreadySaved = notes.some((note) => note.question === question && note.answer === answer.text);
    if (alreadySaved) {
      setMessages((current) => current.map((message, index) => index === messageIndex ? { ...message, saved: true } : message));
      setNotice("This chat is already in Notes.");
      return;
    }
    try {
      const data = await api("/api/notes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, answer: answer.text, sources: answer.sources || [] }) }, token);
      setNotes((current) => data.already_saved ? current : [data.note, ...current]); setMessages((current) => current.map((message, index) => index === messageIndex ? { ...message, saved: true } : message)); setNotice(data.already_saved ? "This chat is already in Notes." : "Saved to Notes");
    } catch (err) { setNotice(err.message); }
  };

  const deleteDocument = async (documentId) => {
    try {
      await api(`/api/documents/${documentId}`, { method: "DELETE" }, token);
      setDocuments((current) => current.filter((document) => document.id !== documentId));
      setNotice("Document deleted.");
    } catch (err) { setNotice(err.message); }
  };

  const rateAnswer = async (messageIndex, rating) => {
    const answer = messages[messageIndex];
    const previous = messages[messageIndex - 1];
    try {
      await api("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: previous?.text || "Saved conversation", answer: answer.text, rating, sources: answer.sources || [] }),
      }, token);
      setMessages((current) => current.map((message, index) => index === messageIndex ? { ...message, rating } : message));
      setNotice("Thanks - your rating was saved.");
    } catch (err) { setNotice(err.message); }
  };

  const uploadPDF = async (file) => {
    if (!file) return;
    if (file.type !== "application/pdf") { setNotice("Please select a PDF file."); return; }
    setUploading(true); setNotice("");
    try {
      const form = new FormData(); form.append("file", file);
      const data = await api("/api/documents/upload", { method: "POST", body: form }, token);
      setDocuments((current) => [{ id: data.document_id, filename: data.filename, file_size: file.size, created_at: new Date().toISOString() }, ...current]);
      setNotice(`${data.filename} indexed — ${data.chunks_created} chunks ready.`);
    } catch (err) { setNotice(err.message); } finally { setUploading(false); }
  };

  const askQuestion = async () => {
    const text = question.trim(); if (!text || loading) return;
    setMessages((current) => [...current, { role: "user", text }]); setQuestion(""); setLoading(true); setNotice("");
    try {
      let assistantIndex = null;
      await streamChat(text, token, (event) => {
        if (event.type === "error") throw new Error(event.message);
        if (event.type === "token") {
          setMessages((current) => {
            if (assistantIndex === null) {
              assistantIndex = current.length;
              return [...current, { role: "assistant", text: event.text, sources: [], saved: false }];
            }
            return current.map((message, index) => index === assistantIndex ? { ...message, text: message.text + event.text } : message);
          });
        }
        if (event.type === "complete") {
          setMessages((current) => current.map((message, index) => index === assistantIndex ? { ...message, sources: event.sources || [] } : message));
        }
      });
    } catch (err) { setMessages((current) => [...current, { role: "assistant", text: err.message, sources: [], error: true }]); setNotice(err.message); }
    finally { setLoading(false); inputRef.current?.focus(); }
  };

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">⌘</span><span className="brand-name">Second Brain</span></div>
      <nav className="nav">
        <div className={`nav-item ${!showNotes && !showLibrary && !showAdmin ? "nav-item--active" : ""}`} onClick={() => { setShowNotes(false); setShowLibrary(false); setShowAdmin(false); }}>Chat</div>
        <label className="upload-card"><span className="upload-icon">↑</span><span><strong>{uploading ? "Indexing PDF…" : "Upload a PDF"}</strong><small>Private to your account</small></span><input type="file" accept="application/pdf" hidden disabled={uploading} onChange={(event) => { uploadPDF(event.target.files?.[0]); event.target.value = ""; }} /></label>
        <div className={`nav-item notes-link ${showLibrary ? "nav-item--active" : ""}`} onClick={() => { setShowLibrary(true); setShowNotes(false); }}>Library <span>{documents.length}</span></div>
        <div className={`nav-item notes-link ${showNotes ? "nav-item--active" : ""}`} onClick={() => { setShowNotes(true); setShowLibrary(false); }}>Notes <span>{notes.length}</span></div>
        {user?.role === "admin" && <div className={`nav-item ${showAdmin ? "nav-item--active" : ""}`} onClick={() => { setShowAdmin(true); setShowNotes(false); setShowLibrary(false); }}>Admin</div>}
      </nav>
      <div className="account"><div className="avatar">{(user?.name || "G").charAt(0).toUpperCase()}</div><div><strong>{user?.name || "Guest"}</strong><small>{user?.is_guest ? "Guest session" : user?.email}</small></div><button onClick={signOut} title="Sign out">↗</button></div>
    </aside>
    <main className="stage">
      <header className="topbar"><span className="welcome">Hey, {user?.name || "there"}</span><span className="topbar-note">Your private knowledge space</span></header>
      <div className="scroll" ref={scrollRef}>
        {showAdmin ? <AdminPanel token={token} onNotice={setNotice} /> : showLibrary ? <div className="notes-page"><p className="eyebrow">YOUR PRIVATE DOCUMENTS</p><h1>Document library</h1><p className="empty-sub">Only PDFs uploaded from this account appear here.</p>{documents.length === 0 ? <div className="library-empty"><span>＋</span><strong>No PDFs yet</strong><small>Use “Upload a PDF” to add your first document.</small></div> : <div className="document-list">{documents.map((document) => <article className="document-item" key={document.id}><div className="document-icon">PDF</div><div className="document-info"><strong>{document.filename}</strong><small>{document.file_size ? `${(document.file_size / 1024 / 1024).toFixed(2)} MB` : "PDF"} · {document.created_at ? new Date(document.created_at).toLocaleDateString() : "Recently added"}</small></div><button className="document-delete" onClick={() => deleteDocument(document.id)} aria-label={`Delete ${document.filename}`}>Delete</button></article>)}</div>}</div> : showNotes ? <div className="notes-page"><p className="eyebrow">YOUR SAVED KNOWLEDGE</p><h1>Notes</h1>{notes.length === 0 ? <p className="empty-sub">Saved chats will appear here when you wishlist an answer.</p> : notes.map((note) => <article className="note-item" key={note.id}><div className="note-question">{note.question}</div><div className="note-answer"><ReactMarkdown>{note.answer}</ReactMarkdown></div><div className="note-date">{new Date(note.created_at).toLocaleString()}</div></article>)}</div> : <>
        {messages.length === 0 && <div className="empty"><p className="empty-title">Ask your notes something.</p><p className="empty-sub">Answers are grounded in what you've actually written — with sources, every time.</p></div>}
        {messages.map((message, index) => <div key={index} className={`row row--${message.role}`}>{message.role === "user" ? <div className="bubble--user">{message.text}</div> : <div className={`card ${message.error ? "card--error" : ""}`}><div className="card-body"><ReactMarkdown>{message.text}</ReactMarkdown></div><div className="card-actions"><SourceList sources={message.sources} />{!message.error && <><div className="rating" aria-label="Rate answer">{[1, 2, 3, 4, 5].map((value) => <button key={value} className={value <= (message.rating || 0) ? "rating--selected" : ""} onClick={() => rateAnswer(index, value)} aria-label={`${value} out of 5`}>★</button>)}</div><button className={`wishlist ${message.saved ? "wishlist--saved" : ""}`} onClick={() => saveChat(index)}>{message.saved ? "♥ Saved in Notes" : "♡ Save to Notes"}</button></>}</div></div>}</div>)}
        {loading && <div className="row row--assistant"><div className="card card--pending"><div className="thinking"><span /><span /><span /></div></div></div>}
        </>}
      </div>
      {notice && <div className="notice">{notice}</div>}
      {!showNotes && <div className="composer"><textarea ref={inputRef} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); askQuestion(); } }} placeholder={`Ask anything, ${user?.name || "there"}…`} rows={1} /><button onClick={askQuestion} disabled={loading || !question.trim()} aria-label="Send">→</button></div>}
    </main>
  </div>;
}

export default App;
