"""
================================================================================
SILVER PROCESSING ENGINE: SCHEMA ENFORCEMENT & SNAPPY PARQUET (REFACTORED)
================================================================================
Purpose:
  Transforms raw Bronze CSVs into cleansed, typed, Snappy-compressed Apache Parquet.
Refactoring Highlights:
  - Object-Oriented design (`SilverLakehouseTransformer`) adhering to SRP.
  - Dedicated private transformation methods per domain entity.
  - Type-safe Pathlib implementation and vectorized pandas operations.
================================================================================
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PATHS

class SilverLakehouseTransformer:
    """Orchestrates cleansing, schema casting, and Parquet serialization."""

    def __init__(self, bronze_dir: Optional[Path] = None, silver_dir: Optional[Path] = None):
        self.bronze_dir = Path(bronze_dir) if bronze_dir else PATHS.bronze_dir
        self.silver_dir = Path(silver_dir) if silver_dir else PATHS.silver_dir
        self.silver_dir.mkdir(parents=True, exist_ok=True)

    def _get_category_translations(self) -> Dict[str, str]:
        trans_path = self.bronze_dir / "product_category_name_translation.csv"
        if not trans_path.exists():
            return {}
        df = pd.read_csv(trans_path)
        return dict(zip(df["product_category_name"], df["product_category_name_english"]))

    def _transform_customers(self) -> int:
        print("  [*] Processing `customers` dataset...")
        df = pd.read_csv(self.bronze_dir / "olist_customers_dataset.csv")
        df["customer_city"] = df["customer_city"].str.title().str.strip()
        df["customer_state"] = df["customer_state"].str.upper().str.strip()
        out_path = self.silver_dir / "silver_customers.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def _transform_sellers(self) -> int:
        print("  [*] Processing `sellers` dataset...")
        df = pd.read_csv(self.bronze_dir / "olist_sellers_dataset.csv")
        df["seller_city"] = df["seller_city"].str.title().str.strip()
        df["seller_state"] = df["seller_state"].str.upper().str.strip()
        out_path = self.silver_dir / "silver_sellers.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def _transform_products(self, translations: Dict[str, str]) -> int:
        print("  [*] Processing `products` dataset with category translation...")
        df = pd.read_csv(self.bronze_dir / "olist_products_dataset.csv")
        df["product_category_name_english"] = df["product_category_name"].map(translations).fillna("Other")
        df["product_name_length"] = df["product_name_lenght"].fillna(0).astype(int)
        df["product_description_length"] = df["product_description_lenght"].fillna(0).astype(int)
        df["product_photos_qty"] = df["product_photos_qty"].fillna(0).astype(int)
        df["product_weight_g"] = df["product_weight_g"].fillna(0.0).astype(float)
        df.drop(columns=["product_name_lenght", "product_description_lenght"], errors="ignore", inplace=True)
        out_path = self.silver_dir / "silver_products.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def _transform_orders(self) -> int:
        print("  [*] Processing `orders` dataset with timestamp normalization...")
        df = pd.read_csv(self.bronze_dir / "olist_orders_dataset.csv")
        time_cols = [
            "order_purchase_timestamp", "order_approved_at",
            "order_delivered_carrier_date", "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
        for col in time_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df["order_status"] = df["order_status"].str.lower().str.strip()
        out_path = self.silver_dir / "silver_orders.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def _transform_order_items(self) -> int:
        print("  [*] Processing `order_items` dataset...")
        df = pd.read_csv(self.bronze_dir / "olist_order_items_dataset.csv")
        df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
        df["price"] = df["price"].astype(float)
        df["freight_value"] = df["freight_value"].astype(float)
        out_path = self.silver_dir / "silver_order_items.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def _transform_order_payments(self) -> int:
        print("  [*] Processing `order_payments` dataset...")
        df = pd.read_csv(self.bronze_dir / "olist_order_payments_dataset.csv")
        df["payment_type"] = df["payment_type"].str.lower().str.strip()
        df["payment_installments"] = df["payment_installments"].astype(int)
        df["payment_value"] = df["payment_value"].astype(float)
        out_path = self.silver_dir / "silver_order_payments.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def _transform_order_reviews(self) -> int:
        print("  [*] Processing `order_reviews` dataset...")
        df = pd.read_csv(self.bronze_dir / "olist_order_reviews_dataset.csv")
        df["review_score"] = df["review_score"].astype(int)
        df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
        df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")
        df["review_comment_title"] = df["review_comment_title"].fillna("").astype(str)
        df["review_comment_message"] = df["review_comment_message"].fillna("").astype(str)
        out_path = self.silver_dir / "silver_order_reviews.parquet"
        df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
        print(f"      -> Wrote {len(df):,} rows to {out_path.name}")
        return len(df)

    def transform_all(self) -> Dict[str, int]:
        """Executes full Silver cleansing pipeline."""
        print("\n[SILVER TRANSFORMATION] Ingesting Bronze CSVs -> Generating Snappy Parquet...")
        print("=" * 75)
        start_time = time.time()
        
        translations = self._get_category_translations()
        stats = {
            "customers": self._transform_customers(),
            "sellers": self._transform_sellers(),
            "products": self._transform_products(translations),
            "orders": self._transform_orders(),
            "order_items": self._transform_order_items(),
            "order_payments": self._transform_order_payments(),
            "order_reviews": self._transform_order_reviews()
        }

        elapsed = time.time() - start_time
        print("=" * 75)
        print(f"[SILVER COMPLETE] Processed 7 core domain entities in {elapsed:.2f}s\n")
        return stats

def run_silver_transformation(base_dir: Optional[str] = None) -> Dict[str, int]:
    """Public procedural wrapper."""
    transformer = SilverLakehouseTransformer(
        bronze_dir=Path(base_dir) / "data" / "bronze" if base_dir else None,
        silver_dir=Path(base_dir) / "data" / "silver" if base_dir else None
    )
    return transformer.transform_all()

if __name__ == "__main__":
    run_silver_transformation()
