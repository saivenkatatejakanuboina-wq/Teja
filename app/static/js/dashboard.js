/**
 * Chart.js renderers for the CRM dashboard.
 */
(function () {
  "use strict";

  const data = window.CRM_DASHBOARD;
  if (!data || typeof Chart === "undefined") {
    return;
  }

  const gridColor = "rgba(15, 39, 68, 0.08)";
  const textColor = "#6b7c8f";

  Chart.defaults.font.family = '"Segoe UI", system-ui, -apple-system, sans-serif';
  Chart.defaults.color = textColor;

  const leadsEl = document.getElementById("leadsChart");
  if (leadsEl) {
    new Chart(leadsEl, {
      type: "line",
      data: {
        labels: data.leadTrend.labels,
        datasets: [
          {
            label: "Leads",
            data: data.leadTrend.values,
            borderColor: "#1d6ef5",
            backgroundColor: "rgba(29, 110, 245, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: "#1d6ef5",
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
            grid: { color: gridColor },
            ticks: { precision: 0 },
          },
        },
      },
    });
  }

  const outcomesEl = document.getElementById("outcomesChart");
  if (outcomesEl) {
    new Chart(outcomesEl, {
      type: "doughnut",
      data: {
        labels: data.dealOutcomes.labels,
        datasets: [
          {
            data: data.dealOutcomes.values,
            backgroundColor: ["#198754", "#dc3545", "#1d6ef5"],
            borderWidth: 0,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, usePointStyle: true, padding: 16 },
          },
        },
      },
    });
  }

  const pipelineEl = document.getElementById("pipelineChart");
  if (pipelineEl) {
    new Chart(pipelineEl, {
      type: "bar",
      data: {
        labels: data.pipelineStages.labels,
        datasets: [
          {
            label: "Deals",
            data: data.pipelineStages.values,
            backgroundColor: [
              "#93c5fd",
              "#7dd3fc",
              "#fbbf24",
              "#c4b5fd",
              "#86efac",
              "#fca5a5",
            ],
            borderRadius: 6,
            maxBarThickness: 36,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxRotation: 40, minRotation: 0 },
          },
          y: {
            beginAtZero: true,
            grid: { color: gridColor },
            ticks: { precision: 0 },
          },
        },
      },
    });
  }

  const revenueEl = document.getElementById("revenueChart");
  if (revenueEl) {
    new Chart(revenueEl, {
      type: "bar",
      data: {
        labels: data.revenueTrend.labels,
        datasets: [
          {
            label: "Won",
            data: data.revenueTrend.won,
            backgroundColor: "#198754",
            borderRadius: 6,
            maxBarThickness: 28,
          },
          {
            label: "Pipeline",
            data: data.revenueTrend.pipeline,
            backgroundColor: "#1d6ef5",
            borderRadius: 6,
            maxBarThickness: 28,
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
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return (
                  ctx.dataset.label +
                  ": $" +
                  Number(ctx.raw).toLocaleString()
                );
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            grid: { color: gridColor },
            ticks: {
              callback: function (value) {
                return "$" + value / 1000 + "k";
              },
            },
          },
        },
      },
    });
  }
})();
