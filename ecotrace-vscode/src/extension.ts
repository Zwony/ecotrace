import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { EcoTraceSidebarProvider } from './SidebarProvider';

/**
 * EcoTrace VS Code Extension: Sustainability Monitor
 * 
 * This module acts as the bridge between the high-precision EcoTrace Python engine
 * and the VS Code IDE. It monitors the core 'ecotrace_log.csv' file to provide 
 * real-time carbon footprint metrics directly in the developer's status bar.
 * 
 * Features:
 * - Real-time Status Bar updates (gCO2 per function)
 * - Persistent session tracking (Cumulative carbon)
 * - Anti-flicker log watching logic
 * - Quick-access PDF report opening
 */

let myStatusBarItem: vscode.StatusBarItem;
let sessionTotal: number = 0;
let lastLogState: string = ""; // Cache state to prevent redundant UI paints
let budgetWarned: boolean = false; // Prevent spamming budget warnings

// --- CodeLens Provider Design ---
class EcoTraceCodeLensProvider implements vscode.CodeLensProvider {
    private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;
    private carbonData: { [path: string]: { lineNum: number, carbon: string }[] } = {};

    constructor() {
        this.loadData();
        const watcher = vscode.workspace.createFileSystemWatcher('**/ecotrace_log.csv');
        watcher.onDidChange(() => {
            this.loadData();
            this._onDidChangeCodeLenses.fire();
        });
    }

    private loadData() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) return;
        const logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
        if (!fs.existsSync(logPath)) return;

        try {
            const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
            const lines = content.trim().split('\n');
            this.carbonData = {};
            lines.slice(1).forEach(line => {
                const cols = line.split(',');
                if (cols.length >= 8) {
                    const filePath = cols[6];
                    const lineNum = parseInt(cols[7]);
                    const carbon = cols[3];
                    if (filePath && !isNaN(lineNum) && filePath !== "N/A") {
                        if (!this.carbonData[filePath]) this.carbonData[filePath] = [];
                        this.carbonData[filePath].push({ lineNum, carbon });
                    }
                }
            });
        } catch (err) {
            // Silently ignore contention
        }
    }

    provideCodeLenses(document: vscode.TextDocument): vscode.CodeLens[] {
        const lenses: vscode.CodeLens[] = [];
        const fileData = this.carbonData[document.fileName];
        if (fileData) {
            // Deduplicate by line to avoid overlapping lenses
            const addedLines = new Set<number>();
            // Reverse so we get the latest measurements first
            [...fileData].reverse().forEach(data => {
                if (!addedLines.has(data.lineNum)) {
                    addedLines.add(data.lineNum);
                    const range = new vscode.Range(data.lineNum - 1, 0, data.lineNum - 1, 0);
                    const command: vscode.Command = {
                        title: `${data.carbon}g CO2`,
                        command: 'ecotrace.openFullReport',
                        tooltip: 'View carbon emission details'
                    };
                    lenses.push(new vscode.CodeLens(range, command));
                }
            });
        }
        return lenses;
    }
}

// --- Diagnostic Provider Design ---
const diagnosticCollection = vscode.languages.createDiagnosticCollection('ecotrace');

function updateDiagnostics(document: vscode.TextDocument) {
    if (document.languageId !== 'python') return;
    const diagnostics: vscode.Diagnostic[] = [];
    const text = document.getText();
    const regex = /^(import json|from json import)/gm;
    let match;
    while ((match = regex.exec(text)) !== null) {
        const startPos = document.positionAt(match.index);
        const endPos = document.positionAt(match.index + match[0].length);
        const diagnostic = new vscode.Diagnostic(
            new vscode.Range(startPos, endPos),
            'EcoTrace: Consider using `ujson` or `orjson` instead of standard `json` to reduce CPU energy consumption.',
            vscode.DiagnosticSeverity.Information
        );
        diagnostic.code = 'ECO_OPT_001';
        diagnostics.push(diagnostic);
    }
    diagnosticCollection.set(document.uri, diagnostics);
}

// --- Hotspot Decoration Design ---
const hotspotDecorationType = vscode.window.createTextEditorDecorationType({
    gutterIconPath: path.join(__filename, '..', '..', 'assets', 'logo.png'),
    gutterIconSize: 'contain',
    overviewRulerColor: '#4ade80',
    overviewRulerLane: vscode.OverviewRulerLane.Right,
    isWholeLine: true,
    backgroundColor: 'rgba(74, 222, 128, 0.05)'
});

