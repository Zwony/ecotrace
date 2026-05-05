import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as cp from 'child_process';
import { EcoTraceSidebarProvider } from './SidebarProvider';

/**
 * EcoTrace VS Code Extension — Sustainability Monitor v1.0.1
 *
 * This module is the bridge between the EcoTrace Python engine and the IDE.
 * Architectural rule: The LIBRARY produces data and enforces rules.
 *                     The EXTENSION reads data and enriches the UX.
 *
 * What's New in v1.0.1:
 *   - Equivalence Engine (TS port): gCO2 → human-readable comparisons
 *   - "✨ AI Optimize" CodeLens button: triggers library's AI analysis
 *   - Budget-aware Status Bar: color shifts with budget consumption %
 *   - Enriched Hover: equivalence + budget status in one tooltip
 */

// =============================================================================
// Module-level State
// =============================================================================
// These are intentionally module-scoped (not class members) so they survive
// sidebar re-renders and editor tab switches without resetting.

let myStatusBarItem: vscode.StatusBarItem;
let sessionTotal: number = 0;
let lastLogState: string = '';         // Anti-flicker: skip identical repaints
let budgetWarned: boolean = false;     // Tier-2 popup fires only once per session
let budgetEarlyWarned: boolean = false; // Tier-1 (80%) fires only once per session

// =============================================================================
// Equivalence Engine — TypeScript Port (v1.0.1)
// =============================================================================
// Mirrors ecotrace/core.py::equivalence(). The library owns the canonical
// implementation; this is a display-only copy for instant IDE feedback
// without spawning a Python subprocess for trivial conversions.
// Source data: IEA 2024, EPA greenhouse gas equivalencies, published LCA.

function carbonEquivalence(gco2: number): string {
    if (gco2 <= 0) { return ''; }

    // --- Tiered comparison selection by magnitude --------------------------
    // Each tier picks the most relatable comparison for that emission range.
    if (gco2 < 0.01) {
        // Sub-milligram range: Google searches (~0.2 gCO2 each)
        return `≈ ${(gco2 / 0.2).toFixed(3)} Google searches`;
    } else if (gco2 < 1.0) {
        // Milligram range: LED bulb minutes (10W bulb = 5.2 gCO2/hr)
        const minutes = (gco2 / 5.2) * 60;
        return `≈ ${minutes.toFixed(1)} min of LED bulb (10W)`;
    } else if (gco2 < 10.0) {
        // Gram range: smartphone charges (~8.22 gCO2 per full charge)
        return `≈ ${(gco2 / 8.22).toFixed(2)} smartphone charges`;
    } else if (gco2 < 100.0) {
        // Tens of grams: Netflix streaming (~36 gCO2/hr)
        const netflixMin = (gco2 / 36.0) * 60;
        return `≈ ${netflixMin.toFixed(1)} min of Netflix streaming`;
    } else {
        // Hundreds of grams: car driving (EU avg petrol: 121 gCO2/km)
        return `≈ ${(gco2 / 121.0).toFixed(2)} km of car driving`;
    }
}

// =============================================================================
// CodeLens Provider — v1.0.1
// =============================================================================
// Reads ecotrace_log.csv and injects two lenses per decorated function:
//   1. Carbon value with equivalence hint  (opens report on click)
//   2. "✨ Optimize" button               (triggers AI analysis command)

class EcoTraceCodeLensProvider implements vscode.CodeLensProvider {
    private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;

    // --- Per-file carbon data keyed by absolute file path -----------------
    private carbonData: { [filePath: string]: { lineNum: number; carbon: string; func: string }[] } = {};

    constructor() {
        this.loadData();
        // --- File watcher: refresh lenses on every CSV write --------------
        const watcher = vscode.workspace.createFileSystemWatcher('**/ecotrace_log.csv');
        watcher.onDidChange(() => { this.loadData(); this._onDidChangeCodeLenses.fire(); });
        watcher.onDidCreate(() => { this.loadData(); this._onDidChangeCodeLenses.fire(); });
    }

