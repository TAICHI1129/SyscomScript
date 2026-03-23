use tower_lsp::{LspService, Server};
use crate::lsp::SyscomLanguageServer;

#[tokio::main]
async fn main() {
    let stdin = tokio::io::stdin();
    let stdout = tokio::io::stdout();

    let (service, socket) = LspService::new(|client| SyscomLanguageServer::new(client));
    Server::new(stdin, stdout, socket).serve(service).await;
}