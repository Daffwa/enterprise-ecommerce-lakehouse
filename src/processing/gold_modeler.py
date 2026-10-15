"""
================================================================================
GOLD MODELING ENGINE: KIMBALL STAR SCHEMA & ADVANCED MARTS (REFACTORED)
================================================================================
Purpose:
  Builds Ralph Kimball Star Schema and specialized Business Marts on top of Silver Parquet.
Refactoring Highlights:
  - Object-Oriented architecture (`GoldDimensionalModeler`) with clean separation.
  - Pure vectorized pandas/numpy logic for sub-second execution.
  - Decoupled Dimension, Fact, and Data Mart builders.
================================================================================
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd

# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PATHS

class GoldDimensionalModeler:
    """Constructs analytical facts, dimensions, and aggregated business data marts."""

    def __init__(self, silver_dir: Optional[Path] = None, gold_dir: Optional[Path] = None):
        self.silver_dir = Path(silver_dir) if silver_dir else PATHS.silver_dir
        self.gold_dir = Path(gold_dir) if gold_dir else PATHS.gold_dir
        self.gold_dir.mkdir(parents=True, exist_ok=True)

    def _load_silver_tables(self) -> Dict[str, pd.DataFrame]:
        return {
            "customers": pd.read_parquet(self.silver_dir / "silver_customers.parquet"),
            "sellers": pd.read_parquet(self.silver_dir / "silver_sellers.parquet"),
            "products": pd.read_parquet(self.silver_dir / "silver_products.parquet"),
            "orders": pd.read_parquet(self.silver_dir / "silver_orders.parquet"),
            "items": pd.read_parquet(self.silver_dir / "silver_order_items.parquet"),
            "payments": pd.read_parquet(self.silver_dir / "silver_order_payments.parquet"),
            "reviews": pd.read_parquet(self.silver_dir / "silver_order_reviews.parquet")
        }

    def build_dimensions(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """Constructs and persists Kimball dimension tables."""
        print("  [*] Building Kimball Dimension tables...")
        counts = {}

        # 1. dim_customers
        dim_cust = tables["customers"][[
            "customer_id", "customer_unique_id", "customer_zip_code_prefix", 
            "customer_city", "customer_state"
        ]].copy()
        dim_cust.to_parquet(self.gold_dir / "dim_customers.parquet", compression="snappy", index=False)
        counts["dim_customers"] = len(dim_cust)

        # 2. dim_sellers
        dim_sel = tables["sellers"][[
            "seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"
        ]].copy()
        dim_sel.to_parquet(self.gold_dir / "dim_sellers.parquet", compression="snappy", index=False)
        counts["dim_sellers"] = len(dim_sel)

        # 3. dim_products
        dim_prod = tables["products"][[
            "product_id", "product_category_name_english", "product_weight_g", "product_photos_qty"
        ]].copy().rename(columns={"product_category_name_english": "category_name"})
        dim_prod.to_parquet(self.gold_dir / "dim_products.parquet", compression="snappy", index=False)
        counts["dim_products"] = len(dim_prod)

        # 4. dim_dates
        min_date = tables["orders"]["order_purchase_timestamp"].min().date()
        max_date = tables["orders"]["order_purchase_timestamp"].max().date()
        date_range = pd.date_range(start=min_date, end=max_date, freq="D")
        dim_dates = pd.DataFrame({
            "date_key": date_range.strftime("%Y%m%d").astype(int),
            "full_date": date_range,
            "year": date_range.year,
            "quarter": date_range.quarter,
            "month": date_range.month,
            "month_name": date_range.strftime("%B"),
            "day": date_range.day,
            "day_of_week": date_range.dayofweek + 1,
            "day_name": date_range.strftime("%A"),
            "is_weekend": (date_range.dayofweek >= 5).astype(int)
        })
        dim_dates.to_parquet(self.gold_dir / "dim_dates.parquet", compression="snappy", index=False)
        counts["dim_dates"] = len(dim_dates)

        return counts

    def build_fact_orders(self, tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Constructs core fact table with calculated revenue, freight, and SLA metrics."""
        print("  [*] Building `fact_orders` with logistics SLA calculations...")
        
        # Aggregate Items
        item_agg = tables["items"].groupby("order_id").agg(
            order_item_count=("order_item_id", "count"),
            total_price=("price", "sum"),
            total_freight=("freight_value", "sum")
        ).reset_index()

        # Aggregate Payments
        pay_agg = tables["payments"].groupby("order_id").agg(
            total_payment_value=("payment_value", "sum"),
            max_installments=("payment_installments", "max"),
            primary_payment_type=("payment_type", lambda x: x.mode()[0] if not x.empty else "other")
        ).reset_index()

        # Aggregate Reviews
        rev_agg = tables["reviews"].groupby("order_id").agg(
            review_score=("review_score", "mean")
        ).reset_index()

        # Merge Fact
        fact = tables["orders"].copy()
        fact = fact.merge(item_agg, on="order_id", how="left")
        fact = fact.merge(pay_agg, on="order_id", how="left")
        fact = fact.merge(rev_agg, on="order_id", how="left")

        # Invariants & Defaults
        fact["order_item_count"] = fact["order_item_count"].fillna(0).astype(int)
        fact["total_price"] = fact["total_price"].fillna(0.0).astype(float)
        fact["total_freight"] = fact["total_freight"].fillna(0.0).astype(float)
        fact["total_order_value"] = fact["total_price"] + fact["total_freight"]
        fact["max_installments"] = fact["max_installments"].fillna(1).astype(int)
        fact["primary_payment_type"] = fact["primary_payment_type"].fillna("not_defined")
        fact["review_score"] = fact["review_score"].fillna(5.0).astype(float)
        fact["purchase_date_key"] = fact["order_purchase_timestamp"].dt.strftime("%Y%m%d").astype(float).fillna(0).astype(int)

        # SLA Durations
        delivered_mask = fact["order_delivered_customer_date"].notnull()
        fact["actual_delivery_days"] = np.nan
        fact.loc[delivered_mask, "actual_delivery_days"] = (
            fact.loc[delivered_mask, "order_delivered_customer_date"] - fact.loc[delivered_mask, "order_purchase_timestamp"]
        ).dt.total_seconds() / (24 * 3600)

        fact["estimated_delivery_days"] = (
            fact["order_estimated_delivery_date"] - fact["order_purchase_timestamp"]
        ).dt.total_seconds() / (24 * 3600)

        fact["delivery_delay_days"] = np.nan
        fact.loc[delivered_mask, "delivery_delay_days"] = (
            fact.loc[delivered_mask, "order_delivered_customer_date"] - fact.loc[delivered_mask, "order_estimated_delivery_date"]
        ).dt.total_seconds() / (24 * 3600)

        fact["is_delayed"] = 0
        fact.loc[fact["delivery_delay_days"] > 0, "is_delayed"] = 1

        fact.to_parquet(self.gold_dir / "fact_orders.parquet", compression="snappy", index=False)
        print(f"      -> Wrote {len(fact):,} rows to fact_orders.parquet")
        return fact

    def build_rfm_mart(self, fact_orders: pd.DataFrame, tables: Dict[str, pd.DataFrame]) -> int:
        """Computes customer RFM behavioral segments."""
        print("  [*] Computing RFM Customer Segmentation...")
        delivered = fact_orders[fact_orders["order_status"] == "delivered"].merge(
            tables["customers"][["customer_id", "customer_unique_id", "customer_city", "customer_state"]],
            on="customer_id", how="inner"
        )

        ref_date = delivered["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
        rfm = delivered.groupby("customer_unique_id").agg(
            recency=("order_purchase_timestamp", lambda x: (ref_date - x.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("total_order_value", "sum"),
            customer_city=("customer_city", "first"),
            customer_state=("customer_state", "first")
        ).reset_index()

        rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm["f_score"] = np.where(rfm["frequency"] >= 3, 5, np.where(rfm["frequency"] == 2, 4, 1))
        rfm["m_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm["rfm_score"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)

        def classify_segment(row):
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"
            elif r >= 3 and f >= 3:
                return "Loyal Customers"
            elif r >= 4 and f <= 2:
                return "New / Promising"
            elif r <= 2 and f >= 3:
                return "At Risk"
            elif r <= 2 and f <= 2 and m >= 4:
                return "High Value Churned"
            elif r <= 2 and f <= 2:
                return "Hibernating / Lost"
            return "Potential Loyalists"

        rfm["customer_segment"] = rfm.apply(classify_segment, axis=1)
        rfm.to_parquet(self.gold_dir / "agg_rfm_segments.parquet", compression="snappy", index=False)
        print(f"      -> Wrote {len(rfm):,} customer profiles to agg_rfm_segments.parquet")
        return len(rfm)

    def build_sankey_mart(self, fact_orders: pd.DataFrame, tables: Dict[str, pd.DataFrame]) -> int:
        """Constructs multi-echelon logistics flow matrix for D3.js."""
        print("  [*] Computing Inter-State Logistics Flow Matrix for D3.js...")
        flow = tables["items"][["order_id", "seller_id"]].drop_duplicates().merge(
            tables["sellers"][["seller_id", "seller_state"]], on="seller_id", how="inner"
        ).merge(
            fact_orders[["order_id", "customer_id", "is_delayed", "total_order_value", "order_status"]], on="order_id", how="inner"
        ).merge(
            tables["customers"][["customer_id", "customer_state"]], on="customer_id", how="inner"
        )
        flow = flow[flow["order_status"] == "delivered"]

        top_sellers = flow["seller_state"].value_counts().nlargest(5).index.tolist()
        top_buyers = flow["customer_state"].value_counts().nlargest(6).index.tolist()

        flow["src_stage"] = flow["seller_state"].apply(lambda s: f"Seller: {s}" if s in top_sellers else "Seller: Other States")
        flow["hub_stage"] = "National Carrier Hub"
        flow["dst_stage"] = flow["customer_state"].apply(lambda s: f"Buyer: {s}" if s in top_buyers else "Buyer: Other States")
        flow["out_stage"] = flow["is_delayed"].apply(lambda d: "Delivery: SLA Breached (Late)" if d == 1 else "Delivery: On-Time Target")

        step1 = flow.groupby(["src_stage", "hub_stage"]).agg(volume=("order_id", "count"), total_gmv=("total_order_value", "sum")).reset_index().rename(columns={"src_stage": "source", "hub_stage": "target"})
        step2 = flow.groupby(["hub_stage", "dst_stage"]).agg(volume=("order_id", "count"), total_gmv=("total_order_value", "sum")).reset_index().rename(columns={"hub_stage": "source", "dst_stage": "target"})
        step3 = flow.groupby(["dst_stage", "out_stage"]).agg(volume=("order_id", "count"), total_gmv=("total_order_value", "sum")).reset_index().rename(columns={"dst_stage": "source", "out_stage": "target"})

        sankey = pd.concat([step1, step2, step3], ignore_index=True)
        sankey.to_parquet(self.gold_dir / "agg_logistics_sankey_flow.parquet", compression="snappy", index=False)
        print(f"      -> Wrote {len(sankey)} flow links to agg_logistics_sankey_flow.parquet")
        return len(sankey)

    def build_executive_kpis(self, fact_orders: pd.DataFrame) -> int:
        """Aggregates monthly C-level financial and SLA trajectory."""
        print("  [*] Computing Executive Monthly KPIs...")
        fact = fact_orders.copy()
        fact["year_month"] = fact["order_purchase_timestamp"].dt.strftime("%Y-%m")

        kpi = fact.groupby("year_month").agg(
            total_orders=("order_id", "count"),
            total_gmv=("total_order_value", "sum"),
            avg_order_value=("total_order_value", "mean"),
            total_delayed_orders=("is_delayed", "sum"),
            avg_review_score=("review_score", "mean"),
            avg_delivery_days=("actual_delivery_days", "mean")
        ).reset_index()

        kpi["sla_breach_rate_pct"] = (kpi["total_delayed_orders"] / kpi["total_orders"]) * 100
        kpi = kpi.sort_values("year_month")
        kpi.to_parquet(self.gold_dir / "agg_monthly_executive_kpi.parquet", compression="snappy", index=False)
        print(f"      -> Wrote {len(kpi)} months of KPI history to agg_monthly_executive_kpi.parquet")
        return len(kpi)

    def model_all(self) -> Dict[str, int]:
        """Runs complete Gold tier dimensional modeling pipeline."""
        print("\n[GOLD MODELING] Building Enterprise Star Schema & Business Data Marts...")
        print("=" * 75)
        start_time = time.time()
        
        tables = self._load_silver_tables()
        stats = self.build_dimensions(tables)
        
        fact_orders = self.build_fact_orders(tables)
        stats["fact_orders"] = len(fact_orders)
        stats["agg_rfm_segments"] = self.build_rfm_mart(fact_orders, tables)
        stats["agg_logistics_sankey_flow"] = self.build_sankey_mart(fact_orders, tables)
        stats["agg_monthly_executive_kpi"] = self.build_executive_kpis(fact_orders)

        elapsed = time.time() - start_time
        print("=" * 75)
        print(f"[GOLD COMPLETE] Built Star Schema & Advanced Marts in {elapsed:.2f}s\n")
        return stats

def run_gold_modeling(base_dir: Optional[str] = None) -> Dict[str, int]:
    """Public procedural wrapper."""
    modeler = GoldDimensionalModeler(
        silver_dir=Path(base_dir) / "data" / "silver" if base_dir else None,
        gold_dir=Path(base_dir) / "data" / "gold" if base_dir else None
    )
    return modeler.model_all()

if __name__ == "__main__":
    run_gold_modeling()
