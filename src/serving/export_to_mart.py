"""
================================================================================
SERVING LAYER ENGINE: DUAL RELATIONAL MART EXPORTER (SQLITE & POSTGRESQL)
================================================================================
Purpose:
  Sinks Gold-tier Parquet files into:
    1. Local High-Speed SQLite Mart (`ecommerce_mart.db`)
    2. Enterprise PostgreSQL Data Warehouse (Docker: port 5433)
  Builds performance B-Tree indices to ensure sub-millisecond analytical query latency.
================================================================================
"""

import sys
import time
import sqlite3
from pathlib import Path
from typing import Optional, List
import pandas as pd

# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PATHS, POSTGRES

class ServingMartExporter:
    """Manages data transfer and indexing to SQLite and PostgreSQL serving marts."""

    INDEX_DEFINITIONS: List[str] = [
        "CREATE INDEX IF NOT EXISTS idx_orders_pk ON fact_orders(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON fact_orders(customer_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_date ON fact_orders(purchase_date_key);",
        "CREATE INDEX IF NOT EXISTS idx_orders_delayed ON fact_orders(is_delayed);",
        "CREATE INDEX IF NOT EXISTS idx_customers_pk ON dim_customers(customer_id);",
        "CREATE INDEX IF NOT EXISTS idx_rfm_segment ON agg_rfm_segments(customer_segment);"
    ]

    # Loading order ensures Dimension tables loaded before Fact tables (Referential Integrity)
    TABLES_TO_EXPORT: List[str] = [
        "dim_customers",
        "dim_sellers",
        "dim_products",
        "dim_dates",
        "fact_orders",
        "agg_rfm_segments",
        "agg_logistics_sankey_flow",
        "agg_monthly_executive_kpi"
    ]

    def __init__(self, gold_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        self.gold_dir = Path(gold_dir) if gold_dir else PATHS.gold_dir
        self.db_path = Path(db_path) if db_path else PATHS.sqlite_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _export_to_sqlite(self):
        print("  [*] Sinking Gold Lakehouse into SQLite Mart...")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for table_name in self.TABLES_TO_EXPORT:
                parquet_file = self.gold_dir / f"{table_name}.parquet"
                if not parquet_file.exists():
                    continue
                df = pd.read_parquet(parquet_file)
                dt_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns
                for col in dt_cols:
                    df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                df.to_sql(table_name, conn, if_exists="replace", index=False)

            for idx_sql in self.INDEX_DEFINITIONS:
                cursor.execute(idx_sql)
            conn.commit()

    def _export_to_postgres(self) -> bool:
        """Sinks Gold Lakehouse into PostgreSQL Docker Container."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(POSTGRES.connection_uri, pool_pre_ping=True)
            
            print(f"  [*] PostgreSQL Warehouse live on {POSTGRES.host}:{POSTGRES.port} ({POSTGRES.database})")
            
            # Drop tables cleanly in reverse dependency order without locking schema
            with engine.connect() as conn:
                for tbl in reversed(self.TABLES_TO_EXPORT):
                    conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE;"))
                conn.commit()
            
            # Execute DDL
            ddl_path = PATHS.sql_ddl_path
            if ddl_path.exists():
                print("      -> Initializing PostgreSQL DDL schema & B-Tree indexes...")
                with engine.connect() as conn:
                    with open(ddl_path, "r", encoding="utf-8") as ddl_file:
                        raw_sql = ddl_file.read()
                        statements = [s.strip() for s in raw_sql.split(";") if s.strip()]
                        for stmt in statements:
                            conn.execute(text(stmt))
                    conn.commit()

            # Load Tables in topological foreign-key order
            print("      -> Bulk-loading Gold Parquet tables into PostgreSQL...")
            for table_name in self.TABLES_TO_EXPORT:
                parquet_file = self.gold_dir / f"{table_name}.parquet"
                if not parquet_file.exists():
                    continue
                df = pd.read_parquet(parquet_file)
                print(f"         * {table_name:<28} ({len(df):,} rows)...", end="", flush=True)
                start_t = time.time()
                df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=5000, method="multi")
                print(f" done in {time.time() - start_t:.1f}s")

            print("  [SUCCESS] PostgreSQL Data Warehouse successfully populated and indexed!")
            return True
        except Exception as exc:
            print(f"  [WARN] PostgreSQL sink error ({exc}).")
            return False

    def export_all(self) -> Path:
        print("\n[SERVING MART EXPORT] Sinking Gold Lakehouse into Analytical Marts...")
        print("=" * 75)
        start_time = time.time()

        # 1. SQLite Local Export
        self._export_to_sqlite()
        
        # 2. PostgreSQL Enterprise Export
        self._export_to_postgres()

        elapsed = time.time() - start_time
        size_mb = self.db_path.stat().st_size / (1024 * 1024)
        print("=" * 75)
        print(f"[SERVING MART READY] Dual Serving Mart ready in {elapsed:.2f}s\n")
        return self.db_path

def export_gold_to_mart(base_dir: Optional[str] = None) -> str:
    exporter = ServingMartExporter(
        gold_dir=Path(base_dir) / "data" / "gold" if base_dir else None,
        db_path=Path(base_dir) / "data" / "serving" / "ecommerce_mart.db" if base_dir else None
    )
    return str(exporter.export_all())

if __name__ == "__main__":
    export_gold_to_mart()
