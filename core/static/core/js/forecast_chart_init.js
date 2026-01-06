(function(){
  // Lightweight Chart init for Revenue Trend; fetches forecast API and renders weekly by default
  // Ensure currencySymbol is available (set by inline template script) or default to empty
  window.currencySymbol = window.currencySymbol || '';

  async function fetchSeries(){
    try{
      // Prefer inline server-side series when available (fast, accurate)
      const range = document.getElementById('rangeSelect')?.value || 'Last 30 Days';
      function pickServerSeries(){
        if(range.includes('90')) return window._serverWeekly || window._serverMonthly || window._serverDaily || null;
        // default to daily for 7/30 day ranges
        return window._serverDaily || window._serverWeekly || window._serverMonthly || null;
      }
      const inline = pickServerSeries();
      if(inline){ window._seriesSource = 'server_inline'; return inline; }

      // Otherwise fetch from API
      const url = '/forecast/api/';
      const res = await fetch(url, { credentials: 'same-origin' });
      if(!res.ok) throw new Error('Network response not ok: ' + res.status);
      const json = await res.json();

      // choose series based on UI range
      const rangePref = document.getElementById('rangeSelect')?.value || 'Last 30 Days';
      let raw = null;
      if(rangePref.includes('90')){
        raw = json.weekly_revenue || json.weekly || json.monthly_revenue || json.monthly;
      } else {
        raw = json.daily_revenue || json.daily || json.weekly_revenue || json.weekly;
      }
      raw = raw || {labels:[], actual:[], forecast:[], upper:[], lower:[]};

      const scale = json.avg_unit_price || 0;

      // If we have revenue-prefixed series from the server/API, use them directly.
      if((json.weekly_revenue || json.daily_revenue || json.monthly_revenue)){
        window._seriesSource = 'revenue_from_server_api';
        return raw;
      }

      // Fallback: if avg_unit_price is available, convert unit series to revenue client-side
      if(scale && scale > 0){
        const scaled = {
          labels: raw.labels || [],
          actual: (raw.actual || []).map(v => (v == null ? null : Math.round(v * scale))),
          forecast: (raw.forecast || []).map(v => (v == null ? null : Math.round(v * scale))),
          upper: (raw.upper || []).map(v => (v == null ? null : Math.round(v * scale))),
          lower: (raw.lower || []).map(v => (v == null ? null : Math.round(v * scale))),
          confidence: raw.confidence || 0
        };
        window._avgUnitPrice = scale;
        window._seriesSource = 'scaled_client_api';

        // sanity-check: if the first forecast point is wildly different from the server-provided today forecast revenue
        try{
          const f0 = (scaled.forecast && scaled.forecast[0]) || null;
          const todayRev = window._todayForecastRevenue || 0;
          if(f0 && todayRev && Math.abs(f0 - todayRev) / Math.max(todayRev,1) > 0.5){
            console.warn('Forecast scaling mismatch: client-scaled forecast first value', f0, 'differs from server today forecast revenue', todayRev);
          }
        }catch(e){}

        return scaled;
      }

      console.warn('Forecast data received in units (no revenue conversion available). Set avg_unit_price or use server-side revenue series to fix display.');
      window._seriesSource = 'units_fallback_api';
      return raw;
    }catch(e){ console.warn('fetchSeries failed', e); return {labels:[], actual:[], forecast:[], upper:[], lower:[]}; }
  }

  function buildForecastLabels(existingLabels, forecastLen){
    if(!forecastLen || forecastLen <= 0) return [];
    if(!existingLabels || existingLabels.length === 0) return Array.from({length: forecastLen}, (_, i) => 'F+' + (i+1));
    const lastLabel = existingLabels[existingLabels.length - 1];
    try{
      const base = new Date(lastLabel);
      return Array.from({length: forecastLen}, (_, i) => {
        const d = new Date(base);
        d.setDate(base.getDate() + (i+1));
        return d.toISOString().slice(0,10);
      });
    }catch(e){ return Array.from({length: forecastLen}, (_, i) => 'F+' + (i+1)); }
  }

  let salesChart = null;
  function renderChart(data){
    const isoLabels = (data.labels || []).slice();
    const forecastLabels = buildForecastLabels(isoLabels, (data.forecast || []).length);
    const combinedIso = isoLabels.concat(forecastLabels);

    // human-friendly labels (e.g., '3 days ago', 'Today', 'Tomorrow', '+1 week')
    function formatXLabel(d){
      try{
        const dt = new Date(d + 'T00:00:00');
        const today = new Date();
        const diffDays = Math.round((dt - new Date(today.getFullYear(), today.getMonth(), today.getDate())) / (1000*60*60*24));
        if(diffDays === 0) return 'Today';
        if(diffDays === 1) return 'Tomorrow';
        if(diffDays < 0 && diffDays >= -6) return `${Math.abs(diffDays)} days ago`;
        if(diffDays >=7 && diffDays % 7 === 0) return `+${diffDays/7} week${diffDays/7 > 1 ? 's' : ''}`;
        if(Math.abs(diffDays) >= 28 && Math.abs(diffDays) <= 31) return '+1 month';
        // fallback compact date
        return dt.toLocaleDateString(undefined, {month: 'short', day: 'numeric'});
      }catch(e){ return d; }
    }

    const labels = combinedIso.map(l => formatXLabel(l));
    const actualPadded = (data.actual || []).concat(Array((data.forecast||[]).length).fill(null));
    const forecastPadded = Array((data.actual||[]).length).fill(null).concat(data.forecast || []);

    const ctx = document.getElementById('salesChart')?.getContext('2d');
    if(!ctx) return;

    // create a soft vertical gradient for the historical (actual) area
    const canvasH = ctx.canvas.height || 420;
    const grad = ctx.createLinearGradient(0, 0, 0, canvasH);
    grad.addColorStop(0, 'rgba(249,115,22,0.12)');
    grad.addColorStop(0.6, 'rgba(249,115,22,0.06)');
    grad.addColorStop(1, 'rgba(249,115,22,0.00)');

    // plugin to draw forecast cutoff/fade
    const forecastCutoffPlugin = {
      id: 'forecastCutoff',
      beforeDraw: (chart) => {
        try{
          const ds = chart.data.datasets[1].data || [];
          const firstForecastIdx = ds.findIndex(v => v != null);
          if(firstForecastIdx <= 0) return;
          const x = chart.scales.x.getPixelForValue(firstForecastIdx);
          const {top, bottom, right} = chart.chartArea;
          const g = chart.ctx.createLinearGradient(x, top, right, top);
          g.addColorStop(0, 'rgba(255,255,255,0)');
          g.addColorStop(1, 'rgba(255,255,255,0.95)');
          chart.ctx.save();
          chart.ctx.fillStyle = g;
          chart.ctx.fillRect(x, top, right - x, bottom - top);
          chart.ctx.beginPath();
          chart.ctx.moveTo(x + 0.5, top);
          chart.ctx.lineTo(x + 0.5, bottom);
          chart.ctx.strokeStyle = 'rgba(15,23,36,0.06)';
          chart.ctx.lineWidth = 1;
          chart.ctx.stroke();
          chart.ctx.restore();
        }catch(e){}
      }
    };

    if(salesChart){ try{ salesChart.destroy(); }catch(e){} }
    salesChart = new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: [
        {
          label: 'Historical Data',
          data: actualPadded,
          borderColor: '#f97316',
          backgroundColor: grad,
          fill: true,
          tension: 0.36,
          pointRadius: 5,
          pointBackgroundColor: '#fff',
          pointBorderColor: '#f97316',
          pointBorderWidth: 2,
          borderWidth: 2,
          pointHoverRadius: 7
        },
        {
          label: 'Forecast Projection',
          data: forecastPadded,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245,158,11,0.02)',
          fill: false,
          tension: 0.36,
          pointRadius: 6,
          pointBackgroundColor: '#fff',
          pointBorderColor: '#f59e0b',
          pointBorderWidth: 2,
          borderWidth: 3,
          pointHoverRadius: 8
        }
      ] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              title: function(items){
                const idx = items[0].dataIndex;
                const raw = combinedIso[idx];
                try{ return new Date(raw + 'T00:00:00').toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}); }catch(e){ return raw; }
              },
              label: function(ctx){
                const val = ctx.raw;
                if(val == null) return ctx.dataset.label + ': —';
                return ctx.dataset.label + ': ' + (window.currencySymbol || '') + Number(val).toLocaleString();
              }
            }
          }
        },
        interaction: { mode: 'nearest', axis: 'x', intersect: false },
        elements: { line: { capStyle: 'round', borderJoinStyle: 'round' } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 12 }, maxRotation: 45, minRotation: 45 } },
          y: { beginAtZero: true, ticks: { callback: function(v){ if(v === 0) return (window.currencySymbol || '') + '0'; return (window.currencySymbol || '') + Number(v).toLocaleString(); }, color: '#9ca3af', font: { size: 12 } }, grid: { color: 'rgba(15,23,36,0.03)' } }
        },
        animation: { duration: 400 }
      },
      plugins: [forecastCutoffPlugin]
    });
  }

  async function refreshAndRender(){
    const data = await fetchSeries();
    renderChart(data);
  }

  // initial render
  window.addEventListener('load', function(){ setTimeout(refreshAndRender, 300); });
  document.getElementById('refreshForecastBtn')?.addEventListener('click', refreshAndRender);
  document.getElementById('rangeSelect')?.addEventListener('change', refreshAndRender);

  // expose for other scripts
  window.refreshForecast = refreshAndRender;
})();
