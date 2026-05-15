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
src/
├── api/            Routes and controllers
│   └── routes/
│       ├── ingest.ts   Batch ingestion endpoint
│       └── query.ts    AI-powered query endpoint
├── db/             ClickHouse client and migrations
│   ├── client.ts
│   └── migrations/
├── services/       Core logic
│   ├── BatchIngester.ts   Memory buffer + periodic flush
│   └── AnalyticAgent.ts   Text-to-SQL via OpenAI
└── types/          TypeScript interfaces
    └── log.ts
```
