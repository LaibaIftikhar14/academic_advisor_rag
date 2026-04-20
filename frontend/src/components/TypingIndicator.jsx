// src/components/TypingIndicator.jsx

export default function TypingIndicator() {
  return (
    <div style={{
      display: "flex", alignItems: "flex-start",
      gap: 12, marginBottom: 20
    }}>
      {/* Avatar */}
      <div style={{
        width: 32, height: 32, borderRadius: 10,
        background: "linear-gradient(135deg, #00d2b4, #00a896)",
        display: "flex", alignItems: "center",
        justifyContent: "center", fontSize: 14,
        flexShrink: 0, marginTop: 2,
        boxShadow: "0 4px 12px rgba(0,210,180,0.25)"
      }}>🎓</div>

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{
          fontSize: 11, fontWeight: 600,
          color: "#484f58", letterSpacing: "0.5px",
          textTransform: "uppercase"
        }}>AcadAI</div>

        <div style={{
          background: "rgba(22,27,34,0.9)",
          border: "1px solid #21262d",
          borderRadius: "4px 18px 18px 18px",
          padding: "14px 18px",
          display: "flex", gap: 5, alignItems: "center"
        }}>
          <style>{`
            @keyframes dotBounce {
              0%, 80%, 100% { transform: translateY(0);    opacity: 0.3; }
              40%            { transform: translateY(-6px); opacity: 1; }
            }
          `}</style>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{
              width: 7, height: 7, borderRadius: "50%",
              background: "#00d2b4",
              animation: "dotBounce 1.2s ease-in-out infinite",
              animationDelay: `${i * 0.18}s`,
              boxShadow: "0 0 6px rgba(0,210,180,0.5)"
            }} />
          ))}
        </div>
      </div>
    </div>
  );
}
