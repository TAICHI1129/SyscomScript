// extension.js — SyscomScript VSCode 拡張エントリポイント
//
// 【動作の流れ】
//   1. VSCode が .scs ファイルを開く
//   2. この拡張が有効化される (activationEvents: onLanguage:syscomscript)
//   3. syscom_lsp バイナリを子プロセスとして起動
//   4. stdin/stdout 経由で LSP プロトコル通信開始
//   5. ファイル編集のたびに lsp.rs の check_scs_file() が呼ばれ
//      エラーがあれば赤波線として表示される

const { workspace, window } = require("vscode");
const {
  LanguageClient,
  TransportKind,
} = require("vscode-languageclient/node");
const path = require("path");
const fs   = require("fs");

let client;

function activate(context) {
  // syscom_lsp バイナリのパスを解決
  // Windows: syscom_lsp.exe  /  Mac・Linux: syscom_lsp
  const ext    = process.platform === "win32" ? ".exe" : "";
  const binary = path.join(context.extensionPath, "bin", `syscom_lsp${ext}`);

  if (!fs.existsSync(binary)) {
    window.showErrorMessage(
      `SyscomScript LSP binary not found: ${binary}\n` +
      `Run "cargo build --release" and copy the binary to the "bin/" folder.`
    );
    return;
  }

  const serverOptions = {
    run:   { command: binary, transport: TransportKind.stdio },
    debug: { command: binary, transport: TransportKind.stdio },
  };

  const clientOptions = {
    // .scs ファイルを開いたときだけ有効化
    documentSelector: [{ scheme: "file", language: "syscomscript" }],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher("**/*.scs"),
    },
  };

  client = new LanguageClient(
    "syscomscript",
    "SyscomScript Language Server",
    serverOptions,
    clientOptions
  );

  client.start();
}

function deactivate() {
  if (client) {
    return client.stop();
  }
}

module.exports = { activate, deactivate };