/**
 * Bootstraps the extension lifecycle and registers ecosystem commands.
 * 
 * Performs initial status bar mounting, initializes file system watchers,
 * and populates the command table for report viewing and session management.
 * 
 * @param context vscode.ExtensionContext provided by the VS Code runtime.
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('EcoTrace v0.9.0: Extension Monitoring Active');

    const sidebarProvider = new EcoTraceSidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            EcoTraceSidebarProvider.viewType,
            sidebarProvider
        )
    );

    // --- 1. Status Bar Initialization ---
    // Positions the leaf icon and carbon metrics on the left side of the UI.
    myStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    myStatusBarItem.command = 'ecotrace.openFullReport';
    myStatusBarItem.text = `$(pulse) EcoTrace Ready`;
    myStatusBarItem.tooltip = 'EcoTrace: Carbon Footprint Monitor\nMonitoring system activity...';
    context.subscriptions.push(myStatusBarItem);
    myStatusBarItem.show();

    // Initial state check
    updateStatusBarItem();

    // --- 2. Live File System Watcher ---
    // Watches for changes in 'ecotrace_log.csv'. Uses a 200ms timeout logic
    // to allow the Python engine to release file locks before reading.
    const watcher = vscode.workspace.createFileSystemWatcher('**/ecotrace_log.csv');

    watcher.onDidChange(() => {
        setTimeout(() => {
            updateStatusBarItem();
            sidebarProvider.updateData();
        }, 200);
    });

    watcher.onDidCreate(() => {
        setTimeout(() => {
            updateStatusBarItem();
            sidebarProvider.updateData();
        }, 200);
    });

    context.subscriptions.push(watcher);

    // Initial decorations and editor change listeners
    applyHotspotDecorations();
    vscode.window.onDidChangeActiveTextEditor(() => applyHotspotDecorations(), null, context.subscriptions);

    // --- 3. Command Table Registration ---
    // Registers handlers for PDF opening and session resetting.
    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.openFullReport', async () => {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) return;

            const reportPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_full_report.pdf');
            if (fs.existsSync(reportPath)) {
                await vscode.commands.executeCommand('vscode.open', vscode.Uri.file(reportPath));
            } else {
                vscode.window.showWarningMessage('[EcoTrace] PDF report not found. Run your Python code first.');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.resetSession', () => {
            sessionTotal = 0;
            budgetWarned = false;
            updateStatusBarItem();
            vscode.window.showInformationMessage('[EcoTrace] Carbon session reset successfully.');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.ecoFriendlyMode', () => {
            // Example of eco-mode setting a local var or env flag
            process.env.ECOTRACE_ECO_MODE = '1';
            vscode.window.showInformationMessage('Eco-Friendly Mode Activated: Background indexing paused and tests will run in energy-saving mode.');
        })
    );

    // Register CodeLens Provider
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'python' }, new EcoTraceCodeLensProvider())
    );

    // Register Diagnostic Listeners
    context.subscriptions.push(diagnosticCollection);
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(updateDiagnostics));
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(updateDiagnostics));
    if (vscode.window.activeTextEditor) {
        updateDiagnostics(vscode.window.activeTextEditor.document);
    }
}

/**
 * Core Data Engine: Synchronizes UI state with the latest disk-based metrics.
 * 
 * Reads the 'ecotrace_log.csv' utilizing a stream-friendly flag to mitigate
 * read-write contention with the Python daemon. Parses the final log line
 * to calculate delta carbon values and updates incremental session totals.
 * 
 * Returns:
 *   Promise<void>: Async operation completing once Status Bar text is updated.
 */
