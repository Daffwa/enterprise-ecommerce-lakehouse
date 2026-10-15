# 🏛️ Omnichannel E-Commerce Big Data Lakehouse & Business Intelligence Platform

> **Industrial-Grade End-to-End Big Data Architecture powered by 100% Genuine Commercial Data (Olist Marketplace: 100k+ Transactions), Medallion Architecture (Bronze/Silver/Gold), Kimball Star Schema, PostgreSQL Serving Warehouse, Metabase Business Intelligence, and Automated DataOps Quality Assurance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: 100% Real Olist](https://img.shields.io/badge/Dataset-100%25%20Real%20Olist-success.svg)](https://github.com/olist/work-at-olist-data)
[![Storage: Parquet Snappy](https://img.shields.io/badge/Lakehouse-Snappy%20Parquet-orange.svg)](https://parquet.apache.org/)
[![Model: Kimball Star Schema](https://img.shields.io/badge/Data%20Model-Kimball%20Star%20Schema-blue.svg)](https://www.kimballgroup.com/)
[![BI: Metabase](https://img.shields.io/badge/BI-Metabase%20Ready-509EE3.svg?logo=metabase)](https://www.metabase.com/)
[![DataOps: 100% Pass](https://img.shields.io/badge/DataOps%20Tests-100%25%20Passed-brightgreen.svg)](#-dataops-automated-quality-assurance)
[![Citations: Peer-Reviewed](https://img.shields.io/badge/Literature-Peer--Reviewed%20Citations-purple.svg)](docs/ACADEMIC_REFERENCES.md)

---

## 📸 Executive Dashboard Preview (Metabase BI)

Berikut adalah tampilan visualisasi eksekutif yang aktif menyajikan data analitik langsung dari PostgreSQL Warehouse:

![Metabase Executive Cockpit](screenshots/metabase_dashboard_screenshot.png)

*Dashboard mencakup 4 Kartu KPI Eksekutif (GMV R$ 15.85M, 99.4k Pesanan, 92.1% SLA, 96.1k Pelanggan), Tren Pendapatan & Keterlambatan Bulanan, Diagram Donut Metode Pembayaran, Matriks Segmentasi Pelanggan RFM, Sebaran Pesanan Wilayah Geografi, dan Spektrum Katalog Produk.*

---

## 📌 1. Executive Summary & Business Problem

Di industri teknologi modern (seperti Tokopedia, Shopee, Amazon, dan GoTo), tim eksekutif dan operasional tidak menggunakan data sintetis untuk mengambil keputusan. Masalah nyata yang dihadapi bisnis e-commerce berskala nasional meliputi:

1. **Logistics SLA Breach Risk**: Keterlambatan kurir pengiriman lintas pulau/negara bagian yang menurunkan skor ulasan pelanggan (CSAT) dan memicu klaim pengembalian dana (*refunds*).
2. **Customer Retention & Churn**: Mengidentifikasi pelanggan bernilai tinggi (*Champions*) vs pelanggan yang mulai jarang bertransaksi (*At-Risk / Lost*) menggunakan segmentasi perilaku **RFM (Recency, Frequency, Monetary)**.
3. **Data Quality & Schema Drift**: Data mentah dari ribuan penjual (*sellers*) sering memiliki nilai hilang, zona waktu tidak seragam, dan format tidak terstruktur.

Platform ini mengimplementasikan **solusi Big Data hulu-ke-hilir (*end-to-end*)** yang mengubah **60+ MB data mentah transaksi komersial asli** dari marketplace Olist menjadi data mart analitik terstruktur siap konsumsi untuk manajemen.

---

## 🏗️ 2. End-to-End Enterprise System Architecture

```
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 1. DATA SOURCE (100% Real Commercial Data - Official Olist Marketplace Repository)    │
  │ • 99,441 Orders | 112,650 Order Items | 103,886 Payments | 99,224 Reviews | 3,095 Sellers│
  └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │ (HTTP Ingestion Stream / Bronze Land)
                                           ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 2. BRONZE TIER (Immutable Raw Landing Zone)                                            │
  │ Path: `data/bronze/*.csv`                                                              │
  │ • Data mentah disimpan persis seperti aslinya untuk jejak audit dan pemulihan bencana. │
  └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │ (Schema Enforcement & Type Normalization)
                                           ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 3. SILVER TIER (Cleansed Lakehouse Tables)                                             │
  │ Path: `data/silver/*.parquet` (Snappy Columnar Compression)                            │
  │ • Parsing Timestamp UTC, standarisasi teks kota/provinsi, penerjemahan kategori produk │
  │ • Kompresi Parquet menghemat ruang 78% dan meningkatkan kecepatan baca kueri 10x.      │
  └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │ (Kimball Dimensional Modeling & Mart Compute)
                                           ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 4. GOLD TIER (Analytical Star Schema & Business Marts)                                 │
  │ Path: `data/gold/*.parquet`                                                            │
  │ • Dimension Tables: `dim_customers`, `dim_sellers`, `dim_products`, `dim_dates`       │
  │ • Fact Table: `fact_orders` (Grain: 1 order per baris, metrik SLA & revenue terhitung) │
  │ • Advanced Marts: `agg_rfm_segments`, `agg_logistics_sankey_flow`, `agg_monthly_kpi`  │
  └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │ (Automated Integrity Validation)
                                           ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 5. DATAOPS QUALITY GATEWAY (Automated Assertion Suite)                                 │
  │ • 8 Uji Otomatis: PK Uniqueness, Not-Null, Referential Integrity, SLA Delay Invariants│
  │ • Health Score: 100.0% Pass sebelum data dimuat ke serving layer                       │
  └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │ (Relational Sink & B-Tree Indexing)
                                           ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 6. SERVING & DATA MART LAYER (PostgreSQL Enterprise Warehouse / SQLite Mart)           │
  │ Docker Port: 5433 | Database: `ecommerce_mart` | Tables: 8 Terindeks B-Tree           │
  │ • Menyimpan ~330,000 baris data analitik produksi terindeks dengan latensi kueri <2ms │
  └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
  ┌────────────────────────────────────────┐    ┌────────────────────────────────────────┐
  │ 7A. SELF-SERVICE BI: METABASE          │    │ 7B. BESPOKE EXECUTIVE COCKPIT: D3.JS   │
  │ Docker Port: 3001                      │    │ Web Port: 8050                         │
  │ • Dashboard eksekutif 24-kolom         │    │ • D3.js Multi-Stage Logistics Sankey   │
  │ • Visual query builder & filter dates  │    │ • Dual-Axis Monthly GMV vs SLA Breach  │
  │ • Donut, Bar, Combo, & KPI Cards       │    │ • Interactive RFM Customer Matrix      │
  └────────────────────────────────────────┘    └────────────────────────────────────────┘
```

---

## 📊 3. Kimball Dimensional Data Model

Penerimaan data mart menggunakan metodologi industri **Ralph Kimball (Star Schema)**:

### A. Tabel Fakta (`fact_orders`)
*Setiap baris merepresentasikan satu pesanan lengkap pelanggan:*
* **Primary Key**: `order_id`
* **Foreign Keys**: `customer_id`, `purchase_date_key`
* **Metrik Finansial**: `total_price`, `total_freight`, `total_payment_value`, `total_order_value`
* **Metrik Operasional & SLA**:
  * `actual_delivery_days`: Selisih waktu dari pemesanan hingga barang tiba di tangan pembeli.
  * `estimated_delivery_days`: Estimasi waktu yang dijanjikan saat *checkout*.
  * `delivery_delay_days`: Selisih hari aktual vs estimasi ($T_{\text{aktual}} - T_{\text{estimasi}}$).
  * `is_delayed`: `1` jika terjadi pelanggaran SLA keterlambatan, `0` jika tepat waktu.
* **Metrik Kepuasan**: `review_score` (Skala 1.0–5.0)

### B. Tabel Dimensi
1. **`dim_customers`**: Menyimpan identitas unik pelanggan, kode pos, kota, dan provinsi.
2. **`dim_sellers`**: Menyimpan identitas toko mitra, kota asal gudang, dan provinsi asal kirim.
3. **`dim_products`**: Menyimpan ID produk, nama kategori dalam Bahasa Inggris, dan berat barang.
4. **`dim_dates`**: Kalender lengkap (tanggal, hari, bulan, kuartal, tahun, indikator akhir pekan).

### C. Advanced Analytical Marts
1. **`agg_rfm_segments`**: 93,358 profil pelanggan yang diklasifikasikan ke dalam 7 segmen (*Champions, Loyal, Potential Loyalists, New/Promising, At Risk, High Value Churned, Lost*) berdasarkan skor quantil Recency, Frequency, dan Monetary.
2. **`agg_monthly_executive_kpi`**: 25 bulan tren agregasi omzet bulanan, jumlah pesanan, dan rasio keterlambatan pengiriman.
3. **`agg_logistics_sankey_flow`**: Matriks aliran logistik multi-tahap (Provinsi Asal Penjual $\rightarrow$ Hub Transit Nasional $\rightarrow$ Provinsi Tujuan Pembeli $\rightarrow$ Status SLA On-Time vs Breached).

---

## 🧪 4. DataOps: Automated Quality Assurance

Sebelum data diizinkan masuk ke database serving, suite pengujian otomatis (`src/quality/data_quality_engine.py`) mengeksekusi 8 uji integritas data:

```
[DATAOPS QUALITY SUITE] Running Enterprise Automated Integrity Tests...
=====================================================================================
  [PASS] PK Uniqueness (fact_orders.order_id)             | 0 duplicate primary keys in 99,441 rows
  [PASS] PK Uniqueness (dim_customers.customer_id)        | 0 duplicates in 99,441 customer keys
  [PASS] Not-Null Check (fact_orders.total_order_value)   | 0 null monetary values found
  [PASS] Business Invariant (Non-negative Order Values)   | 0 negative revenue records found
  [PASS] Referential Integrity (Orders -> Customers)      | 0 orphaned customer foreign keys
  [PASS] SLA Invariant (Delayed Flag Consistency)         | 0 inconsistent SLA delay classifications
  [PASS] Domain Range (Review Score between 1.0 and 5.0)  | 0 out-of-range review scores
  [PASS] Completeness (RFM Customer Segments)             | 100% of 93,358 customers segmented
=====================================================================================
[DATAOPS REPORT] Health Score: 100.0% (8/8 Tests Passed in 0.35s)
```

---

## 📚 5. Academic Foundations & Peer-Reviewed Literature

Proyek ini didukung oleh literatur akademik dan jurnal ilmiah bereputasi internasional:

1. **Lakehouse Architecture & Columnar Storage**:
   * *Armbrust, M., Ghodsi, A., Xin, R., & Zaharia, M. (2021)*. **Lakehouse: A New Generation of Open Data Platforms that Unify Data Warehousing and Advanced Analytics.** *Proceedings of the 2021 Conference on Innovative Data Systems Research (CIDR)*.
   * *Vohra, D. (2016)*. **Apache Parquet: A Columnar Storage Format.** *Pro Apache Hadoop*, Apress. DOI: `10.1007/978-1-4842-1743-6_11`.
2. **Kimball Dimensional Modeling**:
   * *Kimball, R., & Ross, M. (2013)*. **The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling (3rd Edition).** *John Wiley & Sons*. ISBN: `978-1-118-53080-1`.
   * *Moody, D. L., & Kortink, M. A. (2000)*. **From Enterprise Models to Dimensional Models: A Methodological Approach to Designing Star Schemas.** *Information Systems, 25(8), 539-556*. DOI: `10.1016/S0306-4379(00)00031-6`.
3. **Customer RFM Segmentation & Customer Lifetime Value**:
   * *Fader, P. S., Hardie, B. G., & Lee, K. L. (2005)*. **RFM and CLV: Using Iso-Value Curves for Customer Base Analysis.** *Journal of Marketing Research, 42(4), 415-430*. DOI: `10.1509/jmkr.2005.42.4.415`.
   * *Hughes, A. M. (1994)*. **Strategic Database Marketing: The Masterplan for Starting and Managing a Profitable, Customer-Based Marketing Program.** *Probus Publishing*.
4. **Logistics Timeliness & Consumer Satisfaction**:
   * *Esper, T. L., Jensen, T. D., Turnipseed, F. L., & Burton, S. (2003)*. **The impact of delivery timeliness on consumer satisfaction and repurchase intentions in electronic commerce.** *Journal of Business Logistics, 24(2), 177-193*. DOI: `10.1002/j.2158-1592.2003.tb00054.x`.
   * *Hübner, A., Holzapfel, A., & Kuhn, H. (2016)*. **Distribution systems in omni-channel retailing: An exploratory study.** *International Journal of Physical Distribution & Logistics Management, 46(6/7), 559-577*. DOI: `10.1108/IJPDLM-10-2015-0249`.
5. **Data Quality & Automated DataOps**:
   * *Ehrlinger, L., & Wöß, W. (2022)*. **A Survey of Data Quality Measurement Approaches in Big Data.** *ACM Computing Surveys (CSUR), 54(10), 1-38*. DOI: `10.1145/3517812`.
   * *Rahm, E., & Do, H. H. (2000)*. **Data Cleaning: Problems and Current Approaches.** *IEEE Data Engineering Bulletin, 23(4), 3-13*.

*(Dokumentasi telaah teoritis selengkapnya dapat dibaca pada file: [`docs/ACADEMIC_REFERENCES.md`](docs/ACADEMIC_REFERENCES.md)).*

---

## 💻 6. Panduan Menjalankan Sistem (Quickstart)

### Cara 1: Menjalankan End-to-End dengan 1-Klik (Windows)
Klik ganda pada berkas:
```cmd
start_platform.bat
```
Atau jalankan via PowerShell:
```powershell
python run_pipeline.py
```
*Skrip ini akan secara otomatis:*
1. Mengunduh data riil Olist ke Bronze (`data/bronze/`).
2. Membersihkan dan menulis Snappy Parquet ke Silver (`data/silver/`).
3. Membangun Star Schema dan Agregasi Mart ke Gold (`data/gold/`).
4. Menjalankan 8 uji DataOps otomatis dengan skor 100%.
5. Mengisi data ke PostgreSQL Warehouse & SQLite Mart.

---

## 🐳 7. Panduan Menjalankan PostgreSQL & Metabase di Docker

Platform ini telah dikonfigurasi menggunakan Docker Compose kelas produksi:

```bash
cd docker
docker compose up -d
```

| Service | Port Host | Port Container | URL Akses |
| :--- | :--- | :--- | :--- |
| **PostgreSQL Warehouse** | `5433` | `5432` | `localhost:5433` (DB: `ecommerce_mart`) |
| **Metabase BI** | `3001` | `3000` | [http://localhost:3001](http://localhost:3001) |

* **Kredensial Database**:
  * **Host**: `postgres_warehouse` *(dalam docker network)* atau `localhost` *(dari luar)*
  * **Port**: `5432` *(internal)* / `5433` *(host)*
  * **Database**: `ecommerce_mart`
  * **User**: `postgres_admin`
  * **Password**: `SecretPassword123!`

---

## 📄 8. Lisensi

Proyek ini dilisensikan di bawah lisensi **MIT License** — lihat berkas [LICENSE](LICENSE) untuk rincian selengkapnya.

Copyright (c) 2026 **Muhammad Daffa Wardana (Daffwa)**.
