(function(){
  // Lightweight Chart init for Revenue Trend; fetches forecast API and renders weekly by default
  // Ensure currencySymbol is available (set by inline template script) or default to empty
  window.currencySymbol = window.currencySymbol || '';

  async function fetchSeries(){
    try{
      const url = '/forecast/api/';
      const res = await fetch(url, { credentials: 'same-origin' });
      if(!res.ok) throw new Error('Network response not ok: ' + res.status);
      const json = await res.json();
      return json.weekly || json.daily || json.monthly || {labels:[], actual:[], forecast:[], upper:[], lower:[]};
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
    const labels = (data.labels || []).slice();
    const forecastLabels = buildForecastLabels(labels, (data.forecast || []).length);
    const combined = labels.concat(forecastLabels);
    const actualPadded = (data.actual || []).concat(Array((data.forecast||[]).length).fill(null));
    const forecastPadded = Array((data.actual||[]).length).fill(null).concat(data.forecast || []);

    const ctx = document.getElementById('salesChart')?.getContext('2d');
    if(!ctx) return;
    if(salesChart){ try{ salesChart.destroy(); }catch(e){} }
    salesChart = new Chart(ctx, {
      type: 'line',
      data: { labels: combined.map(l=>l), datasets: [
        { label: 'Historical Data', data: actualPadded, borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,0.08)', fill: true, tension: 0.36, pointRadius: 3, borderWidth: 2 },
        { label: 'Forecast Projection', data: forecastPadded, borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.04)', fill: false, borderDash: [6,4], tension: 0.3, pointRadius: 4, borderWidth: 2 }
      ] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(ctx){ return ctx.dataset.label + ': ' + ((window.currencySymbol||'') + Number(ctx.raw).toLocaleString()); } } } },
        scales: { y: { beginAtZero: true, ticks: { callback: function(v){ return (window.currencySymbol||'') + Number(v).toLocaleString(); } } } }
      }
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
