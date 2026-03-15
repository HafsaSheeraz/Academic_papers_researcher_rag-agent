# Use Python 3.12 for better performance with Gemini 3 SDK
FROM python:3.12-slim

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the rest of the application
COPY . .

# 3. Create a non-root user for security (Hugging Face best practice)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 4. Setup work directory permissions
WORKDIR $HOME/app
COPY --chown=user . $HOME/app

# HF Spaces uses 7860 by default
EXPOSE 7860

# 5. Optimized Gunicorn command
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "app:app"]