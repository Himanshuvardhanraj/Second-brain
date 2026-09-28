import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "";


function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 8h11M8.5 3.5L13 8l-4.5 4.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronIcon({ open }) {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ transform: open ? "rotate(90deg)" : "none", transition: "transform 150ms ease" }}>
      <path d="M3 1.5L7 5l-4 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SourceList({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources">
      <button className="sources-toggle" onClick={() => setOpen((v) => !v)}>
        <ChevronIcon open={open} />
        <span>{sources.length} source{sources.length !== 1 ? "s" : ""}</span>
      </button>
      {open && (
        <ol className="sources-list">
          {sources.map((s, i) => (
            <li key={i}>
              <span className="source-num">{i + 1}</span>
              <span className="source-name">{s.source?.split("/").pop() || "unknown"}</span>
              <span className="source-meta">p.{s.page} · {s.score.toFixed(3)}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="thinking">
      <span></span><span></span><span></span>
    </div>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [online, setOnline] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const uploadPDF = async (file) => {
    if (!file) return;

    if (file.type !== "application/pdf") {
      setUploadMessage("Please select a PDF file.");
      return;
    }

    setUploading(true);
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        `${API_URL}/api/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      // Read response as text first
      const responseText = await response.text();

      console.log("Upload status:", response.status);
      console.log("Upload response:", responseText);

      if (!response.ok) {
        throw new Error(
          responseText || `Upload failed with status ${response.status}`
        );
      }

      // Parse JSON only if something was actually returned
      const data = responseText
        ? JSON.parse(responseText)
        : null;

      if (!data) {
        throw new Error("Backend returned an empty response.");
      }

      setUploadMessage(
        `✓ ${data.filename} uploaded successfully — ${data.chunks_created} chunks indexed.`
      );

    } catch (error) {
      console.error("PDF upload error:", error);

      setUploadMessage(
        error.message || "Could not upload the PDF."
      );

    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => setOnline(r.ok))
      .catch(() => setOnline(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const askQuestion = async () => {
    const text = question.trim();

    if (!text || loading) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: text,
          top_k: 5,
        }),
      });

      const responseText = await res.text();

      console.log("Chat status:", res.status);
      console.log("Chat response:", responseText);

      if (!res.ok) {
        let errorMessage = `Server error (${res.status})`;

        try {
          const errorData = JSON.parse(responseText);
          errorMessage =
            errorData.detail ||
            errorData.message ||
            errorMessage;
        } catch {
          if (responseText) {
            errorMessage = responseText;
          }
        }

        throw new Error(errorMessage);
      }

      const data = JSON.parse(responseText);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          sources: data.sources || [],
        },
      ]);

    } catch (err) {
      console.error("Chat error:", err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `⚠️ ${err.message}`,
          sources: [],
          error: true,
        },
      ]);

    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">⌘</span>
          <span className="brand-name">Second Brain</span>
        </div>

        <nav className="nav">
          <div className="nav-item nav-item--active">
            Chat
          </div>

          <label className="nav-item upload-item">
            {uploading ? "Uploading…" : "Upload PDF"}

            <input
              type="file"
              accept="application/pdf"
              hidden
              disabled={uploading}
              onChange={(e) => {
                const file = e.target.files?.[0];
                uploadPDF(file);
                e.target.value = "";
              }}
            />
          </label>

          {uploadMessage && (
            <div className="upload-message">
              {uploadMessage}
            </div>
          )}
        </nav>

        <div className="sidebar-foot">
          <span className={`status-dot ${online ? "status-dot--on" : online === false ? "status-dot--off" : ""}`} />
          <span className="status-text">
            {online === null ? "checking backend…" : online ? "backend online" : "backend unreachable"}
          </span>
        </div>
      </aside>

      <main className="stage">
        <div className="scroll" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="empty">
              <p className="empty-title">Ask your notes something.</p>
              <p className="empty-sub">Answers are grounded in what you've actually written — with sources, every time.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`row row--${msg.role}`}>
              {msg.role === "user" ? (
                <div className="bubble bubble--user">{msg.text}</div>
              ) : (
                <div className={`card ${msg.error ? "card--error" : ""}`}>
                  <div className="card-body">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                  <SourceList sources={msg.sources} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="row row--assistant">
              <div className="card card--pending">
                <ThinkingDots />
              </div>
            </div>
          )}
        </div>

        <div className="composer">
          <textarea
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your notes…"
            rows={1}
          />
          <button onClick={askQuestion} disabled={loading || !question.trim()} aria-label="Send">
            <SendIcon />
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;