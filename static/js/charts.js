/* ============================================================
   charts.js — Premium Chart.js Wrappers v2.0
   ------------------------------------------------------------
   Beautiful gradient charts with animations, custom tooltips,
   shadows and Gen-Z aesthetics.
   ============================================================ */

/* ------------------------------------------------------------
   GLOBAL CHART.JS DEFAULTS
   ------------------------------------------------------------ */
if (window.Chart) {
  // Global font
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.font.weight = '600';
  Chart.defaults.color = '#64748b';

  // Global animations
  Chart.defaults.animation.duration = 900;
  Chart.defaults.animation.easing = 'easeOutQuart';

  // Global interaction
  Chart.defaults.interaction.mode = 'index';
  Chart.defaults.interaction.intersect = false;

  // Global tooltip
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
    caretSize: 8,
    caretPadding: 8,
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

/* ------------------------------------------------------------
   COLOR PALETTE
   ------------------------------------------------------------ */
const PALETTE = {
  indigo:   { solid: '#6366f1', light: 'rgba(99, 102, 241, 0.15)', dark: '#4338ca' },
  violet:   { solid: '#8b5cf6', light: 'rgba(139, 92, 246, 0.15)', dark: '#6d28d9' },
  pink:     { solid: '#ec4899', light: 'rgba(236, 72, 153, 0.15)', dark: '#be185d' },
  cyan:     { solid: '#06b6d4', light: 'rgba(6, 182, 212, 0.15)', dark: '#0e7490' },
  emerald:  { solid: '#10b981', light: 'rgba(16, 185, 129, 0.15)', dark: '#047857' },
  amber:    { solid: '#f59e0b', light: 'rgba(245, 158, 11, 0.15)', dark: '#b45309' },
  red:      { solid: '#ef4444', light: 'rgba(239, 68, 68, 0.15)', dark: '#b91c1c' },
  sky:      { solid: '#0ea5e9', light: 'rgba(14, 165, 233, 0.15)', dark: '#0369a1' },
};

const CHART_COLORS = {
  primary: PALETTE.indigo.solid,
  primaryLight: PALETTE.indigo.light,
  green: PALETTE.emerald.solid,
  greenLight: PALETTE.emerald.light,
  red: PALETTE.red.solid,
  redLight: PALETTE.red.light,
  amber: PALETTE.amber.solid,
  blue: PALETTE.sky.solid,
  purple: PALETTE.violet.solid,
  pink: PALETTE.pink.solid,
};

/* ------------------------------------------------------------
   UTILS
   ------------------------------------------------------------ */
function _gradient(ctx, color1, color2, height = 260) {
  const g = ctx.createLinearGradient(0, 0, 0, height);
  g.addColorStop(0, color1);
  g.addColorStop(1, color2);
  return g;
}

function _roundedTopBarRadius() {
  return { topLeft: 10, topRight: 10, bottomLeft: 0, bottomRight: 0 };
}

/* ------------------------------------------------------------
   1. BAR CHART — Premium (gradient, rounded, shadow)
   ------------------------------------------------------------ */
function renderBarChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;

  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;

  const gradient = _gradient(ctx, p.solid, p.dark, 260);

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: gradient,
        hoverBackgroundColor: p.dark,
        borderColor: p.solid,
        borderWidth: 0,
        borderRadius: _roundedTopBarRadius(),
        borderSkipped: false,
        maxBarThickness: 52,
        barPercentage: 0.7,
        categoryPercentage: 0.65,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1100,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 60,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString()}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(99, 102, 241, 0.07)',
            drawBorder: false,
            lineWidth: 1,
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '600' },
            padding: 8,
          },
          border: { display: false },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 11, weight: '700' },
            padding: 8,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------
   2. LINE CHART — Premium (area fill, smooth, glowing points)
   ------------------------------------------------------------ */
function renderLineChart(canvasId, labels, data, label = 'Value', colorKey = 'indigo') {
  const el = document.getElementById(canvasId);
  if (!el) return null;

  const ctx = el.getContext('2d');
  const p = PALETTE[colorKey] || PALETTE.indigo;

  const areaGradient = _gradient(ctx, p.light.replace('0.15', '0.55'), 'rgba(255,255,255,0)', 260);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: p.solid,
        borderWidth: 3,
        backgroundColor: areaGradient,
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
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1300,
        easing: 'easeOutQuart',
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString()}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(99, 102, 241, 0.07)',
            drawBorder: false,
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '600' },
            padding: 8,
          },
          border: { display: false },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 11, weight: '700' },
            padding: 8,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------
   3. DOUGHNUT CHART — Premium (thick, colorful, centered text)
   ------------------------------------------------------------ */
