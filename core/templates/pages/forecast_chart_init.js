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

  function formatChartLabel(dateStr, isHistorical, dataLength, actualLength, period = 'daily') {
    try {
      const date = new Date(dateStr);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      date.setHours(0, 0, 0, 0);
      
      const diffTime = today - date;
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
      
      // For historical data, show relative dates
      if (isHistorical) {
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays > 1 && diffDays <= 7) return `${diffDays} days ago`;
        
        // For older dates, show month/day
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } else {
        // For forecast data, show relative future dates
        const futureDays = -diffDays;
        if (futureDays === 0) return 'Today';
        if (futureDays === 1) return 'Tomorrow';
        
        if (period === 'weekly' && futureDays === 7) return '+1 week';
        if (period === 'monthly' && futureDays >= 28) return '+1 month';
        if (period === 'monthly' && futureDays >= 56) return '+2 months';
        
        if (futureDays > 1 && futureDays <= 7) return `+${futureDays} days`;
        
        // For further dates, show month/day
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }
    } catch (e) {
      return dateStr;
    }
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

  // Plugin to draw vertical separator at the last historical index
  const separatorPlugin = {
    id: 'separatorLine',
    afterDatasetsDraw(chart) {
      if (!chart.data || !chart.data.labels) return;
      const labels = chart.data.labels;
      const lastHistoricalIndex = (labels.findIndex(l => l === 'Today')) || (labels.length ? labels.indexOf('Today') : -1);
      // Fallback: if 'Today' not found, use last label of historical length
      if (lastHistoricalIndex <= 0) return;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;
      if (!xAxis || !yAxis) return;
      const xPos = xAxis.getPixelForValue(lastHistoricalIndex);
      const ctx = chart.ctx;
      ctx.save();
      ctx.strokeStyle = 'rgba(148,163,184,0.6)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4,4]);
      ctx.beginPath();
      ctx.moveTo(xPos, yAxis.top);
      ctx.lineTo(xPos, yAxis.bottom);
      ctx.stroke();
      ctx.restore();
    }
  };

  function renderChart(data){
    const labels = (data.labels || []).slice();
    const forecastLabels = buildForecastLabels(labels, (data.forecast || []).length);
    const combined = labels.concat(forecastLabels);
    const actualPadded = (data.actual || []).concat(Array((data.forecast||[]).length).fill(null));
    const forecastPadded = Array((data.actual||[]).length).fill(null).concat(data.forecast || []);

    // Format labels for display (always calendar dates, show 'Today' when applicable)
    const formattedLabels = combined.map((dateStr, idx) => {
      const isHistorical = idx < labels.length;
      // Reuse existing formatter but show absolute dates for everything and 'Today'
      try {
        const date = new Date(dateStr);
        const today = new Date(); today.setHours(0,0,0,0);
        date.setHours(0,0,0,0);
        const diffDays = Math.round((today - date) / (1000*60*60*24));
        if (diffDays === 0) return 'Today';
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } catch(e){ return dateStr; }
    });

    const ctx = document.getElementById('salesChart')?.getContext('2d');
    if(!ctx) return;
    if(salesChart){ try{ salesChart.destroy(); }catch(e){} }
    salesChart = new Chart(ctx, {
      type: 'line',
      data: { labels: formattedLabels, datasets: [
        { label: 'Historical Daily Sales', data: actualPadded, borderColor: '#FF8C42', backgroundColor: 'rgba(255,140,66,0.08)', fill: true, tension: 0.4, pointRadius: 6, pointBackgroundColor: '#FF8C42', pointBorderColor:'#fff', pointBorderWidth:2, borderWidth:3 },
        { label: 'AI-Driven Forecast', data: forecastPadded, borderColor: '#FF8C42', backgroundColor: 'rgba(255,140,66,0.04)', fill: false, borderDash:[7,4], tension: 0.4, pointRadius: 6, pointBackgroundColor:'#FF8C42', pointBorderColor:'#fff', pointBorderWidth:2, borderWidth:3 }
      ] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true, position:'top', labels: { usePointStyle:true } }, tooltip: { mode:'index', intersect:false, callbacks:{ label: function(ctx){ if (ctx.raw === null) return ctx.dataset.label + ': —'; return ctx.dataset.label + ': ' + (window.currencySymbol||'₱') + Number(ctx.raw).toLocaleString('en-PH'); } } } },
        scales: { y: { beginAtZero:true, ticks:{ callback: function(v){ return (window.currencySymbol||'₱') + Number(v).toLocaleString('en-PH'); } }, grid: { color:'rgba(229,231,235,0.6)' } }, x: { grid:{display:false} } }
      },
      plugins: [separatorPlugin]
    });
  }

  async function refreshAndRender(){
    const data = await fetchSeries();
    console.log('[Template Forecast] Data fetched:', data);
    renderChart(data);
  }

  // initial render
  window.addEventListener('load', function(){ setTimeout(refreshAndRender, 300); });
  document.getElementById('refreshForecastBtn')?.addEventListener('click', refreshAndRender);
  document.getElementById('rangeSelect')?.addEventListener('change', refreshAndRender);

  // expose for other scripts
  window.refreshForecast = refreshAndRender;
})();
