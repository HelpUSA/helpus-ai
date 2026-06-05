FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cria diretório para o modelo
RUN mkdir -p /app/modelos

# Baixa o modelo Qwen 2.5 3B (versão quantizada Q4_K_M)
RUN echo "Baixando modelo Qwen 2.5 3B..." && \
    curl -L -o /app/modelos/qwen2.5-3b-instruct-q4_k_m.gguf \
    https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf

# Copia o código da aplicação
COPY . .

# Expõe a porta
EXPOSE 8000

# Comando para iniciar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
