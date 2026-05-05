import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";

export class EcoTraceSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "ecotrace-sidebar";
  private _view?: vscode.WebviewView;

  constructor(private readonly _extensionUri: vscode.Uri) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

    // Message handling
    webviewView.webview.onDidReceiveMessage((data) => {
      switch (data.type) {
        case "openReport":
          vscode.commands.executeCommand("ecotrace.openFullReport");
          break;
      }
    });

    this.updateData();
  }

  public updateData() {
    if (!this._view) return;

    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) return;

    const logPath = path.join(workspaceFolders[0].uri.fsPath, "ecotrace_log.csv");
    const config = vscode.workspace.getConfiguration("ecotrace");
    const budgetLimit = config.get<number>("carbonBudget", 10.0);

    if (!fs.existsSync(logPath)) {
      this._view.webview.postMessage({ type: "noData", budgetLimit });
      return;
    }

    try {
      const content = fs.readFileSync(logPath, { encoding: "utf8", flag: "r" });
      const lines = content.trim().split("\n");
      if (lines.length <= 1) return;

      const data = lines.slice(1).map((line) => {
        const [timestamp, func, duration, carbon, cpu] = line.split(",");
        return { timestamp, func, duration, carbon: parseFloat(carbon), cpu };
      });

      const totalCarbon = data.reduce((acc, curr) => acc + curr.carbon, 0);
      const topFunctions = [...data]
        .sort((a, b) => b.carbon - a.carbon)
        .slice(0, 5);

      this._view.webview.postMessage({
        type: "update",
        totalCarbon: totalCarbon.toFixed(6),
        budgetLimit: budgetLimit,
        usedPct: Math.min((totalCarbon / budgetLimit) * 100, 100).toFixed(1),
        topFunctions: topFunctions.map(f => ({
            name: f.func,
            carbon: f.carbon.toFixed(6),
            cpu: f.cpu
        }))
      });
    } catch (err) {
      console.error("Sidebar update failed", err);
    }
  }

  private _getHtmlForWebview(webview: vscode.Webview) {
    // Sleek Dark Theme UI with Budget Progress Bar
    return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>EcoTrace</title>
                <style>
                    body {
                        padding: 10px;
                        color: var(--vscode-foreground);
                        font-family: var(--vscode-font-family);
                        background-color: var(--vscode-sideBar-background);
                    }
                    .card {
                        background: rgba(45, 45, 45, 0.4);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        padding: 15px;
                        margin-bottom: 20px;
                        backdrop-filter: blur(5px);
                    }
                    .stat-label {
                        font-size: 10px;
                        text-transform: uppercase;
                        opacity: 0.7;
                        letter-spacing: 1px;
                        margin-bottom: 5px;
                        display: flex;
                        justify-content: space-between;
                    }
                    .stat-value {
                        font-size: 24px;
                        font-weight: bold;
                        color: #4ade80;
                    }
                    .stat-unit {
                        font-size: 12px;
                        opacity: 0.8;
                        margin-left: 4px;
                    }
                    
                    /* --- Budget Progress Bar --- */
                    .progress-container {
                        width: 100%;
                        background-color: rgba(255,255,255,0.1);
                        border-radius: 4px;
                        height: 8px;
                        margin-top: 10px;
                        overflow: hidden;
                    }
                    .progress-bar {
                        height: 100%;
                        background-color: #4ade80;
                        width: 0%;
                        transition: width 0.3s ease, background-color 0.3s ease;
                    }

                    h3 {
                        font-size: 12px;
                        margin: 20px 0 10px 0;
                        opacity: 0.9;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        padding-bottom: 5px;
                    }
                    .function-list {
                        list-style: none;
                        padding: 0;
                        margin: 0;
                    }
                    .function-item {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 8px 0;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                        font-size: 11px;
                    }
                    .function-name {
                        max-width: 60%;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                    .function-carbon {
                        color: #fbbf24;
                        font-family: monospace;
                    }
                    .btn {
                        background: #2e8b57;
                        color: white;
                        border: none;
                        padding: 8px 12px;
                        border-radius: 4px;
                        cursor: pointer;
                        width: 100%;
                        margin-top: 20px;
                        font-size: 12px;
                        transition: background 0.2s;
                    }
                    .btn:hover {
                        background: #3cb371;
                    }
                    .no-data {
                        text-align: center;
                        opacity: 0.5;
                        margin-top: 40px;
                    }
                    .pulse {
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        background: #4ade80;
                        border-radius: 50%;
                        margin-right: 5px;
                        box-shadow: 0 0 10px #4ade80;
                        animation: pulse-animation 2s infinite;
                    }
                    @keyframes pulse-animation {
                        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
                        70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
                        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
                    }
                </style>
			</head>
			<body>
				<div id="content">
                    <div class="card">
                        <div class="stat-label">
                            <span><span class="pulse"></span>Session Carbon</span>
                            <span id="budget-text">0 / 10g</span>
                        </div>
                        <div class="stat-value" id="total-carbon">0.000<span class="stat-unit">g CO2</span></div>
                        <div class="progress-container">
                            <div class="progress-bar" id="budget-bar"></div>
                        </div>
                    </div>

                    <h3>TOP EMITTERS</h3>
                    <div class="function-list" id="function-list">
                        <!-- Items injected here -->
                        <div class="no-data">Searching for hotspots...</div>
                    </div>

                    <button class="btn" onclick="openReport()">Open Full PDF Report</button>
                    <div style="font-size: 9px; margin-top: 15px; opacity: 0.5; text-align: center;">
                        EcoTrace v1.0.1 | Active Enforcement Mode
                    </div>
                </div>

				<script>
					const vscode = acquireVsCodeApi();
                    
                    function openReport() {
                        vscode.postMessage({ type: 'openReport' });
                    }

					window.addEventListener('message', event => {
						const message = event.data;
						if (message.type === 'update') {
                            // Update total value
							document.getElementById('total-carbon').innerHTML = \`\${message.totalCarbon}<span class="stat-unit">g CO2</span>\`;
                            
                            // Update Budget Gauge
                            document.getElementById('budget-text').innerText = \`\${message.usedPct}% of Budget\`;
                            const bar = document.getElementById('budget-bar');
                            bar.style.width = \`\${message.usedPct}%\`;
                            
                            if (message.usedPct >= 100) {
                                bar.style.backgroundColor = '#ef4444'; // Red
                                document.getElementById('total-carbon').style.color = '#ef4444';
                            } else if (message.usedPct >= 80) {
                                bar.style.backgroundColor = '#fbbf24'; // Yellow
                                document.getElementById('total-carbon').style.color = '#fbbf24';
                            } else {
                                bar.style.backgroundColor = '#4ade80'; // Green
                                document.getElementById('total-carbon').style.color = '#4ade80';
                            }
							
                            // Update Top Functions
                            const list = document.getElementById('function-list');
                            list.innerHTML = '';
                            message.topFunctions.forEach(f => {
                                const item = document.createElement('div');
                                item.className = 'function-item';
                                const isHigh = parseFloat(f.carbon) > 0.1;
                                const style = isHigh ? 'color: #ef4444; font-weight: bold;' : 'color: #fbbf24;';
                                const alert = '';

                                item.innerHTML = \`
                                    <div class="function-name" title="\${f.name}">\${f.name}</div>
                                    <div class="function-carbon" style="\${style}">\${f.carbon}g\${alert}</div>
                                \`;
                                list.appendChild(item);
                            });
						} else if (message.type === 'noData') {
                            document.getElementById('budget-text').innerText = \`0 / \${message.budgetLimit}g\`;
                            document.getElementById('function-list').innerHTML = '<div class="no-data">No execution logs found.<br>Run your code with @eco.track to see data.</div>';
                        }
					});
				</script>
			</body>
			</html>`;
  }
}

