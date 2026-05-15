import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.query import QueryPlan

SYSTEM_PROMPT = """You are an AI observability assistant.
Your task is to convert natural language questions into a structured JSON query plan.
The logs schema contains: latency_ms, event_type, url, user_agent, timestamp, event_id.
Allowed aggregations: avg, count, sum, min, max, p95, p99.

CRITICAL INSTRUCTIONS:
1. Respond ONLY with valid JSON matching the QueryPlan schema.
2. NO explanations. NO markdown formatting.
3. NEVER generate raw SQL syntax.
4. The `order_by.field` MUST match exactly either a column in `group_by` or the canonical aggregation alias.

Aggregation aliases MUST follow:
{aggregation}_{metric}

Examples:
avg_latency_ms
count_event_id
sum_latency_ms

Example Output:
{
  "metric": "event_id",
  "aggregation": "count",
  "group_by": ["event_type"],
  "order_by": {
    "field": "count_event_id",
    "direction": "desc"
  },
  "limit": 10,
  "timeframe": "24h"
}
"""

class Planner:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

    async def get_query_plan(self, question: str) -> QueryPlan:
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("No content returned from AI planner")
            
        plan_dict = json.loads(content)
        return QueryPlan.model_validate(plan_dict)
