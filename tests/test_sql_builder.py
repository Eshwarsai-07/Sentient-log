import pytest
from app.schemas.query import QueryPlan
from app.analytics.sql_builder import SqlBuilder, SqlBuilderError

def test_sql_builder_valid_plan():
    plan = QueryPlan(
        metric="latency_ms",
        aggregation="p95",
        group_by=["url"],
        limit=10,
        timeframe="24h"
    )
    builder = SqlBuilder(plan)
    sql = builder.build()
    
    assert "SELECT url, quantile(0.95)(latency_ms) AS p95_latency_ms FROM events WHERE timestamp >=" in sql
    assert "GROUP BY url" in sql
    assert "LIMIT 10" in sql

def test_sql_builder_invalid_metric():
    plan = QueryPlan(metric="password_hash")
    builder = SqlBuilder(plan)
    with pytest.raises(SqlBuilderError):
        builder.build()

def test_sql_builder_invalid_aggregation():
    plan = QueryPlan(metric="latency_ms", aggregation="DELETE")
    builder = SqlBuilder(plan)
    with pytest.raises(SqlBuilderError):
        builder.build()
