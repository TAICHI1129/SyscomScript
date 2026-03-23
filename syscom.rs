use tower_lsp::jsonrpc::Result;
use tower_lsp::lsp_types::*;
use tower_lsp::{Client, LanguageServer, LspService, Server};
use std::process::Command;

pub struct SyscomLanguageServer {
    client: Client,
}

impl SyscomLanguageServer {
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    // Python で syscom パーサを呼んで解析結果を返す
    fn parse_scs_file(&self, path: &str) -> Option<String> {
        let output = Command::new("python")
            .arg("syscom.py")
            .arg(path)
            .output()
            .ok()?;

        if output.status.success() {
            Some(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            let err = String::from_utf8_lossy(&output.stderr);
            self.client.log_message(MessageType::ERROR, err.to_string());
            None
        }
    }
}

#[tower_lsp::async_trait]
impl LanguageServer for SyscomLanguageServer {
    async fn initialize(&self, _: InitializeParams) -> Result<InitializeResult> {
        Ok(InitializeResult {
            capabilities: ServerCapabilities {
                text_document_sync: Some(TextDocumentSyncCapability::Kind(TextDocumentSyncKind::FULL)),
                hover_provider: Some(HoverProviderCapability::Simple(true)),
                ..Default::default()
            },
            ..Default::default()
        })
    }

    async fn initialized(&self, _: InitializedParams) {
        self.client.log_message(MessageType::INFO, "Syscom LSP initialized").await;
    }

    async fn shutdown(&self) -> Result<()> {
        Ok(())
    }

    async fn did_open(&self, params: DidOpenTextDocumentParams) {
        let path = params.text_document.uri.path();
        if let Some(parsed) = self.parse_scs_file(path) {
            self.client.log_message(MessageType::INFO, format!("Parsed file {}", parsed)).await;
        }
    }

    async fn did_change(&self, params: DidChangeTextDocumentParams) {
        let path = params.text_document.uri.path();
        if let Some(parsed) = self.parse_scs_file(path) {
            self.client.log_message(MessageType::INFO, format!("Updated parse {}", parsed)).await;
        }
    }

    async fn hover(&self, params: HoverParams) -> Result<Option<Hover>> {
        // 簡単にマウスオーバーした単語を返すだけ
        Ok(Some(Hover {
            contents: HoverContents::Scalar(MarkedString::String(
                format!("Hover info for {}", params.text_document_position_params.position),
            )),
            range: None,
        }))
    }
}