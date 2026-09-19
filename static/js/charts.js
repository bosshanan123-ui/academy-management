/* ============================================================
   charts.js — Premium Chart.js Wrappers v3.0
   Gradient bar/line/doughnut + multi-bar + radar
   ------------------------------------------------------------ */

if (window.Chart) {
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.font.weight = '600';
  Chart.defaults.color = '#64748b';
  Chart.defaults.animation.duration = 900;
  Chart.defaults.animation.easing = 'easeOutQuart';
  Chart.defaults.interaction.mode = 'index';
  Chart.defaults.interaction.intersect = false;
  Chart.defaults.plugins.tooltip = {
    backgroundColor: 'rgba(15, 23, 42, 0.94)',
    titleColor: '#fff',
    titleFont: { size: 13, weight: '800' },
    bodyColor: '#e2e8f0',
    bodyFont: { size: 12, weight: '600' },
    padding: 12,
    cornerRadius: 10,
    borderColor: 'rgba(99, 102, 241, 0.4)',
    borderWidth: 1,
    displayColors: true,
    boxPadding: 6,
    usePointStyle: true,
  };
  Chart.defaults.plugins.legend = {
    labels: {
      usePointStyle: true,
      pointStyle: 'circle',
      padding: 16,
      font: { size: 12, weight: '700' },
      color: '#475569',
    },
  };
}

const PALETTE = {
  indigo:   { solid: '#2f5aa3', dark: '#1c3b70', light: 'rgba(47, 90, 163, 0.15)' },
  violet:   { solid: '#6d5fbd', dark: '#443a80', light: 'rgba(109, 95, 189, 0.15)' },
  pink:     { solid: '#a95f8a', dark: '#8a4a6f', light: 'rgba(169, 95, 138, 0.15)' },
  cyan:     { solid: '#34889b', dark: '#1d525f', light: 'rgba(52, 136, 155, 0.15)' },
  emerald:  { solid: '#1f9670', dark: '#105c44', light: 'rgba(31, 150, 112, 0.15)' },
  amber:    { solid: '#d4901c', dark: '#8a5a0e', light: 'rgba(212, 144, 28, 0.15)' },
  red:      { solid: '#c0433f', dark: '#7c393c', light: 'rgba(192, 67, 63, 0.15)' },
  sky:      { solid: '#3d87b0', dark: '#2e6c92', light: 'rgba(61, 135, 176, 0.15)' },
};

const CHART_COLORS = {
  primary: PALETTE.indigo.solid,
  green:   PALETTE.emerald.solid,
  red:     PALETTE.red.solid,
  amber:   PALETTE.amber.solid,
  blue:    PALETTE.sky.solid,
  purple:  PALETTE.violet.solid,
  pink:    PALETTE.pink.solid,
};

function _gradient(ctx, c1, c2, h = 260) {
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, c1);
  g.addColorStop(1, c2);
  return g;
}
function _barRadius() { return { topLeft: 10, topRight: 10, bottomLeft: 0, bottomRight: 0 }; }

/* ---------------- BAR CHART ---------------- */
function renderBarChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label, data,
        backgroundColor: _gradient(ctx, p.solid, p.dark, 260),
        hoverBackgroundColor: p.dark,
        borderRadius: _barRadius(),
        borderSkipped: false,
        maxBarThickness: 52,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 1100, easing: 'easeOutQuart', delay: (c) => c.dataIndex * 60 },
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(99,102,241,0.07)' }, ticks: { color: '#94a3b8', font: { size: 11, weight: '600' }, padding: 8 }, border: { display: false } },
        x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11, weight: '700' }, padding: 8 }, border: { display: false } },
      },
    },
  });
}

