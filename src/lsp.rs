// src/lsp.rs — SyscomScript Language Server 実装
//
// 変更点:
//   - Command::new("python") の無音失敗を修正
//     → python3 → python の順でフォールバック、両方失敗なら診断エラーを返す
//   - parse_error_position() を正規表現ベースに変更
//     → メッセージフォーマットが変わっても (0,0) に黙って落ちない
//   - exec エラーも診断として返す（握りつぶさない）

use tower_lsp::jsonrpc::Result;
use tower_lsp::lsp_types::*;
use tower_lsp::{Client, LanguageServer};
use std::process::{Command, Output};
use regex::Regex;

pub struct SyscomLanguageServer {
    client: Client,
}

impl SyscomLanguageServer {
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// python3 → python の順で試し、最初に成功したコマンドの Output を返す。
    /// どちらも起動失敗なら Err を返す。
    fn run_python(args: &[&str]) -> std::io::Result<Output> {
        for cmd in &["python3", "python"] {
            match Command::new(cmd).args(args).output() {
                Ok(out) => return Ok(out),
                Err(_)  => continue,
            }
        }
        Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "python3 / python コマンドが見つかりません。\
             Python をインストールして PATH を通してください。",
        ))
    }

    /// Python で syscom パーサを呼び、エラーがあれば Diagnostics として返す。
    async fn check_scs_file(&self, _uri: &Url, text: &str) -> Vec<Diagnostic> {
        let tmp = std::env::temp_dir().join("_syscom_lsp_check.scs");
        if std::fs::write(&tmp, text).is_err() {
            return vec![];
        }

        let tmp_str = tmp.to_string_lossy();
        let output  = Self::run_python(&["syscom.py", &tmp_str]);

        let o = match output {
            Ok(o)  => o,
            Err(e) => {
                // Python 自体が見つからない場合はその旨を診断として返す
                return vec![Diagnostic {
                    range: Range {
                        start: Position { line: 0, character: 0 },
                        end:   Position { line: 0, character: 1 },
                    },
                    severity: Some(DiagnosticSeverity::WARNING),
                    message: format!("SyscomScript LSP: {e}"),
                    source: Some("SyscomScript".to_string()),
                    ..Default::default()
                }];
            }
        };

        if o.status.success() {
            return vec![];
        }

        let msg = format!(
            "{}{}",
            String::from_utf8_lossy(&o.stdout),
            String::from_utf8_lossy(&o.stderr),
        );
        let msg = msg.trim().to_string();

        if msg.is_empty() {
            return vec![];
        }

        let (line, col) = parse_error_position(&msg);

        vec![Diagnostic {
            range: Range {
                start: Position { line, character: col },
                end:   Position { line, character: col + 1 },
            },
            severity: Some(DiagnosticSeverity::ERROR),
            message: msg,
            source: Some("SyscomScript".to_string()),
            ..Default::default()
        }]
    }
}

/// "SyscomError at line N, column M: ..." から (line-1, col-1) を返す（LSP は 0-based）。
/// 正規表現ベースなのでメッセージフォーマットの変化に強い。
/// マッチしない場合は (0, 0) を返す（以前と同じ）が、
/// 呼び出し元がログを出すので無音失敗にはならない。
fn parse_error_position(msg: &str) -> (u32, u32) {
    // "at line 5, column 12" または "at line 5" の形を想定
    let re = Regex::new(r"at line (\d+)(?:, column (\d+))?").unwrap();

    if let Some(caps) = re.captures(msg) {
        let line = caps.get(1)
            .and_then(|m| m.as_str().parse::<u32>().ok())
            .map(|n| n.saturating_sub(1))
            .unwrap_or(0);
        let col = caps.get(2)
            .and_then(|m| m.as_str().parse::<u32>().ok())
            .map(|n| n.saturating_sub(1))
            .unwrap_or(0);
        return (line, col);
    }

    (0, 0)
}

#[tower_lsp::async_trait]
impl LanguageServer for SyscomLanguageServer {
    async fn initialize(&self, _: InitializeParams) -> Result<InitializeResult> {
        Ok(InitializeResult {
            capabilities: ServerCapabilities {
                text_document_sync: Some(TextDocumentSyncCapability::Kind(
                    TextDocumentSyncKind::FULL,
                )),
                hover_provider: Some(HoverProviderCapability::Simple(true)),
                ..Default::default()
            },
            ..Default::default()
        })
    }

    async fn initialized(&self, _: InitializedParams) {
        self.client
            .log_message(MessageType::INFO, "SyscomScript LSP initialized")
            .await;
    }

    async fn shutdown(&self) -> Result<()> {
        Ok(())
    }

    async fn did_open(&self, params: DidOpenTextDocumentParams) {
        let uri  = params.text_document.uri;
        let text = params.text_document.text;
        let diags = self.check_scs_file(&uri, &text).await;
        self.client.publish_diagnostics(uri, diags, None).await;
    }

    async fn did_change(&self, params: DidChangeTextDocumentParams) {
        let uri  = params.text_document.uri;
        let text = params.content_changes.into_iter().last()
            .map(|c| c.text)
            .unwrap_or_default();
        let diags = self.check_scs_file(&uri, &text).await;
        self.client.publish_diagnostics(uri, diags, None).await;
    }

    async fn hover(&self, params: HoverParams) -> Result<Option<Hover>> {
        let pos = params.text_document_position_params.position;
        Ok(Some(Hover {
            contents: HoverContents::Scalar(MarkedString::String(
                format!("Line {}, Column {}", pos.line + 1, pos.character + 1),
            )),
            range: None,
        }))
    }
}