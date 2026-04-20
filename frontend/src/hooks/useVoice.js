// src/hooks/useVoice.js
// ─────────────────────────────────────────────
// Voice Hook — handles microphone recording
// and audio playback
//
// What it does:
//   1. Records audio from microphone
//   2. Sends audio to /ws/voice
//   3. Receives transcription + text + audio
//   4. Plays audio response
// ─────────────────────────────────────────────

import { useState, useRef, useCallback } from "react";

const VOICE_WS_URL = "ws://localhost:8000/ws/voice";

export function useVoice({ onTranscription, onToken, onEnd, onStatus }) {
  const [isRecording, setIsRecording]   = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying]       = useState(false);

  const wsRef          = useRef(null);
  const mediaRecorder  = useRef(null);
  const audioChunks    = useRef([]);

  // Connect to voice WebSocket
  const connectVoiceWS = useCallback(() => {
    const ws = new WebSocket(VOICE_WS_URL);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "status") {
        // Show status: "Transcribing...", "Thinking...", "Speaking..."
        onStatus?.(data.content);
      }

      if (data.type === "transcription") {
        // Show what the AI heard
        onTranscription?.(data.content);
        setIsProcessing(true);
      }

      if (data.type === "token") {
        // Stream text response
        onToken?.(data.content);
      }

      if (data.type === "audio") {
        // Decode base64 audio and play it
        playAudio(data.content);
      }

      if (data.type === "end") {
        setIsProcessing(false);
        onEnd?.();
      }

      if (data.type === "error") {
        setIsProcessing(false);
        onStatus?.("Error: " + data.content);
      }
    };

    ws.onclose = () => {
      setTimeout(connectVoiceWS, 2000);
    };

    wsRef.current = ws;
  }, []);

  // Play base64 audio in browser
const playAudio = async (base64Audio) => {
    try {
      setIsPlaying(true);
      console.log("Audio received, length:", base64Audio.length);

      // Decode base64 to array buffer
      const binaryString = atob(base64Audio);
      const len          = binaryString.length;
      const bytes        = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      console.log("Decoded bytes:", bytes.length);

      // Use AudioContext to play
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioCtx     = new AudioContext();

      // Resume context (required by browsers)
      await audioCtx.resume();

      // Decode WAV
      const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer.slice(0));

      // Play
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      source.start(0);

      console.log("✅ Playing audio!");

      source.onended = () => {
        setIsPlaying(false);
        audioCtx.close();
      };

    } catch (err) {
      console.error("Audio playback error:", err);
      setIsPlaying(false);
    }
  };

  // Start recording from microphone
  const startRecording = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
      });

      audioChunks.current  = [];
      mediaRecorder.current = new MediaRecorder(stream);

      // Collect audio chunks as they come in
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };

      // When recording stops — send audio to backend
      mediaRecorder.current.onstop = async () => {
        const audioBlob  = new Blob(audioChunks.current, {
          type: "audio/webm"
        });
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBytes  = new Uint8Array(arrayBuffer);

        // Make sure WebSocket is open
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(audioBytes);
          setIsProcessing(true);
        }

        // Stop microphone tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.current.start();
      setIsRecording(true);

    } catch (err) {
      console.error("Microphone error:", err);
      onStatus?.("Microphone access denied.");
    }
  }, []);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorder.current?.state === "recording") {
      mediaRecorder.current.stop();
      setIsRecording(false);
    }
  }, []);

  return {
    isRecording,
    isProcessing,
    isPlaying,
    connectVoiceWS,
    startRecording,
    stopRecording
  };
}