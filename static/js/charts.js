/* ============================================================
   charts.js — Premium Chart.js Wrappers v4.0
   Rich gradients, animations, custom tooltips, depth
   ============================================================ */

if (window.Chart) {
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.font.weight = '600';
  Chart.defaults.color = '#64748b';
  Chart.defaults.animation.duration = 1100;
  Chart.defaults.animation.easing = 'easeOutQuart';
  Chart.defaults.interaction.mode = 'index';
  Chart.defaults.interaction.intersect = false;

  Chart.defaults.plugins.tooltip = {
    backgroundColor: 'rgba(15, 23, 42, 0.96)',
    titleColor: '#fff',
    titleFont: { size: 13, weight: '800' },
    bodyColor: '#e2e8f0',
    bodyFont: { size: 12, weight: '600' },
    padding: 14,
    cornerRadius: 12,
    borderColor: 'rgba(99, 102, 241, 0.5)',
    borderWidth: 1.5,
    displayColors: true,
    boxPadding: 8,
    usePointStyle: true,
    caretSize: 8,
    caretPadding: 10,
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
  indigo:  { solid: '#2f5aa3', dark: '#1c3b70', light: 'rgba(47, 90, 163, 0.15)',  top: '#4a7ac7' },
  violet:  { solid: '#6d5fbd', dark: '#443a80', light: 'rgba(109, 95, 189, 0.15)', top: '#9b8ee0' },
  pink:    { solid: '#a95f8a', dark: '#8a4a6f', light: 'rgba(169, 95, 138, 0.15)', top: '#c98bb4' },
  cyan:    { solid: '#34889b', dark: '#1d525f', light: 'rgba(52, 136, 155, 0.15)', top: '#56b3c9' },
  emerald: { solid: '#1f9670', dark: '#105c44', light: 'rgba(31, 150, 112, 0.15)', top: '#40c394' },
  amber:   { solid: '#d4901c', dark: '#8a5a0e', light: 'rgba(212, 144, 28, 0.15)', top: '#f2b844' },
  red:     { solid: '#c0433f', dark: '#7c393c', light: 'rgba(192, 67, 63, 0.15)',  top: '#e8706c' },
  sky:     { solid: '#3d87b0', dark: '#2e6c92', light: 'rgba(61, 135, 176, 0.15)', top: '#6ab1d9' },
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

function _gradient(ctx, c1, c2, h = 300) {
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, c1);
  g.addColorStop(1, c2);
  return g;
}

function _barRadius() {
  return { topLeft: 10, topRight: 10, bottomLeft: 0, bottomRight: 0 };
}

/* ------------------------------------------------------------------
   1. BAR CHART — Premium (rich gradient, shadow, rounded, animated)
   ------------------------------------------------------------------ */
function renderBarChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;

  // Gradient: top light → bottom solid
  const gradient = _gradient(ctx, p.top, p.dark, 320);

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: gradient,
        hoverBackgroundColor: p.solid,
        borderColor: p.solid,
        borderWidth: 0,
        borderRadius: _barRadius(),
        borderSkipped: false,
        maxBarThickness: 56,
        barPercentage: 0.72,
        categoryPercentage: 0.65,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1200,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 70,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.96)',
          titleColor: '#fff',
          bodyColor: '#fff',
          callbacks: {
            label: (ctx) => `  ${ctx.dataset.label}: ${ctx.parsed.y}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(47, 90, 163, 0.10)',
            drawBorder: false,
            lineWidth: 1,
            borderDash: [4, 4],
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
        x: {
          grid: { display: false, drawBorder: false },
          ticks: {
            color: '#475569',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------------
   2. LINE CHART — Premium (glowing area, points with shadow)
   ------------------------------------------------------------------ */
function renderLineChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;

  // Rich area gradient
  const area = _gradient(ctx, p.light.replace('0.15', '0.70'), 'rgba(255,255,255,0)', 320);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: p.solid,
        borderWidth: 3.5,
        backgroundColor: area,
        fill: true,
        tension: 0.45,
        pointRadius: 6,
        pointHoverRadius: 10,
        pointBackgroundColor: '#fff',
        pointBorderColor: p.solid,
        pointBorderWidth: 3.5,
        pointHoverBackgroundColor: p.solid,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 1400, easing: 'easeOutQuart' },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `  ${ctx.dataset.label}: ${ctx.parsed.y}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(47, 90, 163, 0.10)',
            drawBorder: false,
            borderDash: [4, 4],
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
        x: {
          grid: { display: false, drawBorder: false },
          ticks: {
            color: '#475569',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------------
   3. DOUGHNUT CHART — Premium (thick, shadow, gradient slices)
   ------------------------------------------------------------------ */
function renderDoughnutChart(canvasId, labels, data, colors) {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');

  const defaults = [
    PALETTE.emerald.solid,
    PALETTE.red.solid,
    PALETTE.amber.solid,
    PALETTE.indigo.solid,
    PALETTE.violet.solid,
  ];

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || defaults,
        hoverBackgroundColor: colors || defaults,
        borderWidth: 5,
        borderColor: '#ffffff',
        hoverOffset: 14,
        spacing: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      animation: { duration: 1200, easing: 'easeOutQuart' },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 18,
            font: { size: 12, weight: '700' },
            color: '#475569',
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
              return `  ${ctx.label}: ${ctx.parsed} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* ------------------------------------------------------------------
   4. MULTI-BAR CHART — Premium (grouped, colored, gradients)
   ------------------------------------------------------------------ */
function renderMultiBarChart(canvasId, labels, datasets) {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const colorKeys = ['emerald', 'red', 'indigo', 'amber', 'violet'];

  const styled = datasets.map((ds, i) => {
    const p = PALETTE[colorKeys[i % colorKeys.length]];
    return {
      ...ds,
      backgroundColor: _gradient(ctx, p.top, p.dark, 320),
      hoverBackgroundColor: p.solid,
      borderRadius: _barRadius(),
      borderSkipped: false,
      maxBarThickness: 48,
    };
  });

  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: styled },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1200,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 70,
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 18,
            font: { size: 12, weight: '700' },
            color: '#475569',
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(47, 90, 163, 0.10)',
            drawBorder: false,
            borderDash: [4, 4],
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
        x: {
          grid: { display: false, drawBorder: false },
          ticks: {
            color: '#475569',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------------
   5. HORIZONTAL BAR — Premium (for rankings)
   ------------------------------------------------------------------ */
function renderHorizontalBarChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;
  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;

  const gradient = ctx.createLinearGradient(0, 0, 400, 0);
  gradient.addColorStop(0, p.top);
  gradient.addColorStop(1, p.dark);

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: gradient,
        hoverBackgroundColor: p.solid,
        borderRadius: { topRight: 10, bottomRight: 10, topLeft: 0, bottomLeft: 0 },
        borderSkipped: false,
        maxBarThickness: 34,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1200,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 80,
      },
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: {
            color: 'rgba(47, 90, 163, 0.10)',
            drawBorder: false,
            borderDash: [4, 4],
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
        y: {
          grid: { display: false, drawBorder: false },
          ticks: {
            color: '#475569',
            font: { size: 11, weight: '700' },
            padding: 10,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------------
   6. RADAR CHART — Premium (multi-subject comparison)
   ------------------------------------------------------------------ */
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
      backgroundColor: p.light.replace('0.15', '0.35'),
      borderWidth: 3,
      pointBackgroundColor: p.solid,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 6,
      pointHoverRadius: 9,
    };
  });

  return new Chart(ctx, {
    type: 'radar',
    data: { labels, datasets: styled },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 1200, easing: 'easeOutQuart' },
      plugins: {
        legend: { position: 'bottom' },
      },
      scales: {
        r: {
          beginAtZero: true,
          grid: { color: 'rgba(47, 90, 163, 0.15)' },
          angleLines: { color: 'rgba(47, 90, 163, 0.10)' },
          pointLabels: {
            color: '#475569',
            font: { size: 11, weight: '700' },
          },
          ticks: {
            backdropColor: 'transparent',
            color: '#94a3b8',
            font: { size: 10 },
          },
        },
      },
    },
  });
}

/* ------------------------------------------------------------------
   EXPORTS
   ------------------------------------------------------------------ */
if (typeof window !== 'undefined') {
  window.PALETTE = PALETTE;
  window.CHART_COLORS = CHART_COLORS;
  window.renderBarChart = renderBarChart;
  window.renderLineChart = renderLineChart;
  window.renderDoughnutChart = renderDoughnutChart;
  window.renderMultiBarChart = renderMultiBarChart;
  window.renderHorizontalBarChart = renderHorizontalBarChart;
  window.renderRadarChart = renderRadarChart;
}
