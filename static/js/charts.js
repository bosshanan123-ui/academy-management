/* =====================================================
   charts.js — reusable Chart.js wrappers
   ===================================================== */

const CHART_COLORS = {
  primary: '#4f46e5',
  primaryLight: 'rgba(79,70,229,0.15)',
  green: '#16a34a',
  greenLight: 'rgba(22,163,74,0.15)',
  red: '#dc2626',
  redLight: 'rgba(220,38,38,0.15)',
  amber: '#d97706',
  blue: '#0ea5e9',
  purple: '#7c3aed',
  pink: '#db2777',
};

function renderBarChart(canvasId, labels, data, label = 'Value', color = CHART_COLORS.primary) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: color,
        borderRadius: 6,
        maxBarThickness: 48,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#eef2f7' } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderLineChart(canvasId, labels, data, label = 'Value', color = CHART_COLORS.primary) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: color,
        backgroundColor: 'rgba(79,70,229,0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointBackgroundColor: color,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#eef2f7' } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderDoughnutChart(canvasId, labels, data, colors) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || [
          CHART_COLORS.green,
          CHART_COLORS.red,
          CHART_COLORS.amber,
        ],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12 } },
      },
    },
  });
}

function renderMultiBarChart(canvasId, labels, datasets) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#eef2f7' } },
        x: { grid: { display: false } },
      },
    },
  });
}