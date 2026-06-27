# Jelajah Jogja API — container image (Hugging Face Spaces / any Docker host).
# Serves the FastAPI backend (NLU model + knowledge base) on port 7860.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
# requirements-api.txt pulls in requirements.txt via its `-r` line.
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy the project
COPY . .

ENV PYTHONPATH=/app/src
EXPOSE 7860

# Hugging Face Spaces routes traffic to port 7860.
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "7860"]
