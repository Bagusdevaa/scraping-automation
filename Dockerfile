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

# Install Chrome dan ChromeDriver dengan auto-compatibility detection
RUN apt-get update && apt-get install -y \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome stable dengan cross-platform support
RUN DEBIAN_ARCH=$(dpkg --print-architecture) \
    && echo "Debian architecture: $DEBIAN_ARCH" \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=$DEBIAN_ARCH signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install matching ChromeDriver with cross-platform detection
RUN CHROME_VERSION=$(google-chrome --version | grep -oP "\d+" | head -1) \
    && echo "Chrome major version: $CHROME_VERSION" \
    && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_VERSION") \
    && echo "ChromeDriver version: $CHROMEDRIVER_VERSION" \
    && ARCH=$(uname -m) \
    && DEBIAN_ARCH=$(dpkg --print-architecture) \
    && echo "System architecture: $ARCH" \
    && echo "Debian architecture: $DEBIAN_ARCH" \
    && if [ "$ARCH" = "aarch64" ] || [ "$DEBIAN_ARCH" = "arm64" ]; then \
        CHROME_ARCH="linux-arm64"; \
        CHROME_DIR="chromedriver-linux-arm64"; \
    else \
        CHROME_ARCH="linux64"; \
        CHROME_DIR="chromedriver-linux64"; \
    fi \
    && echo "Using ChromeDriver architecture: $CHROME_ARCH" \
    && wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/$CHROME_ARCH/$CHROME_DIR.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/$CHROME_DIR/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && echo "=== VERSION CHECK ===" \
    && google-chrome --version \
    && chromedriver --version \
    && echo "Final architecture: $(uname -m)" \
    && echo "Final Debian arch: $(dpkg --print-architecture)"

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
ENV CHROME_BIN=/usr/bin/google-chrome-stable
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