function renderDoughnutChart(canvasId, labels, data, colors) {
  const el = document.getElementById(canvasId);
  if (!el) return null;

  const ctx = el.getContext('2d');

  const defaultColors = [
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
        backgroundColor: colors || defaultColors,
        hoverBackgroundColor: colors || defaultColors,
        borderWidth: 4,
        borderColor: '#ffffff',
        hoverOffset: 12,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      animation: {
        duration: 1100,
        easing: 'easeOutQuart',
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16,
            font: { size: 12, weight: '700' },
            color: '#475569',
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* ------------------------------------------------------------
   4. MULTI-BAR CHART — Premium (grouped, colored)
   ------------------------------------------------------------ */
function renderMultiBarChart(canvasId, labels, datasets) {
  const el = document.getElementById(canvasId);
  if (!el) return null;

  const ctx = el.getContext('2d');

  // Apply gradients to each dataset
  const styledDatasets = datasets.map((ds, i) => {
    const colorKeys = ['emerald', 'red', 'indigo', 'amber', 'violet'];
    const p = PALETTE[colorKeys[i % colorKeys.length]];
    return {
      ...ds,
      backgroundColor: _gradient(ctx, p.solid, p.dark, 260),
      hoverBackgroundColor: p.dark,
      borderRadius: _roundedTopBarRadius(),
      borderSkipped: false,
      maxBarThickness: 42,
    };
  });

  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: styledDatasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1100,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 60,
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16,
            font: { size: 12, weight: '700' },
            color: '#475569',
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(99, 102, 241, 0.07)',
            drawBorder: false,
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '600' },
            padding: 8,
          },
          border: { display: false },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 11, weight: '700' },
            padding: 8,
          },
          border: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------
   5. POLAR AREA CHART — Premium (bonus, for future use)
   ------------------------------------------------------------ */
function renderPolarChart(canvasId, labels, data) {
  const el = document.getElementById(canvasId);
  if (!el) return null;

  return new Chart(el.getContext('2d'), {
    type: 'polarArea',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: [
          'rgba(99, 102, 241, 0.75)',
          'rgba(236, 72, 153, 0.75)',
          'rgba(6, 182, 212, 0.75)',
          'rgba(16, 185, 129, 0.75)',
          'rgba(245, 158, 11, 0.75)',
        ],
        borderColor: '#fff',
        borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
      },
      scales: {
        r: {
          grid: { color: 'rgba(99, 102, 241, 0.1)' },
          ticks: { display: false },
        },
      },
    },
  });
}

/* ------------------------------------------------------------
   6. RADAR CHART — Premium (bonus, for subject comparison)
   ------------------------------------------------------------ */
function renderRadarChart(canvasId, labels, datasets) {
  const el = document.getElementById(canvasId);
  if (!el) return null;

  const styledDatasets = datasets.map((ds, i) => {
    const colorKeys = ['indigo', 'pink', 'emerald'];
    const p = PALETTE[colorKeys[i % colorKeys.length]];
    return {
      ...ds,
      borderColor: p.solid,
      backgroundColor: p.light.replace('0.15', '0.35'),
      borderWidth: 3,
      pointBackgroundColor: p.solid,
      pointBorderColor: '#fff',
      pointRadius: 5,
      pointHoverRadius: 8,
    };
  });

  return new Chart(el.getContext('2d'), {
    type: 'radar',
    data: { labels, datasets: styledDatasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
      },
      scales: {
        r: {
          beginAtZero: true,
          grid: { color: 'rgba(99, 102, 241, 0.12)' },
          angleLines: { color: 'rgba(99, 102, 241, 0.08)' },
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

/* ------------------------------------------------------------
   EXPORTS (for modules) — optional
   ------------------------------------------------------------ */
if (typeof window !== 'undefined') {
  window.PALETTE = PALETTE;
  window.CHART_COLORS = CHART_COLORS;
  window.renderBarChart = renderBarChart;
  window.renderLineChart = renderLineChart;
  window.renderDoughnutChart = renderDoughnutChart;
  window.renderMultiBarChart = renderMultiBarChart;
  window.renderPolarChart = renderPolarChart;
  window.renderRadarChart = renderRadarChart;
}
