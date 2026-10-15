/**
 * ==============================================================================
 * D3.JS ENTERPRISE VISUALIZATION CLIENT
 * ==============================================================================
 * Renders:
 *   1. Animated KPI Ribbon
 *   2. Interactive D3.js Logistics SLA Sankey Flow
 *   3. Dual-Axis Monthly GMV & SLA Breach Trajectory
 *   4. Customer RFM Segmentation Matrix
 * ==============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  const tooltip = d3.select("body").append("div")
    .attr("class", "d3-tooltip")
    .style("opacity", 0);

  // 1. Fetch and Populate KPIs
  fetch("/api/kpis")
    .then(r => r.json())
    .then(data => {
      document.getElementById("kpi-gmv").textContent = "R$ " + (data.total_gmv / 1e6).toFixed(2) + "M";
      document.getElementById("kpi-orders").textContent = Number(data.total_orders).toLocaleString();
      document.getElementById("kpi-sla").textContent = data.on_time_pct + "%";
      document.getElementById("kpi-sla-breach").textContent = data.sla_breach_pct + "% SLA Breach";
      document.getElementById("kpi-days").textContent = data.avg_delivery_days + " Days";
      document.getElementById("kpi-csat").textContent = data.avg_review_score + " / 5.0";
      document.getElementById("kpi-customers").textContent = Number(data.total_customers).toLocaleString();
      const badge = document.getElementById("engine-badge");
      if (badge && data.backend_engine) {
        badge.textContent = data.backend_engine;
      }
    });

  // 2. Render D3.js Logistics Sankey Diagram
  renderSankey(tooltip);

  // 3. Render Monthly Trajectory Chart
  renderMonthlyTrend(tooltip);

  // 4. Render RFM Customer Table
  renderRFMTable();
});

function renderSankey(tooltip) {
  const container = document.getElementById("sankey-chart");
  const width = container.clientWidth || 1100;
  const height = 520;

  const svg = d3.select("#sankey-chart")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", `0 0 ${width} ${height}`);

  fetch("/api/sankey")
    .then(r => r.json())
    .then(energy => {
      const sankey = d3.sankey()
        .nodeWidth(20)
        .nodePadding(14)
        .extent([[10, 15], [width - 15, height - 20]]);

      const graph = sankey({
        nodes: energy.nodes.map(d => Object.assign({}, d)),
        links: energy.links.map(d => Object.assign({}, d))
      });

      // Color mapping by node stage
      function getNodeColor(name) {
        if (name.includes("Seller")) return "#06b6d4"; // Cyan
        if (name.includes("Carrier")) return "#f59e0b"; // Amber Hub
        if (name.includes("Buyer")) return "#8b5cf6";  // Purple
        if (name.includes("On-Time")) return "#10b981"; // Emerald Green
        if (name.includes("Breached")) return "#ef4444"; // Red Late
        return "#3b82f6";
      }

      // Draw Links
      svg.append("g")
        .selectAll("path")
        .data(graph.links)
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("d", d3.sankeyLinkHorizontal())
        .attr("stroke", d => getNodeColor(d.target.name))
        .attr("stroke-width", d => Math.max(1, d.width))
        .on("mousemove", (event, d) => {
          tooltip.transition().duration(100).style("opacity", 1);
          tooltip.html(`
            <strong>${d.source.name} → ${d.target.name}</strong><br/>
            📦 Volume: <strong>${d.value.toLocaleString()} orders</strong><br/>
            💰 Revenue: <strong>R$ ${d.gmv.toLocaleString()}</strong>
          `)
          .style("left", (event.pageX + 15) + "px")
          .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => {
          tooltip.transition().duration(200).style("opacity", 0);
        });

      // Draw Nodes
      const node = svg.append("g")
        .selectAll(".node")
        .data(graph.nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x0},${d.y0})`);

      node.append("rect")
        .attr("height", d => d.y1 - d.y0)
        .attr("width", d => d.x1 - d.x0)
        .attr("fill", d => getNodeColor(d.name))
        .attr("stroke", "#0a0d14")
        .attr("stroke-width", 1.5)
        .on("mousemove", (event, d) => {
          tooltip.transition().duration(100).style("opacity", 1);
          tooltip.html(`
            <strong>${d.name}</strong><br/>
            Total Throughput: <strong>${d.value.toLocaleString()} orders</strong>
          `)
          .style("left", (event.pageX + 15) + "px")
          .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => {
          tooltip.transition().duration(200).style("opacity", 0);
        });

      node.append("text")
        .attr("x", d => d.x0 < width / 2 ? (d.x1 - d.x0) + 8 : -8)
        .attr("y", d => (d.y1 - d.y0) / 2)
        .attr("dy", "0.35em")
        .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
        .text(d => d.name)
        .filter(d => (d.y1 - d.y0) > 10);
    });
}

function renderMonthlyTrend(tooltip) {
  const container = document.getElementById("monthly-chart");
  const margin = { top: 20, right: 50, bottom: 45, left: 60 };
  const width = (container.clientWidth || 600) - margin.left - margin.right;
  const height = 320 - margin.top - margin.bottom;

  const svg = d3.select("#monthly-chart")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  fetch("/api/monthly")
    .then(r => r.json())
    .then(data => {
      // Filter out incomplete startup months
      const cleanData = data.filter(d => d.total_orders > 100);

      const x = d3.scaleBand()
        .range([0, width])
        .domain(cleanData.map(d => d.year_month))
        .padding(0.25);

      const yGMV = d3.scaleLinear()
        .domain([0, d3.max(cleanData, d => d.total_gmv) * 1.15])
        .range([height, 0]);

      const ySLA = d3.scaleLinear()
        .domain([0, Math.max(25, d3.max(cleanData, d => d.sla_breach_rate_pct) * 1.3)])
        .range([height, 0]);

      // X Axis
      svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickValues(x.domain().filter((d, i) => !(i % 3))))
        .attr("color", "#64748b")
        .selectAll("text")
        .style("font-size", "11px");

      // Left Y Axis (GMV)
      svg.append("g")
        .call(d3.axisLeft(yGMV).ticks(5).tickFormat(d => "R$ " + (d / 1e3).toFixed(0) + "k"))
        .attr("color", "#64748b")
        .selectAll("text")
        .style("font-size", "11px");

      // Right Y Axis (SLA Breach %)
      svg.append("g")
        .attr("transform", `translate(${width}, 0)`)
        .call(d3.axisRight(ySLA).ticks(4).tickFormat(d => d + "%"))
        .attr("color", "#ef4444")
        .selectAll("text")
        .style("font-size", "11px");

      // GMV Bars
      svg.selectAll(".bar")
        .data(cleanData)
        .enter()
        .append("rect")
        .attr("x", d => x(d.year_month))
        .attr("width", x.bandwidth())
        .attr("y", d => yGMV(d.total_gmv))
        .attr("height", d => height - yGMV(d.total_gmv))
        .attr("fill", "#3b82f6")
        .attr("rx", 3)
        .attr("opacity", 0.8)
        .on("mousemove", (event, d) => {
          tooltip.transition().duration(100).style("opacity", 1);
          tooltip.html(`
            <strong>Period: ${d.year_month}</strong><br/>
            💰 GMV: <strong>R$ ${Number(d.total_gmv).toLocaleString()}</strong><br/>
            📦 Orders: <strong>${d.total_orders.toLocaleString()}</strong><br/>
            🚨 SLA Breach: <strong>${d.sla_breach_rate_pct}%</strong>
          `)
          .style("left", (event.pageX + 15) + "px")
          .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => tooltip.transition().duration(200).style("opacity", 0));

      // SLA Breach Line
      const line = d3.line()
        .x(d => x(d.year_month) + x.bandwidth() / 2)
        .y(d => ySLA(d.sla_breach_rate_pct))
        .curve(d3.curveMonotoneX);

      svg.append("path")
        .datum(cleanData)
        .attr("fill", "none")
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 2.5)
        .attr("d", line);

      // Dots on line
      svg.selectAll(".dot")
        .data(cleanData)
        .enter()
        .append("circle")
        .attr("cx", d => x(d.year_month) + x.bandwidth() / 2)
        .attr("cy", d => ySLA(d.sla_breach_rate_pct))
        .attr("r", 3.5)
        .attr("fill", "#ef4444");
    });
}

function renderRFMTable() {
  const tbody = document.getElementById("rfm-tbody");
  
  const badgeColors = {
    "Champions": "background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4);",
    "Loyal Customers": "background: rgba(59, 130, 246, 0.2); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.4);",
    "Potential Loyalists": "background: rgba(6, 182, 212, 0.2); color: #06b6d4; border: 1px solid rgba(6, 182, 212, 0.4);",
    "New / Promising": "background: rgba(139, 92, 246, 0.2); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.4);",
    "At Risk": "background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4);",
    "High Value Churned": "background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4);",
    "Hibernating / Lost": "background: rgba(100, 116, 139, 0.2); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.4);"
  };

  fetch("/api/rfm")
    .then(r => r.json())
    .then(segments => {
      tbody.innerHTML = "";
      segments.forEach(seg => {
        const tr = document.createElement("tr");
        const style = badgeColors[seg.customer_segment] || "";
        tr.innerHTML = `
          <td><span class="segment-badge" style="${style}">${seg.customer_segment}</span></td>
          <td><strong>${Number(seg.customer_count).toLocaleString()}</strong></td>
          <td>${seg.avg_recency} days</td>
          <td>${seg.avg_frequency}</td>
          <td>R$ ${Number(seg.total_segment_revenue).toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
      });
    });
}
