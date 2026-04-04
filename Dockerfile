# Build Stage
FROM python:3.12-slim

# Metadados
LABEL maintainer="NutricioneS <coach@nutriciones.com>"
LABEL project="Sabla - Automação Clínica"

# Configurações de Ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV GOOGLE_APPLICATION_CREDENTIALS /app/credentials.json

# Diretório de Trabalho
WORKDIR /app

# Instalação de Dependências de Sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalação de Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do Código Fonte
COPY . .

# Garante que as pastas de dados e logs existam internamente
RUN mkdir -p data logs \
    && chmod -R 777 data logs

# O SQLite será copiado como base (leitura), mas os estados estarão no Redis.
# Idealmente, o taco.sqlite deve ser persistido via Volume caso queira atualizá-lo.
# Por agora, ele entra como asset de leitura imutável no container.

# Porta Exposta para a API
EXPOSE 8000

# Ponto de Entrada (API + Onboarding)
CMD ["python", "main_api.py"]
