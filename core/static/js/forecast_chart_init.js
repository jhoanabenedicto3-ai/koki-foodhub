// Forecast Chart Initialization Script
// This script is loaded after the Django template has been rendered

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

function renderChart(data){
  const labels = (data.labels || []).slice();
  const forecastLabels = buildForecastLabels(labels, (data.forecast || []).length);
  const combined = labels.concat(forecastLabels);
  const actualPadded = (data.actual || []).concat(Array((data.forecast||[]).length).fill(null));
  const forecastPadded = Array((data.actual||[]).length).fill(null).concat(data.forecast || []);
  
  // Detect period for label formatting
  let period = 'daily';
  if (labels.length >= 2) {
    try {
      const last = new Date(labels[labels.length - 1]);
      const secondLast = new Date(labels[labels.length - 2]);
      const dayDiff = Math.round((last - secondLast) / (1000 * 60 * 60 * 24));
      if (dayDiff >= 28) {
        period = 'monthly';
      } else if (dayDiff >= 6) {
        period = 'weekly';
      }
    } catch (e) {}
  }
  
  // Format labels for display
  const formattedLabels = combined.map((dateStr, idx) => {
    const isHistorical = idx < labels.length;
    return formatChartLabel(dateStr, isHistorical, combined.length, labels.length, period);
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
document.addEventListener('DOMContentLoaded', function(){
  refreshAndRender();
  
  // Wire up event listeners
  const refreshBtn = document.getElementById('refreshForecastBtn');
  const rangeSelect = document.getElementById('rangeSelect');
  
  if(refreshBtn) {
    refreshBtn.addEventListener('click', refreshAndRender);
  }
  
  if(rangeSelect) {
    rangeSelect.addEventListener('change', refreshAndRender);
  }
  
  // Expose for other scripts
  window.refreshForecast = refreshAndRender;
});