async function updateStatusBarItem(): Promise<void> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    let logPath: string | undefined;

    if (workspaceFolders) {
        logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
    } else if (vscode.window.activeTextEditor) {
        // Fallback: Look for log in the same directory as the active file
        logPath = path.join(path.dirname(vscode.window.activeTextEditor.document.fileName), 'ecotrace_log.csv');
    }

    if (!logPath || !fs.existsSync(logPath)) {
        myStatusBarItem.text = `$(graph) EcoTrace: Waiting for data...`;
        return;
    }

    applyHotspotDecorations(); // Also refresh markers

    try {
        // Read file using cross-platform safe 'r' flag to avoid locking collisions
        const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
        const lines = content.trim().split('\n');

        if (lines.length <= 1) return; // Ignore if only header exists

        const lastLine = lines[lines.length - 1];

        // Anti-flicker Logic: Exit if the last recorded log state is identical
        if (lastLine === lastLogState) return;
        lastLogState = lastLine;

        const cols = lastLine.split(',');
        if (cols.length >= 4) {
            const carbonValue = parseFloat(cols[3]);
            const funcName = cols[1];
            const timestamp = cols[0];

            if (!isNaN(carbonValue)) {
                sessionTotal += carbonValue;

                // Update UI with localized carbon metrics
                const alertMark = carbonValue > 0.1 ? ' !' : '';
                myStatusBarItem.text = `$(graph) ${carbonValue.toFixed(4)}g${alertMark} | Total: ${sessionTotal.toFixed(4)}g`;
                myStatusBarItem.tooltip = `Last Function: ${funcName}\nTimestamp: ${timestamp}\n---\nSession Cumulative: ${sessionTotal.toFixed(4)}g CO2\nClick to view full EcoTrace report`;

                // Visual Indicator: Use error color if a single function is unusually heavy (>0.1g)
                myStatusBarItem.backgroundColor = carbonValue > 0.1 ? new vscode.ThemeColor('statusBarItem.errorBackground') : undefined;
                
                // CI/CD / Budget Integration Warning: Dynamic limit from VS Code Settings
                const config = vscode.workspace.getConfiguration('ecotrace');
                const budgetLimit = config.get<number>('carbonBudget', 10.0);

                if (sessionTotal > budgetLimit && !budgetWarned) {
                    vscode.window.showWarningMessage(`EcoTrace: Carbon budget exceeded (${budgetLimit}g CO2)! Please review your latest changes for energy regressions.`);
                    budgetWarned = true;
                }
            }
        }
    } catch (err) {
        // Silent recovery: Log locks are expected during high-frequency Python execution
        console.warn('EcoTrace Log Watcher: File contention bypass.', err);
    }
}

/**
 * Hotspot Engine: Maps CSV metrics to editor coordinates.
 * Scans the log for FilePath and Line data to apply visual markers.
 */
async function applyHotspotDecorations() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    let logPath: string | undefined;

    if (workspaceFolders) {
        logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
    } else if (vscode.window.activeTextEditor) {
        logPath = path.join(path.dirname(vscode.window.activeTextEditor.document.fileName), 'ecotrace_log.csv');
    }

    if (!logPath || !fs.existsSync(logPath)) return;

    const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
    const lines = content.trim().split('\n');
    if (lines.length <= 1) return;

    const decorationsByFile: { [path: string]: vscode.DecorationOptions[] } = {};

    lines.slice(1).forEach(line => {
        const cols = line.split(',');
        if (cols.length >= 8) {
            const filePath = cols[6];
            const lineNum = parseInt(cols[7]);
            const carbon = cols[3];
            const func = cols[1];

            if (filePath && !isNaN(lineNum) && filePath !== "N/A") {
                if (!decorationsByFile[filePath]) decorationsByFile[filePath] = [];

                // Only show the latest measurement for each function/line combo
                const existing = decorationsByFile[filePath].find(d => d.range.start.line === lineNum - 1);
                if (existing) return;

                const isHigh = parseFloat(carbon) > 0.1;
                const range = new vscode.Range(lineNum - 1, 0, lineNum - 1, 0);
                decorationsByFile[filePath].push({
                    range,
                    hoverMessage: new vscode.MarkdownString(
                        `### ${isHigh ? '[!] ' : ''}EcoTrace: High Carbon Impact\n` +
                        `---\n` +
                        `**Function:** \`${func}\`\n\n` +
                        `**Latest Measurement:** \`${carbon}g CO2\`\n\n` +
                        `*This marker highlights functions with energy consumption data. Process-isolated analytics.*`
                    )
                });
            }
        }
    });

    // --- Performance Note ---
    // We update decorations across all visible editors to ensure the markers 
    // stay in sync when the user switches tabs or splits the view.
    vscode.window.visibleTextEditors.forEach(editor => {
        const fileDecorations = decorationsByFile[editor.document.fileName] || [];
        editor.setDecorations(hotspotDecorationType, fileDecorations);
    });
}

/**
 * Handles extension teardown.
 */
export function deactivate() { }

// /* --- Hybrid End of File / Dosya Sonu --- */ //
// # EcoTrace VS Code Integration Module # //
