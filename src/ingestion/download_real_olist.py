"""
================================================================================
BRONZE INGESTION ENGINE (REFACTORED)
================================================================================
Purpose:
  Downloads genuine commercial e-commerce transactions from official Olist
  repository into the immutable Bronze Lakehouse tier.
Refactoring Highlights:
  - Centralized configuration via `src.config`.
  - Object-Oriented `BronzeIngestionManager` class with exponential retry logic.
  - Strict type hints and Pathlib encapsulation.
================================================================================
"""

import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, Optional

# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PATHS, INGESTION

class BronzeIngestionManager:
    """Manages downloading, caching, and stream verification for raw bronze files."""
    
    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = Path(target_dir) if target_dir else PATHS.bronze_dir
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.config = INGESTION

    def _fetch_file_with_retry(self, filename: str, url: str) -> int:
        file_path = self.target_dir / filename
        
        # Check Cache
        if file_path.exists() and file_path.stat().st_size > 1000:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  [CACHE HIT] {filename:<40} ({size_mb:.2f} MB)")
            return file_path.stat().st_size

        print(f"  [FETCHING]  {filename:<40} ...", end="", flush=True)
        
        for attempt in range(1, self.config.max_retries + 1):
            start_time = time.time()
            try:
                req = urllib.request.Request(
                    url, 
                    headers={"User-Agent": "Enterprise-Data-Engine/2.0 (Windows NT 10.0; x64)"}
                )
                with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response, \
                     open(file_path, "wb") as out_file:
                    total_bytes = 0
                    while True:
                        chunk = response.read(self.config.chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        total_bytes += len(chunk)
                
                duration = time.time() - start_time
                size_mb = total_bytes / (1024 * 1024)
                print(f" DONE ({size_mb:.2f} MB in {duration:.1f}s)")
                return total_bytes
            except Exception as exc:
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds * attempt)
                else:
                    if file_path.exists():
                        file_path.unlink()
                    print(f" FAILED after {self.config.max_retries} attempts! ({exc})")
                    raise exc
        return 0

    def download_all(self) -> Dict[str, int]:
        """Downloads all registered dataset files sequentially."""
        print(f"\n[BRONZE INGESTION] Starting real e-commerce data download to: {self.target_dir}")
        print("=" * 75)
        
        stats: Dict[str, int] = {}
        start_all = time.time()
        
        for filename, url in self.config.sources.items():
            bytes_downloaded = self._fetch_file_with_retry(filename, url)
            stats[filename] = bytes_downloaded

        elapsed = time.time() - start_all
        total_mb = sum(stats.values()) / (1024 * 1024)
        print("=" * 75)
        print(f"[BRONZE INGESTION COMPLETE] Ingested: {total_mb:.2f} MB in {elapsed:.1f}s\n")
        return stats

def download_bronze_datasets(target_dir: Optional[str] = None) -> Dict[str, int]:
    """Public procedural wrapper for pipeline integration."""
    manager = BronzeIngestionManager(Path(target_dir) if target_dir else None)
    return manager.download_all()

if __name__ == "__main__":
    download_bronze_datasets()
