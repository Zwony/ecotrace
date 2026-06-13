"""EcoTrace live dashboard (v1.3.0) — stdlib-only local HTTP server.

Serves a real-time, auto-refreshing browser dashboard that reads from
``ecotrace_log.csv``. Zero external dependencies — uses only Python's
built-in ``http.server``, ``json``, and ``csv`` modules.

Usage (CLI)::

    ecotrace dashboard [--port 8585] [--file ecotrace_log.csv]

Usage (programmatic)::

    from ecotrace.dashboard import DashboardServer
    srv = DashboardServer(csv_path="ecotrace_log.csv", port=8585)
    srv.serve_forever()   # blocks; Ctrl-C to stop
"""

import csv
import json
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# Static HTML/CSS/JS — embedded as a module-level string so the package
# ships as a single pure-Python file with no asset directories.
# ---------------------------------------------------------------------------
_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EcoTrace — Live Dashboard</title>
<style>
  :root {
    --bg:        #0d1117;
    --surface:   #161b22;
    --border:    #30363d;
    --green:     #2ea043;
    --green-dim: #238636;
    --green-hi:  #56d364;
    --text:      #e6edf3;
    --muted:     #8b949e;
    --warn:      #d29922;
    --danger:    #da3633;
    --radius:    10px;
    --font:      'Inter', system-ui, sans-serif;
  }
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; background: var(--bg); color: var(--text);
                font-family: var(--font); font-size: 14px; }

  /* ── Layout ── */
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 24px; border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  header h1 { font-size: 18px; font-weight: 700; letter-spacing: .5px; }
  header h1 span { color: var(--green-hi); }
  #status { font-size: 12px; color: var(--muted); }
  #status .dot { display: inline-block; width: 8px; height: 8px;
                 border-radius: 50%; background: var(--green); margin-right: 5px;
                 animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  main { padding: 24px; display: grid;
         grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
         gap: 16px; }

  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius); padding: 20px; }
  .card-title { font-size: 11px; font-weight: 600; letter-spacing: .8px;
                text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
  .card-value { font-size: 28px; font-weight: 700; color: var(--green-hi); }
  .card-sub   { font-size: 12px; color: var(--muted); margin-top: 4px; }

  .wide { grid-column: 1 / -1; }

  /* ── Charts ── */
  canvas { width: 100% !important; max-height: 220px; }

  /* ── Table ── */
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { padding: 8px 10px; background: rgba(46,160,67,.15);
       color: var(--green-hi); text-align: left; font-weight: 600;
       border-bottom: 1px solid var(--border); }
  td { padding: 7px 10px; border-bottom: 1px solid var(--border); color: var(--text); }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,.03); }

  /* ── Run selector ── */
  #run-filter { background: var(--surface); border: 1px solid var(--border);
                color: var(--text); border-radius: 6px; padding: 5px 10px;
                font-size: 12px; margin-left: 12px; }

  /* ── Budget gauge ── */
  .gauge-wrap { display: flex; align-items: center; gap: 12px; }
  .gauge-bar { flex: 1; height: 8px; background: var(--border);
               border-radius: 4px; overflow: hidden; }
  .gauge-fill { height: 100%; border-radius: 4px;
                transition: width .4s ease, background .4s; }
  .gauge-label { font-size: 12px; color: var(--muted); min-width: 40px; text-align: right; }

  footer { text-align: center; padding: 16px; color: var(--muted); font-size: 11px;
           border-top: 1px solid var(--border); }
</style>
</head>
<body>
<header>
  <h1>Eco<span>Trace</span> — Live Dashboard</h1>
  <div style="display:flex;align-items:center">
    <select id="run-filter" onchange="filterRun(this.value)">
      <option value="">All Runs</option>
    </select>
    <div id="status" style="margin-left:16px">
      <span class="dot"></span>Auto-refreshing
    </div>
  </div>
</header>

