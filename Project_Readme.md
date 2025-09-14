# Particle Agent

This is a conversational agent for the e-commerce website PartSelect.

## A sneak Peek
- Backend: FastAPI (endpoint - (`/chat`)), LangChain, Pinecone, OpenAI, DeepSeek
- Frontend: React + Vite (TypeScript), CSS, Axios, UUID
- Vector DB: Pinecone (index: `partselect-parts` with namespaces `products`, `transactions`)
- Retrieval: Few shot prompting, hybrid retrieval 

## Tech stack
- Python 3.10+
- FastAPI, Uvicorn
- LangChain, langchain-openai, langchain-pinecone
- Pinecone
- OpenAI API, DeepSeek API
- Node.js (LTS via nvm), React, Vite, TypeScript, Axios

## 1) Setup options
You can run locally using a Python virtual environment or Docker.

- **Virtual environment**: quickest for development. You’ll install from `requirements.txt`.
- **Docker**: best for consistent, reproducible environments and deployment.

**>> Both options require a `.env` file with your API keys (see “Environment variables”).**

---

## 2) Environment variables

Create a `.env` in the repository root (not committed to git). Example:

```
# Backend
PINECONE_API_KEY=YOUR_KEY
PINECONE_ENVIRONMENT=  
OPENAI_API_KEY=YOUR_KEY
DEEPSEEK_API_KEY=YOUR_KEY

# Frontend
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Tip: keep a tracked template for collaborators:
```
cp .env.example .env
```
(and fill in your own keys locally)

This is how my database looks like. The two namespaces have data pertaining to products (parts of **refrigerators & dishwashers** and **transactions made by customers**.
---

## 3) Run with a Python virtual environment

```bash
# From repo root
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Start the backend (FastAPI):
```bash
# From repo root
uvicorn backend.app:app --reload --port 8000
# API root: http://127.0.0.1:8000/
# Chat endpoint: POST /chat
# Debug endpoint: GET /_debug/pinecone
```

Backend notes:
- **`backend/app.py` is the main entry (contains the `/chat` endpoint).**
- CORS is enabled for `http://localhost:5173` and `http://127.0.0.1:5173`.
>> (When building a frontend-backend app locally, browsers enforce CORS for security. 
The frontend and backend run on different ports, so the browser sends a preflight OPTIONS request.
FastAPI needs CORS middleware to handle this, otherwise you'll get 405 errors 
and network errors in the frontend.) 

---
## 4) Data Ingestion
####  (this is to simulate the experience)
- Generate an API key from the Pinecone project where you want to store the data.
- Ensure you have the following JSON files in the data directory: `parts_data.json` and `transactions_data.json`
- Add the Pinecone API key to your .env file:
```
PINECONE_API_KEY=your_manager_api_key
```
- Run the `pc_vdb.py` file to ingest data. **This will create your index and also the namespaces that I have used (products and transactions).**
   

## 5) Frontend (React + Vite + TypeScript)

I have used NodeJS and there are multiple ways of configuring it on the Ubuntu server. I referred to this link for setting it up on my system, you are free to choose any method but I chose NVM (version manager).

https://www.digitalocean.com/community/tutorials/how-to-install-node-js-on-ubuntu-20-04

Install Node (LTS) via nvm:
```bash
# If you don’t have nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"

# Install and use LTS
nvm install --lts
nvm use --lts
node -v && npm -v
```

Install dependencies and run dev server:
```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

#### Environment for frontend:
- Ensure `.env` at the repo root has `VITE_API_BASE_URL=http://127.0.0.1:8000`.
- Axios reads `VITE_API_BASE_URL` to call the backend.

Scaffold (for reference only; already done in this repo):
```bash
# From frontend/
npm create vite@latest . -- --template react-ts
npm i
npm i axios uuid
npm i -D @types/uuid
```
---
## 6) Project layout

```
backend/
  app.py            # FastAPI app with /chat endpoint (chatpoint)
  core.py           # Chains, retriever, Pinecone utilities
  utils.py          # Intent routing, tools for tool calling
  prompt.yaml       # System prompt for LLM
  test_app.py       # This is to test the backend by calling the chatpoint without a configured frontend

part_agent/          # This is my virtual environment
data/
  parts_data.json
  transactions_data.json
  pc_vdb.py         # This is the main Ingestion file for the vector database on PineCone
frontend/
  src/
    components/
    services/
    types/
requirements.txt
.env                # Please create your own with the required keys.
```
---

## 7) Usage

- Start backend (port 8000).
- Start frontend (port 5173).
- Open the UI and chat. The app:
  - Detects intent (products vs transactions).
  - Pulls context from Pinecone (`products` or `transactions` namespace).
  - Uses tools for simple transactional queries (status/cancel/return).
  - Falls back to LLM with retrieved metadata for richer answers.

---

## 8) Docker vs virtual environment?

- Virtual environment:
  - Faster iteration during development on Linux/macOS.
  - Simple: `pip install -r requirements.txt`, run Uvicorn directly.
---


## 9) Run with Docker (optional)

Quick backend container:
```bash
# Build backend image
docker build -t partselect-backend -f - . <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expose 8000 for FastAPI
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Run (mount .env)
docker run --rm -it --env-file .env -p 8000:8000 partselect-backend
```

Frontend container (optional):
```bash
# Build frontend image
docker build -t partselect-frontend -f - frontend <<'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF

# Run (frontend will call backend via VITE_API_BASE_URL)
docker run --rm -it -p 5173:5173 partselect-frontend
```

Tip: For multi-service dev, consider docker-compose to wire env and ports together.

#### Here is my architecture
<img width="1040" height="582" alt="image" src="https://github.com/user-attachments/assets/c373001a-f04d-4a5a-8d95-8adc5e8a1fac" />

---

## 10) Troubleshooting

- CORS issues:
  - Backend allows `http://localhost:5173` and `http://127.0.0.1:5173`. Adjust in `backend/app.py` if needed.

<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/973e87e4-cce5-4fce-9814-7f4e011b2668" />


