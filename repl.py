# repl.py — SyscomScript 対話実行モード (REPL)
#
# 変数保持の仕組み:
#   run_main(session_vars=...) に変数辞書を渡すと
#   Main インスタンスへ setattr() で注入し、実行後に更新辞書を返す。
#   独自の _execute()/_to_py() は廃止し、bootstrap を共通で使う。
#
# 複数行入力の仕組み:
#   { } のネスト深度をカウントし、depth > 0 の間は入力を継続する。

import sys
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main
from compiler.error import SyscomSyntaxError, SyscomRuntimeError

BANNER = """\
╔══════════════════════════════════════╗
║   SyscomScript REPL  (type 'exit')  ║
╚══════════════════════════════════════╝
  :vars   変数一覧    :clear  リセット
  :debug  Pythonコード表示    :help
"""

HELP_TEXT = """
使い方:
  式や文を1行ずつ入力して Enter で実行します。
  ブロック構文 (if/while) は { } が閉じるまで自動で複数行入力になります。

特殊コマンド:
  :vars    現在のセッション変数を一覧表示
  :clear   セッションをリセット（変数をすべて消去）
  :debug   直前に実行した Python コードを表示
  :help    このヘルプを表示
  exit     REPL を終了

入力例:
  >>> x = 10
  >>> y = 3
  >>> print(x + y)
  13
  >>> while (x > 0) {
  ...     print(x)
  ...     x = x - 3
  ... }
"""

PROMPT      = ">>> "
PROMPT_CONT = "... "


# ──────────────────────────────────────────
# ユーティリティ
# ──────────────────────────────────────────

def _brace_depth(text: str) -> int:
    """テキスト中の { と } のネスト差分を返す（文字列リテラル内は無視）"""
    depth = 0
    in_str = False
    str_char = None
    for ch in text:
        if in_str:
            if ch == str_char:
                in_str = False
        elif ch in ('"', "'"):
            in_str = True
            str_char = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
    return depth


def _wrap(stmt_lines: str) -> str:
    """ユーザー入力を class Main { run() { ... } } でラップする。"""
    indented = "\n".join("        " + line for line in stmt_lines.splitlines())
    return f"class Main {{\n    run() {{\n{indented}\n    }}\n}}"


def _compile(source: str) -> tuple[str | None, str | None]:
    """
    ソースをラップ→parse→to_python して (py_code, error_str) を返す。
    成功時は error_str=None。
    """
    wrapped = _wrap(source)
    try:
        tree = parse(wrapped)
    except SyscomSyntaxError as e:
        return None, str(e)
    return to_python(tree), None


# ──────────────────────────────────────────
# REPL メインループ
# ──────────────────────────────────────────

def run_repl():
    print(BANNER)

    session_vars: dict = {}
    last_py_code: str  = ""

    while True:

        # ── 入力収集 ──────────────────────────
        lines: list[str] = []
        depth = 0

        try:
            first_line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        stripped = first_line.strip()

        # 特殊コマンド
        if stripped in ("exit", "quit"):
            print("Bye!")
            break

        if stripped == ":vars":
            if session_vars:
                for k, v in session_vars.items():
                    try:
                        display = repr(v)
                    except Exception:
                        display = f"<{type(v).__name__}>"
                    print(f"  {k} = {display}")
            else:
                print("  (変数なし)")
            continue

        if stripped == ":clear":
            session_vars.clear()
            last_py_code = ""
            print("  セッションをリセットしました。")
            continue

        if stripped == ":debug":
            if last_py_code:
                print("\n=== Last Generated Python ===")
                print(last_py_code)
                print("=============================\n")
            else:
                print("  (まだ実行していません)")
            continue

        if stripped == ":help":
            print(HELP_TEXT)
            continue

        if stripped == "":
            continue

        lines.append(first_line)
        depth += _brace_depth(first_line)

        while depth > 0:
            try:
                cont = input(PROMPT_CONT)
            except (EOFError, KeyboardInterrupt):
                print()
                lines = []
                depth = 0
                break
            lines.append(cont)
            depth += _brace_depth(cont)

        if not lines:
            continue

        source = "\n".join(lines)

        # ── コンパイル ───────────────────────
        py_code, err = _compile(source)
        if err:
            print(err)
            continue

        last_py_code = py_code

        # ── 実行（bootstrap.run_main で統一） ─
        try:
            session_vars = run_main(py_code, session_vars=session_vars)
        except (SyscomSyntaxError, SyscomRuntimeError) as e:
            print(e)
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    run_repl()