// Forecast Chart Initialization Script
// This script is loaded after the Django template has been rendered

function formatChartLabel(dateStr, isHistorical, historicalCount, totalCount) {
  try {
    const date = new Date(dateStr + 'T00:00:00Z');
    
    // Format: "Mon Jan 2" for readability
    const monthDay = date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric' 
    });
    
    // Show all forecast dates clearly
    if (!isHistorical) {
      return monthDay;
    }
    
    // For historical data, show fewer labels to avoid crowding
    // Show labels every ~2 days when there's 7+ days
    if (historicalCount >= 7) {
      const position = totalCount - historicalCount;
      if (position % 2 === 0) {
        return monthDay;
      }
      return '';
    }
    
    // For short ranges (< 7 days), show all labels
    return monthDay;
    
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
  console.log('[Forecast Chart] Rendering chart with data:', data);
  
  const labels = (data.labels || []).slice();
  const forecastLabels = buildForecastLabels(labels, (data.forecast || []).length);
  const combined = labels.concat(forecastLabels);
  const actualPadded = (data.actual || []).concat(Array((data.forecast||[]).length).fill(null));
  const forecastPadded = Array((data.actual||[]).length).fill(null).concat(data.forecast || []);
  
  console.log('[Forecast Chart] Historical dates:', labels);
  console.log('[Forecast Chart] Forecast dates:', forecastLabels);
  
  // Format labels for display
  const formattedLabels = combined.map((dateStr, idx) => {
    const isHistorical = idx < labels.length;
    return formatChartLabel(dateStr, isHistorical, labels.length, combined.length);
  });

  const ctx = document.getElementById('salesChart')?.getContext('2d');
  if(!ctx) {
    console.warn('[Forecast Chart] Canvas context not found');
    return;
  }
  
  if(salesChart){ 
    try{ 
      salesChart.destroy();
    }catch(e){
      console.warn('[Forecast Chart] Error destroying old chart:', e);
    } 
  }
  
  // Add plugin to draw vertical line separating historical from forecast
  const separatorPlugin = {
    id: 'separatorLine',
    afterDatasetsDraw(chart) {
      if (labels.length === 0) return;
      
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;
      
      // Get position of last historical data point
      const lastHistoricalIndex = labels.length - 1;
      const xPos = xAxis.getPixelForValue(lastHistoricalIndex);
      
      const ctx = chart.ctx;
      ctx.save();
      ctx.strokeStyle = 'rgba(100, 100, 100, 0.3)';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(xPos, yAxis.getPixelForValue(yAxis.max));
      ctx.lineTo(xPos, yAxis.getPixelForValue(yAxis.min));
      ctx.stroke();
      ctx.restore();
    }
  };
  
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
        legend: { display: true },
        separatorLine: true,
        tooltip: { 
          mode: 'index',
          intersect: false,
          callbacks: { 
            title: function(ctx) {
              if (ctx.length > 0) {
                return ctx[0].label;
              }
              return '';
            },
            label: function(ctx){ 
              const symbol = window.currencySymbol || '';
              const value = ctx.raw !== null ? Number(ctx.raw).toLocaleString() : 'N/A';
              return ctx.dataset.label + ': ' + symbol + value; 
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
    },
    plugins: [separatorPlugin]
  });
  
  console.log('[Forecast Chart] Chart rendered successfully');
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
    
    console.log('[Forecast Chart] Fetching from URL:', url.toString());
    
    const res = await fetch(url, { credentials: 'same-origin' });
    if(!res.ok) throw new Error('Network response not ok: ' + res.status);
    const json = await res.json();
    
    console.log('[Forecast Chart] API Response:', json);
    
    // Prefer daily data for all ranges
    const data = json.daily || json.weekly || json.monthly || {labels:[], actual:[], forecast:[], upper:[], lower:[]};
    
    console.log('[Forecast Chart] Using data:', data);
    
    return data;
  }catch(e){ 
    console.error('fetchSeries failed:', e); 
    return {labels:[], actual:[], forecast:[], upper:[], lower:[]}; 
  }
}
}

async function refreshAndRender(){
  console.log('[Forecast Chart] refreshAndRender called');
  try {
    const data = await fetchSeries();
    console.log('[Forecast Chart] Data fetched:', data);
    
    if (!data || !data.labels) {
      console.warn('[Forecast Chart] No data or labels in response');
      return;
    }
    
    console.log('[Forecast Chart] Historical count:', data.labels.length);
    console.log('[Forecast Chart] Forecast count:', (data.forecast || []).length);
    
    renderChart(data);
  } catch (e) {
    console.error('[Forecast Chart] Error in refreshAndRender:', e);
  }
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