    private loadData() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) { return; }

        const logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
        if (!fs.existsSync(logPath)) { return; }

        try {
            const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
            const lines = content.trim().split('\n');
            this.carbonData = {};

            lines.slice(1).forEach(line => {
                const cols = line.split(',');
                // CSV schema: timestamp, func, duration, carbon, cpu, ..., filePath, lineNum
                if (cols.length >= 8) {
                    const filePath = cols[6];
                    const lineNum  = parseInt(cols[7]);
                    const carbon   = cols[3];
                    const func     = cols[1];

                    if (filePath && !isNaN(lineNum) && filePath !== 'N/A') {
                        if (!this.carbonData[filePath]) { this.carbonData[filePath] = []; }
                        this.carbonData[filePath].push({ lineNum, carbon, func });
                    }
                }
            });
        } catch {
            // Silently ignore read contention with Python process
        }
    }

    provideCodeLenses(document: vscode.TextDocument): vscode.CodeLens[] {
        const lenses: vscode.CodeLens[] = [];
        const fileData = this.carbonData[document.fileName];
        if (!fileData) { return lenses; }

        // --- Deduplicate by line: keep only the latest measurement ---------
        const addedLines = new Set<number>();
        [...fileData].reverse().forEach(data => {
            if (addedLines.has(data.lineNum)) { return; }
            addedLines.add(data.lineNum);

            const range   = new vscode.Range(data.lineNum - 1, 0, data.lineNum - 1, 0);
            const gco2    = parseFloat(data.carbon);
            const equiv   = carbonEquivalence(gco2);
            const equivHint = equiv ? `  (${equiv})` : '';

            // --- Lens 1: Carbon value + equivalence hint -------------------
            lenses.push(new vscode.CodeLens(range, {
                title: `EcoTrace: ${data.carbon}g CO2${equivHint}`,
                command: 'ecotrace.openFullReport',
                tooltip: `Click to open the full EcoTrace PDF report\n${equiv}`
            }));

            // --- Lens 2: AI Optimize button --------------------------------
            lenses.push(new vscode.CodeLens(range, {
                title: 'AI Optimize',
                command: 'ecotrace.optimizeFunction',
                arguments: [document.fileName, data.lineNum, data.func],
                tooltip: 'Ask EcoTrace AI for a greener version of this function'
            }));
        });

        return lenses;
    }
}

// =============================================================================
// Diagnostic Provider
// =============================================================================
// Static analysis hints: flags known energy-inefficient patterns in Python.
// These are zero-cost hints — no subprocess, no CSV read.

const diagnosticCollection = vscode.languages.createDiagnosticCollection('ecotrace');

function updateDiagnostics(document: vscode.TextDocument) {
    if (document.languageId !== 'python') { return; }
    const diagnostics: vscode.Diagnostic[] = [];
    const text = document.getText();

    // --- ECO_OPT_001: json → ujson/orjson --------------------------------
    const jsonRegex = /^(import json|from json import)/gm;
    let match;
    while ((match = jsonRegex.exec(text)) !== null) {
        const range = new vscode.Range(
            document.positionAt(match.index),
            document.positionAt(match.index + match[0].length)
        );
        const diag = new vscode.Diagnostic(
            range,
            'EcoTrace: Consider `ujson` or `orjson` instead of `json` — lower CPU energy per parse.',
            vscode.DiagnosticSeverity.Information
        );
        diag.code = 'ECO_OPT_001';
        diagnostics.push(diag);
    }

    diagnosticCollection.set(document.uri, diagnostics);
}

// =============================================================================
// Hotspot Decoration
// =============================================================================
// Applies a subtle green gutter icon + background tint to measured functions.
// Color intensity is uniform — hotspot severity is communicated via CodeLens.

const hotspotDecorationType = vscode.window.createTextEditorDecorationType({
    gutterIconPath: path.join(__filename, '..', '..', 'assets', 'logo.png'),
    gutterIconSize: 'contain',
    overviewRulerColor: '#4ade80',
    overviewRulerLane: vscode.OverviewRulerLane.Right,
    isWholeLine: true,
    backgroundColor: 'rgba(74, 222, 128, 0.04)'
});

// =============================================================================
// Extension Lifecycle — activate()
// =============================================================================

