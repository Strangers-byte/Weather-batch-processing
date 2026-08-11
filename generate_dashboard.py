"""
Weather Insights Dashboard Generator
Connects to DuckDB gold tables and generates a self-contained HTML dashboard.
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime, date
from string import Template

DB_PATH = "weather_dbt/dev.duckdb"
OUTPUT_PATH = "weather_dashboard.html"


def fetch_data(con: duckdb.DuckDBPyConnection):
    """Query gold tables from DuckDB."""

    daily = con.execute("""
        SELECT
            city_id,
            date_day,
            min_temp_c,
            max_temp_c,
            avg_temp_c,
            avg_humidity_pct,
            max_wind_speed_kmh,
            min_european_aqi,
            max_european_aqi,
            avg_european_aqi,
            hour_count,
            aq_hour_count
        FROM main_gold.fct_weather_daily
        ORDER BY city_id, date_day
    """).fetchall()

    daily_cols = ['city_id', 'date_day', 'min_temp_c', 'max_temp_c', 'avg_temp_c',
                  'avg_humidity_pct', 'max_wind_speed_kmh', 'min_european_aqi',
                  'max_european_aqi', 'avg_european_aqi', 'hour_count', 'aq_hour_count']
    daily_data = [dict(zip(daily_cols, row)) for row in daily]

    weekly = con.execute("""
        SELECT
            city_id,
            week_start,
            weekly_min_temp_c,
            weekly_max_temp_c,
            weekly_avg_temp_c,
            weekly_max_wind_speed_kmh,
            weekly_max_european_aqi,
            hour_count,
            aq_hour_count,
            rank_by_avg_temp
        FROM main_gold.fct_weather_weekly
        ORDER BY rank_by_avg_temp
    """).fetchall()

    weekly_cols = ['city_id', 'week_start', 'weekly_min_temp_c', 'weekly_max_temp_c',
                   'weekly_avg_temp_c', 'weekly_max_wind_speed_kmh',
                   'weekly_max_european_aqi', 'hour_count', 'aq_hour_count',
                   'rank_by_avg_temp']
    weekly_data = [dict(zip(weekly_cols, row)) for row in weekly]

    cities = con.execute("""
        SELECT city_id, city_name, country, latitude, longitude
        FROM main_gold.dim_city
    """).fetchall()

    city_cols = ['city_id', 'city_name', 'country', 'latitude', 'longitude']
    city_data = [dict(zip(city_cols, row)) for row in cities]

    return daily_data, weekly_data, city_data


def json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Weather Insights Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8;
    --accent: #38bdf8; --hot: #f87171; --cold: #60a5fa; --rain: #34d399;
    --aqi-good: #34d399; --aqi-moderate: #fbbf24; --aqi-bad: #f87171; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; }
  header { text-align: center; margin-bottom: 2rem; }
  header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--accent), var(--rain));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  header p { color: var(--muted); margin-top: 0.5rem; font-size: 0.95rem; }
  .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    background: rgba(56,189,248,0.1); color: var(--accent); border: 1px solid rgba(56,189,248,0.2); margin-top: 0.75rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; max-width: 1400px; margin: 0 auto; }
  .card { background: var(--card); border-radius: 1rem; padding: 1.5rem;
    border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
  .card h2 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--muted); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
  .metric { display: flex; flex-direction: column; gap: 0.25rem; }
  .metric-value { font-size: 2.5rem; font-weight: 700; line-height: 1; }
  .metric-label { color: var(--muted); font-size: 0.875rem; }
  .chart-container { position: relative; height: 300px; }
  .chart-container-lg { position: relative; height: 400px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  th { text-align: left; padding: 0.75rem; color: var(--muted); font-weight: 600;
    text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em;
    border-bottom: 1px solid rgba(255,255,255,0.1); }
  td { padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.03); }
  tr:hover td { background: rgba(255,255,255,0.02); }
  .rank { font-weight: 700; font-size: 0.875rem; }
  .rank-1 { color: #fbbf24; } .rank-2 { color: #94a3b8; } .rank-3 { color: #b45309; }
  .wide { grid-column: 1 / -1; }
  @media (min-width: 768px) { .wide { grid-column: span 2; } }
  .footer { text-align: center; color: var(--muted); font-size: 0.75rem; margin-top: 2rem; }
  .aqi-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
  .aqi-good { background: rgba(52,211,153,0.15); color: #34d399; }
  .aqi-moderate { background: rgba(251,191,36,0.15); color: #fbbf24; }
  .aqi-bad { background: rgba(248,113,113,0.15); color: #f87171; }
  .aqi-missing { background: rgba(148,163,184,0.15); color: #94a3b8; }
</style>
</head>
<body>

<header>
  <h1>Weather Insights Dashboard</h1>
  <p>10 German Cities · <span id="date-range">--</span> · Open-Meteo API</p>
  <span class="badge">Bronze → Silver → Gold · dbt · DuckDB</span>
</header>

<div class="grid">
  <div class="card">
    <h2>🏆 Hottest City</h2>
    <div class="metric">
      <span class="metric-value" style="color:var(--hot)" id="hottest-city">--</span>
      <span class="metric-label" id="hottest-temp">-- °C avg</span>
    </div>
  </div>
  <div class="card">
    <h2>💨 Windiest</h2>
    <div class="metric">
      <span class="metric-value" style="color:var(--accent)" id="windiest-city">--</span>
      <span class="metric-label" id="windiest-speed">-- km/h max</span>
    </div>
  </div>
  <div class="card">
    <h2>🏭 Worst Air Quality</h2>
    <div class="metric">
      <span class="metric-value" style="color:var(--aqi-bad)" id="worst-aqi-city">--</span>
      <span class="metric-label" id="worst-aqi-val">-- AQI max</span>
    </div>
  </div>
  <div class="card wide">
    <h2>📈 Daily Average Temperature by City</h2>
    <div class="chart-container-lg"><canvas id="dailyTempChart"></canvas></div>
  </div>
  <div class="card wide">
    <h2>💧 Daily Average Humidity by City</h2>
    <div class="chart-container-lg"><canvas id="dailyHumidityChart"></canvas></div>
  </div>
  <div class="card wide">
    <h2>🏭 Daily Max European AQI by City</h2>
    <div class="chart-container-lg"><canvas id="dailyAqiChart"></canvas></div>
  </div>
  <div class="card wide">
    <h2>🏅 Weekly Temperature Rankings</h2>
    <div class="chart-container"><canvas id="rankingChart"></canvas></div>
  </div>
  <div class="card wide">
    <h2>🏭 Weekly Max Air Quality Index</h2>
    <div class="chart-container"><canvas id="aqiChart"></canvas></div>
  </div>
  <div class="card wide">
    <h2>📋 Weekly Summary Table</h2>
    <table id="summaryTable">
      <thead><tr>
        <th>Rank</th><th>City</th><th>Avg Temp (°C)</th><th>Min / Max (°C)</th>
        <th>Max Wind (km/h)</th><th>Max AQI</th><th>Data Quality</th>
      </tr></thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>
</div>

<div class="footer">Generated on $generated_at · Pipeline: Python → DuckDB → dbt → HTML</div>

<script>
const dailyData = $daily_json;
const weeklyData = $weekly_json;
const cities = $cities_json;

function titleCase(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function getCityName(id) {
  const c = cities.find(x => x.city_id === id);
  return c ? c.city_name : titleCase(id);
}

function aqiClass(val) {
  if (val === null || val === undefined) return 'aqi-missing';
  if (val <= 50) return 'aqi-good';
  if (val <= 100) return 'aqi-moderate';
  return 'aqi-bad';
}

function aqiLabel(val) {
  if (val === null || val === undefined) return 'N/A';
  if (val <= 50) return 'Good';
  if (val <= 100) return 'Moderate';
  if (val <= 150) return 'Unhealthy (Sensitive)';
  return 'Unhealthy';
}

const hottest = weeklyData.reduce((a, b) => a.weekly_avg_temp_c > b.weekly_avg_temp_c ? a : b);
const windiest = weeklyData.reduce((a, b) => a.weekly_max_wind_speed_kmh > b.weekly_max_wind_speed_kmh ? a : b);
const worstAqi = weeklyData
  .filter(d => d.weekly_max_european_aqi !== null && d.weekly_max_european_aqi !== undefined)
  .reduce((a, b) => a.weekly_max_european_aqi > b.weekly_max_european_aqi ? a : b, weeklyData[0]);

document.getElementById('hottest-city').textContent = getCityName(hottest.city_id);
document.getElementById('hottest-temp').textContent = hottest.weekly_avg_temp_c.toFixed(1) + ' °C avg';
document.getElementById('windiest-city').textContent = getCityName(windiest.city_id);
document.getElementById('windiest-speed').textContent = windiest.weekly_max_wind_speed_kmh.toFixed(1) + ' km/h max';
if (worstAqi && worstAqi.weekly_max_european_aqi != null) {
  document.getElementById('worst-aqi-city').textContent = getCityName(worstAqi.city_id);
  document.getElementById('worst-aqi-val').textContent = worstAqi.weekly_max_european_aqi + ' AQI max (' + aqiLabel(worstAqi.weekly_max_european_aqi) + ')';
} else {
  document.getElementById('worst-aqi-city').textContent = 'N/A';
  document.getElementById('worst-aqi-val').textContent = 'No AQ data';
}

const dates = [...new Set(dailyData.map(d => d.date_day))].sort();
if (dates.length > 0) {
  const fmt = d => new Date(d).toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' });
  document.getElementById('date-range').textContent =
    dates.length === 1 ? fmt(dates[0]) : '$${fmt(dates[0])} – $${fmt(dates[dates.length - 1])}';
}

const cityColors = {
  'berlin': '#38bdf8', 'hamburg': '#818cf8', 'munich': '#f472b6',
  'cologne': '#34d399', 'frankfurt': '#fbbf24', 'stuttgart': '#f87171',
  'duesseldorf': '#a78bfa', 'dortmund': '#2dd4bf', 'essen': '#fb923c', 'leipzig': '#e879f9'
};

new Chart(document.getElementById('dailyTempChart'), {
  type: 'line',
  data: {
    labels: dates.map(d => new Date(d).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })),
    datasets: cities.map(city => ({
      label: city.city_name,
      data: dates.map(date => {
        const row = dailyData.find(d => d.city_id === city.city_id && d.date_day === date);
        return row ? row.avg_temp_c : null;
      }),
      borderColor: cityColors[city.city_id] || '#94a3b8',
      backgroundColor: cityColors[city.city_id] || '#94a3b8',
      tension: 0.3, pointRadius: 3, borderWidth: 2
    }))
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { position: 'top', labels: { color: '#94a3b8', usePointStyle: true } },
      tooltip: { backgroundColor: '#1e293b', titleColor: '#e2e8f0', bodyColor: '#e2e8f0', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 }
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, title: { display: true, text: '°C', color: '#64748b' } }
    }
  }
});

new Chart(document.getElementById('dailyHumidityChart'), {
  type: 'line',
  data: {
    labels: dates.map(d => new Date(d).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })),
    datasets: cities.map(city => ({
      label: city.city_name,
      data: dates.map(date => {
        const row = dailyData.find(d => d.city_id === city.city_id && d.date_day === date);
        return row ? row.avg_humidity_pct : null;
      }),
      borderColor: cityColors[city.city_id] || '#94a3b8',
      backgroundColor: cityColors[city.city_id] || '#94a3b8',
      tension: 0.3, pointRadius: 3, borderWidth: 2
    }))
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { position: 'top', labels: { color: '#94a3b8', usePointStyle: true } },
      tooltip: { backgroundColor: '#1e293b', titleColor: '#e2e8f0', bodyColor: '#e2e8f0', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 }
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, title: { display: true, text: '%', color: '#64748b' }, min: 0, max: 100 }
    }
  }
});

new Chart(document.getElementById('dailyAqiChart'), {
  type: 'line',
  data: {
    labels: dates.map(d => new Date(d).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })),
    datasets: cities.map(city => ({
      label: city.city_name,
      data: dates.map(date => {
        const row = dailyData.find(d => d.city_id === city.city_id && d.date_day === date);
        return row && row.max_european_aqi != null ? row.max_european_aqi : null;
      }),
      borderColor: cityColors[city.city_id] || '#94a3b8',
      backgroundColor: cityColors[city.city_id] || '#94a3b8',
      tension: 0.3, pointRadius: 3, borderWidth: 2
    }))
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { position: 'top', labels: { color: '#94a3b8', usePointStyle: true } },
      tooltip: { backgroundColor: '#1e293b', titleColor: '#e2e8f0', bodyColor: '#e2e8f0', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 }
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, title: { display: true, text: 'AQI', color: '#64748b' } }
    }
  }
});

weeklyData.sort((a, b) => a.rank_by_avg_temp - b.rank_by_avg_temp);
new Chart(document.getElementById('rankingChart'), {
  type: 'bar',
  data: {
    labels: weeklyData.map(d => getCityName(d.city_id)),
    datasets: [{
      label: 'Avg Temp (°C)',
      data: weeklyData.map(d => d.weekly_avg_temp_c),
      backgroundColor: weeklyData.map(d => d.rank_by_avg_temp === 1 ? '#fbbf24' : '#38bdf8'),
      borderRadius: 6
    }]
  },
  options: {
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 } },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y: { grid: { display: false }, ticks: { color: '#e2e8f0' } }
    }
  }
});

weeklyData.sort((a, b) => (b.weekly_max_european_aqi || 0) - (a.weekly_max_european_aqi || 0));
new Chart(document.getElementById('aqiChart'), {
  type: 'bar',
  data: {
    labels: weeklyData.map(d => getCityName(d.city_id)),
    datasets: [{
      label: 'Max European AQI',
      data: weeklyData.map(d => d.weekly_max_european_aqi != null ? d.weekly_max_european_aqi : 0),
      backgroundColor: weeklyData.map(d => {
        const v = d.weekly_max_european_aqi;
        if (v == null) return '#64748b';
        if (v <= 50) return '#34d399';
        if (v <= 100) return '#fbbf24';
        return '#f87171';
      }),
      borderRadius: 6
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 } },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#e2e8f0' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, title: { display: true, text: 'AQI', color: '#64748b' } }
    }
  }
});

weeklyData.sort((a, b) => a.rank_by_avg_temp - b.rank_by_avg_temp);
const tbody = document.getElementById('tableBody');
weeklyData.forEach(row => {
  const tr = document.createElement('tr');
  const rankClass = row.rank_by_avg_temp <= 3 ? 'rank-' + row.rank_by_avg_temp : '';
  const aqiVal = row.weekly_max_european_aqi;
  const aqiHtml = aqiVal != null
    ? '<span class="aqi-badge ' + aqiClass(aqiVal) + '">' + aqiVal + ' — ' + aqiLabel(aqiVal) + '</span>'
    : '<span class="aqi-badge aqi-missing">N/A</span>';
  tr.innerHTML = '<td><span class="rank ' + rankClass + '">#' + row.rank_by_avg_temp + '</span></td>' +
    '<td><strong>' + getCityName(row.city_id) + '</strong></td>' +
    '<td>' + row.weekly_avg_temp_c.toFixed(1) + ' °C</td>' +
    '<td>' + row.weekly_min_temp_c.toFixed(1) + ' / ' + row.weekly_max_temp_c.toFixed(1) + '</td>' +
    '<td>' + row.weekly_max_wind_speed_kmh.toFixed(1) + '</td>' +
    '<td>' + aqiHtml + '</td>' +
    '<td>' + (row.hour_count === 168 ? '✅ 168 hrs' : '⚠️ ' + row.hour_count + ' hrs') + '</td>';
  tbody.appendChild(tr);
});
</script>
</body>
</html>"""


def main():
    if not Path(DB_PATH).exists():
        print(f"Error: DuckDB not found at {DB_PATH}")
        print("Run: python fetch_weather.py && dbt build")
        return

    con = duckdb.connect(DB_PATH)
    try:
        daily, weekly, cities = fetch_data(con)

        tmpl = Template(HTML_TEMPLATE)
        html = tmpl.substitute(
            daily_json=json.dumps(daily, default=json_default),
            weekly_json=json.dumps(weekly, default=json_default),
            cities_json=json.dumps(cities, default=json_default),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Dashboard generated: {OUTPUT_PATH}")
        print(f"   Cities: {len(cities)}")
        print(f"   Daily rows: {len(daily)}")
        print(f"   Weekly rows: {len(weekly)}")
        print(f"   Open {OUTPUT_PATH} in your browser")
    finally:
        con.close()


if __name__ == "__main__":
    main()