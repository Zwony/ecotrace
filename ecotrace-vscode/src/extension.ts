import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

let myStatusBarItem: vscode.StatusBarItem;
let sessionTotal: number = 0;
let lastLogState: string = ""; // Track state to avoid redundant updates

export function activate(context: vscode.ExtensionContext) {
    console.log('EcoTrace v0.7.0: Extension Monitoring Active');

    // 1. Initialize Status Bar Item
    myStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    myStatusBarItem.command = 'ecotrace.openFullReport';
    myStatusBarItem.text = `$(leaf) EcoTrace Ready`;
    myStatusBarItem.tooltip = 'EcoTrace: Carbon Footprint Monitor\nRunning in background...';
    context.subscriptions.push(myStatusBarItem);
    myStatusBarItem.show();

    // 2. Perform Initial Bootstrap
    updateStatusBarItem();

    // 3. Intelligent File System Watcher
    const watcher = vscode.workspace.createFileSystemWatcher('**/ecotrace_log.csv');

    watcher.onDidChange(() => {
        // Delay update slightly to ensure file lock is released by Python process
        setTimeout(() => updateStatusBarItem(), 200);
    });

    watcher.onDidCreate(() => {
        setTimeout(() => updateStatusBarItem(), 200);
    });

    context.subscriptions.push(watcher);

    // 4. Command Table
    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.openFullReport', async () => {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) return;

            const reportPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_full_report.pdf');
            if (fs.existsSync(reportPath)) {
                await vscode.commands.executeCommand('vscode.open', vscode.Uri.file(reportPath));
            } else {
                vscode.window.showWarningMessage('🌱 EcoTrace: PDF report not found yet. Run your code first.');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ecotrace.resetSession', () => {
            sessionTotal = 0;
            updateStatusBarItem();
            vscode.window.showInformationMessage('🌱 EcoTrace: Carbon session reset successfully.');
        })
    );

    // Initial Welcome Message (First launch focus)
    // vscode.window.showInformationMessage('EcoTrace Sustainability OS: Extension is monitoring your workspace.');
}

async function updateStatusBarItem(): Promise<void> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) return;

    const logPath = path.join(workspaceFolders[0].uri.fsPath, 'ecotrace_log.csv');

    if (!fs.existsSync(logPath)) {
        myStatusBarItem.text = `$(leaf) EcoTrace: Waiting for data...`;
        return;
    }

    try {
        // Read file using stream-compatible logic to handle potential locks
        const content = fs.readFileSync(logPath, { encoding: 'utf8', flag: 'r' });
        const lines = content.trim().split('\n');

        if (lines.length <= 1) return; // Only header exists

        const lastLine = lines[lines.length - 1];

        // Anti-flicker: Only update if the log content changed
        if (lastLine === lastLogState) return;
        lastLogState = lastLine;

        const cols = lastLine.split(',');
        if (cols.length >= 4) {
            const carbonValue = parseFloat(cols[3]);
            const funcName = cols[1];
            const timestamp = cols[0];

            if (!isNaN(carbonValue)) {
                sessionTotal += carbonValue;

                myStatusBarItem.text = `$(leaf) ${carbonValue.toFixed(4)}g | Total: ${sessionTotal.toFixed(4)}g`;
                myStatusBarItem.tooltip = `Last Function: ${funcName}\nTimestamp: ${timestamp}\n---\n$(graph) Session Cumulative: ${sessionTotal.toFixed(4)}g CO2\nClick to view full EcoTrace report`;
                myStatusBarItem.backgroundColor = carbonValue > 0.1 ? new vscode.ThemeColor('statusBarItem.warningBackground') : undefined;
            }
        }
    } catch (err) {
        // Silently handle read locks during heavy logging
        console.warn('EcoTrace Log Watcher: Busy or locked file bypass.', err);
    }
}

export function deactivate() { }
