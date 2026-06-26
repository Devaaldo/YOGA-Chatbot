# YOGA Chatbot — container image (works on Hugging Face Spaces, Fly.io, any VPS)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Make the package importable and expose the HF Spaces health port
ENV PYTHONPATH=/app/src
ENV PORT=7860
EXPOSE 7860

# TELEGRAM_BOT_TOKEN must be provided at runtime (HF Space secret / -e flag)
CMD ["python", "app.py"]
