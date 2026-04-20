// src/App.jsx
import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { useVoice } from "./hooks/useVoice";
import ChatBubble from "./components/ChatBubble";
import ChatInput from "./components/ChatInput";
import TypingIndicator from "./components/TypingIndicator";

export default function App() {
  const {
    messages, setMessages, isTyping, isEnded,
    connect, sendMessage, resetChat
  } = useWebSocket();

  const bottomRef = useRef(null);
  const [voiceStatus, setVoiceStatus] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistory] = useState([
    { id: 1, title: "Exam preparation tips" },
    { id: 2, title: "Course registration help" },
    { id: 3, title: "GPA calculation" },
  ]);

  const {
    isRecording, isProcessing, isPlaying,
    connectVoiceWS, startRecording, stopRecording
  } = useVoice({
    onTranscription: (text) => {
      setMessages(prev => [...prev, { role: "user", content: `🎤 ${text}` }]);
    },
    onToken: (token) => {
      if (token === "__CONVERSATION_ENDED__") return;
      setMessages(prev => {
        const updated = [...prev];
        if (updated[updated.length - 1]?.role === "assistant") {
          updated[updated.length - 1] = {
            role: "assistant",
            content: updated[updated.length - 1].content + token
          };
        } else {
          updated.push({ role: "assistant", content: token });
        }
        return updated;
      });
    },
    onEnd: () => setVoiceStatus(""),
    onStatus: (s) => setVoiceStatus(s)
  });

  useEffect(() => { connect(); connectVoiceWS(); }, [connect, connectVoiceWS]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const suggestions = [
    { icon: "📅", title: "Plan my semester", sub: "Course selection & scheduling" },
    { icon: "📚", title: "Exam preparation", sub: "I have 3 exams next week" },
    { icon: "🧠", title: "Study techniques", sub: "Best methods for retention" },
    { icon: "📊", title: "Calculate my GPA", sub: "Grade point average" },
  ];

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      background: "#0d1117",
      fontFamily: "'DM Sans', sans-serif",
      color: "#e6edf3",
      overflow: "hidden",
      position: "relative"
    }}>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Clash+Display:wght@500;600;700&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes shimmer {
          0%   { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.5; transform: scale(0.8); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50%       { transform: translateY(-8px); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(0,210,180,0.15); }
          50%       { box-shadow: 0 0 40px rgba(0,210,180,0.35); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-20px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes dotBounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.3; }
          40%            { transform: translateY(-6px); opacity: 1; }
        }

        .msg-appear { animation: fadeUp 0.25s ease forwards; }

        .sidebar-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px 12px;
          border-radius: 10px;
          font-size: 13px;
          color: #8b949e;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid transparent;
          font-family: 'DM Sans', sans-serif;
        }
        .sidebar-item:hover {
          background: rgba(0,210,180,0.06);
          border-color: rgba(0,210,180,0.15);
          color: #00d2b4;
        }

        .suggestion-card {
          background: rgba(22,27,34,0.8);
          border: 1px solid #21262d;
          color: #c9d1d9;
          padding: 16px 18px;
          border-radius: 14px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.25s;
          text-align: left;
          width: 100%;
          backdrop-filter: blur(8px);
        }
        .suggestion-card:hover {
          background: rgba(0,210,180,0.08);
          border-color: rgba(0,210,180,0.3);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0,210,180,0.1);
        }

        .send-btn {
          width: 36px; height: 36px;
          border-radius: 10px;
          border: none;
          display: flex; align-items: center; justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
          flex-shrink: 0;
          font-size: 16px;
        }
        .send-btn:disabled {
          background: #21262d;
          color: #484f58;
          cursor: not-allowed;
        }
        .send-btn:not(:disabled) {
          background: linear-gradient(135deg, #00d2b4, #00a896);
          color: #0d1117;
          box-shadow: 0 4px 12px rgba(0,210,180,0.3);
        }
        .send-btn:not(:disabled):hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(0,210,180,0.4);
        }

        .new-session-btn {
          background: linear-gradient(135deg, #00d2b4, #00a896);
          border: none;
          color: #0d1117;
          padding: 11px 28px;
          border-radius: 24px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          transition: all 0.2s;
          box-shadow: 0 4px 16px rgba(0,210,180,0.3);
        }
        .new-session-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0,210,180,0.4);
        }

        .toggle-btn {
          background: rgba(22,27,34,0.9);
          border: 1px solid #21262d;
          color: #8b949e;
          width: 32px; height: 32px;
          border-radius: 8px;
          cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          transition: all 0.2s;
          font-size: 14px;
          flex-shrink: 0;
        }
        .toggle-btn:hover {
          border-color: #00d2b4;
          color: #00d2b4;
        }

        .voice-btn {
          width: 38px; height: 38px;
          border-radius: 10px;
          border: 1px solid #21262d;
          display: flex; align-items: center; justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
          flex-shrink: 0;
          font-size: 16px;
        }
        .voice-btn.idle {
          background: #161b22;
          color: #8b949e;
        }
        .voice-btn.idle:hover {
          border-color: #00d2b4;
          color: #00d2b4;
          background: rgba(0,210,180,0.08);
        }
        .voice-btn.recording {
          background: rgba(239,68,68,0.15);
          border-color: #ef4444;
          color: #ef4444;
          animation: glow 1.5s infinite;
        }
        .voice-btn.processing {
          background: #161b22;
          color: #484f58;
          cursor: not-allowed;
        }
        .voice-btn.playing {
          background: rgba(0,210,180,0.1);
          border-color: #00d2b4;
          color: #00d2b4;
        }
      `}</style>

      {/* ── AMBIENT BACKGROUND ── */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 0,
        pointerEvents: "none", overflow: "hidden"
      }}>
        {/* Top left glow */}
        <div style={{
          position: "absolute", top: -200, left: -100,
          width: 600, height: 600,
          background: "radial-gradient(circle, rgba(0,210,180,0.06) 0%, transparent 70%)",
        }} />
        {/* Bottom right glow */}
        <div style={{
          position: "absolute", bottom: -200, right: -100,
          width: 500, height: 500,
          background: "radial-gradient(circle, rgba(0,168,150,0.05) 0%, transparent 70%)",
        }} />
        {/* Grid */}
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: `
            linear-gradient(rgba(0,210,180,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,210,180,0.025) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px"
        }} />
      </div>

      {/* ── SIDEBAR ── */}
      <aside style={{
        width: sidebarOpen ? 260 : 0,
        minWidth: sidebarOpen ? 260 : 0,
        background: "rgba(13,17,23,0.95)",
        borderRight: sidebarOpen ? "1px solid #21262d" : "none",
        display: "flex",
        flexDirection: "column",
        padding: sidebarOpen ? "16px 12px" : 0,
        overflow: "hidden",
        transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)",
        position: "relative",
        zIndex: 10,
        backdropFilter: "blur(12px)"
      }}>

        {sidebarOpen && (
          <>
            {/* Logo */}
            <div style={{
              display: "flex", alignItems: "center",
              justifyContent: "space-between", marginBottom: 24
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 34, height: 34, borderRadius: 10,
                  background: "linear-gradient(135deg, #00d2b4, #00a896)",
                  display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: 16,
                  boxShadow: "0 4px 12px rgba(0,210,180,0.3)",
                  animation: "glow 3s infinite"
                }}>🎓</div>
                <div>
                  <div style={{
                    fontFamily: "'Clash Display', sans-serif",
                    fontWeight: 700, fontSize: 16,
                    background: "linear-gradient(90deg, #00d2b4, #7ee8a2)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent"
                  }}>AcadAI</div>
                  <div style={{ fontSize: 10, color: "#484f58", letterSpacing: "0.8px", textTransform: "uppercase" }}>
                    Advisor
                  </div>
                </div>
              </div>
            </div>

            {/* New Chat */}
            <button
              className="sidebar-item"
              onClick={resetChat}
              style={{
                background: "rgba(0,210,180,0.06)",
                border: "1px solid rgba(0,210,180,0.2)",
                color: "#00d2b4",
                marginBottom: 20,
                justifyContent: "center",
                fontWeight: 500
              }}
            >
              <span>＋</span> New Chat
            </button>

            {/* Recent chats */}
            <div style={{ fontSize: 10, color: "#484f58", letterSpacing: "1px", textTransform: "uppercase", marginBottom: 8, paddingLeft: 4 }}>
              Recent
            </div>
            {chatHistory.map(chat => (
              <button key={chat.id} className="sidebar-item">
                <span style={{ fontSize: 14 }}>💬</span>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {chat.title}
                </span>
              </button>
            ))}

            <div style={{ flex: 1 }} />

            {/* Bottom user area */}
            <div style={{
              borderTop: "1px solid #21262d",
              paddingTop: 12, marginTop: 12
            }}>
              <div style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "8px 12px", borderRadius: 10,
                background: "rgba(22,27,34,0.5)"
              }}>
                <div style={{
                  width: 30, height: 30, borderRadius: "50%",
                  background: "linear-gradient(135deg, #00d2b4, #00a896)",
                  display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: 13,
                  color: "#0d1117", fontWeight: 700
                }}>S</div>
                <div>
                  <div style={{ fontSize: 13, color: "#e6edf3", fontWeight: 500 }}>Student</div>
                  <div style={{ fontSize: 11, color: "#484f58" }}>Free plan</div>
                </div>
              </div>
            </div>
          </>
        )}
      </aside>

      {/* ── MAIN AREA ── */}
      <div style={{
        flex: 1, display: "flex", flexDirection: "column",
        overflow: "hidden", position: "relative", zIndex: 1
      }}>

        {/* Header */}
        <header style={{
          display: "flex", alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 20px",
          borderBottom: "1px solid #21262d",
          background: "rgba(13,17,23,0.8)",
          backdropFilter: "blur(12px)"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button className="toggle-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? "◀" : "▶"}
            </button>
            {!sidebarOpen && (
              <div style={{
                fontFamily: "'Clash Display', sans-serif",
                fontWeight: 700, fontSize: 16,
                background: "linear-gradient(90deg, #00d2b4, #7ee8a2)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent"
              }}>AcadAI</div>
            )}
          </div>

          {/* Status indicators */}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {voiceStatus && (
              <div style={{
                fontSize: 12, color: "#00d2b4",
                display: "flex", alignItems: "center", gap: 6,
                background: "rgba(0,210,180,0.08)",
                padding: "4px 12px", borderRadius: 20,
                border: "1px solid rgba(0,210,180,0.2)"
              }}>
                <div style={{
                  width: 6, height: 6, borderRadius: "50%",
                  background: "#00d2b4",
                  animation: "pulse-dot 1s infinite"
                }} />
                {voiceStatus}
              </div>
            )}
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{
                width: 7, height: 7, borderRadius: "50%",
                background: "#00d2b4",
                boxShadow: "0 0 8px #00d2b4",
                animation: "pulse-dot 2s infinite"
              }} />
              <span style={{ fontSize: 11, color: "#484f58" }}>Online</span>
            </div>
          </div>
        </header>

        {/* Messages */}
        <main style={{
          flex: 1, overflowY: "auto",
          display: "flex", flexDirection: "column",
          padding: "24px 20px"
        }}>
          <div style={{ maxWidth: 720, width: "100%", margin: "0 auto", flex: 1, display: "flex", flexDirection: "column" }}>

            {/* Empty state */}
            {messages.length === 0 && !isTyping && (
              <div style={{
                flex: 1, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                gap: 28, textAlign: "center",
                animation: "fadeUp 0.5s ease forwards"
              }}>
                {/* Logo mark */}
                <div style={{
                  width: 80, height: 80,
                  background: "linear-gradient(135deg, #00d2b4, #00a896)",
                  borderRadius: 24,
                  display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: 36,
                  boxShadow: "0 16px 48px rgba(0,210,180,0.25)",
                  animation: "float 4s ease-in-out infinite"
                }}>🎓</div>

                <div>
                  <h1 style={{
                    fontFamily: "'Clash Display', sans-serif",
                    fontWeight: 700, fontSize: 32,
                    marginBottom: 10, letterSpacing: "-0.5px",
                    background: "linear-gradient(135deg, #e6edf3 0%, #8b949e 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent"
                  }}>
                    How can I help you today?
                  </h1>
                  <p style={{ color: "#484f58", fontSize: 14, lineHeight: 1.6 }}>
                    Your AI-powered university academic advisor.<br/>
                    Ask me anything about courses, exams, or campus life.
                  </p>
                </div>

                {/* Suggestion cards */}
                <div style={{
                  display: "grid", gridTemplateColumns: "1fr 1fr",
                  gap: 10, width: "100%", maxWidth: 560
                }}>
                  {suggestions.map((s) => (
                    <button
                      key={s.title}
                      className="suggestion-card"
                      onClick={() => sendMessage(s.title)}
                    >
                      <span style={{ fontSize: 20, display: "block", marginBottom: 8 }}>{s.icon}</span>
                      <span style={{ fontWeight: 500, display: "block", marginBottom: 3, color: "#e6edf3", fontSize: 13 }}>
                        {s.title}
                      </span>
                      <span style={{ color: "#484f58", fontSize: 12 }}>{s.sub}</span>
                    </button>
                  ))}
                </div>

                {/* Feature pills */}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
                  {["📄 RAG Documents", "🧠 Memory", "🔧 Tools", "🎤 Voice"].map(f => (
                    <div key={f} style={{
                      padding: "5px 12px",
                      background: "rgba(0,210,180,0.06)",
                      border: "1px solid rgba(0,210,180,0.15)",
                      borderRadius: 20,
                      fontSize: 11, color: "#00d2b4",
                      fontWeight: 500
                    }}>{f}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((msg, idx) => (
              <div key={idx} className="msg-appear">
                <ChatBubble message={msg} />
              </div>
            ))}

            {/* Typing */}
            {isTyping && messages[messages.length - 1]?.role !== "assistant" && (
              <TypingIndicator />
            )}

            {/* Ended */}
            {isEnded && (
              <div style={{
                display: "flex", flexDirection: "column",
                alignItems: "center", padding: "48px 20px",
                gap: 16, animation: "fadeUp 0.4s ease forwards"
              }}>
                <div style={{
                  width: 60, height: 60, borderRadius: 18,
                  background: "linear-gradient(135deg, #00d2b4, #00a896)",
                  display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: 26,
                  boxShadow: "0 12px 32px rgba(0,210,180,0.3)"
                }}>✅</div>
                <div style={{
                  fontFamily: "'Clash Display', sans-serif",
                  fontWeight: 700, fontSize: 20, color: "#e6edf3"
                }}>Session Complete</div>
                <p style={{ color: "#484f58", fontSize: 14, textAlign: "center", maxWidth: 300, lineHeight: 1.6 }}>
                  Best of luck with your studies! Come back anytime.
                </p>
                <button className="new-session-btn" onClick={resetChat}>
                  Start New Session
                </button>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </main>

        {/* Input */}
        {!isEnded && (
          <footer style={{
            padding: "12px 20px 20px",
            borderTop: "1px solid #21262d",
            background: "rgba(13,17,23,0.9)",
            backdropFilter: "blur(12px)"
          }}>
            <div style={{ maxWidth: 720, margin: "0 auto" }}>
              <ChatInput
                onSend={sendMessage}
                disabled={isTyping}
                isRecording={isRecording}
                isProcessing={isProcessing}
                isPlaying={isPlaying}
                onVoiceStart={startRecording}
                onVoiceStop={stopRecording}
              />
              <p style={{
                textAlign: "center", fontSize: 11,
                color: "#30363d", marginTop: 10,
                fontFamily: "'DM Sans', sans-serif"
              }}>
                AcadAI may make mistakes · Always verify important academic decisions
              </p>
            </div>
          </footer>
        )}
      </div>
    </div>
  );
}
