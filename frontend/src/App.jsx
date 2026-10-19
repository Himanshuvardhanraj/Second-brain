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
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error("The backend is temporarily unavailable. Please try again.");
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
  const [userId, setUserId] = useState("");
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
        body: JSON.stringify({ user_id: userId, password, name: mode === "signup" ? name : undefined }),
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
        <p className="login-copy">Create a free account to keep your saved chats across devices. Passwords are stored as secure hashes in Supabase, never as plain text.</p>
        <div className="auth-tabs">
          <button className={mode === "login" ? "auth-tab auth-tab--active" : "auth-tab"} onClick={() => { setMode("login"); setError(""); }}>Log in</button>
          <button className={mode === "signup" ? "auth-tab auth-tab--active" : "auth-tab"} onClick={() => { setMode("signup"); setError(""); }}>Sign up</button>
        </div>
        <form onSubmit={submitCredentials} className="auth-form">
          {mode === "signup" && <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Display name" maxLength={100} />}
          <input value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="User ID" minLength={3} maxLength={80} required />
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

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [notes, setNotes] = useState([]);
  const [showNotes, setShowNotes] = useState(false);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const loadAccount = async (activeToken) => {
    try {
      const [account, saved] = await Promise.all([api("/api/auth/me", {}, activeToken), api("/api/notes", {}, activeToken)]);
      setUser(account.user); setNotes(saved.notes || []);
    } catch { localStorage.removeItem(TOKEN_KEY); setToken(null); }
  };

  useEffect(() => { if (token) loadAccount(token); }, [token]);
  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages, loading]);

  if (!token) return <Login onAuthenticated={setToken} />;

  const signOut = () => { localStorage.removeItem(TOKEN_KEY); setToken(null); };
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
      setNotice(`${data.filename} indexed — ${data.chunks_created} chunks ready.`);
    } catch (err) { setNotice(err.message); } finally { setUploading(false); }
  };

  const askQuestion = async () => {
    const text = question.trim(); if (!text || loading) return;
    setMessages((current) => [...current, { role: "user", text }]); setQuestion(""); setLoading(true); setNotice("");
    try {
      const data = await api("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: text, top_k: 8 }) }, token);
      setMessages((current) => [...current, { role: "assistant", text: data.answer, sources: data.sources || [], saved: false }]);
    } catch (err) { setMessages((current) => [...current, { role: "assistant", text: err.message, sources: [], error: true }]); setNotice(err.message); }
    finally { setLoading(false); inputRef.current?.focus(); }
  };

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">⌘</span><span className="brand-name">Second Brain</span></div>
      <nav className="nav">
        <div className={`nav-item ${!showNotes ? "nav-item--active" : ""}`} onClick={() => setShowNotes(false)}>Chat</div>
        <label className="nav-item upload-item">{uploading ? "Indexing…" : "Upload PDF"}<input type="file" accept="application/pdf" hidden disabled={uploading} onChange={(event) => { uploadPDF(event.target.files?.[0]); event.target.value = ""; }} /></label>
        <div className={`nav-item notes-link ${showNotes ? "nav-item--active" : ""}`} onClick={() => setShowNotes(true)}>Notes <span>{notes.length}</span></div>
      </nav>
      <div className="account"><div className="avatar">{(user?.name || "G").charAt(0).toUpperCase()}</div><div><strong>{user?.name || "Guest"}</strong><small>{user?.is_guest ? "Guest session" : user?.email}</small></div><button onClick={signOut} title="Sign out">↗</button></div>
    </aside>
    <main className="stage">
      <header className="topbar"><span className="welcome">Hey, {user?.name || "there"}</span><span className="topbar-note">Your private knowledge space</span></header>
      <div className="scroll" ref={scrollRef}>
        {showNotes ? <div className="notes-page"><p className="eyebrow">YOUR SAVED KNOWLEDGE</p><h1>Notes</h1>{notes.length === 0 ? <p className="empty-sub">Saved chats will appear here when you wishlist an answer.</p> : notes.map((note) => <article className="note-item" key={note.id}><div className="note-question">{note.question}</div><div className="note-answer"><ReactMarkdown>{note.answer}</ReactMarkdown></div><div className="note-date">{new Date(note.created_at).toLocaleString()}</div></article>)}</div> : <>
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
