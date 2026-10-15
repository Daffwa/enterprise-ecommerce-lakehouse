"""
================================================================================
CENTRALIZED PIPELINE CONFIGURATION & CONSTANTS
================================================================================
Purpose:
  Defines immutable configurations, paths, SLA thresholds, and domain schemas
  used across Bronze, Silver, Gold, Serving, and Visualizer layers.
================================================================================
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

# Base Root Path
PACKAGE_ROOT = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class PathConfig:
    """Centralized directory and file paths."""
    root_dir: Path = PACKAGE_ROOT
    data_dir: Path = PACKAGE_ROOT / "data"
    bronze_dir: Path = PACKAGE_ROOT / "data" / "bronze"
    silver_dir: Path = PACKAGE_ROOT / "data" / "silver"
    gold_dir: Path = PACKAGE_ROOT / "data" / "gold"
    serving_dir: Path = PACKAGE_ROOT / "data" / "serving"
    web_dir: Path = PACKAGE_ROOT / "web"
    configs_dir: Path = PACKAGE_ROOT / "configs"
    
    # Serving Database Path
    sqlite_db_path: Path = PACKAGE_ROOT / "data" / "serving" / "ecommerce_mart.db"
    sql_ddl_path: Path = PACKAGE_ROOT / "configs" / "metabase_database.sql"

@dataclass(frozen=True)
class PostgresConfig:
    """PostgreSQL production serving mart configuration."""
    host: str = "localhost"
    port: int = 5433
    user: str = "postgres_admin"
    password: str = "SecretPassword123!"
    database: str = "ecommerce_mart"

    @property
    def connection_uri(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass(frozen=True)
class IngestionConfig:
    """Data source URLs and timeouts."""
    timeout_seconds: int = 30
    chunk_size: int = 64 * 1024  # 64 KB
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    sources: Dict[str, str] = field(default_factory=lambda: {
        "olist_orders_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_orders_dataset.csv",
        "olist_order_items_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_order_items_dataset.csv",
        "olist_order_payments_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_order_payments_dataset.csv",
        "olist_customers_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_customers_dataset.csv",
        "olist_products_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_products_dataset.csv",
        "olist_sellers_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_sellers_dataset.csv",
        "olist_order_reviews_dataset.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_order_reviews_dataset.csv",
        "product_category_name_translation.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/product_category_name_translation.csv"
    })

@dataclass(frozen=True)
class QualityConfig:
    """Thresholds for automated quality assertions."""
    min_order_count: int = 90_000
    min_customer_count: int = 90_000
    min_review_score: float = 1.0
    max_review_score: float = 5.0
    max_acceptable_delay_rate_pct: float = 30.0

@dataclass(frozen=True)
class ServerConfig:
    """Web visualizer and API configuration."""
    default_host: str = "0.0.0.0"
    default_port: int = 8050

# Global singletons
PATHS = PathConfig()
POSTGRES = PostgresConfig()
INGESTION = IngestionConfig()
QUALITY = QualityConfig()
SERVER = ServerConfig()
