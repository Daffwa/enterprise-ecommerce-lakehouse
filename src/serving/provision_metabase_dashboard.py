"""
================================================================================
METABASE AUTOMATED DASHBOARD PROVISIONER (V2 - POLISHED & ROBUST)
================================================================================
Purpose:
  Provisions a high-grade Executive Cockpit Dashboard in Metabase (Dashboard 5)
  with 9 clean, fully functional, beautifully styled cards across a 24-col grid:
    - 4 Executive KPI Cards (Row 0)
    - Monthly Revenue Trajectory & SLA Breach Dual-Axis (Row 3)
    - Payment Methods Donut/Pie Chart (Row 3)
    - Customer RFM Segmentation Horizontal Bar (Row 11)
    - Top Buyer States Distribution (Row 11)
    - Top 10 Product Categories by Catalog Volume (Row 19)
================================================================================
"""

import sys
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import psycopg2
from src.config import POSTGRES

def provision_dashboard():
    conn = psycopg2.connect(
        host=POSTGRES.host,
        port=POSTGRES.port,
        user=POSTGRES.user,
        password=POSTGRES.password,
        dbname=POSTGRES.database
    )
    c = conn.cursor()

    now = datetime.now(timezone.utc)
    db_id = 2  # E-Commerce Lakehouse Warehouse
    creator_id = 1

    # 1. Target Dashboard ID 5
    dash_id = 5
    dashboard_name = "E-Commerce 360° Executive Cockpit"
    
    # Check if dashboard 5 exists
    c.execute("SELECT id FROM report_dashboard WHERE id = %s;", (dash_id,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO report_dashboard (
                id, name, description, creator_id, parameters, width, archived,
                created_at, updated_at, entity_id, auto_apply_filters
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            dash_id,
            dashboard_name,
            "Real-time Enterprise E-Commerce KPI Cockpit: Revenue, Logistics SLAs, RFM Matrix & Product Demand",
            creator_id,
            "[]",
            "full",
            False,
            now,
            now,
            str(uuid.uuid4())[:20],
            True
        ))
    else:
        c.execute("""
            UPDATE report_dashboard 
            SET name = %s, description = %s, width = 'full', updated_at = %s 
            WHERE id = %s;
        """, (dashboard_name, "Real-time Enterprise E-Commerce KPI Cockpit", now, dash_id))

    # Clean old dashboard cards and old cards associated with dashboard 5
    c.execute("SELECT card_id FROM report_dashboardcard WHERE dashboard_id = %s;", (dash_id,))
    old_card_ids = [r[0] for r in c.fetchall() if r[0]]
    c.execute("DELETE FROM report_dashboardcard WHERE dashboard_id = %s;", (dash_id,))
    if old_card_ids:
        c.execute("DELETE FROM report_card WHERE id = ANY(%s);", (old_card_ids,))

    print(f"[*] Provisioning clean cards for Dashboard {dash_id}...")

    # 2. Card Definitions (100% verified against PostgreSQL schema)
    cards = [
        # --- ROW 0: KPI CARDS ---
        {
            "name": "💰 Total Settled GMV",
            "display": "scalar",
            "sql": 'SELECT ROUND(SUM(total_order_value)::numeric, 2) AS "Total GMV" FROM fact_orders;',
            "viz": {
                "scalar.field": "Total GMV",
                "scalar.compact_primary_number": False,
                "column_settings": {
                    '["name","Total GMV"]': {
                        "currency": "BRL",
                        "currency_style": "symbol"
                    }
                }
            },
            "grid": {"row": 0, "col": 0, "size_x": 6, "size_y": 3}
        },
        {
            "name": "📦 Completed Orders",
            "display": "scalar",
            "sql": 'SELECT COUNT(*) AS "Completed Orders" FROM fact_orders;',
            "viz": {
                "scalar.field": "Completed Orders",
                "scalar.compact_primary_number": False
            },
            "grid": {"row": 0, "col": 6, "size_x": 6, "size_y": 3}
        },
        {
            "name": "⏱️ Logistics On-Time SLA %",
            "display": "scalar",
            "sql": 'SELECT ROUND(100.0 - (SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 1) AS "On-Time SLA %" FROM fact_orders;',
            "viz": {
                "scalar.field": "On-Time SLA %",
                "scalar.compact_primary_number": False
            },
            "grid": {"row": 0, "col": 12, "size_x": 6, "size_y": 3}
        },
        {
            "name": "👥 Unique Customers",
            "display": "scalar",
            "sql": 'SELECT COUNT(DISTINCT customer_unique_id) AS "Customer Base" FROM dim_customers;',
            "viz": {
                "scalar.field": "Customer Base",
                "scalar.compact_primary_number": False
            },
            "grid": {"row": 0, "col": 18, "size_x": 6, "size_y": 3}
        },

        # --- ROW 3: REVENUE TRAJECTORY & PAYMENT METHODS ---
        {
            "name": "📈 Monthly Revenue & SLA Breach Trajectory",
            "display": "line",
            "sql": '''
                SELECT 
                    year_month AS "Month",
                    ROUND(total_gmv::numeric, 2) AS "GMV BRL",
                    ROUND(sla_breach_rate_pct::numeric, 1) AS "SLA Breach %"
                FROM agg_monthly_executive_kpi
                WHERE total_orders > 100
                ORDER BY year_month ASC;
            ''',
            "viz": {
                "graph.dimensions": ["Month"],
                "graph.metrics": ["GMV BRL", "SLA Breach %"],
                "series_settings": {
                    "GMV BRL": {"display": "bar", "color": "#3B82F6"},
                    "SLA Breach %": {"display": "line", "color": "#EF4444", "axis": "right"}
                }
            },
            "grid": {"row": 3, "col": 0, "size_x": 14, "size_y": 8}
        },
        {
            "name": "💳 Payment Methods Breakdown",
            "display": "pie",
            "sql": '''
                SELECT 
                    primary_payment_type AS "Payment Method",
                    ROUND(SUM(total_order_value)::numeric, 2) AS "Total Revenue"
                FROM fact_orders
                WHERE primary_payment_type IS NOT NULL AND primary_payment_type != 'not_defined'
                GROUP BY primary_payment_type
                ORDER BY "Total Revenue" DESC;
            ''',
            "viz": {
                "pie.dimension": "Payment Method",
                "pie.metric": "Total Revenue",
                "pie.show_legend": True
            },
            "grid": {"row": 3, "col": 14, "size_x": 10, "size_y": 8}
        },

        # --- ROW 11: CUSTOMER SEGMENTATION & GEOGRAPHIC DISTRIBUTION ---
        {
            "name": "🎯 Customer RFM Segmentation & Revenue Contribution",
            "display": "row",
            "sql": '''
                SELECT 
                    customer_segment AS "Customer Segment",
                    ROUND(SUM(monetary)::numeric, 2) AS "Revenue BRL"
                FROM agg_rfm_segments
                GROUP BY customer_segment
                ORDER BY "Revenue BRL" DESC;
            ''',
            "viz": {
                "graph.dimensions": ["Customer Segment"],
                "graph.metrics": ["Revenue BRL"],
                "graph.colors": ["#10B981"]
            },
            "grid": {"row": 11, "col": 0, "size_x": 12, "size_y": 8}
        },
        {
            "name": "🚚 Top 8 Buyer States by Order Volume",
            "display": "bar",
            "sql": '''
                SELECT 
                    c.customer_state AS "Buyer State",
                    COUNT(f.order_id) AS "Orders Completed"
                FROM fact_orders f
                JOIN dim_customers c ON f.customer_id = c.customer_id
                GROUP BY c.customer_state
                ORDER BY "Orders Completed" DESC
                LIMIT 8;
            ''',
            "viz": {
                "graph.dimensions": ["Buyer State"],
                "graph.metrics": ["Orders Completed"],
                "graph.colors": ["#8B5CF6"]
            },
            "grid": {"row": 11, "col": 12, "size_x": 12, "size_y": 8}
        },

        # --- ROW 19: PRODUCT CATALOG SPECTRUM ---
        {
            "name": "🏷️ Top 10 Product Categories by Catalog Volume",
            "display": "row",
            "sql": '''
                SELECT 
                    category_name AS "Product Category",
                    COUNT(*) AS "Products Listed"
                FROM dim_products
                WHERE category_name IS NOT NULL AND category_name != 'Other'
                GROUP BY category_name
                ORDER BY "Products Listed" DESC
                LIMIT 10;
            ''',
            "viz": {
                "graph.dimensions": ["Product Category"],
                "graph.metrics": ["Products Listed"],
                "graph.colors": ["#F59E0B"]
            },
            "grid": {"row": 19, "col": 0, "size_x": 24, "size_y": 7}
        }
    ]

    for item in cards:
        dataset_query = {
            "database": db_id,
            "type": "native",
            "native": {
                "query": item["sql"].strip()
            }
        }
        
        card_entity_id = str(uuid.uuid4())[:20]
        c.execute("""
            INSERT INTO report_card (
                name, description, display, dataset_query, visualization_settings,
                creator_id, database_id, query_type, archived, created_at, updated_at,
                entity_id, type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            item["name"],
            f"Analytic metric for {item['name']}",
            item["display"],
            json.dumps(dataset_query),
            json.dumps(item["viz"]),
            creator_id,
            db_id,
            "native",
            False,
            now,
            now,
            card_entity_id,
            "question"
        ))
        card_id = c.fetchone()[0]

        # Attach to DashboardCard
        dashcard_entity_id = str(uuid.uuid4())[:20]
        c.execute("""
            INSERT INTO report_dashboardcard (
                dashboard_id, card_id, row, col, size_x, size_y,
                created_at, updated_at, entity_id, visualization_settings, parameter_mappings
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            dash_id,
            card_id,
            item["grid"]["row"],
            item["grid"]["col"],
            item["grid"]["size_x"],
            item["grid"]["size_y"],
            now,
            now,
            dashcard_entity_id,
            "{}",
            "[]"
        ))
        safe_name = item["name"].encode("ascii", "replace").decode("ascii")
        print(f"  [+] Added '{safe_name}' (card_id: {card_id}, pos: row {item['grid']['row']}, col {item['grid']['col']})")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] Metabase Executive Cockpit Dashboard v2 successfully provisioned!")
    print(f"URL: http://localhost:3001/dashboard/{dash_id}")

if __name__ == "__main__":
    provision_dashboard()
