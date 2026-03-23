use tower_lspjsonrpcResult;
use tower_lsplsp_types;
use tower_lsp{Client, LanguageServer, LspService, Server};
use stdprocessCommand;

pub struct SyscomLanguageServer {
    client Client,
}

impl SyscomLanguageServer {
    pub fn new(client Client) - Self {
        Self { client }
    }

     Python で syscom パーサを呼んで解析結果を返す
    fn parse_scs_file(&self, path &str) - OptionString {
        let output = Commandnew(python)
            .arg(syscom.py)
            .arg(path)
            .output()
            .ok();

        if output.status.success() {
            Some(Stringfrom_utf8_lossy(&output.stdout).to_string())
        } else {
            let err = Stringfrom_utf8_lossy(&output.stderr);
            self.client.log_message(MessageTypeERROR, err.to_string());
            None
        }
    }
}

#[tower_lspasync_trait]
impl LanguageServer for SyscomLanguageServer {
    async fn initialize(&self, _ InitializeParams) - ResultInitializeResult {
        Ok(InitializeResult {
            capabilities ServerCapabilities {
                text_document_sync Some(TextDocumentSyncCapabilityKind(TextDocumentSyncKindFULL)),
                hover_provider Some(HoverProviderCapabilitySimple(true)),
                ..Defaultdefault()
            },
            ..Defaultdefault()
        })
    }

    async fn initialized(&self, _ InitializedParams) {
        self.client.log_message(MessageTypeINFO, Syscom LSP initialized).await;
    }

    async fn shutdown(&self) - Result() {
        Ok(())
    }

    async fn did_open(&self, params DidOpenTextDocumentParams) {
        let path = params.text_document.uri.path();
        if let Some(parsed) = self.parse_scs_file(path) {
            self.client.log_message(MessageTypeINFO, format!(Parsed file {}, parsed)).await;
        }
    }

    async fn did_change(&self, params DidChangeTextDocumentParams) {
        let path = params.text_document.uri.path();
        if let Some(parsed) = self.parse_scs_file(path) {
            self.client.log_message(MessageTypeINFO, format!(Updated parse {}, parsed)).await;
        }
    }

    async fn hover(&self, params HoverParams) - ResultOptionHover {
         簡単にマウスオーバーした単語を返すだけ
        Ok(Some(Hover {
            contents HoverContentsScalar(MarkedStringString(
                format!(Hover info for {}, params.text_document_position_params.position),
            )),
            range None,
        }))
    }
}