<main id="main">
  <!-- Hero cards -->
  <div class="card">
    <div class="card-title">Total Carbon</div>
    <div class="card-value" id="total-carbon">—</div>
    <div class="card-sub" id="equiv">—</div>
  </div>
  <div class="card">
    <div class="card-title">Measurements</div>
    <div class="card-value" id="meas-count">—</div>
    <div class="card-sub" id="runs-count">—</div>
  </div>
  <div class="card">
    <div class="card-title">Total Duration</div>
    <div class="card-value" id="total-dur">—</div>
    <div class="card-sub">seconds tracked</div>
  </div>
  <div class="card">
    <div class="card-title">Top Emitter</div>
    <div class="card-value" style="font-size:15px;word-break:break-all" id="top-func">—</div>
    <div class="card-sub" id="top-carbon">—</div>
  </div>

  <!-- Timeline -->
  <div class="card wide">
    <div class="card-title">Carbon Timeline</div>
    <canvas id="timeline-chart"></canvas>
  </div>

  <!-- Per-function bar chart -->
  <div class="card wide">
    <div class="card-title">Emissions by Function (top 10)</div>
    <canvas id="func-chart"></canvas>
  </div>

  <!-- Run history table -->
  <div class="card wide">
    <div class="card-title">Run History</div>
    <div class="table-wrap">
      <table id="run-table">
        <thead>
          <tr>
            <th>Run ID</th><th>Label</th><th>Date</th>
            <th>Functions</th><th>Duration (s)</th><th>Carbon (gCO2)</th>
          </tr>
        </thead>
        <tbody id="run-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- Recent measurements table -->
  <div class="card wide">
    <div class="card-title">Recent Measurements</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Function</th><th>Duration (s)</th>
            <th>Carbon (gCO2)</th><th>CPU%</th><th>Run ID</th>
          </tr>
        </thead>
        <tbody id="meas-tbody"></tbody>
      </table>
    </div>
  </div>
</main>

<footer>EcoTrace v1.3.0 — <a href="https://github.com/Zwony/ecotrace" style="color:var(--green-hi)">github.com/Zwony/ecotrace</a></footer>

<script>
// ── Tiny charting library (vanilla Canvas — no deps) ───────────────────────
function drawLineChart(canvas, labels, values, color) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  canvas.width  = canvas.offsetWidth  * dpr;
  canvas.height = canvas.offsetHeight * dpr;
  ctx.scale(dpr, dpr);
  const W = canvas.offsetWidth, H = canvas.offsetHeight;
  const pad = { t: 10, r: 16, b: 36, l: 60 };
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;
  ctx.clearRect(0, 0, W, H);
  if (!values.length) return;

  const maxV = Math.max(...values) || 1;
  const minV = Math.min(...values);

  // Grid
  ctx.strokeStyle = 'rgba(48,54,61,.6)'; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.t + cH - (i / 4) * cH;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + cW, y); ctx.stroke();
    ctx.fillStyle = '#8b949e'; ctx.font = '10px Inter';
    ctx.fillText(((minV + (maxV - minV) * i / 4)).toExponential(2), 2, y + 4);
  }

  // Line + fill
  const pts = values.map((v, i) => ({
    x: pad.l + (i / Math.max(values.length - 1, 1)) * cW,
    y: pad.t + cH - ((v - minV) / (maxV - minV || 1)) * cH
  }));
  ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
  pts.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
  ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();

  const grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + cH);
  grad.addColorStop(0, color + '55'); grad.addColorStop(1, color + '00');
  ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
  pts.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(pts[pts.length-1].x, pad.t + cH); ctx.lineTo(pts[0].x, pad.t + cH);
  ctx.closePath(); ctx.fillStyle = grad; ctx.fill();

  // X labels (show max 8)
  ctx.fillStyle = '#8b949e'; ctx.font = '10px Inter'; ctx.textAlign = 'center';
  const step = Math.ceil(labels.length / 8);
  labels.forEach((l, i) => {
    if (i % step === 0)
      ctx.fillText(l.slice(5,16), pts[i].x, pad.t + cH + 16);
  });
}

function drawBarChart(canvas, labels, values, color) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  canvas.width  = canvas.offsetWidth  * dpr;
  canvas.height = canvas.offsetHeight * dpr;
  ctx.scale(dpr, dpr);
  const W = canvas.offsetWidth, H = canvas.offsetHeight;
  const pad = { t: 10, r: 16, b: 60, l: 70 };
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;
  ctx.clearRect(0, 0, W, H);
  if (!values.length) return;

  const maxV = Math.max(...values) || 1;
  const barH = cH / values.length * 0.7;
  const gap   = cH / values.length * 0.3;

  values.forEach((v, i) => {
    const y = pad.t + i * (barH + gap);
    const w = (v / maxV) * cW;
    ctx.fillStyle = color + 'cc';
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(pad.l, y, w, barH, 3) : ctx.rect(pad.l, y, w, barH);
    ctx.fill();

    // Label
    ctx.fillStyle = '#8b949e'; ctx.font = '10px Inter';
    ctx.textAlign = 'right';
    const lbl = labels[i].length > 18 ? labels[i].slice(0,18)+'…' : labels[i];
    ctx.fillText(lbl, pad.l - 4, y + barH / 2 + 4);

    // Value
    ctx.fillStyle = '#e6edf3'; ctx.textAlign = 'left';
    ctx.fillText(v.toExponential(2) + ' g', pad.l + w + 4, y + barH / 2 + 4);
  });
}