/* ---------------- LINE CHART ---------------- */
function renderLineChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;
  const area = _gradient(ctx, p.light.replace('0.15', '0.55'), 'rgba(255,255,255,0)', 260);
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label, data,
        borderColor: p.solid,
        borderWidth: 3,
        backgroundColor: area,
        fill: true,
        tension: 0.42,
        pointRadius: 5,
        pointHoverRadius: 9,
        pointBackgroundColor: '#fff',
        pointBorderColor: p.solid,
        pointBorderWidth: 3,
        pointHoverBackgroundColor: p.solid,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 3,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 1300, easing: 'easeOutQuart' },
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(99,102,241,0.07)' }, ticks: { color: '#94a3b8', font: { size: 11, weight: '600' }, padding: 8 }, border: { display: false } },
        x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11, weight: '700' }, padding: 8 }, border: { display: false } },
      },
    },
  });
}

/* ---------------- DOUGHNUT CHART ---------------- */
function renderDoughnutChart(canvasId, labels, data, colors) {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const defaults = [PALETTE.emerald.solid, PALETTE.red.solid, PALETTE.amber.solid, PALETTE.indigo.solid];
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || defaults,
        borderWidth: 4,
        borderColor: '#ffffff',
        hoverOffset: 12,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '68%',
      animation: { duration: 1100, easing: 'easeOutQuart' },
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, font: { size: 12, weight: '700' }, color: '#475569' } },
        tooltip: {
          callbacks: {
            label: (c) => {
              const total = c.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total ? ((c.parsed / total) * 100).toFixed(1) : 0;
              return ` ${c.label}: ${c.parsed} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* ---------------- MULTI-BAR CHART ---------------- */
function renderMultiBarChart(canvasId, labels, datasets) {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const colorKeys = ['emerald', 'red', 'indigo', 'amber', 'violet'];
  const styled = datasets.map((ds, i) => {
    const p = PALETTE[colorKeys[i % colorKeys.length]];
    return {
      ...ds,
      backgroundColor: _gradient(ctx, p.solid, p.dark, 260),
      hoverBackgroundColor: p.dark,
      borderRadius: _barRadius(),
      borderSkipped: false,
      maxBarThickness: 42,
    };
  });
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: styled },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 1100, easing: 'easeOutQuart', delay: (c) => c.dataIndex * 60 },
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, font: { size: 12, weight: '700' }, color: '#475569' } },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(99,102,241,0.07)' }, ticks: { color: '#94a3b8', font: { size: 11, weight: '600' }, padding: 8 }, border: { display: false } },
        x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11, weight: '700' }, padding: 8 }, border: { display: false } },
      },
    },
  });
}

/* ---------------- RADAR CHART ---------------- */
function renderRadarChart(canvasId, labels, datasets) {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const keys = ['indigo', 'pink', 'emerald'];
  const styled = datasets.map((ds, i) => {
    const p = PALETTE[keys[i % keys.length]];
    return {
      ...ds,
      borderColor: p.solid,
      backgroundColor: p.light,
      borderWidth: 3,
      pointBackgroundColor: p.solid,
      pointBorderColor: '#fff',
      pointRadius: 5,
    };
  });
  return new Chart(ctx, {
    type: 'radar',
    data: { labels, datasets: styled },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
      scales: {
        r: {
          beginAtZero: true,
          grid: { color: 'rgba(99,102,241,0.12)' },
          angleLines: { color: 'rgba(99,102,241,0.08)' },
          pointLabels: { color: '#475569', font: { size: 11, weight: '700' } },
          ticks: { backdropColor: 'transparent', color: '#94a3b8', font: { size: 10 } },
        },
      },
    },
  });
}

/* ---------------- EXPORTS ---------------- */
if (typeof window !== 'undefined') {
  window.PALETTE = PALETTE;
  window.CHART_COLORS = CHART_COLORS;
  window.renderBarChart = renderBarChart;
  window.renderLineChart = renderLineChart;
  window.renderDoughnutChart = renderDoughnutChart;
  window.renderMultiBarChart = renderMultiBarChart;
  window.renderRadarChart = renderRadarChart;
}
