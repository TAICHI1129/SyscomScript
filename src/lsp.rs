// src/lsp.rs — SyscomScript Language Server 実装

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

    fn run_python(args: &[&str]) -> std::io::Result<Output> {
        for cmd in &["python3", "python"] {
            match Command::new(cmd).args(args).output() {
                Ok(out) => return Ok(out),
                Err(_)  => continue,
            }
        }
        Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "python3 / python コマンドが見つかりません。",
        ))
    }

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
        if msg.is_empty() { return vec![]; }

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

fn parse_error_position(msg: &str) -> (u32, u32) {
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

fn completion_items() -> Vec<CompletionItem> {
    let snippets: &[(&str, &str, &str)] = &[
        ("if",      "if (${1:cond}) {\n\t${2}\n}",                     "if statement"),
        ("else",    "else {\n\t${1}\n}",                               "else block"),
        ("while",   "while (${1:cond}) {\n\t${2}\n}",                  "while loop"),
        ("for",     "for ${1:i} in range(${2:n}) {\n\t${3}\n}",        "for loop"),
        ("return",  "return ${1}",                                      "return statement"),
        ("class",   "class ${1:Name} {\n\trun() {\n\t\t${2}\n\t}\n}",  "class definition"),
        ("func",    "func ${1:name}(${2:args}) {\n\t${3}\n}",          "function definition"),
        ("print",   "print(${1})",                                      "print to stdout"),
        ("import",  "import ${1:module}",                               "import module"),
        ("py.math.sqrt",     "py.math.sqrt(${1})",            "math.sqrt()"),
        ("py.math.floor",    "py.math.floor(${1})",           "math.floor()"),
        ("py.math.ceil",     "py.math.ceil(${1})",            "math.ceil()"),
        ("py.os.getcwd",     "py.os.getcwd()",                 "os.getcwd()"),
        ("py.os.path.join",  "py.os.path.join(${1}, ${2})",   "os.path.join()"),
        ("py.open",          "py.open(${1:\"file\"}, ${2:\"r\"})", "open file"),
        ("py.subprocess.run","py.subprocess.run([${1}])",      "subprocess.run()"),
    ];

    snippets.iter().map(|(label, insert, detail)| {
        let kind = if label.starts_with("py.") {
            CompletionItemKind::FUNCTION
        } else if ["class", "func"].contains(label) {
            CompletionItemKind::CLASS
        } else {
            CompletionItemKind::KEYWORD
        };
        CompletionItem {
            label: label.to_string(),
            kind: Some(kind),
            detail: Some(detail.to_string()),
            insert_text: Some(insert.to_string()),
            insert_text_format: Some(InsertTextFormat::SNIPPET),
            ..Default::default()
        }
    }).collect()
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
                completion_provider: Some(CompletionOptions {
                    trigger_characters: Some(vec![
                        ".".to_string(),
                        " ".to_string(),
                    ]),
                    ..Default::default()
                }),
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

    async fn completion(
        &self,
        _params: CompletionParams,
    ) -> Result<Option<CompletionResponse>> {
        Ok(Some(CompletionResponse::Array(completion_items())))
    }

    async fn hover(&self, params: HoverParams) -> Result<Option<Hover>> {
        let pos = params.text_document_position_params.position;
        Ok(Some(Hover {
            contents: HoverContents::Markup(MarkupContent {
                kind: MarkupKind::Markdown,
                value: format!(
                    "**SyscomScript** — Line {}, Column {}",
                    pos.line + 1,
                    pos.character + 1
                ),
            }),
            range: None,
        }))
    }
}