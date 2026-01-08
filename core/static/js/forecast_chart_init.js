// Forecast Chart Initialization Script
// This script is loaded after the Django template has been rendered

function formatChartLabel(dateStr, isHistorical, historicalCount, totalCount) {
  try {
    const date = new Date(dateStr + 'T00:00:00Z');
    const today = new Date();
    today.setUTCHours(0, 0, 0, 0);
    
    const daysFromToday = Math.round((today - date) / (1000 * 60 * 60 * 24));
    
    // Always show "Today" for today's date
    if (daysFromToday === 0) {
      return 'Today';
    }
    
    // Always show absolute calendar dates (e.g., "Jan 01", "Jan 02", "Nov 05")
    // This applies to both historical and forecast data
    const formatted = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: '2-digit' 
    });
    return formatted;
    
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
    // Parse YYYY-MM-DD string to avoid timezone issues
    const parts = lastLabel.split('-');
    const baseDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
    const forecastDates = [];
    
    for (let i = 1; i <= forecastLen; i++) {
      const forecastDate = new Date(baseDate);
      forecastDate.setDate(baseDate.getDate() + i);
      forecastDates.push(forecastDate.toISOString().slice(0, 10));
    }
    
    console.log('[Forecast Chart] Built forecast labels from base:', lastLabel, 'count:', forecastDates.length);
    return forecastDates;
  } catch (e) {
    console.warn('Error building forecast labels:', e);
    return Array.from({length: forecastLen}, (_, i) => 'F+' + (i+1));
  }
}

let salesChart = null;