// ── Data & state ──────────────────────────────────────────────────────────
let allData = null, filteredRun = '';

function filterRun(runId) {
  filteredRun = runId;
  if (allData) renderData(allData);
}

function equiv(gco2) {
  if (gco2 <= 0) return '';
  if (gco2 < 0.01) return (gco2/0.2).toFixed(2) + ' Google searches';
  if (gco2 < 1)    return ((gco2/5.2)*60).toFixed(1) + ' min LED bulb (10W)';
  if (gco2 < 10)   return (gco2/8.22).toFixed(2) + ' smartphone charges';
  if (gco2 < 100)  return ((gco2/36)*60).toFixed(1) + ' min Netflix';
  return (gco2/121).toFixed(2) + ' km car driving';
}

function renderData(data) {
  const rows = filteredRun
    ? data.measurements.filter(m => m.run_id === filteredRun)
    : data.measurements;

  // Hero cards
  const totalC = rows.reduce((s, m) => s + m.carbon_gco2, 0);
  const totalD = rows.reduce((s, m) => s + m.duration_s, 0);
  document.getElementById('total-carbon').textContent = totalC.toExponential(4) + ' gCO2';
  document.getElementById('equiv').textContent = equiv(totalC);
  document.getElementById('meas-count').textContent = rows.length.toLocaleString();
  document.getElementById('runs-count').textContent = data.summary.run_count + ' unique run(s)';
  document.getElementById('total-dur').textContent = totalD.toFixed(2);

  // Top emitter
  const byFunc = {};
  rows.forEach(m => { byFunc[m.function] = (byFunc[m.function]||0) + m.carbon_gco2; });
  const sorted = Object.entries(byFunc).sort((a,b)=>b[1]-a[1]);
  if (sorted.length) {
    document.getElementById('top-func').textContent = sorted[0][0];
    document.getElementById('top-carbon').textContent = sorted[0][1].toExponential(4) + ' gCO2';
  }

  // Timeline chart
  const tCanvas = document.getElementById('timeline-chart');
  tCanvas.style.height = '200px';
  const last50 = rows.slice(-50);
  drawLineChart(tCanvas, last50.map(m=>m.date), last50.map(m=>m.carbon_gco2), '#56d364');

  // Bar chart (top 10 functions)
  const bCanvas = document.getElementById('func-chart');
  bCanvas.style.height = '220px';
  const top10 = sorted.slice(0, 10);
  drawBarChart(bCanvas, top10.map(x=>x[0]), top10.map(x=>x[1]), '#2ea043');

  // Run table
  const tbody = document.getElementById('run-tbody');
  tbody.innerHTML = '';
  data.summary.runs.forEach(r => {
    const tr = document.createElement('tr');
    const labelBadge = r.label ? `<span style="background:rgba(86,211,100,.15);color:#56d364;padding:1px 6px;border-radius:4px;font-size:11px">${r.label}</span>` : '—';
    tr.innerHTML = `<td><code style="font-size:11px">${r.run_id}</code></td><td>${labelBadge}</td><td>${r.date}</td><td>${r.count}</td><td>${r.duration_s.toFixed(2)}</td><td>${r.carbon_gco2.toExponential(4)}</td>`;
    tbody.appendChild(tr);
  });

  // Recent measurements table (last 20)
  const mtbody = document.getElementById('meas-tbody');
  mtbody.innerHTML = '';
  rows.slice(-20).reverse().forEach(m => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${m.date}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${m.function}">${m.function}</td><td>${m.duration_s.toFixed(4)}</td><td>${m.carbon_gco2.toExponential(4)}</td><td>${m.avg_cpu_pct}</td><td><code style="font-size:11px">${m.run_id||'—'}</code></td>`;
    mtbody.appendChild(tr);
  });

  // Populate run selector
  const sel = document.getElementById('run-filter');
  const existing = new Set([...sel.options].map(o=>o.value));
  data.summary.runs.forEach(r => {
    if (!existing.has(r.run_id)) {
      const opt = document.createElement('option');
      opt.value = r.run_id;
      opt.textContent = r.run_id + (r.label ? ` [${r.label}]` : '');
      sel.appendChild(opt);
    }
  });
}

// ── Polling ───────────────────────────────────────────────────────────────
async function refresh() {
  try {
    const resp = await fetch('/api/data');
    if (!resp.ok) return;
    allData = await resp.json();
    renderData(allData);
    document.getElementById('status').innerHTML =
      '<span class="dot"></span>Updated ' + new Date().toLocaleTimeString();
  } catch(e) {
    document.getElementById('status').textContent = 'Waiting for data…';
  }
}

