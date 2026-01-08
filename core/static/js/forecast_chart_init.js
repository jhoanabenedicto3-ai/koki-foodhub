// Forecast Chart Initialization Script
// This script is loaded after the Django template has been rendered

function formatChartLabel(dateStr, isHistorical, totalDataPoints, historicalCount, period = 'daily') {
  try {
    const date = new Date(dateStr + 'T00:00:00Z'); // Parse as UTC to avoid timezone issues
    const today = new Date();
    today.setUTCHours(0, 0, 0, 0);
    
    const dateUTC = new Date(date);
    dateUTC.setUTCHours(0, 0, 0, 0);
    
    const diffTime = today - dateUTC;
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    
    // For historical data, show relative dates
    if (isHistorical) {
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays > 1 && diffDays <= 30) return `${diffDays}d ago`;
      
      // For older dates, show date format
      const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      return formatted;
    } else {
      // For forecast data, show relative future dates or actual dates
      const futureDays = -diffDays;
      
      if (futureDays === 0) return 'Today';
      if (futureDays === 1) return 'Tomorrow';
      if (futureDays > 1 && futureDays <= 7) return `+${futureDays}d`;
      
      // For dates further out, show date
      const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      return formatted;
    }
  } catch (e) {
    console.warn('Error formatting chart label:', dateStr, e);
    return dateStr;
  }
}

function buildForecastLabels(existingLabels, forecastLen){
  if(!forecastLen || forecastLen <= 0) return [];
  if(!existingLabels || existingLabels.length === 0) return Array.from({length: forecastLen}, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i + 1);
    return d.toISOString().slice(0, 10);
  });
  
  // Always generate daily forecast dates, one day at a time
  const lastLabel = existingLabels[existingLabels.length - 1];
  try {
    const baseDate = new Date(lastLabel);
    const forecastDates = [];
    
    for (let i = 1; i <= forecastLen; i++) {
      const forecastDate = new Date(baseDate);
      forecastDate.setDate(baseDate.getDate() + i);
      forecastDates.push(forecastDate.toISOString().slice(0, 10));
    }
    
    return forecastDates;
  } catch (e) {
    console.warn('Error building forecast labels:', e);
    return Array.from({length: forecastLen}, (_, i) => 'F+' + (i+1));
  }
}

let salesChart = null;

function renderChart(data){
  const labels = (data.labels || []).slice();
  const forecastLabels = buildForecastLabels(labels, (data.forecast || []).length);
  const combined = labels.concat(forecastLabels);
  const actualPadded = (data.actual || []).concat(Array((data.forecast||[]).length).fill(null));
  const forecastPadded = Array((data.actual||[]).length).fill(null).concat(data.forecast || []);
  
  // Format labels for display
  const formattedLabels = combined.map((dateStr, idx) => {
    const isHistorical = idx < labels.length;
    return formatChartLabel(dateStr, isHistorical, combined.length, labels.length);
  });

  const ctx = document.getElementById('salesChart')?.getContext('2d');
  if(!ctx) return;
  if(salesChart){ try{ salesChart.destroy(); }catch(e){} }
  
  salesChart = new Chart(ctx, {
    type: 'line',
    data: { 
      labels: formattedLabels, 
      datasets: [
        { 
          label: 'Historical Data', 
          data: actualPadded, 
          borderColor: '#f97316', 
          backgroundColor: 'rgba(249,115,22,0.08)', 
          fill: true, 
          tension: 0.36, 
          pointRadius: 3, 
          borderWidth: 2 
        },
        { 
          label: 'Forecast Projection', 
          data: forecastPadded, 
          borderColor: '#f59e0b', 
          backgroundColor: 'rgba(245,158,11,0.04)', 
          fill: false, 
          borderDash: [6,4], 
          tension: 0.3, 
          pointRadius: 4, 
          borderWidth: 2 
        }
      ] 
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { 
        legend: { display: false }, 
        tooltip: { 
          callbacks: { 
            label: function(ctx){ 
              const symbol = window.currencySymbol || '';
              return ctx.dataset.label + ': ' + (symbol + Number(ctx.raw).toLocaleString()); 
            } 
          } 
        } 
      },
      scales: { 
        y: { 
          beginAtZero: true, 
          ticks: { 
            callback: function(v){ 
              const symbol = window.currencySymbol || '';
              return symbol + Number(v).toLocaleString(); 
            } 
          } 
        } 
      }
    }
  });
}

async function fetchSeries(){
  try{
    const url = new URL('/forecast/api/', window.location.origin);
    
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
  }catch(e){ 
    console.warn('fetchSeries failed', e); 
    return {labels:[], actual:[], forecast:[], upper:[], lower:[]}; 
  }
}

async function refreshAndRender(){
  const data = await fetchSeries();
  renderChart(data);
}

// Initialize chart when page loads
(function() {
  console.log('[Forecast Chart] Initializing...');
  
  function init() {
    console.log('[Forecast Chart] DOMContentLoaded event fired');
    
    // Fetch and render chart
    refreshAndRender().then(() => {
      console.log('[Forecast Chart] Chart rendered successfully');
    }).catch((err) => {
      console.error('[Forecast Chart] Error during render:', err);
    });
    
    // Wire up event listeners
    const refreshBtn = document.getElementById('refreshForecastBtn');
    const rangeSelect = document.getElementById('rangeSelect');
    
    if(refreshBtn) {
      console.log('[Forecast Chart] Wired refresh button');
      refreshBtn.addEventListener('click', refreshAndRender);
    }
    
    if(rangeSelect) {
      console.log('[Forecast Chart] Wired range select');
      rangeSelect.addEventListener('change', refreshAndRender);
    }
    
    // Expose for other scripts
    window.refreshForecast = refreshAndRender;
  }
  
  // Try multiple initialization methods
  if (document.readyState === 'loading') {
    console.log('[Forecast Chart] Document still loading, adding DOMContentLoaded listener');
    document.addEventListener('DOMContentLoaded', init);
  } else {
    console.log('[Forecast Chart] Document already loaded, initializing immediately');
    init();
  }
  
  // Also initialize on window load as fallback
  window.addEventListener('load', function() {
    console.log('[Forecast Chart] Window load event fired');
    if (!salesChart) {
      console.log('[Forecast Chart] Chart not initialized yet, initializing now');
      init();
    }
  });
})();

