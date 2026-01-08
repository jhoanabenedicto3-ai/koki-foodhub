(function(){
  // Lightweight Chart init for Revenue Trend; fetches forecast API and renders weekly by default
  window.currencySymbol = window.currencySymbol || '{{ currency|escapejs }}' || '';

  async function fetchSeries(){
    try{
      const url = new URL('{% url "forecast_api" %}', window.location.origin);
      
      // Get range selection
      const rangeSelect = document.getElementById('rangeSelect');
      const range = rangeSelect ? rangeSelect.value : 'Last 30 Days';
      
      // Calculate date range based on selection
      const today = new Date();
      let startDate = new Date(today);
      let endDate = new Date(today);
      
      if (range === 'Last 7 Days') {
        startDate.setDate(today.getDate() - 7);
      } else if (range === 'Last 30 Days') {
        startDate.setDate(today.getDate() - 30);
      } else if (range === 'Last 90 Days') {
        startDate.setDate(today.getDate() - 90);
      }
      
      // Format dates as YYYY-MM-DD
      const formatDate = (date) => date.toISOString().slice(0, 10);
      
      url.searchParams.append('start', formatDate(startDate));
      url.searchParams.append('end', formatDate(endDate));
      
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
    let period = 'daily'; // default to daily
    
    // Detect period type by analyzing existing labels
    if (existingLabels.length >= 2) {
      const secondLastLabel = existingLabels[existingLabels.length - 2];
      try {
        const last = new Date(lastLabel);
        const secondLast = new Date(secondLastLabel);
        const dayDiff = Math.round((last - secondLast) / (1000 * 60 * 60 * 24));
        
        if (dayDiff >= 28) {
          period = 'monthly';
        } else if (dayDiff >= 6) {
          period = 'weekly';
        }
      } catch (e) {
        // Fall back to daily if date parsing fails
      }
    }
    
    try{
      const base = new Date(lastLabel);
      return Array.from({length: forecastLen}, (_, i) => {
        const d = new Date(base);
        if (period === 'monthly') {
          // Increment by month
          d.setMonth(base.getMonth() + (i+1));
        } else if (period === 'weekly') {
          // Increment by week (7 days)
          d.setDate(base.getDate() + (i+1) * 7);
        } else {
          // Increment by day
          d.setDate(base.getDate() + (i+1));
        }
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