export function activate(context: vscode.ExtensionContext) {
    console.log('EcoTrace v1.0.1: Extension Monitoring Active');

    // --- Sidebar Panel ----------------------------------------------------
    const sidebarProvider = new EcoTraceSidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(EcoTraceSidebarProvider.viewType, sidebarProvider)
    );

    // --- 1. Status Bar Initialization ---
    // Drop our little leaf icon on the left side so it's always in the developer's face.
    myStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    myStatusBarItem.command = 'ecotrace.openFullReport';
    myStatusBarItem.text = 'EcoTrace Ready';
    myStatusBarItem.tooltip = 'EcoTrace: Carbon Footprint Monitor\nMonitoring system activity in the background...';
    context.subscriptions.push(myStatusBarItem);
    myStatusBarItem.show();
    updateStatusBarItem(sidebarProvider);

    // --- 2. Live File System Watcher ---
    // Watching the CSV, but we can't just jump on every change.
    // If Python is mid-write, Windows will throw a nasty EBUSY lock error and crash the extension.
    // So we add a 200ms timeout to let Python release the lock. Debounce saves lives.
    const watcher = vscode.workspace.createFileSystemWatcher('**/ecotrace_log.csv');
    watcher.onDidChange(() => setTimeout(() => { updateStatusBarItem(sidebarProvider); }, 200));
    watcher.onDidCreate(() => setTimeout(() => { updateStatusBarItem(sidebarProvider); }, 200));
    context.subscriptions.push(watcher);

    // --- Hotspot Decorations ---------------------------------------------
    applyHotspotDecorations();
    vscode.window.onDidChangeActiveTextEditor(() => applyHotspotDecorations(), null, context.subscriptions);

    // --- Command: Open PDF Report ----------------------------------------
    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.openFullReport', async () => {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) { return; }
            const reportPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_full_report.pdf');
            if (fs.existsSync(reportPath)) {
                await vscode.commands.executeCommand('vscode.open', vscode.Uri.file(reportPath));
            } else {
                vscode.window.showWarningMessage('[EcoTrace] PDF report not found. Run your Python code first.');
            }
        })
    );

    // --- Command: Reset Session ------------------------------------------
    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.resetSession', () => {
            sessionTotal       = 0;
            budgetWarned       = false;
            budgetEarlyWarned  = false;
            updateStatusBarItem(sidebarProvider);
            vscode.window.showInformationMessage('[EcoTrace] Carbon session reset successfully.');
        })
    );

    // --- Command: Eco-Friendly Mode --------------------------------------
    // Sets an env flag that Python scripts can optionally respect.
    // The extension toggles the flag; the library reads it — clear separation.
    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.ecoFriendlyMode', () => {
            process.env.ECOTRACE_ECO_MODE = '1';
            vscode.window.showInformationMessage(
                '[EcoTrace] Eco-Friendly Mode Activated: Energy-saving constraints enabled.'
            );
        })
    );

    // --- Command: AI Optimize Function (v1.0.1) --------------------------
    // The extension passes file + function context to the library's AI CLI.
    // The library does the analysis; the extension presents the result.
    // This is the boundary: IDE calls into library, never the other way.
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'ecotrace.optimizeFunction',
            async (filePath: string, lineNum: number, funcName: string) => {
                const config    = vscode.workspace.getConfiguration('ecotrace');
                const apiKey    = config.get<string>('geminiApiKey', '');
                const region    = config.get<string>('region', 'GLOBAL');

                if (!apiKey) {
                    const action = await vscode.window.showWarningMessage(
                        '[EcoTrace] Gemini API key not set. Add it in Settings → EcoTrace → Gemini API Key.',
                        'Open Settings'
                    );
                    if (action === 'Open Settings') {
                        vscode.commands.executeCommand('workbench.action.openSettings', 'ecotrace.geminiApiKey');
                    }
                    return;
                }

                // --- Read function source from document ------------------
                const doc = await vscode.workspace.openTextDocument(filePath);
                const funcLine = doc.lineAt(lineNum - 1).text;

                vscode.window.withProgress(
                    { location: vscode.ProgressLocation.Notification, title: `EcoTrace: Analyzing ${funcName}...`, cancellable: false },
                    async () => {
                        return new Promise<void>((resolve) => {
                            // Invoke library CLI: ecotrace optimize <file> --func <name>
                            // The result comes back via stdout and is shown in a panel.
                            const cmd = `python -m ecotrace optimize "${filePath}" --func "${funcName}" --region ${region}`;
                            cp.exec(cmd, { env: { ...process.env, GEMINI_API_KEY: apiKey } }, (err, stdout, stderr) => {
                                if (err || !stdout.trim()) {
                                    vscode.window.showErrorMessage(`[EcoTrace] AI analysis failed: ${stderr || err?.message}`);
                                } else {
                                    // --- Display result in a Markdown panel --
                                    // The panel reads library output; it does not
                                    // generate or modify analysis on its own.
                                    const panel = vscode.window.createWebviewPanel(
                                        'ecotraceOptimize',
                                        `EcoTrace: Optimize ${funcName}`,
                                        vscode.ViewColumn.Beside,
                                        { enableScripts: false }
                                    );
                                    panel.webview.html = _buildOptimizeHtml(funcName, stdout);
                                }
                                resolve();
                            });
                        });
                    }
                );
            }
        )
    );

    // --- CodeLens Provider -----------------------------------------------
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'python' }, new EcoTraceCodeLensProvider())
    );

    // --- Diagnostic Listeners --------------------------------------------
    context.subscriptions.push(diagnosticCollection);
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(updateDiagnostics));
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(updateDiagnostics));
    if (vscode.window.activeTextEditor) {
        updateDiagnostics(vscode.window.activeTextEditor.document);
    }
}

