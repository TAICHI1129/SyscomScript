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
            .output();

        let o = match output {
            Ok(o) => o,
            Err(_) => return vec![],
        };

        // FIX: syscom.py は SyscomError 時に sys.exit(1) するので
        //      exit code で判定できる（以前は常に 0 だったため波線が出なかった）
        if o.status.success() {
            return vec![];
        }

        let msg = String::from_utf8_lossy(&o.stdout).to_string()
            + &String::from_utf8_lossy(&o.stderr);
        let msg = msg.trim().to_string();

        if msg.is_empty() {
            return vec![];
        }

        // "SyscomError at line N, column M: ..." を正確な行・列に変換
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
}

/// "SyscomError at line N, column M: ..." から (line-1, col-1) を返す（LSP は 0-based）
fn parse_error_position(msg: &str) -> (u32, u32) {
    let line = msg
        .split("at line ")
        .nth(1)
        .and_then(|s| s.split([',', ':']).next())
        .and_then(|s| s.trim().parse::<u32>().ok())
        .map(|n| n.saturating_sub(1))
        .unwrap_or(0);

    let col = msg
        .split("column ")
        .nth(1)
        .and_then(|s| s.split([',', ':']).next())
        .and_then(|s| s.trim().parse::<u32>().ok())
        .map(|n| n.saturating_sub(1))
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