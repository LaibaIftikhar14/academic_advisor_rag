# AcadAI — University Academic Advisor AI

A fully local, production-style conversational AI system built with FastAPI, React, and a quantized LLM running on CPU. No cloud APIs. No external tools. Pure prompt engineering and conversation memory.

---

## System Architecture
```
Browser (React UI)
      ↕ WebSocket (ws://localhost:8000/ws/chat)
FastAPI Backend
      ↕ Session Manager (UUID-based memory)
      ↕ Conversation Manager (prompt + policy + memory)
      ↕ LLM Engine (httpx async streaming)
Ollama (qwen2.5:1.5b running on CPU)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | FastAPI + WebSocket |
| LLM Engine | Ollama (qwen2.5:1.5b Q4 quantized) |
| Memory | In-memory sliding window |
| Deployment | Docker + docker-compose |

---

## Project Structure
```
NLP_Assignment2/
├── backend/
│   ├── config.py          # Central config + system prompt
│   ├── session.py         # Multi-user session memory store
│   ├── conversation.py    # Core logic: policy + memory + streaming
│   ├── llm.py             # Ollama API interface
│   └── main.py            # FastAPI app + WebSocket endpoint
├── frontend/
│   └── src/
│       ├── App.jsx                    # Main UI layout
│       ├── components/
│       │   ├── ChatBubble.jsx         # Message bubbles
│       │   ├── ChatInput.jsx          # Input box
│       │   └── TypingIndicator.jsx    # Animated dots
│       └── hooks/
│           └── useWebSocket.js        # WebSocket + streaming hook
├── tests/
│   └── test_conversation.py  # Unit tests
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirement.txt
└── README.md
```

---

## Features

- Fully local — no internet required after setup
- Real-time token streaming via WebSocket
- Multi-user support with isolated sessions
- Sliding window conversation memory (last 10 turns)
- Two-layer policy enforcement — ethics, wellbeing, scope
- Stress and distress detection with empathetic responses
- Conversation conclusion detection
- ChatGPT-style React UI with sidebar
- Docker-ready deployment

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama installed — https://ollama.com

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/NLP_Assignment2.git
cd NLP_Assignment2
```

### 2. Install backend dependencies
```bash
pip install -r requirement.txt
```

### 3. Pull the LLM model
```bash
ollama pull qwen2.5:1.5b
```

### 4. Start Ollama
```bash
ollama serve
```

### 5. Start the backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 7. Open the app
```
http://localhost:5173
```

---

## Docker Deployment
```bash
docker compose up --build
docker exec -it ollama ollama pull qwen2.5:1.5b
```

---

## How Conversation Memory Works

Every session maintains a list of messages:
```
[system prompt] → always kept
[user turn 1]   → kept until window fills
[assistant 1]   →
[user turn 2]   →
[assistant 2]   →
...
[last 20 msgs]  → sliding window trims oldest
```

The entire trimmed history is sent to the LLM on every turn — this is how the AI remembers.

---

## Conversation Policies

| Policy | Trigger | Response |
|---|---|---|
| Ethics | "write my assignment" | Redirect to planning help |
| Wellbeing | "give up", "hopeless" | Empathy + counseling suggestion |
| Closing | "bye", "thanks", "done" | Warm goodbye + session end screen |
| Scope | Off-topic questions | Polite redirect to academics |

---

## Stress & Distress Handling

The system uses a two-layer approach:

**Layer 1 — Keyword Detection (instant)**
Phrases like "give up", "feeling hopeless", "I'm a failure" trigger an immediate empathetic response pointing the student to university counseling services.

**Layer 2 — System Prompt Policy**
The LLM is instructed to always respond with empathy first when detecting distress, even for phrases not caught by keywords.

---

## Benchmark (Laptop CPU)

| Hardware | Tokens/sec | First token |
|---|---|---|
| Intel i5 8GB | ~8–12 | ~3s |
| Ryzen 7 16GB | ~15–20 | ~1.5s |
| Apple M1 | ~25–35 | <1s |

---

## Known Limitations

- Sessions stored in memory — lost on server restart
- No authentication — anyone with the URL can chat
- CPU inference is slower than GPU
- Policy enforcement is keyword-based — not foolproof
- Model may occasionally go off-topic despite system prompt

---

## Voice Features

