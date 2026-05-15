# SentientLog

AI-driven observability platform. Ingests high-frequency website interaction logs into ClickHouse and answers performance questions via Text-to-SQL.

## Quick Start

### 1. Start ClickHouse

```bash
docker compose up -d
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY for the AI query agent
```

### 3. Install & run migration

```bash
npm install
npm run migrate
```

### 4. Start the server

```bash
npm run dev
```

The server starts on `http://localhost:3100`.

## API

### `POST /api/v1/ingest`

Accepts a batch of log events. Returns `202 Accepted` immediately — events are buffered in memory and flushed to ClickHouse every 5 seconds or when the buffer reaches 1,000 items.

```json
{
  "events": [
    {
      "event_type": "page_view",
      "url": "/dashboard",
      "latency_ms": 142.5,
      "metadata": { "referrer": "google.com" }
    }
  ]
}
```

### `POST /api/v1/query`

Accepts a natural-language question about your logs. The AnalyticAgent converts it to ClickHouse SQL, executes it, and returns the results.

```json
{ "question": "What is the p99 latency for page views in the last hour?" }
```

### `GET /health`

Returns `{ "status": "ok" }`.

## Project Structure

```
.
├── app/                    Python FastAPI Backend
│   ├── ai/                 AI query planner and prompt logic
│   ├── analytics/          SQL builder and validation
│   ├── api/                FastAPI routes (ingest, query, health)
│   ├── core/               Config and utilities
│   ├── db/                 ClickHouse client and initialization
│   ├── ingestion/          Background task worker and buffering
│   ├── schemas/            Pydantic validation models
│   └── main.py             FastAPI application entry point
│
└── frontend/               React Vite Frontend
    └── src/
        ├── components/     Reusable UI & Layout components
        ├── lib/            Utility functions
        ├── pages/          React Router view pages
        ├── services/       API client (Axios)
        ├── store/          Global Zustand state
        ├── types/          TypeScript interfaces
        ├── App.tsx         Router and providers
        └── main.tsx        React entry point
```
