FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 \
    && apt-get clean

# Set working directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install --with-deps

# Copy code
COPY . .

CMD ["python", "login_test.py"]
