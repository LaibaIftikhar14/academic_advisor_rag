


// src/hooks/useWebSocket.js

import { useState, useRef, useCallback } from "react";

const WS_URL = "ws://localhost:8000/ws/chat";

export function useWebSocket() {
  const [messages, setMessages]       = useState([]);
  const [isTyping, setIsTyping]       = useState(false);
  const [isEnded, setIsEnded]         = useState(false); // NEW
  const wsRef                         = useRef(null);
  const currentReplyRef               = useRef("");

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("Connected to backend");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "start") {
        setIsTyping(true);
        currentReplyRef.current = "";
      }

      if (data.type === "token") {
        // Check for conversation ended signal
        if (data.content === "__CONVERSATION_ENDED__") {
          setIsEnded(true);   // NEW
          setIsTyping(false);
          return;
        }

        currentReplyRef.current += data.content;
        setMessages((prev) => {
          const updated = [...prev];
          if (updated[updated.length - 1]?.role === "assistant") {
            updated[updated.length - 1] = {
              role: "assistant",
              content: currentReplyRef.current,
            };
          } else {
            updated.push({
              role: "assistant",
              content: currentReplyRef.current,
            });
          }
          return updated;
        });
      }

      if (data.type === "end") {
        setIsTyping(false);
        currentReplyRef.current = "";
      }

      if (data.type === "error") {
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Something went wrong. Please try again." },
        ]);
      }
    };

    ws.onclose = () => {
      setTimeout(connect, 2000);
    };

    ws.onerror = (err) => console.error("WebSocket error:", err);

    wsRef.current = ws;
  }, []);

  const sendMessage = useCallback((text) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    wsRef.current.send(JSON.stringify({ message: text }));
  }, []);

  const resetChat = useCallback(() => {
    setMessages([]);
    setIsTyping(false);
    setIsEnded(false);  // NEW
    if (wsRef.current) wsRef.current.close();
  }, []);

  return { messages, setMessages, isTyping, isEnded, connect, sendMessage, resetChat };
}