function renderChart(data){
  console.log('[Forecast Chart] ===== RENDERchart START =====');
  console.log('[Forecast Chart] Rendering chart with data:', data);
  
  const labels = (data.labels || []).slice();
  const actualData = (data.actual || []).slice();
  const forecastData = (data.forecast || []).slice();
  
  console.log('[Forecast Chart] ===== DATA ARRAYS =====');
  console.log('[Forecast Chart] Historical dates count:', labels.length);
  console.log('[Forecast Chart] Historical actual data count:', actualData.length);
  console.log('[Forecast Chart] Forecast data count:', forecastData.length);
  console.log('[Forecast Chart] Actual data:', actualData);
  console.log('[Forecast Chart] Forecast data:', forecastData);
  console.log('[Forecast Chart] First few forecast values:', forecastData.slice(0, 5));
  
  // Generate forecast labels from the last historical date
  const forecastLabels = buildForecastLabels(labels, forecastData.length);
  console.log('[Forecast Chart] Generated forecast labels count:', forecastLabels.length);
  console.log('[Forecast Chart] First few forecast labels:', forecastLabels.slice(0, 5));
  
  const combined = labels.concat(forecastLabels);
  
  // Pad the actual data with nulls for forecast period
  const actualPadded = actualData.concat(Array(forecastData.length).fill(null));
  
  // Pad the forecast data with nulls for historical period
  const forecastPadded = Array(actualData.length).fill(null).concat(forecastData);
  
  console.log('[Forecast Chart] Combined labels count:', combined.length);
  console.log('[Forecast Chart] Actual padded count:', actualPadded.length);
  console.log('[Forecast Chart] Forecast padded count:', forecastPadded.length);
  
  // Format labels for display
  const formattedLabels = combined.map((dateStr, idx) => {
    const isHistorical = idx < labels.length;
    const formatted = formatChartLabel(dateStr, isHistorical, labels.length, combined.length);
    if (idx < 3 || idx >= combined.length - 3) {
      console.log(`[Forecast Chart] Label[${idx}]: "${dateStr}" -> "${formatted}" (historical: ${isHistorical})`);
    }
    return formatted;
  });

  const ctx = document.getElementById('salesChart')?.getContext('2d');
  if(!ctx) {
    console.warn('[Forecast Chart] Canvas context not found');
    return;
  }
  
  if(salesChart){ 
    try{ 
      salesChart.destroy();
      console.log('[Forecast Chart] Old chart destroyed');
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
      
      if (!xAxis || !yAxis) {
        console.warn('[Forecast Chart] Scales not available');
        return;
      }
      
      // Get position of last historical data point
      const lastHistoricalIndex = labels.length - 1;
      const xPos = xAxis.getPixelForValue(lastHistoricalIndex);
      
      const ctx = chart.ctx;
      ctx.save();
      ctx.strokeStyle = 'rgba(150, 150, 150, 0.5)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(xPos, yAxis.getPixelForValue(yAxis.max));
      ctx.lineTo(xPos, yAxis.getPixelForValue(yAxis.min));
      ctx.stroke();
      ctx.restore();
      
      console.log('[Forecast Chart] Separator line drawn at index:', lastHistoricalIndex);
    }
  };
  
  salesChart = new Chart(ctx, {
    type: 'line',
    data: { 
      labels: formattedLabels, 
      datasets: [
        { 
          label: 'Historical Daily Sales', 
          data: actualPadded, 
          borderColor: '#FF8C42',
          backgroundColor: 'rgba(255, 140, 66, 0.12)', 
          fill: true, 
          tension: 0.4, 
          pointRadius: 6, 
          pointBackgroundColor: '#FF8C42',
          pointBorderColor: '#FFFFFF',
          pointBorderWidth: 2,
          borderWidth: 3,
          spanGaps: false
        },
        { 
          label: 'AI-Driven Forecast', 
          data: forecastPadded, 
          borderColor: '#FF8C42',
          backgroundColor: 'rgba(255, 140, 66, 0.04)', 
          fill: false, 
          borderDash: [7, 5], 
          tension: 0.4, 
          pointRadius: 6, 
          pointBackgroundColor: '#FF8C42',
          pointBorderColor: '#FFFFFF',
          pointBorderWidth: 2,
          borderWidth: 3,
          spanGaps: false,
          hidden: false
        }
      ] 
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { 
        legend: { 
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              size: 14,
              weight: '600'
            },
            color: '#374151',
            boxPadding: 8
          },
          onClick: null
        },
        separatorLine: true,
        tooltip: { 
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(31, 41, 55, 0.95)',
          padding: 12,
          titleFont: { size: 13, weight: 'bold' },
          bodyFont: { size: 13 },
          borderRadius: 8,
          displayColors: true,
          callbacks: { 
            title: function(ctx) {
              if (ctx.length > 0) {
                return ctx[0].label;
              }
              return '';
            },
            label: function(ctx){ 
              if (ctx.raw === null) {
                return ctx.dataset.label + ': —';
              }
              const value = Number(ctx.raw).toLocaleString('en-PH', {
                style: 'currency',
                currency: 'PHP',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
              });
              // If this is the forecast dataset, show 'Projected' for clarity
              if (/forecast|project/i.test(ctx.dataset.label)) {
                return 'Projected: ' + value;
              }
              return ctx.dataset.label + ': ' + value; 
            } 
          } 
        } 
      },
      scales: { 
        y: { 
          beginAtZero: true,
          ticks: { 
            callback: function(v){ 
              return '₱' + Number(v).toLocaleString('en-PH', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
              });
            },
            font: {
              size: 12
            },
            color: '#9CA3AF',
            padding: 8
          },
          grid: {
            color: 'rgba(229, 231, 235, 0.5)',
            drawBorder: false
          }
        },
        x: {
          ticks: {
            font: {
              size: 12
            },
            color: '#9CA3AF',
            padding: 8
          },
          grid: {
            display: false,
            drawBorder: false
          }
        }
      }
    },
    plugins: [separatorPlugin]
  });
  
  console.log('[Forecast Chart] ===== CHART CREATED =====');
  console.log('[Forecast Chart] Chart instance created:', !!salesChart);
  console.log('[Forecast Chart] Chart datasets count:', salesChart.data.datasets.length);
  console.log('[Forecast Chart] Dataset 0 (Historical) data count:', salesChart.data.datasets[0].data.length);
  console.log('[Forecast Chart] Dataset 0 (Historical) data:', salesChart.data.datasets[0].data.slice(0, 5));
  console.log('[Forecast Chart] Dataset 1 (Forecast) data count:', salesChart.data.datasets[1].data.length);
  console.log('[Forecast Chart] Dataset 1 (Forecast) data:', salesChart.data.datasets[1].data.slice(0, 5));
  console.log('[Forecast Chart] Dataset 1 hidden?', salesChart.data.datasets[1].hidden);
  console.log('[Forecast Chart] Dataset 1 borderColor:', salesChart.data.datasets[1].borderColor);
  console.log('[Forecast Chart] Forecast points count:', forecastPadded.filter(v => v !== null).length);
  console.log('[Forecast Chart] ===== renderChart COMPLETE =====');
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
    
    const res = await fetch(url, { credentials: 'same-origin', cache: 'no-store' });
    if(!res.ok) throw new Error('Network response not ok: ' + res.status);
    const json = await res.json();
    // expose last raw payload for diagnostics
    try { window._lastForecastPayload = json; } catch(e){}
    
    console.log('[Forecast Chart] Raw API Response keys:', Object.keys(json));
    console.log('[Forecast Chart] Daily data present:', !!json.daily);
    if (json.daily) {
      console.log('[Forecast Chart] Daily.forecast length:', (json.daily.forecast || []).length);
      console.log('[Forecast Chart] Daily.actual length:', (json.daily.actual || []).length);
      console.log('[Forecast Chart] Daily.labels length:', (json.daily.labels || []).length);
    }
    
    // Prefer daily data for all ranges
    const data = json.daily || json.weekly || json.monthly || {labels:[], actual:[], forecast:[], upper:[], lower:[]};
    
    console.log('[Forecast Chart] Selected data keys:', Object.keys(data));
    console.log('[Forecast Chart] Forecast array length in selected data:', (data.forecast || []).length);
    console.log('[Forecast Chart] Using data:', data);
    
    return { series: data, raw: json };
  }catch(e){ 
    console.error('fetchSeries failed:', e); 
    return { series: {labels:[], actual:[], forecast:[], upper:[], lower:[]}, raw: {} }; 
  }
}
}

