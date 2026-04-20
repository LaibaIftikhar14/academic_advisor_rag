// src/components/ChatBubble.jsx
import { useState } from "react";

export default function ChatBubble({ message }) {
  const isUser = message.role === "user";
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speakMessage = async () => {
    if (isSpeaking) return;
    try {
      setIsSpeaking(true);
      const response = await fetch("http://localhost:8000/voice/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: message.content })
      });
      if (!response.ok) throw new Error("TTS failed");
      const audioBlob = await response.blob();
      const audioUrl  = URL.createObjectURL(audioBlob);
      const audio     = new Audio(audioUrl);
      audio.play();
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
      };
    } catch (err) {
      setIsSpeaking(false);
    }
  };

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 20,
      gap: 12,
      alignItems: "flex-start"
    }}>

      {/* AI Avatar */}
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: 10,
          background: "linear-gradient(135deg, #00d2b4, #00a896)",
          display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: 14,
          flexShrink: 0, marginTop: 2,
          boxShadow: "0 4px 12px rgba(0,210,180,0.25)"
        }}>🎓</div>
      )}

      <div style={{ maxWidth: "72%", display: "flex", flexDirection: "column", gap: 6 }}>

        {/* Name */}
        <div style={{
          fontSize: 11, fontWeight: 600,
          color: isUser ? "#00d2b4" : "#484f58",
          textAlign: isUser ? "right" : "left",
          letterSpacing: "0.5px",
          textTransform: "uppercase"
        }}>
          {isUser ? "You" : "AcadAI"}
        </div>

        {/* Bubble */}
        <div style={{
          padding: "12px 16px",
          borderRadius: isUser ? "18px 4px 18px 18px" : "4px 18px 18px 18px",
          fontSize: 14,
          lineHeight: 1.7,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          fontFamily: "'DM Sans', sans-serif",
          ...(isUser ? {
            background: "linear-gradient(135deg, #00d2b4, #00a896)",
            color: "#0d1117",
            fontWeight: 500,
            boxShadow: "0 4px 16px rgba(0,210,180,0.2)"
          } : {
            background: "rgba(22,27,34,0.9)",
            color: "#c9d1d9",
            border: "1px solid #21262d",
            boxShadow: "0 2px 8px rgba(0,0,0,0.3)"
          })
        }}>
          {message.content}
        </div>

        {/* Speak button for AI */}
        {!isUser && (
          <button
            onClick={speakMessage}
            disabled={isSpeaking}
            style={{
              alignSelf: "flex-start",
              background: "transparent",
              border: `1px solid ${isSpeaking ? "#00d2b4" : "#21262d"}`,
              borderRadius: 6,
              padding: "3px 10px",
              color: isSpeaking ? "#00d2b4" : "#484f58",
              fontSize: 11,
              cursor: isSpeaking ? "not-allowed" : "pointer",
              fontFamily: "'DM Sans', sans-serif",
              display: "flex", alignItems: "center", gap: 4,
              transition: "all 0.2s"
            }}
          >
            {isSpeaking ? "🔊 Speaking..." : "🔊 Speak"}
          </button>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: 10,
          background: "rgba(22,27,34,0.9)",
          border: "1px solid #21262d",
          display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: 13,
          color: "#484f58", flexShrink: 0, marginTop: 2
        }}>U</div>
      )}
    </div>
  );
}
