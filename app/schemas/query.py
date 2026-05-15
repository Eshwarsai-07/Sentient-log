from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)

class OrderBy(BaseModel):
    field: str = Field(..., description="The exact field name to order by")
    direction: Literal["asc", "desc"] = Field(..., description="Order direction")

class QueryPlan(BaseModel):
    metric: Optional[str] = Field(default=None, description="The column to aggregate or query, e.g., 'latency_ms', 'event_type'")
    aggregation: Optional[str] = Field(default=None, description="The aggregation function to apply, e.g., 'avg', 'count', 'p95'")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Equality filters to apply, e.g., {'event_type': 'http_request'}")
    group_by: List[str] = Field(default_factory=list, description="Columns to group by, e.g., ['url']")
    order_by: Optional[OrderBy] = Field(default=None, description="Order by details")
    limit: int = Field(default=100, le=1000, description="Max rows to return")
    timeframe: str = Field(default="24h", description="Time window, e.g., '1h', '24h', '7d'")

class QueryResponse(BaseModel):
    question: str
    query_plan: QueryPlan
    sql: str
    results: List[Dict[str, Any]]
