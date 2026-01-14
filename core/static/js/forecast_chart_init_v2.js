// Forecast Chart Initialization Script (v2)
// This file is a unique copy to ensure correct static collection in deployments.

(function(){
  // The original logic was copied from `core/static/js/forecast_chart_init.js` to avoid
  // collectstatic path collisions when multiple files share the same destination path.
  // All further maintenance should happen in this file while we validate the deploy.

  // --- Begin original script content ---

  function formatChartLabel(dateStr, isHistorical, historicalCount, totalCount) {
    try {
      const date = new Date(dateStr + 'T00:00:00Z');
      const today = new Date();
      today.setUTCHours(0, 0, 0, 0);

      // positive if date is in the future relative to today
      const daysDiff = Math.round((date - today) / (1000 * 60 * 60 * 24));

      if (daysDiff === 0) return 'Today';
      if (daysDiff > 0) return `+${daysDiff}d`;

      // Past dates: short month-day (e.g., Jan 01)
      const formatted = date.toLocaleDateString(undefined, { month: 'short', day: '2-digit' });
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
    
    const lastLabel = existingLabels[existingLabels.length - 1];
    try {
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
    
    const forecastLabels = buildForecastLabels(labels, forecastData.length);
    console.log('[Forecast Chart] Generated forecast labels count:', forecastLabels.length);
    console.log('[Forecast Chart] First few forecast labels:', forecastLabels.slice(0, 5));
    
    const combined = labels.concat(forecastLabels);
    const combinedDates = combined.slice();
    const firstForecastIndex = actualData.length;
    const actualPadded = actualData.concat(Array(forecastData.length).fill(null));
    const forecastPadded = Array(actualData.length).fill(null).concat(forecastData);
    
    console.log('[Forecast Chart] Combined labels count:', combined.length);
    console.log('[Forecast Chart] Actual padded count:', actualPadded.length);
    console.log('[Forecast Chart] Forecast padded count:', forecastPadded.length);
    console.log('[Forecast Chart] actualPadded (first 10):', actualPadded.slice(0, 10));
    console.log('[Forecast Chart] forecastPadded (last 10):', forecastPadded.slice(-10));
    console.log('[Forecast Chart] CRITICAL: Check if actualPadded has data:', actualPadded.some(v => v !== null));
    console.log('[Forecast Chart] CRITICAL: Check if forecastPadded has data:', forecastPadded.some(v => v !== null));
    
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

    function drawRoundedRect(ctx, x, y, width, height, r){
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + width, y, x + width, y + height, r);
      ctx.arcTo(x + width, y + height, x, y + height, r);
      ctx.arcTo(x, y + height, x, y, r);
      ctx.arcTo(x, y, x + width, y, r);
      ctx.closePath();
    }

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

        // Draw small 'TODAY' pill below the chart
        try{
          const labelText = 'TODAY';
          const padding = 8;
          ctx.font = '12px system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial';
          const textWidth = ctx.measureText(labelText).width;
          const rectW = textWidth + padding * 2;
          const rectH = 28;
          const rectX = xPos - rectW/2;
          const rectY = chart.chartArea.bottom + 8;
          ctx.fillStyle = '#ffffff';
          ctx.strokeStyle = 'rgba(226,232,240,0.95)';
          ctx.lineWidth = 1;
          drawRoundedRect(ctx, rectX, rectY, rectW, rectH, 6);
          ctx.fill();
          ctx.stroke();
          ctx.fillStyle = '#6b7280';
          ctx.fillText(labelText, xPos - textWidth/2, rectY + rectH/2 + 5);
        }catch(e){ console.warn('Failed to draw TODAY pill', e); }

        ctx.restore();

        console.log('[Forecast Chart] Separator line drawn at index:', lastHistoricalIndex);
      }
    };

    // Create gradients BEFORE using them in the chart config
    const forecastGradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    forecastGradient.addColorStop(0, 'rgba(255, 140, 66, 0.18)');
    forecastGradient.addColorStop(1, 'rgba(255, 140, 66, 0.02)');

    const histGradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    histGradient.addColorStop(0, 'rgba(17,24,39,0.06)');
    histGradient.addColorStop(1, 'rgba(17,24,39,0.02)');

    // DIAGNOSTIC: Log the actual data arrays before chart creation
    console.log('[Forecast Chart] === PRE-CHART DATA ===');
    console.log('[Forecast Chart] actualPadded length:', actualPadded.length, 'sample:', actualPadded.slice(0, 3), '...', actualPadded.slice(-3));
    console.log('[Forecast Chart] forecastPadded length:', forecastPadded.length, 'sample:', forecastPadded.slice(0, 3), '...', forecastPadded.slice(-3));

    salesChart = new Chart(ctx, {
      type: 'line',
      data: { 
        labels: formattedLabels,
        datasets: [
          {
            label: 'Historical Data',
            data: actualPadded,
            borderColor: '#0f172a',
            backgroundColor: histGradient,
            fill: true,
            tension: 0.32,
            pointRadius: (ctx)=> (ctx.raw === null ? 0 : 4),
            pointBackgroundColor: '#0f172a',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            borderWidth: 3,
            spanGaps: false
          },
          {
            label: 'Forecast Projection',
            data: forecastPadded,
            borderColor: '#FF8C42',
            backgroundColor: forecastGradient,
            fill: true,
            borderDash: [6,3],
            tension: 0.32,
            pointRadius: (ctx)=> {
              if (ctx.raw === null) return 0;
              return ctx.dataIndex === firstForecastIndex ? 8 : 5;
            },
            pointBackgroundColor: '#FF8C42',
            pointBorderColor: '#ffffff',
            pointBorderWidth: (ctx)=> ctx.dataIndex === firstForecastIndex ? 3 : 2,
            borderWidth: 3,
            spanGaps: false
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
                if (!ctx.length) return '';
                const idx = ctx[0].dataIndex;
                const iso = combinedDates[idx];
                try{
                  const d = new Date(iso + 'T00:00:00Z');
                  const opts = { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' };
                  return d.toLocaleDateString(undefined, opts).toUpperCase();
                }catch(e){ return ctx[0].label || ''; }
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
    
    // Enforce visual styles explicitly to avoid old bundles or data issues overriding colors
    try{
      // Ensure historical dataset appears as a dark line with subtle fill
      if(salesChart.data.datasets && salesChart.data.datasets[0]){
        salesChart.data.datasets[0].borderColor = '#0f172a';
        salesChart.data.datasets[0].pointBackgroundColor = '#0f172a';
        salesChart.data.datasets[0].pointBorderColor = '#ffffff';
        salesChart.data.datasets[0].backgroundColor = histGradient;
        salesChart.data.datasets[0].borderWidth = 3;
      }

      // Ensure forecast dataset is orange, dashed, and highlights first forecast point
      if(salesChart.data.datasets && salesChart.data.datasets[1]){
        salesChart.data.datasets[1].borderColor = '#FF8C42';
        salesChart.data.datasets[1].pointBackgroundColor = '#FF8C42';
        salesChart.data.datasets[1].pointBorderColor = '#ffffff';
        salesChart.data.datasets[1].borderDash = [6,3];
        salesChart.data.datasets[1].backgroundColor = forecastGradient;
        salesChart.data.datasets[1].borderWidth = 3;
      }

      salesChart.update();
    }catch(e){ console.warn('[Forecast Chart] Failed to enforce dataset visuals', e); }

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
      
      const rangeSelect = document.getElementById('rangeSelect');
      const range = rangeSelect ? rangeSelect.value : 'Last 30 Days';
      
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
      
      const formatDate = (date) => date.toISOString().slice(0, 10);
      
      url.searchParams.append('start', formatDate(startDate));
      url.searchParams.append('end', formatDate(endDate));
      
      console.log('[Forecast Chart] Fetching from URL:', url.toString());
      
      const res = await fetch(url, { credentials: 'same-origin', cache: 'no-store' });
      if(!res.ok) {
        const txt = await res.text();
        console.warn('[Forecast Chart] API response not ok:', res.status, res.statusText);
        console.warn('[Forecast Chart] Response body (start):', txt.slice(0,800));
        try{ const s = document.getElementById('forecastStatus'); if(s){ s.innerText = 'Forecast API error: ' + res.status; s.style.display = 'block'; } }catch(e){}
        return { series: {labels:[], actual:[], forecast:[], upper:[], lower:[]}, raw: {error:'api_response_not_ok', status: res.status, body: txt.slice(0,800)} };
      }

      let json = null;
      try {
        json = await res.json();
      } catch(parseErr){
        const textBody = await res.text();
        console.warn('[Forecast Chart] Failed to parse API JSON; response text start:', textBody.slice(0,800));
        try{ const s = document.getElementById('forecastStatus'); if(s){ s.innerText = 'Forecast API returned non-JSON response'; s.style.display = 'block'; } }catch(e){}
        return { series: {labels:[], actual:[], forecast:[], upper:[], lower:[]}, raw: {error:'invalid_json', body: textBody.slice(0,800)} };
      }

      try { window._lastForecastPayload = json; } catch(e){}

      console.log('[Forecast Chart] Raw API Response keys:', Object.keys(json));

      // Prefer revenue-prefixed series if present (server provides *_revenue in many cases)
      // First check for daily_revenue, then fall back to daily
      let data = json.daily_revenue || json.daily || json.weekly_revenue || json.weekly || json.monthly_revenue || json.monthly || {labels:[], actual:[], forecast:[], upper:[], lower:[]};
      
      console.log('[Forecast Chart] Selected data type:', data === json.daily_revenue ? 'daily_revenue' : data === json.daily ? 'daily' : 'fallback');
      console.log('[Forecast Chart] Selected data structure:', {labels: (data.labels||[]).length, actual: (data.actual||[]).length, forecast: (data.forecast||[]).length});

      console.log('[Forecast Chart] Selected data keys:', Object.keys(data));
      console.log('[Forecast Chart] Forecast array length in selected data:', (data.forecast || []).length);
      console.log('[Forecast Chart] Using data (sample):', {labelsCount:(data.labels||[]).length, actualCount:(data.actual||[]).length, forecastCount:(data.forecast||[]).length});

      return { series: data, raw: json };
    }catch(e){ 
      console.error('fetchSeries failed:', e); 
      return { series: {labels:[], actual:[], forecast:[], upper:[], lower:[]}, raw: {} }; 
    }
  }

  async function refreshAndRender(){
    console.log('[Forecast Chart] ===== refreshAndRender START =====');
    try {
      const payload = await fetchSeries();
      const data = payload.series;
      const raw = payload.raw || {};

      console.log('[Forecast Chart] Data fetched:', data, 'raw payload:', raw);

      try {
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

      try {
        const statusEl = document.getElementById('forecastStatus');
        const serverDailyFallback = raw && raw.daily && raw.daily.fallback;
        const serverYearlyFallback = raw && raw.yearly && raw.yearly.fallback;
        const clientFallback = data && data.fallback;

        try {
          const debugPre = document.getElementById('forecastDebugJson');
          if (debugPre) {
            debugPre.innerText = JSON.stringify(raw, null, 2);
          }
        } catch (e) { }

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
      console.log('[Forecast Chart] Forecast count from API:', (data.forecast || []).length);
      
      // Initialize finalForecast from API data
      let finalForecast = (data.forecast || []).slice();
      console.log('[Forecast Chart] Initial forecast array:', finalForecast.slice(0, 5), '...');
      
      // Always generate sufficient forecast if needed (minimum 7 days)
      const minimumForecastDays = 7;
      const forecastValidCount = (data.forecast || []).filter(v => v !== null && v !== undefined && Number(v) > 0).length;
      
      if (!data.forecast || data.forecast.length === 0 || data.forecast.length < minimumForecastDays || forecastValidCount === 0) {
        console.warn('[Forecast Chart] Forecast insufficient (' + (data.forecast || []).length + ' days) — generating fallback to ensure minimum ' + minimumForecastDays + ' days');
        const recent = (data.actual || []).filter(v => v !== null && v !== undefined).slice(-14);
        const requiredDays = Math.max(minimumForecastDays, (data.forecast || []).length || minimumForecastDays);
        
        function simpleForecastFromRecent(recentArr, h) {
          if (!recentArr || recentArr.length === 0) return Array(h).fill(0);
          const n = recentArr.length;
          const last = recentArr[n-1] || 0;
          const prev = recentArr[n-2] || last;
          const prev2 = recentArr[n-3] || prev;
          const slope = ((last - prev) + (prev - prev2)) / 2 || 0;
          const base = Math.round(recentArr.reduce((a,b)=>a+b,0)/n);
          const res = [];
          for (let i=1;i<=h;i++){ res.push(Math.max(0, Math.round(base + slope * i))); }
          return res;
        }
        
        finalForecast = simpleForecastFromRecent(recent, requiredDays);
        const statusEl = document.getElementById('forecastStatus'); if (statusEl) statusEl.innerText = 'Forecast (calculated) — estimated from recent trend';
        console.warn('[Forecast Chart] Generated ' + finalForecast.length + '-day fallback forecast:', finalForecast);
      } else {
        console.log('[Forecast Chart] Using API forecast data, count:', finalForecast.length);
      }

      console.log('[Forecast Chart] Final forecast to render:', finalForecast.slice(0, 10));
      
      // Finally render the chart with all components
      const renderData = { 
        labels: data.labels || [], 
        actual: data.actual || [], 
        forecast: finalForecast,
        upper: data.upper || [],
        lower: data.lower || []
      };
      console.log('[Forecast Chart] renderChart input:', {labelsCount: renderData.labels.length, actualCount: renderData.actual.length, forecastCount: renderData.forecast.length});
      renderChart(renderData);

    } catch (e) {
      console.error('[Forecast Chart] refreshAndRender failed', e);
    }
  }

  // Initialize
  window._lastForecastPayload = null;
  window._live = { enabled: false, timerId: null, intervalSec: 60, paused: false };
  
  // Expose refreshAndRender globally so template scripts can call it
  window.refreshForecast = refreshAndRender;
  
  window.addEventListener('load', function(){ setTimeout(refreshAndRender, 500); });

})();

// --- End of v2 file ---
