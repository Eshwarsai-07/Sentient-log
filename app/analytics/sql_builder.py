import logging
from app.schemas.query import QueryPlan
from app.core.utils import aggregation_alias

logger = logging.getLogger(__name__)

ALLOWED_METRICS = {"latency_ms", "event_type", "url", "user_agent", "timestamp", "event_id", "*"}
ALLOWED_AGGREGATIONS = {"avg", "count", "sum", "min", "max", "p95", "p99"}
ALLOWED_GROUP_BYS = {"url", "event_type", "user_agent", "toStartOfMinute(timestamp)", "toStartOfHour(timestamp)", "toStartOfDay(timestamp)"}

class SqlBuilderError(Exception):
    pass

class SqlBuilder:
    def __init__(self, plan: QueryPlan):
        self.plan = plan

    def build(self) -> str:
        self._validate()

        select_clause = self._build_select()
        where_clause = self._build_where()
        group_by_clause = self._build_group_by()
        order_by_clause = self._build_order_by()
        limit_clause = f"LIMIT {self.plan.limit}"

        sql = f"SELECT {select_clause} FROM events WHERE {where_clause}"
        if group_by_clause:
            sql += f" GROUP BY {group_by_clause}"
        if order_by_clause:
            sql += f" ORDER BY {order_by_clause}"
        sql += f" {limit_clause}"

        return sql

    def _validate(self):
        if self.plan.metric and self.plan.metric not in ALLOWED_METRICS:
            raise SqlBuilderError(f"Invalid metric: {self.plan.metric}")
        if self.plan.aggregation and self.plan.aggregation not in ALLOWED_AGGREGATIONS:
            raise SqlBuilderError(f"Invalid aggregation: {self.plan.aggregation}")
        for gb in self.plan.group_by:
            if gb not in ALLOWED_GROUP_BYS:
                raise SqlBuilderError(f"Invalid group by column: {gb}")
        for k in self.plan.filters.keys():
            if k not in ALLOWED_METRICS:
                raise SqlBuilderError(f"Invalid filter column: {k}")
                
        if self.plan.order_by:
            field = self.plan.order_by.field
            allowed_order_fields = set(self.plan.group_by)
            
            if self.plan.metric and self.plan.aggregation:
                alias = aggregation_alias(self.plan.aggregation, self.plan.metric)
                allowed_order_fields.add(alias)
            elif self.plan.metric:
                allowed_order_fields.add(self.plan.metric)
                
            logger.info(f"Validator decisions: Allowed order_by fields: {allowed_order_fields}")
                
            if field not in allowed_order_fields:
                raise SqlBuilderError(f"Invalid order_by field: {field}. Must be one of {allowed_order_fields}")

    def _build_select(self) -> str:
        select_parts = []
        if self.plan.group_by:
            select_parts.extend(self.plan.group_by)
        
        if self.plan.aggregation and self.plan.metric:
            agg = self.plan.aggregation
            metric = self.plan.metric
            alias = aggregation_alias(agg, metric)
            logger.info(f"Calculated aggregation alias: {alias}")
            
            if agg == "p95":
                select_parts.append(f"quantile(0.95)({metric}) AS {alias}")
            elif agg == "p99":
                select_parts.append(f"quantile(0.99)({metric}) AS {alias}")
            elif agg == "count" and metric == "*":
                select_parts.append(f"count(*) AS {alias}")
            else:
                select_parts.append(f"{agg}({metric}) AS {alias}")
        elif self.plan.metric:
            if not self.plan.group_by or self.plan.metric in self.plan.group_by:
                select_parts.append(self.plan.metric)
            else:
                raise SqlBuilderError("Metric must be aggregated if grouping by other columns")
        
        if not select_parts:
            return "*"
            
        return ", ".join(select_parts)

    def _build_where(self) -> str:
        conditions = []
        
        # Timeframe mapping
        tf = self.plan.timeframe
        if tf.endswith("h"):
            hours = int(tf[:-1])
            conditions.append(f"timestamp >= now() - INTERVAL {hours} HOUR")
        elif tf.endswith("d"):
            days = int(tf[:-1])
            conditions.append(f"timestamp >= now() - INTERVAL {days} DAY")
        elif tf.endswith("m"):
            mins = int(tf[:-1])
            conditions.append(f"timestamp >= now() - INTERVAL {mins} MINUTE")
        else:
            conditions.append("timestamp >= now() - INTERVAL 1 DAY")

        for k, v in self.plan.filters.items():
            if isinstance(v, str):
                # Simple escape to prevent SQL injection
                safe_val = v.replace("'", "''")
                conditions.append(f"{k} = '{safe_val}'")
            elif isinstance(v, (int, float)):
                conditions.append(f"{k} = {v}")
                
        return " AND ".join(conditions)

    def _build_group_by(self) -> str:
        if not self.plan.group_by:
            return ""
        return ", ".join(self.plan.group_by)

    def _build_order_by(self) -> str:
        if not self.plan.order_by:
            return ""
        
        field = self.plan.order_by.field
        direction = self.plan.order_by.direction.upper()
        return f"{field} {direction}"