async function refreshAndRender(){
  console.log('[Forecast Chart] ===== refreshAndRender START =====');
  try {
    const payload = await fetchSeries();
    const data = payload.series;
    const raw = payload.raw || {};

    console.log('[Forecast Chart] Data fetched:', data, 'raw payload:', raw);
    
    // Update hero cards (tomorrow / next week / next month / next year) when API provides forecasts
    try {
      // Daily / Tomorrow - use raw.daily when available otherwise use returned series
      const daily = raw.daily || data;
      if (daily && daily.forecast && daily.forecast.length) {
        const v = daily.forecast[0] || 0;
        document.getElementById('hero-tomorrow-amount')?.innerText = '₱' + Number(v).toLocaleString('en-PH', {minimumFractionDigits:0});
        const upper = (daily.upper || [])[0];
        const lower = (daily.lower || [])[0];
        if (upper !== undefined && lower !== undefined) {
          const margin = Math.max(0, Math.round((upper - lower) / 2));
          document.getElementById('hero-tomorrow-margin')?.innerText = '±' + Number(margin).toLocaleString('en-PH', {minimumFractionDigits:0});
        }
        document.getElementById('hero-tomorrow-conf-pct')?.innerText = '▲ ' + (daily.confidence || 0) + '%';
      }

      // Weekly
      const weekly = raw.weekly || window._serverWeekly || null;
      if (weekly && weekly.forecast && weekly.forecast.length) {
        const v = weekly.forecast[0] || 0;
        document.getElementById('hero-week-amount')?.innerText = '₱' + Number(v).toLocaleString('en-PH', {minimumFractionDigits:0});
        const u = (weekly.upper || [])[0];
        const l = (weekly.lower || [])[0];
        if (u !== undefined && l !== undefined) {
          const margin = Math.max(0, Math.round((u - l) / 2));
          document.getElementById('hero-week-margin')?.innerText = '±' + Number(margin).toLocaleString('en-PH', {minimumFractionDigits:0});
        }
        document.getElementById('hero-week-conf-pct')?.innerText = '▲ ' + (weekly.confidence || 0) + '%';
      }

      // Monthly
      const monthly = raw.monthly || window._serverMonthly || null;
      if (monthly && monthly.forecast && monthly.forecast.length) {
        const v = monthly.forecast[0] || 0;
        document.getElementById('hero-month-amount')?.innerText = '₱' + Number(v).toLocaleString('en-PH', {minimumFractionDigits:0});
        const u = (monthly.upper || [])[0];
        const l = (monthly.lower || [])[0];
        if (u !== undefined && l !== undefined) {
          const margin = Math.max(0, Math.round((u - l) / 2));
          document.getElementById('hero-month-margin')?.innerText = '±' + Number(margin).toLocaleString('en-PH', {minimumFractionDigits:0});
        }
        document.getElementById('hero-month-conf-pct')?.innerText = '▲ ' + (monthly.confidence || 0) + '%';
      }

      // Yearly (sum of 12 monthly forecast steps if present in API)
      const yearly = raw.yearly || window._serverYearly || null;
      if (yearly && (yearly.forecast || []).length) {
        const total = (yearly.forecast || []).reduce((a,b)=>a+(b||0),0);
        document.getElementById('hero-year-amount')?.innerText = '₱' + Number(total).toLocaleString('en-PH', {minimumFractionDigits:0});
        const ups = yearly.upper || [];
        const lows = yearly.lower || [];
        let margin = 0;
        for (let i=0;i<Math.min(ups.length,lows.length);i++){ margin += Math.max(0, (ups[i]-lows[i])/2); }
        document.getElementById('hero-year-margin')?.innerText = '±' + Number(Math.round(margin)).toLocaleString('en-PH', {minimumFractionDigits:0});
        document.getElementById('hero-year-conf-pct')?.innerText = '▲ ' + (yearly.confidence || 0) + '%';
      }
    } catch (e) {
      console.warn('[Forecast Chart] Updating hero cards failed', e);
    }

    // Show fallback status if the server indicated a fallback or if the client generated one
    try {
      const statusEl = document.getElementById('forecastStatus');
      const serverDailyFallback = raw && raw.daily && raw.daily.fallback;
      const serverYearlyFallback = raw && raw.yearly && raw.yearly.fallback;
      const clientFallback = data && data.fallback;

      // Populate debug panel JSON area if open
      try {
        const debugPre = document.getElementById('forecastDebugJson');
        if (debugPre) {
          debugPre.innerText = JSON.stringify(raw, null, 2);
        }
      } catch (e) { /* ignore */ }

      if (statusEl) {
        if (serverDailyFallback || serverYearlyFallback) {
          statusEl.innerText = 'Forecast (server fallback) — estimated from recent history';
          statusEl.style.display = 'block';
        } else if (clientFallback) {
          statusEl.innerText = 'Forecast (client fallback) — estimated from recent history';
          statusEl.style.display = 'block';
        } else {
          statusEl.style.display = 'none';
        }
      }

      // also populate a small visible banner if API returned empty forecast arrays
      try {
        if (raw && raw.daily && Array.isArray(raw.daily.forecast) && raw.daily.forecast.length === 0) {
          const statusEl2 = document.getElementById('forecastStatus'); if (statusEl2) { statusEl2.innerText = 'Forecast returned empty from server — using fallback'; statusEl2.style.display = 'block'; }
        }
      } catch (e) {}

    } catch (e) {
      /* ignore status display errors */
    }

    if (!data || !data.labels) {
      console.warn('[Forecast Chart] No data or labels in response');
      return;
    }
    
    console.log('[Forecast Chart] Historical count:', data.labels.length);
    console.log('[Forecast Chart] Forecast count:', (data.forecast || []).length);
    
    // If the API returned an empty forecast array or only zeros, create a reasonable client-side fallback
    const forecastValidCount = (data.forecast || []).filter(v => v !== null && v !== undefined && Number(v) > 0).length;
    if (!data.forecast || data.forecast.length === 0 || forecastValidCount === 0) {
      console.warn('[Forecast Chart] Forecast missing or empty — generating fallback based on recent trend');
      const recent = (data.actual || []).filter(v => v !== null && v !== undefined).slice(-14);
      const range = document.getElementById('rangeSelect')?.value || 'Last 30 Days';
      const fallbackHorizon = range === 'Last 7 Days' ? 5 : (range === 'Last 90 Days' ? 14 : 7);
      function simpleForecastFromRecent(recentArr, h) {
        if (!recentArr || recentArr.length === 0) return Array(h).fill(0);
        const n = recentArr.length;
        const last = recentArr[n-1] || 0;
        const prev = recentArr[n-2] || last;
        const prev2 = recentArr[n-3] || prev;
        // Use simple slope on last 3 points and mean baseline
        const slope = ((last - prev) + (prev - prev2)) / 2 || 0;
        const base = Math.round(recentArr.reduce((a,b)=>a+b,0)/n);
        const res = [];
        for (let i=1;i<=h;i++){ res.push(Math.max(0, Math.round(base + slope * i))); }
        return res;
      }
      data.forecast = simpleForecastFromRecent(recent, fallbackHorizon);
      console.warn('[Forecast Chart] Fallback forecast generated:', data.forecast);
      const statusEl = document.getElementById('forecastStatus'); if(statusEl) statusEl.innerText = 'Forecast (fallback) — based on recent trend';
    } else {
      console.log('[Forecast Chart] ✓ Forecast data present, count:', data.forecast.length);
    }
    
    console.log('[Forecast Chart] About to call renderChart...');
    renderChart(data);
    console.log('[Forecast Chart] ===== refreshAndRender COMPLETE =====');
  } catch (e) {
    console.error('[Forecast Chart] ⚠️ CRITICAL ERROR in refreshAndRender:', e);
    console.error('[Forecast Chart] Error stack:', e.stack);
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

    // Diag toggle wiring
    const btnDiag = document.getElementById('btnDiag');
    if (btnDiag) {
      btnDiag.addEventListener('click', function(){
        const panel = document.getElementById('forecast-debug-panel');
        if (panel) panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
      });
    }
    const closeBtn = document.getElementById('closeDebug');
    if (closeBtn) closeBtn.addEventListener('click', function(){ document.getElementById('forecast-debug-panel').style.display = 'none'; });
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

