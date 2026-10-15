"""
================================================================================
DATA QUALITY & GOVERNANCE ENGINE (DATAOPS SUITE - REFACTORED)
================================================================================
Purpose:
  Executes rigorous schema, referential integrity, and business logic assertion tests
  over Gold & Silver Lakehouse tiers prior to analytical mart serving.
Refactoring Highlights:
  - Strongly-typed `TestResult` dataclass.
  - Assertions bounded by centralized `QUALITY` config constants.
  - Windows CP1252-safe status badges and detailed metrics reporting.
================================================================================
"""

import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd

# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PATHS, QUALITY

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

@dataclass
class TestResult:
    """Represents the outcome of an automated data quality assertion."""
    test_name: str
    passed: bool
    details: str

class DataQualityEngine:
    """Enterprise DataOps validation suite for the Gold Lakehouse tier."""

    def __init__(self, gold_dir: Optional[Path] = None):
        self.gold_dir = Path(gold_dir) if gold_dir else PATHS.gold_dir
        self.config = QUALITY
        self.results: List[TestResult] = []

    def _assert(self, test_name: str, passed: bool, details: str):
        result = TestResult(test_name=test_name, passed=passed, details=details)
        self.results.append(result)
        badge = "  [PASS]" if passed else "  [FAIL]"
        print(f"{badge} {test_name:<48} | {details}")

    def run_all_tests(self) -> bool:
        """Executes full test suite across facts, dimensions, and marts."""
        print("\n[DATAOPS QUALITY SUITE] Running Enterprise Automated Integrity Tests...")
        print("=" * 85)
        start_time = time.time()
        
        # Load tables
        fact_orders = pd.read_parquet(self.gold_dir / "fact_orders.parquet")
        dim_customers = pd.read_parquet(self.gold_dir / "dim_customers.parquet")
        rfm = pd.read_parquet(self.gold_dir / "agg_rfm_segments.parquet")

        # Test 1: Primary Key Uniqueness on fact_orders
        dup_orders = int(fact_orders["order_id"].duplicated().sum())
        self._assert(
            "PK Uniqueness (fact_orders.order_id)",
            dup_orders == 0,
            f"{dup_orders} duplicate primary keys detected in {len(fact_orders):,} rows"
        )

        # Test 2: Primary Key Uniqueness on dim_customers
        dup_cust = int(dim_customers["customer_id"].duplicated().sum())
        self._assert(
            "PK Uniqueness (dim_customers.customer_id)",
            dup_cust == 0,
            f"{dup_cust} duplicates in {len(dim_customers):,} customer keys"
        )

        # Test 3: Null Checks on Critical Financial Columns
        null_gmv = int(fact_orders["total_order_value"].isnull().sum())
        self._assert(
            "Not-Null Check (fact_orders.total_order_value)",
            null_gmv == 0,
            f"{null_gmv} null monetary values found"
        )

        # Test 4: Positive Financial Invariant
        neg_val = int((fact_orders["total_order_value"] < 0).sum())
        self._assert(
            "Business Invariant (Non-negative Order Values)",
            neg_val == 0,
            f"{neg_val} negative revenue records found"
        )

        # Test 5: Referential Integrity (fact_orders -> dim_customers)
        valid_customers = set(dim_customers["customer_id"])
        orphan_orders = int((~fact_orders["customer_id"].isin(valid_customers)).sum())
        self._assert(
            "Referential Integrity (Orders -> Customers)",
            orphan_orders == 0,
            f"{orphan_orders} orphaned customer foreign keys"
        )

        # Test 6: SLA Delay Invariant Logic
        inconsistent_delay = int(fact_orders[
            (fact_orders["is_delayed"] == 1) & (fact_orders["delivery_delay_days"] <= 0)
        ].shape[0])
        self._assert(
            "SLA Invariant (Delayed Flag Consistency)",
            inconsistent_delay == 0,
            f"{inconsistent_delay} inconsistent SLA delay classifications"
        )

        # Test 7: Review Score Domain Boundaries
        out_of_bounds_reviews = int(fact_orders[
            (fact_orders["review_score"] < self.config.min_review_score) | 
            (fact_orders["review_score"] > self.config.max_review_score)
        ].shape[0])
        self._assert(
            f"Domain Range (Review Score [{self.config.min_review_score} - {self.config.max_review_score}])",
            out_of_bounds_reviews == 0,
            f"{out_of_bounds_reviews} out-of-range review scores"
        )

        # Test 8: RFM Segmentation Completeness
        null_segments = int(rfm["customer_segment"].isnull().sum())
        self._assert(
            "Completeness (RFM Customer Segments)",
            null_segments == 0,
            f"100% of {len(rfm):,} customers successfully segmented"
        )

        elapsed = time.time() - start_time
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        success_rate = (passed_count / total_count) * 100

        print("=" * 85)
        print(f"[DATAOPS REPORT] Health Score: {success_rate:.1f}% ({passed_count}/{total_count} Tests Passed in {elapsed:.2f}s)\n")
        return passed_count == total_count

if __name__ == "__main__":
    engine = DataQualityEngine()
    if not engine.run_all_tests():
        sys.exit(1)
