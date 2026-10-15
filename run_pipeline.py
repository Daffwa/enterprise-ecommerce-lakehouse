"""
================================================================================
MASTER END-TO-END PIPELINE RUNNER: ENTERPRISE E-COMMERCE LAKEHOUSE
================================================================================
Executes the full enterprise data lifecycle:
  [Phase 1] Bronze Ingestion (Raw CSV Download)
  [Phase 2] Silver Cleansing & Snappy Parquet Generation
  [Phase 3] Gold Kimball Star Schema & Business Mart Modeling
  [Phase 4] Automated DataOps Quality Assurance & Testing
  [Phase 5] Serving Mart Export & Indexing
  [Phase 6] Web Cockpit Visualizer Launcher (D3.js)
================================================================================
"""

import os
import sys
import time
import argparse
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.ingestion.download_real_olist import download_bronze_datasets
from src.processing.silver_transformer import run_silver_transformation
from src.processing.gold_modeler import run_gold_modeling
from src.quality.data_quality_engine import DataQualityEngine
from src.serving.export_to_mart import export_gold_to_mart
from src.visualizer.server import start_server

def print_banner():
    banner = """
===============================================================================
       ENTERPRISE E-COMMERCE BIG DATA LAKEHOUSE & ANALYTICS PLATFORM
       100% Real Commercial Data (Olist Marketplace, 100k+ Transactions)
===============================================================================
    """
    print(banner)

def main():
    parser = argparse.ArgumentParser(description="Master Lakehouse Pipeline Orchestrator")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading bronze datasets if already cached")
    parser.add_argument("--serve-only", action="store_true", help="Only launch the D3.js web visualizer server")
    parser.add_argument("--port", type=int, default=8050, help="Web visualizer port (default: 8050)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    args = parser.parse_args()

    print_banner()

    if args.serve_only:
        print(f"[*] Starting D3.js Cockpit Server on port {args.port}...")
        if not args.no_browser:
            webbrowser.open(f"http://localhost:{args.port}")
        start_server(args.port)
        return

    pipeline_start = time.time()

    # PHASE 1: BRONZE INGESTION
    print("\n>>> [PHASE 1/5] Ingesting Raw Data into Bronze Lakehouse...")
    download_bronze_datasets()

    # PHASE 2: SILVER TRANSFORMATION
    print("\n>>> [PHASE 2/5] Cleaning & Writing Snappy Parquet Lakehouse (Silver)...")
    run_silver_transformation()

    # PHASE 3: GOLD MODELING
    print("\n>>> [PHASE 3/5] Building Kimball Star Schema & Business Marts (Gold)...")
    run_gold_modeling()

    # PHASE 4: DATA QUALITY ASSURANCE
    print("\n>>> [PHASE 4/5] Executing DataOps Automated Quality Suite...")
    quality_engine = DataQualityEngine()
    passed = quality_engine.run_all_tests()
    if not passed:
        print("\n[CRITICAL ERROR] Data Quality Assertion Failed! Halting pipeline.")
        sys.exit(1)

    # PHASE 5: SERVING MART EXPORT
    print("\n>>> [PHASE 5/5] Sinking Gold Tier into Analytical Serving Mart...")
    export_gold_to_mart()

    total_pipeline_time = time.time() - pipeline_start
    print("=" * 79)
    print(f"[SUCCESS] Pipeline execution finished flawlessly in {total_pipeline_time:.2f} seconds!")
    print("   Data is fully modeled, indexed, and ready for Metabase and D3.js.")
    print("=" * 79)

    print(f"\n[*] Launching D3.js Executive Cockpit at http://localhost:{args.port}...")
    if not args.no_browser:
        try:
            webbrowser.open(f"http://localhost:{args.port}")
        except Exception:
            pass
    start_server(args.port)

if __name__ == "__main__":
    main()