refresh();
setInterval(refresh, 5000);
window.addEventListener('resize', () => { if (allData) renderData(allData); });
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------

class _DashboardHandler(BaseHTTPRequestHandler):
    """Internal request handler — serves the HTML dashboard and /api/data."""

    # csv_path is injected by DashboardServer when creating the handler class
    csv_path: str = "ecotrace_log.csv"

    def log_message(self, format, *args):
        """Suppress default access log clutter."""
        pass

    def _send_json(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/data":
            self._send_json(self._build_data())
        elif self.path in ("/", "/index.html"):
            self._send_html(_DASHBOARD_HTML)
        else:
            self.send_response(404)
            self.end_headers()

    # ------------------------------------------------------------------
    # Data aggregation (reads CSV each poll — fast enough for local use)
    # ------------------------------------------------------------------

    def _build_data(self) -> dict:
        measurements = []
        if os.path.isfile(self.csv_path):
            try:
                with open(self.csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            measurements.append({
                                "date": row.get("Date", ""),
                                "function": row.get("Function", "unknown"),
                                "duration_s": float(row.get("Duration(s)", 0)),
                                "carbon_gco2": float(row.get("Carbon(gCO2)", 0)),
                                "region": row.get("Region", ""),
                                "avg_cpu_pct": row.get("AvgCPU(%)", "N/A"),
                                "file_path": row.get("FilePath", "N/A"),
                                "line": row.get("Line", "N/A"),
                                "run_id": row.get("RunID", ""),
                                "run_label": row.get("RunLabel", ""),
                            })
                        except (ValueError, TypeError):
                            continue
            except Exception:
                pass

        # Aggregate per-run stats
        run_map: dict = {}
        for m in measurements:
            rid = m["run_id"] or "legacy"
            if rid not in run_map:
                run_map[rid] = {
                    "run_id": rid,
                    "label": m["run_label"],
                    "date": m["date"],
                    "count": 0,
                    "duration_s": 0.0,
                    "carbon_gco2": 0.0,
                }
            r = run_map[rid]
            r["count"] += 1
            r["duration_s"] += m["duration_s"]
            r["carbon_gco2"] += m["carbon_gco2"]
            if m["date"] > r["date"]:
                r["date"] = m["date"]

        runs = sorted(run_map.values(), key=lambda r: r["date"], reverse=True)

        total_carbon = sum(m["carbon_gco2"] for m in measurements)
        total_duration = sum(m["duration_s"] for m in measurements)

        func_map: dict = {}
        for m in measurements:
            fn = m["function"]
            func_map[fn] = func_map.get(fn, 0.0) + m["carbon_gco2"]
        top_emitters = sorted(func_map.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "measurements": measurements,
            "summary": {
                "total_carbon_gco2": round(total_carbon, 8),
                "total_duration_s": round(total_duration, 4),
                "measurement_count": len(measurements),
                "run_count": len(runs),
                "runs": runs,
                "top_emitters": [
                    {"function": fn, "carbon_gco2": round(c, 8)}
                    for fn, c in top_emitters
                ],
            },
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class DashboardServer:
    """Lightweight localhost HTTP server serving the EcoTrace live dashboard.

    Args:
        csv_path: Path to the CSV audit log (default ``ecotrace_log.csv``).
        port: TCP port to listen on (default 8585).
        host: Hostname to bind to (default ``127.0.0.1`` — localhost only).
    """

    def __init__(
        self,
        csv_path: str = "ecotrace_log.csv",
        port: int = 8585,
        host: str = "127.0.0.1",
    ):
        self.csv_path = csv_path
        self.port = port
        self.host = host

        # Build a per-instance handler class so csv_path is bound correctly
        # without relying on global state.
        handler_cls = type(
            "_BoundHandler",
            (_DashboardHandler,),
            {"csv_path": csv_path},
        )
        self._server = HTTPServer((host, port), handler_cls)

    def serve_forever(self):
        """Starts the HTTP server and blocks until Ctrl-C."""
        url = f"http://{self.host}:{self.port}"
        print(f"[EcoTrace Dashboard] Serving at {url}")
        print("[EcoTrace Dashboard] Press Ctrl-C to stop.")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._server.server_close()
            print("\n[EcoTrace Dashboard] Stopped.")

    def start_background(self) -> threading.Thread:
        """Starts the server in a background daemon thread.

        Returns:
            threading.Thread: The running server thread.
        """
        t = threading.Thread(target=self._server.serve_forever, daemon=True)
        t.start()
        return t

    def stop(self):
        """Shuts down the server if running in background mode."""
        self._server.shutdown()
        self._server.server_close()