- Voice input via microphone (ASR)
- Voice output — AI speaks responses automatically (TTS)
- Hold 🎤 mic button to speak, release to send


---

## Voice Pipeline
```
User speaks 🎤
        ↓
MediaRecorder captures audio (webm)
        ↓
FFmpeg converts webm → wav (16kHz mono)
        ↓
faster-whisper transcribes audio → text
        ↓
Conversation Manager processes text
        ↓
LLM generates text response (streamed)
        ↓
Piper TTS converts text → WAV audio
        ↓
Base64 encoded → sent to browser
        ↓
Web Audio API decodes + plays 🔊
```

---

## Academic Scope Filtering
```
User message arrives
        ↓
Layer 1: Keyword check (ethics + wellbeing)
        ↓
Layer 2: LLM classifier (is this academic? YES/NO)
        ↓
Academic → process normally
Non-academic → polite refusal (not saved to memory)
```

---

## New Dependencies
```bash
pip install faster-whisper piper-tts soundfile ffmpeg-python
```

FFmpeg required — download from https://ffmpeg.org and add to PATH

---

## Voice API Endpoints

| Endpoint | Type | Description |
|---|---|---|
| `/ws/voice` | WebSocket | Full voice pipeline |
| `/voice/transcribe` | POST | Audio → text only |
| `/voice/speak` | POST | Text → audio only |

---

## New Known Limitations

- Voice requires microphone permission in browser
- Sub-second latency difficult on low-end CPU
- LLM scope classifier occasionally misclassifies edge cases
- Sessions lost on server restart
---

## Future Improvements

- Redis for persistent session storage
- User authentication
- Database for chat history
- Rate limiting per session
- Classifier model for more robust policy enforcement
- GPU support for faster inference


---

## Assignment 4 Extensions — RAG + Tools + CRM

### New Components Added

| Component | File | Description |
|---|---|---|
| RAG Module | `rag.py` | Indexes 70 documents, retrieves top-3 relevant chunks |
| CRM Tool | `crm.py` | Stores student profiles across sessions |
| Tools | `tools.py` | Calculator, Study Planner, GPA Calculator |

---

### Document Collection

| Category | Documents |
|---|---|
| Course Descriptions | 15 |
| Exam Policies | 10 |
| Study Strategies | 15 |
| University Policies | 10 |
| Career Guidance | 10 |
| Mental Health | 10 |
| **Total** | **70** |

Chunk size: 512 characters | Overlap: 50 | Total chunks: 186
Embedding model: all-MiniLM-L6-v2 | Vector DB: ChromaDB | Top-k: 3

---

### Tools Description

**Calculator** — Evaluates math expressions using sympy
Example: "what is 15% of 200" → 30.0

**Study Planner** — Creates personalized study schedules
Example: "study plan for math and CS for 5 days" → day by day schedule

**GPA Calculator** — Calculates GPA from letter grades or percentages
Example: "I got A, B+, A-, C" → GPA: 3.25 / 4.0

**CRM** — Remembers student name, year, major, concerns across sessions
Example: "I'm Sara, 2nd year CS" → saved automatically

---

### New API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/rag/search` | GET | Test RAG retrieval |
| `/crm/{session_id}` | GET | View student profile |
| `/tools/list` | GET | List available tools |
| `/tools/run` | POST | Run a tool directly |

---

### Conversation Pipeline (Updated)
User message
↓
Policy check → Closing check → CRM update
↓
Tool detection → Scope check → RAG retrieval
↓
Build enhanced prompt:
[System Prompt + CRM Profile + RAG Context + Tool Result]
↓
Stream LLM response → Summarize → Save to memory
---

### New Dependencies

```bash
pip install sentence-transformers chromadb faiss-cpu
pip install langchain langchain-community pydantic sympy pypdf
```

---

### RAG Verification

```bash
curl "http://localhost:8000/rag/search?query=exam attendance policy"
```
### Postman 
https://i236102-7322480.postman.co/workspace/Zara-Ali's-Workspace~b63bc304-3fa6-423b-8f41-d6cf20ab28a7/collection/54153054-bf124066-7dd3-4770-8ec8-db9638fb51c4?action=share&source=copy-link&creator=54153054
Or visit: `http://localhost:8000/rag/search?query=how to study for exams`
