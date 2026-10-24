# Deployment & Operations Guide

## 1. System Requirements & Environment

### Minimum Production Specifications:
- **CPU**: 4 Cores (8 Cores recommended for local Whisper/Embeddings)
- **RAM**: 8 GB (16 GB recommended for high-volume vector indexing)
- **Storage**: 50 GB SSD
- **OS**: Linux (Ubuntu 22.04 LTS / Debian 12), Windows Server 2022, or macOS

### Runtime Prerequisites:
- Python 3.11 or 3.12
- Node.js 18+ & npm 9+
- Docker & Docker Compose (Optional for containerized Qdrant / Postgres)

---

## 2. Docker & Containerized Deployment

A production-ready `docker-compose.yml` is provided at the repository root:

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: rag_voice_qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant_storage:/qdrant/storage:z
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

  postgres:
    image: postgres:16-alpine
    container_name: rag_voice_postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: production_strong_password
      POSTGRES_DB: rag_voice_db
    volumes:
      - ./data/postgres_data:/var/lib/postgresql/data:z
```

To start supporting services:
```bash
docker compose up -d
```

---

## 3. Bare-Metal / Virtual Machine Deployment

### 3.1 Backend Setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your JWT secret, DB URL, and settings

# 4. Initialize Database & Seed Models
python -m backend.app.core.database

# 5. Start Backend Server via Uvicorn
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3.2 Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Build optimized static bundle
npm run build

# 4. Serve bundle using Nginx or Caddy
# Built assets will be in frontend/dist/
```

---

## 4. Production Reverse Proxy (Nginx Configuration)

```nginx
server {
    listen 443 ssl http2;
    server_name ragvoice.enterprise.internal;

    ssl_certificate /etc/ssl/certs/ragvoice.crt;
    ssl_certificate_key /etc/ssl/private/ragvoice.key;

    # Frontend Single Page App
    location / {
        root /var/www/rag-voice/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API Gateway
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 30M;
    }

    # WebSockets / Streaming
    location /api/voice/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
