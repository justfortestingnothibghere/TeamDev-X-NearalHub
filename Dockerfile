# ───── TeamDev X NeuralHub ─────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip \
    xvfb \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libxcomposite1 libxrandr2 \
    libxdamage1 libxfixes3 libgbm1 \
    libasound2 libpangocairo-1.0-0 \
    libpango-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /etc/apt/keyrings/google.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] \
       http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py .
COPY batbin_loader.py .
COPY c-gpt.py .
COPY bot.py .
COPY lang.py .
COPY groq_api.py .
COPY start.sh .
COPY models/ ./models/
COPY assets/ ./assets/

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