// =============================================================================
// Status Bar Updater — v1.0.1
// =============================================================================
// Reads the latest CSV entry and paints status bar with budget-aware colors:
//   Green  → under 80% of budget
//   Yellow → 80–100% of budget  (warning tier)
//   Red    → budget exceeded     (error tier)

async function updateStatusBarItem(sidebarProvider: EcoTraceSidebarProvider): Promise<void> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    let logPath: string | undefined;

    if (workspaceFolders) {
        logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
    } else if (vscode.window.activeTextEditor) {
        logPath = path.join(
            path.dirname(vscode.window.activeTextEditor.document.fileName),
            'ecotrace_log.csv'
        );
    }

    if (!logPath || !fs.existsSync(logPath)) {
        myStatusBarItem.text = '$(graph) EcoTrace: Waiting for data...';
        return;
    }

    applyHotspotDecorations();

    try {
        // Using the cross-platform safe 'r' flag here.
        // Python writes to this file insanely fast on Windows, so we need to avoid locking collisions.
        const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
        const lines   = content.trim().split('\n');
        if (lines.length <= 1) { return; }

        const lastLine = lines[lines.length - 1];
        if (lastLine === lastLogState) { return; }  // Anti-flicker: don't exhaust the UI for nothing
        lastLogState = lastLine;

        const cols = lastLine.split(',');
        if (cols.length < 4) { return; }

        const carbonValue = parseFloat(cols[3]);
        const funcName    = cols[1];
        const timestamp   = cols[0];

        if (isNaN(carbonValue)) { return; }

        sessionTotal += carbonValue;
        const equiv   = carbonEquivalence(sessionTotal);

        // --- Budget calculation ------------------------------------------
        // If the user hasn't set a limit, default to 10g. Play nice with the environment.
        const config      = vscode.workspace.getConfiguration('ecotrace');
        const budgetLimit = config.get<number>('carbonBudget', 10.0);
        const usedPct     = (sessionTotal / budgetLimit) * 100;

        // --- Status bar text and color -----------------------------------
        myStatusBarItem.text = `$(leaf) ${carbonValue.toFixed(5)}g | Total: ${sessionTotal.toFixed(5)}g`;
        myStatusBarItem.tooltip = [
            `Last: ${funcName} @ ${timestamp}`,
            `Session Total : ${sessionTotal.toFixed(8)} gCO2`,
            equiv ? `Equivalent    : ${equiv}` : '',
            `Budget        : ${sessionTotal.toFixed(5)} / ${budgetLimit} gCO2 (${usedPct.toFixed(1)}%)`,
            '',
            'Click to open full EcoTrace report'
        ].filter(Boolean).join('\n');

        // --- Budget-aware color shift ------------------------------------
        // Pop a warning when the budget is cooked or getting close, but don't spam the poor dev on every save.
        if (usedPct >= 100 && !budgetWarned) {
            budgetWarned = true;
            myStatusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            vscode.window.showWarningMessage(
                `[EcoTrace] Dude, what did you do? Carbon budget EXCEEDED: ${sessionTotal.toFixed(4)}g / ${budgetLimit}g CO2`,
                'Reset Session'
            ).then(action => {
                if (action === 'Reset Session') {
                    vscode.commands.executeCommand('ecotrace.resetSession');
                }
            });
        } else if (usedPct >= 80 && !budgetEarlyWarned) {
            budgetEarlyWarned = true;
            myStatusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            vscode.window.showInformationMessage(
                `[EcoTrace] Carbon budget is looking spicy (80%). Might wanna check that: ${sessionTotal.toFixed(4)}g / ${budgetLimit}g CO2`
            );
        } else if (usedPct < 80) {
            myStatusBarItem.backgroundColor = undefined;
        }

        // --- Push data to sidebar ----------------------------------------
        sidebarProvider.updateData();

    } catch (err) {
        // Silent recovery: If Python holds the lock while we try to read, just ignore it.
        // We'll catch the data on the next loop anyway.
        console.warn('EcoTrace: Log read contention bypass. We will catch it when Python lets go of the file.', err);
    }
}

