"""
================================================================================
UNIT & INTEGRATION TEST SUITE: ENTERPRISE E-COMMERCE LAKEHOUSE
================================================================================
"""

import os
import unittest
import sqlite3
import pandas as pd

class TestEcommerceLakehouse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.bronze_dir = os.path.join(cls.base_dir, "data", "bronze")
        cls.silver_dir = os.path.join(cls.base_dir, "data", "silver")
        cls.gold_dir = os.path.join(cls.base_dir, "data", "gold")
        cls.db_path = os.path.join(cls.base_dir, "data", "serving", "ecommerce_mart.db")

    def test_bronze_files_exist(self):
        required_files = [
            "olist_orders_dataset.csv",
            "olist_order_items_dataset.csv",
            "olist_customers_dataset.csv"
        ]
        for f in required_files:
            p = os.path.join(self.bronze_dir, f)
            self.assertTrue(os.path.exists(p), f"Bronze file missing: {f}")
            self.assertGreater(os.path.getsize(p), 1000, f"Bronze file too small: {f}")

    def test_silver_parquet_validity(self):
        silver_orders = os.path.join(self.silver_dir, "silver_orders.parquet")
        self.assertTrue(os.path.exists(silver_orders))
        df = pd.read_parquet(silver_orders)
        self.assertGreater(len(df), 90000, "Silver orders row count under expected threshold")
        self.assertIn("order_purchase_timestamp", df.columns)

    def test_gold_star_schema(self):
        gold_fact = os.path.join(self.gold_dir, "fact_orders.parquet")
        gold_rfm = os.path.join(self.gold_dir, "agg_rfm_segments.parquet")
        self.assertTrue(os.path.exists(gold_fact))
        self.assertTrue(os.path.exists(gold_rfm))
        
        df_fact = pd.read_parquet(gold_fact)
        self.assertIn("is_delayed", df_fact.columns)
        self.assertIn("total_order_value", df_fact.columns)
        
        df_rfm = pd.read_parquet(gold_rfm)
        self.assertIn("customer_segment", df_rfm.columns)

    def test_sqlite_mart_query(self):
        self.assertTrue(os.path.exists(self.db_path), "Serving database does not exist")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM fact_orders;")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 90000)
        
        cursor.execute("SELECT COUNT(DISTINCT customer_segment) FROM agg_rfm_segments;")
        seg_count = cursor.fetchone()[0]
        self.assertGreaterEqual(seg_count, 5, "Expected at least 5 RFM customer segments")
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
