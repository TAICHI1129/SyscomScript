// src/lsp.rs — SyscomScript Language Server 実装

use tower_lsp::jsonrpc::Result;
use tower_lsp::lsp_types::*;
use tower_lsp::{Client, LanguageServer};
use std::process::Command;

pub struct SyscomLanguageServer {
    client: Client,
}

impl SyscomLanguageServer {
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Python で syscom パーサを呼び、エラーがあれば Diagnostics として返す
    async fn check_scs_file(&self, _uri: &Url, text: &str) -> Vec<Diagnostic> {
        let tmp = std::env::temp_dir().join("_syscom_lsp_check.scs");
        if std::fs::write(&tmp, text).is_err() {
            return vec![];
        }

        let output = Command::new("python")
            .arg("syscom.py")
            .arg(&tmp)
            .arg("--debug-python")
            .output();

        match output {
            Ok(o) if !o.status.success() => {
                // stdout に SyscomError メッセージが出る
                let msg = String::from_utf8_lossy(&o.stdout).to_string()
                    + &String::from_utf8_lossy(&o.stderr);
                let msg = msg.trim().to_string();

                // "SyscomError at line N, column M: ..." をパースして正確な位置に波線を出す
                let (line, col) = parse_error_position(&msg);

                let diag = Diagnostic {
                    range: Range {
                        start: Position { line, character: col },
                        end:   Position { line, character: col + 1 },
                    },
                    severity: Some(DiagnosticSeverity::ERROR),
                    message: msg,
                    source: Some("SyscomScript".to_string()),
                    ..Default::default()
                };
                vec![diag]
            }
            _ => vec![],
        }
    }
}

/// "SyscomError at line N, column M: ..." から (line-1, col-1) を返す
/// パース失敗時は (0, 0)
fn parse_error_position(msg: &str) -> (u32, u32) {
    // "at line N" を探す
    let line = msg
        .split("at line ")
        .nth(1)
        .and_then(|s| s.split([',', ':']).next())
        .and_then(|s| s.trim().parse::<u32>().ok())
        .map(|n| n.saturating_sub(1))   // LSP は 0-based
        .unwrap_or(0);

    // "column M" を探す
    let col = msg
        .split("column ")
        .nth(1)
        .and_then(|s| s.split([',', ':']).next())
        .and_then(|s| s.trim().parse::<u32>().ok())
        .map(|n| n.saturating_sub(1))   // LSP は 0-based
        .unwrap_or(0);

    (line, col)
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