// =============================================================================
// Hotspot Decoration Engine
// =============================================================================
// Maps CSV metrics to editor line coordinates and applies gutter markers.
// Hover messages now include equivalence data (v1.0.1).

async function applyHotspotDecorations() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    let logPath: string | undefined;

    if (workspaceFolders) {
        logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
    } else if (vscode.window.activeTextEditor) {
        logPath = path.join(
            path.dirname(vscode.window.activeTextEditor.document.fileName),
            'ecotrace_log.csv'
        );
    }

    if (!logPath || !fs.existsSync(logPath)) { return; }

    const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
    const lines   = content.trim().split('\n');
    if (lines.length <= 1) { return; }

    const decorationsByFile: { [filePath: string]: vscode.DecorationOptions[] } = {};

    lines.slice(1).forEach(line => {
        const cols = line.split(',');
        if (cols.length < 8) { return; }

        const filePath = cols[6];
        const lineNum  = parseInt(cols[7]);
        const carbon   = cols[3];
        const func     = cols[1];

        if (!filePath || isNaN(lineNum) || filePath === 'N/A') { return; }
        if (!decorationsByFile[filePath]) { decorationsByFile[filePath] = []; }

        // --- Skip if this line already has a decoration ------------------
        const alreadySet = decorationsByFile[filePath].some(d => d.range.start.line === lineNum - 1);
        if (alreadySet) { return; }

        const gco2   = parseFloat(carbon);
        const isHigh = gco2 > 0.1;
        const equiv  = carbonEquivalence(gco2);
        const range  = new vscode.Range(lineNum - 1, 0, lineNum - 1, 0);

        // --- Enriched hover (v1.0.1): equivalence line added -------------
        const md = new vscode.MarkdownString(
            `### EcoTrace Carbon Measurement\n` +
            `---\n` +
            `**Function:** \`${func}\`\n\n` +
            `**Carbon:** \`${carbon}g CO2\`\n\n` +
            (equiv ? `**Equivalent:** ${equiv}\n\n` : '') +
            `*Click the AI Optimize lens above to get greener suggestions.*`
        );
        md.isTrusted = true;

        decorationsByFile[filePath].push({ range, hoverMessage: md });
    });

    // --- Apply decorations across all visible editors --------------------
    // Ensures markers stay in sync when the user splits or switches tabs.
    vscode.window.visibleTextEditors.forEach(editor => {
        const fileDecorations = decorationsByFile[editor.document.fileName] || [];
        editor.setDecorations(hotspotDecorationType, fileDecorations);
    });
}

// =============================================================================
// AI Optimize Panel HTML Builder (v1.0.1)
// =============================================================================
// Renders the library's AI output in a clean, readable panel.
// The extension only formats — it never modifies the AI's content.

function _buildOptimizeHtml(funcName: string, output: string): string {
    const escaped = output
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoTrace: Optimize ${funcName}</title>
    <style>
        body { font-family: var(--vscode-font-family); padding: 20px; line-height: 1.6; }
        h1   { color: #4ade80; font-size: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
        pre  { background: rgba(0,0,0,0.3); border-radius: 6px; padding: 15px; overflow-x: auto; white-space: pre-wrap; font-size: 13px; }
        .badge { display: inline-block; background: #2e8b57; color: white; border-radius: 4px; padding: 2px 8px; font-size: 11px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>AI Optimization Report</h1>
    <span class="badge">Function: ${funcName}</span>
    <pre>${escaped}</pre>
</body>
</html>`;
}

// =============================================================================
// Extension Teardown
// =============================================================================

export function deactivate() { }

// /* --- Hybrid End of File / Dosya Sonu --- */ //
// # EcoTrace VS Code Integration Module v1.0.1 # //
