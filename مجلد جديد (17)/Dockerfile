FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# تثبيت Chromium و ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxrandr2 \
    libxrender1 \
    libdbus-glib-1-2 \
    libfontconfig1 \
    fonts-liberation \
    xdg-utils \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# تعيين المتغيرات
ENV PATH="/usr/lib/chromium/:$PATH"
ENV CHROME_BIN="/usr/bin/chromium"
ENV CHROMEDRIVER_BIN="/usr/bin/chromedriver"

# نسخ التطبيق وتثبيت المتطلبات
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
