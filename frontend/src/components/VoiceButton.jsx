// src/components/VoiceButton.jsx

export default function VoiceButton({
  isRecording, isProcessing, isPlaying,
  onStart, onStop
}) {
  const getStatus = () => {
    if (isRecording)  return "recording";
    if (isProcessing) return "processing";
    if (isPlaying)    return "playing";
    return "idle";
  };

  const status = getStatus();

  const icons = {
    idle:       "🎤",
    recording:  "⏹",
    processing: "⏳",
    playing:    "🔊"
  };

  const labels = {
    idle:       "hold",
    recording:  "stop",
    processing: "wait",
    playing:    "play"
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
      <button
        className={`voice-btn ${status}`}
        onMouseDown={onStart}
        onMouseUp={onStop}
        onTouchStart={onStart}
        onTouchEnd={onStop}
        disabled={isProcessing || isPlaying}
      >
        <span style={{ fontSize: 16 }}>{icons[status]}</span>
      </button>
      <span style={{
        fontSize: 9, color: "#30363d",
        fontFamily: "'DM Sans', sans-serif",
        letterSpacing: "0.3px"
      }}>
        {labels[status]}
      </span>
    </div>
  );
}
