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
    console.log('EcoTrace v0.8.0: Extension Monitoring Active');

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
    myStatusBarItem.text = `$(leaf) EcoTrace Ready`;
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
            updateStatusBarItem();
            vscode.window.showInformationMessage('[EcoTrace] Carbon session reset successfully.');
        })
    );
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
    if (!workspaceFolders) return;

    applyHotspotDecorations(); // Also refresh markers

    const logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');

    if (!fs.existsSync(logPath)) {
        myStatusBarItem.text = `$(graph) EcoTrace: Waiting for data...`;
        return;
    }

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
    if (!workspaceFolders) return;

    const logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');
    if (!fs.existsSync(logPath)) return;

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
