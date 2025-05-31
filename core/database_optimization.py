"""
Database optimization utilities for query performance.
"""
from typing import Any, Dict, List, Optional
from functools import wraps
from sqlalchemy import text
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import ClauseElement
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryProfiler:
    """Profile database queries for performance analysis"""
    
    def __init__(self):
        self.query_stats: List[Dict[str, Any]] = []
    
    def profile_query(self, query: Query, db: Session) -> Dict[str, Any]:
        """Profile a SQLAlchemy query using EXPLAIN ANALYZE"""
        compiled = query.statement.compile(compile_kwargs={"literal_binds": True})
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS) {compiled}"
        
        start_time = time.time()
        result = db.execute(text(explain_query)).fetchall()
        execution_time = time.time() - start_time
        
        # Parse execution plan
        plan_lines = [row[0] for row in result]
        total_time = self._extract_total_time(plan_lines)
        
        stats = {
            "query": str(compiled),
            "execution_time": execution_time,
            "total_time": total_time,
            "plan": plan_lines,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.query_stats.append(stats)
        return stats
    
    def _extract_total_time(self, plan_lines: List[str]) -> Optional[float]:
        """Extract total execution time from EXPLAIN output"""
        for line in plan_lines:
            if "Execution Time:" in line:
                time_str = line.split("Execution Time:")[1].strip().split(" ")[0]
                return float(time_str)
        return None
    
    def get_slow_queries(self, threshold_ms: float = 50) -> List[Dict[str, Any]]:
        """Get queries slower than threshold"""
        return [
            stat for stat in self.query_stats
            if stat.get("total_time", 0) > threshold_ms
        ]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        if not self.query_stats:
            return {"status": "no_queries"}
        
        total_queries = len(self.query_stats)
        slow_queries = self.get_slow_queries()
        avg_time = sum(s.get("total_time", 0) for s in self.query_stats) / total_queries
        
        return {
            "total_queries": total_queries,
            "slow_queries": len(slow_queries),
            "average_time_ms": avg_time,
            "slowest_queries": sorted(
                slow_queries,
                key=lambda x: x.get("total_time", 0),
                reverse=True
            )[:10]
        }


class QueryOptimizer:
    """Optimize database queries with eager loading and batching"""
    
    @staticmethod
    def optimize_n_plus_one(query: Query, relationships: List[str]) -> Query:
        """Add eager loading to prevent N+1 queries"""
        from sqlalchemy.orm import joinedload
        
        for rel in relationships:
            query = query.options(joinedload(rel))
        return query
    
    @staticmethod
    def add_pagination(query: Query, page: int, per_page: int) -> Query:
        """Add optimized pagination"""
        offset = (page - 1) * per_page
        return query.limit(per_page).offset(offset)
    
    @staticmethod
    def batch_insert(db: Session, model_class: Any, items: List[Dict[str, Any]], 
                    batch_size: int = 1000):
        """Batch insert for better performance"""
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            db.bulk_insert_mappings(model_class, batch)
            db.commit()
    
    @staticmethod
    def optimize_count_query(query: Query) -> int:
        """Optimize count queries by removing unnecessary joins and ordering"""
        from sqlalchemy import func
        
        # Remove ordering which is not needed for counts
        query = query.order_by(None)
        
        # Use COUNT(*) which is generally faster
        return query.with_entities(func.count()).scalar()


def profile_db_operation(func):
    """Decorator to profile database operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"DB Operation {func.__name__} completed in {execution_time:.3f}s"
            )
            
            # Log slow operations
            if execution_time > 1.0:
                logger.warning(
                    f"Slow DB operation detected: {func.__name__} took {execution_time:.3f}s"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"DB Operation {func.__name__} failed after {execution_time:.3f}s: {str(e)}"
            )
            raise
    
    return wrapper


class ConnectionPoolMonitor:
    """Monitor database connection pool health"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status"""
        pool = self.engine.pool
        
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow()
        }
    
    def log_pool_status(self):
        """Log connection pool status"""
        status = self.get_pool_status()
        logger.info(f"Connection pool status: {status}")
        
        # Warn if pool is exhausted
        if status["checked_out"] >= status["total"]:
            logger.warning("Connection pool exhausted!")


# Query optimization hints
OPTIMIZATION_HINTS = {
    "use_indexes": "Ensure proper indexes exist for WHERE and JOIN columns",
    "limit_columns": "Select only required columns instead of SELECT *",
    "avoid_or": "Replace OR conditions with UNION when possible",
    "batch_operations": "Use bulk operations for multiple inserts/updates",
    "connection_pooling": "Configure appropriate connection pool size",
    "query_caching": "Cache frequently accessed, rarely changing data",
    "explain_analyze": "Use EXPLAIN ANALYZE to understand query performance",
    "vacuum_analyze": "Run VACUUM ANALYZE regularly to update statistics"
}