# Dockerfile
# ─────────────────────────────────────────────
# Builds the FastAPI backend into a container.
# Ollama runs separately (see docker-compose.yml)
# ─────────────────────────────────────────────

# Use lightweight Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (better Docker caching)
COPY requirement.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Copy entire backend into container
COPY backend/ ./backend/

# Move into backend folder
WORKDIR /app/backend

# Expose port 8000
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]