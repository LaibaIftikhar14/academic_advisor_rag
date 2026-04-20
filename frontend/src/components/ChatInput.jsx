// src/components/ChatInput.jsx
import { useState } from "react";
import VoiceButton from "./VoiceButton";

export default function ChatInput({
  onSend, disabled,
  isRecording, isProcessing, isPlaying,
  onVoiceStart, onVoiceStop
}) {
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      display: "flex",
      alignItems: "flex-end",
      gap: 8,
      background: "rgba(22,27,34,0.9)",
      border: `1px solid ${focused ? "rgba(0,210,180,0.4)" : "#21262d"}`,
      borderRadius: 16,
      padding: "10px 10px 10px 18px",
      transition: "border-color 0.2s, box-shadow 0.2s",
      boxShadow: focused
        ? "0 0 0 3px rgba(0,210,180,0.08), 0 4px 16px rgba(0,0,0,0.3)"
        : "0 4px 16px rgba(0,0,0,0.2)",
      backdropFilter: "blur(8px)"
    }}>
      <textarea
        rows={1}
        placeholder="Message AcadAI... or hold 🎤 to speak"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          e.target.style.height = "auto";
          e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        disabled={disabled}
        style={{
          flex: 1,
          background: "transparent",
          border: "none",
          outline: "none",
          color: "#e6edf3",
          fontSize: 14,
          fontFamily: "'DM Sans', sans-serif",
          resize: "none",
          lineHeight: 1.6,
          paddingTop: 2,
          minHeight: 26,
          maxHeight: 160,
          overflowY: "auto",
        }}
      />

      {/* Voice button */}
      <VoiceButton
        isRecording={isRecording}
        isProcessing={isProcessing}
        isPlaying={isPlaying}
        onStart={onVoiceStart}
        onStop={onVoiceStop}
      />

      {/* Send button */}
      <button
        className="send-btn"
        onClick={handleSend}
        disabled={disabled || !text.trim()}
      >
        ↑
      </button>
    </div>
  );
}
