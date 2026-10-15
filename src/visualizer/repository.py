"""
================================================================================
MART REPOSITORY: DUAL-STORE DATA ACCESS LAYER (POSTGRESQL & SQLITE)
================================================================================
Purpose:
  Provides resilient, decoupled access to analytical datasets.
  Prefers PostgreSQL Enterprise Warehouse (port 5433), with transparent
  fallback to SQLite Mart (`ecommerce_mart.db`) if container is offline.
================================================================================
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.config import PATHS, POSTGRES

class MartRepository:
    """Resilient Data Access Object supporting both PostgreSQL and SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else PATHS.sqlite_db_path

    def _is_postgres_alive(self) -> bool:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=POSTGRES.host,
                port=POSTGRES.port,
                user=POSTGRES.user,
                password=POSTGRES.password,
                dbname=POSTGRES.database,
                connect_timeout=2
            )
            conn.close()
            return True
        except Exception:
            return False

    def _get_pg_connection(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(
            host=POSTGRES.host,
            port=POSTGRES.port,
            user=POSTGRES.user,
            password=POSTGRES.password,
            dbname=POSTGRES.database,
            cursor_factory=RealDictCursor
        )

    def _get_sqlite_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_executive_kpis(self) -> Dict[str, Any]:
        """Calculates headline operational and financial KPIs."""
        if self._is_postgres_alive():
            with self._get_pg_connection() as conn, conn.cursor() as c:
                c.execute("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(total_order_value) as total_gmv,
                        AVG(total_order_value) as avg_order_value,
                        AVG(actual_delivery_days) as avg_delivery_days,
                        AVG(review_score) as avg_review_score,
                        SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed_orders
                    FROM fact_orders;
                """)
                row = c.fetchone()
                c.execute("SELECT COUNT(DISTINCT customer_unique_id) FROM dim_customers;")
                total_customers = c.fetchone()["count"]
                c.execute("SELECT COUNT(DISTINCT seller_id) FROM dim_sellers;")
                total_sellers = c.fetchone()["count"]
        else:
            with self._get_sqlite_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(total_order_value) as total_gmv,
                        AVG(total_order_value) as avg_order_value,
                        AVG(actual_delivery_days) as avg_delivery_days,
                        AVG(review_score) as avg_review_score,
                        SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed_orders
                    FROM fact_orders;
                """)
                row = c.fetchone()
                c.execute("SELECT COUNT(DISTINCT customer_unique_id) FROM dim_customers;")
                total_customers = c.fetchone()[0]
                c.execute("SELECT COUNT(DISTINCT seller_id) FROM dim_sellers;")
                total_sellers = c.fetchone()[0]

        total_orders = row["total_orders"] or 1
        delayed_orders = row["delayed_orders"] or 0
        sla_breach_pct = (delayed_orders / total_orders) * 100

        return {
            "total_orders": total_orders,
            "total_gmv": round(float(row["total_gmv"] or 0), 2),
            "avg_order_value": round(float(row["avg_order_value"] or 0), 2),
            "avg_delivery_days": round(float(row["avg_delivery_days"] or 0), 1),
            "avg_review_score": round(float(row["avg_review_score"] or 0), 2),
            "sla_breach_pct": round(sla_breach_pct, 1),
            "on_time_pct": round(100 - sla_breach_pct, 1),
            "total_customers": total_customers,
            "total_sellers": total_sellers,
            "backend_engine": "PostgreSQL (Docker: 5433)" if self._is_postgres_alive() else "SQLite Mart"
        }

    def get_sankey_flow(self) -> Dict[str, Any]:
        """Retrieves multi-stage logistics flow for D3 Sankey."""
        if self._is_postgres_alive():
            with self._get_pg_connection() as conn, conn.cursor() as c:
                c.execute("SELECT source, target, volume, total_gmv FROM agg_logistics_sankey_flow;")
                rows = c.fetchall()
        else:
            with self._get_sqlite_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT source, target, volume, total_gmv FROM agg_logistics_sankey_flow;")
                rows = c.fetchall()

        node_names = set()
        for r in rows:
            node_names.add(r["source"])
            node_names.add(r["target"])

        node_list = sorted(list(node_names))
        node_index = {name: idx for idx, name in enumerate(node_list)}

        links = [
            {
                "source": node_index[r["source"]],
                "target": node_index[r["target"]],
                "value": int(r["volume"]),
                "gmv": round(float(r["total_gmv"]), 2),
                "source_name": r["source"],
                "target_name": r["target"]
            }
            for r in rows
        ]

        nodes = [{"name": name} for name in node_list]
        return {"nodes": nodes, "links": links}

    def get_rfm_segments(self) -> List[Dict[str, Any]]:
        """Retrieves customer segmentation aggregated statistics."""
        sql = """
            SELECT 
                customer_segment,
                COUNT(*) as customer_count,
                ROUND(AVG(recency)::numeric, 1) as avg_recency,
                ROUND(AVG(frequency)::numeric, 2) as avg_frequency,
                ROUND(AVG(monetary)::numeric, 2) as avg_monetary,
                ROUND(SUM(monetary)::numeric, 2) as total_segment_revenue
            FROM agg_rfm_segments
            GROUP BY customer_segment
            ORDER BY total_segment_revenue DESC;
        """ if self._is_postgres_alive() else """
            SELECT 
                customer_segment,
                COUNT(*) as customer_count,
                ROUND(AVG(recency), 1) as avg_recency,
                ROUND(AVG(frequency), 2) as avg_frequency,
                ROUND(AVG(monetary), 2) as avg_monetary,
                ROUND(SUM(monetary), 2) as total_segment_revenue
            FROM agg_rfm_segments
            GROUP BY customer_segment
            ORDER BY total_segment_revenue DESC;
        """

        if self._is_postgres_alive():
            with self._get_pg_connection() as conn, conn.cursor() as c:
                c.execute(sql)
                rows = c.fetchall()
                return [{k: float(v) if hasattr(v, '__float__') and not isinstance(v, (int, float, bool)) else v for k, v in dict(r).items()} for r in rows]
        else:
            with self._get_sqlite_connection() as conn:
                c = conn.cursor()
                c.execute(sql)
                return [dict(r) for r in c.fetchall()]

    def get_monthly_trajectory(self) -> List[Dict[str, Any]]:
        """Retrieves 25 months historical revenue and SLA breach trajectory."""
        sql = """
            SELECT 
                year_month,
                total_orders,
                ROUND(total_gmv::numeric, 2) as total_gmv,
                ROUND(avg_order_value::numeric, 2) as avg_order_value,
                ROUND(sla_breach_rate_pct::numeric, 1) as sla_breach_rate_pct,
                ROUND(avg_delivery_days::numeric, 1) as avg_delivery_days
            FROM agg_monthly_executive_kpi
            ORDER BY year_month ASC;
        """ if self._is_postgres_alive() else """
            SELECT 
                year_month,
                total_orders,
                ROUND(total_gmv, 2) as total_gmv,
                ROUND(avg_order_value, 2) as avg_order_value,
                ROUND(sla_breach_rate_pct, 1) as sla_breach_rate_pct,
                ROUND(avg_delivery_days, 1) as avg_delivery_days
            FROM agg_monthly_executive_kpi
            ORDER BY year_month ASC;
        """

        if self._is_postgres_alive():
            with self._get_pg_connection() as conn, conn.cursor() as c:
                c.execute(sql)
                rows = c.fetchall()
                return [{k: float(v) if hasattr(v, '__float__') and not isinstance(v, (int, float, bool)) else v for k, v in dict(r).items()} for r in rows]
        else:
            with self._get_sqlite_connection() as conn:
                c = conn.cursor()
                c.execute(sql)
                return [dict(r) for r in c.fetchall()]

    def get_top_categories(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Retrieves top product categories by catalog volume."""
        if self._is_postgres_alive():
            with self._get_pg_connection() as conn, conn.cursor() as c:
                c.execute("""
                    SELECT category_name, COUNT(product_id) as product_count
                    FROM dim_products
                    WHERE category_name IS NOT NULL AND category_name != 'Other'
                    GROUP BY category_name
                    ORDER BY product_count DESC
                    LIMIT %s;
                """, (limit,))
                return [dict(r) for r in c.fetchall()]
        else:
            with self._get_sqlite_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT category_name, COUNT(product_id) as product_count
                    FROM dim_products
                    WHERE category_name IS NOT NULL AND category_name != 'Other'
                    GROUP BY category_name
                    ORDER BY product_count DESC
                    LIMIT ?;
                """, (limit,))
                return [dict(r) for r in c.fetchall()]
