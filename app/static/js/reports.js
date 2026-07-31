/**
 * Chart.js renderers for the Reports module.
 */
(function () {
  "use strict";

  const data = window.CRM_REPORTS;
  if (!data || typeof Chart === "undefined") {
    return;
  }

  const gridColor = "rgba(15, 39, 68, 0.08)";
  const textColor = "#6b7c8f";
  const palette = [
    "#1d6ef5",
    "#198754",
    "#d97706",
    "#7c3aed",
    "#dc3545",
    "#0ea5e9",
    "#f59e0b",
    "#64748b",
  ];

  Chart.defaults.font.family = '"Segoe UI", system-ui, -apple-system, sans-serif';
  Chart.defaults.color = textColor;

  const monthlyEl = document.getElementById("monthlyLeadsChart");
  if (monthlyEl) {
    new Chart(monthlyEl, {
      type: "bar",
      data: {
        labels: data.monthly_leads.labels,
        datasets: [
          {
            label: "Leads",
            data: data.monthly_leads.values,
            backgroundColor: "#1d6ef5",
            borderRadius: 6,
            maxBarThickness: 28,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: gridColor },
          },
        },
      },
    });
  }

  const sourcesEl = document.getElementById("leadSourcesChart");
  if (sourcesEl) {
    new Chart(sourcesEl, {
      type: "doughnut",
      data: {
        labels: data.lead_sources.labels,
        datasets: [
          {
            data: data.lead_sources.values,
            backgroundColor: data.lead_sources.labels.map(
              (_, i) => palette[i % palette.length]
            ),
            borderWidth: 0,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "60%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, usePointStyle: true, padding: 14 },
          },
        },
      },
    });
  }

  const wonLostEl = document.getElementById("wonLostChart");
  if (wonLostEl) {
    new Chart(wonLostEl, {
      type: "bar",
      data: {
        labels: ["Leads", "Deals", "Combined"],
        datasets: [
          {
            label: "Won",
            data: data.won_vs_lost.rows.map((r) => r.won),
            backgroundColor: "#198754",
            borderRadius: 6,
            maxBarThickness: 36,
          },
          {
            label: "Lost",
            data: data.won_vs_lost.rows.map((r) => r.lost),
            backgroundColor: "#dc3545",
            borderRadius: 6,
            maxBarThickness: 36,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, usePointStyle: true, padding: 16 },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: gridColor },
          },
        },
      },
    });
  }

  const growthEl = document.getElementById("customerGrowthChart");
  if (growthEl) {
    new Chart(growthEl, {
      type: "line",
      data: {
        labels: data.customer_growth.labels,
        datasets: [
          {
            label: "New customers",
            data: data.customer_growth.new_customers,
            borderColor: "#1d6ef5",
            backgroundColor: "rgba(29, 110, 245, 0.12)",
            fill: true,
            tension: 0.3,
            pointRadius: 3,
          },
          {
            label: "Cumulative",
            data: data.customer_growth.cumulative,
            borderColor: "#198754",
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, usePointStyle: true, padding: 16 },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: gridColor },
          },
        },
      },
    });
  }

  const perfEl = document.getElementById("employeePerformanceChart");
  if (perfEl) {
    new Chart(perfEl, {
      type: "bar",
      data: {
        labels: data.employee_performance.labels,
        datasets: [
          {
            label: "Leads assigned",
            data: data.employee_performance.leads_assigned,
            backgroundColor: "#1d6ef5",
            borderRadius: 6,
            maxBarThickness: 24,
          },
          {
            label: "Leads won",
            data: data.employee_performance.leads_won,
            backgroundColor: "#198754",
            borderRadius: 6,
            maxBarThickness: 24,
          },
          {
            label: "Customers",
            data: data.employee_performance.customers,
            backgroundColor: "#0ea5e9",
            borderRadius: 6,
            maxBarThickness: 24,
          },
          {
            label: "Tasks completed",
            data: data.employee_performance.tasks_completed,
            backgroundColor: "#d97706",
            borderRadius: 6,
            maxBarThickness: 24,
          },
          {
            label: "Deals won",
            data: data.employee_performance.deals_won,
            backgroundColor: "#7c3aed",
            borderRadius: 6,
            maxBarThickness: 24,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, usePointStyle: true, padding: 16 },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: gridColor },
          },
        },
      },
    });
  }
})();
