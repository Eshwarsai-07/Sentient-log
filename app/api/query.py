from fastapi import APIRouter, HTTPException
import logging
from app.schemas.query import QueryRequest, QueryResponse
from app.ai.planner import Planner
from app.analytics.sql_builder import SqlBuilder, SqlBuilderError
from app.clickhouse.client import get_client

logger = logging.getLogger(__name__)
router = APIRouter()
planner = Planner()

@router.post("/query", response_model=QueryResponse)
async def query_logs(payload: QueryRequest):
    try:
        # 1. Extract Structured Intent
        query_plan = await planner.get_query_plan(payload.question)
        logger.info(f"Generated QueryPlan: {query_plan.model_dump_json()}")
        
        # 2. Build and Validate SQL
        builder = SqlBuilder(query_plan)
        sql = builder.build()
        logger.info(f"Generated SQL: {sql}")
        
        # 3. Execute
        client = await get_client()
        result_set = await client.query(sql)
        
        # Format results to list of dicts
        results = []
        if result_set.result_rows:
            columns = result_set.column_names
            for row in result_set.result_rows:
                results.append(dict(zip(columns, row)))
                
        return QueryResponse(
            question=payload.question,
            query_plan=query_plan,
            sql=sql,
            results=results
        )
    except SqlBuilderError as e:
        raise HTTPException(status_code=400, detail=f"Invalid query plan: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
