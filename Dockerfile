FROM python:3.13-slim

# Install system dependencies, termasuk wget, unzip, dan library grafis yang hilang
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libgbm1 \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libcups2 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Mengunduh Chromium dan ChromeDriver versi spesifik untuk Linux ARM64
RUN CHROME_VERSION="139.0.7258.66" \
    && ARCH="linux64" \
    && CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" \
    && CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && wget -q "${CHROME_URL}" -O /tmp/chrome.zip \
    && wget -q "${CHROMEDRIVER_URL}" -O /tmp/chromedriver.zip \
    && unzip /tmp/chrome.zip -d /usr/local/bin/ \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chrome.zip /tmp/chromedriver.zip \
    && mv /usr/local/bin/chrome-linux64/chrome /usr/local/bin/chrome \
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chrome /usr/local/bin/chromedriver \
    && rm -rf /usr/local/bin/chrome-linux64 /usr/local/bin/chromedriver-linux64 \
    && /usr/local/bin/chrome --version \
    && /usr/local/bin/chromedriver --version

# Buat direktori logs
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Set working directory
WORKDIR /app

# Salin requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Salin kode aplikasi
COPY . .

# Set environment variables
ENV CHROME_BIN=/usr/local/bin/chrome
ENV CHROMEDRIVER_BIN=/usr/local/bin/chromedriver
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV DISPLAY=:99

# Chrome flags yang dioptimalkan untuk headless
ENV CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --headless=new --disable-gpu --disable-web-security --disable-features=VizDisplayCompositor --window-size=1920,1080 --remote-debugging-port=9222"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Jalankan aplikasi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]