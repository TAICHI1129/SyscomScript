const vscode = require('vscode');
const cp = require('child_process');

function activate(context) {
    let disposable = vscode.commands.registerCommand('syscom.run', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const file = editor.document.fileName;

        cp.exec(`python syscom.py "${file}"`, { cwd: vscode.workspace.rootPath }, (err, stdout, stderr) => {
            if (err) {
                vscode.window.showErrorMessage(stderr);
            } else {
                vscode.window.showInformationMessage(stdout);
            }
        });
    });

    context.subscriptions.push(disposable);
}

exports.activate = activate;
function deactivate() {}
exports.deactivate = deactivate;
