FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do app
COPY . .

# Rodar o Flask
CMD ["python", "app/main.py"]
