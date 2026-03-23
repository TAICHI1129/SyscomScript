# repl.py — SyscomScript 対話実行モード (REPL)
#
# 【変数保持の仕組み】
#   SyscomScript の assign は Python の「self.x = ...」になる。
#   つまり変数はインスタンス属性として保存される。
#   REPL では毎回新しい Main() を作るため、そのままでは変数が消えてしまう。
#
#   解決策:
#     - session_vars 辞書にセッション変数を蓄積する
#     - 毎回の run() 前に instance.__dict__ へ注入し、
#       run() 後に instance.__dict__ から読み出して session_vars に書き戻す
#
# 【複数行入力の仕組み】
#   { } のネスト深度をカウントし、depth > 0 の間は入力を継続する。
#   while / if などのブロック構文は自動的に複数行入力モードになる。

import sys
from compiler.parser import parse
from compiler.transformer import to_python
from compiler.error import SyscomSyntaxError

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


def _wrap(stmt_lines: str, session_vars: dict) -> str:
    """
    ユーザー入力を class Main { run() { ... } } でラップする。
    セッション変数を run() の先頭で self.xxx = <値> として注入することで
    前回の実行結果を引き継げるようにする。
    """
    # セッション変数の注入コード（Python として直接埋め込む）
    inject_lines = []
    for k, v in session_vars.items():
        inject_lines.append(f"        self.{k} = {v!r}")

    inject_block = "\n".join(inject_lines)

    # ユーザー入力をインデント
    indented = "\n".join("        " + line for line in stmt_lines.splitlines())

    if inject_block:
        body = inject_block + "\n" + indented
    else:
        body = indented

    return f"class Main {{\n    run() {{\n{body}\n    }}\n}}"


def _extract_vars(instance) -> dict:
    """run() 後のインスタンス属性（_ で始まらないもの）をすべて返す"""
    return {k: v for k, v in instance.__dict__.items() if not k.startswith("_")}


def _to_py(source: str, session_vars: dict):
    """
    ラップ→parse→to_python を行い (py_code, error_str) を返す。
    成功時は error_str=None。
    """
    wrapped = _wrap(source, session_vars)
    try:
        tree = parse(wrapped)
    except SyscomSyntaxError as e:
        return None, str(e)
    py_code = to_python(tree)
    return py_code, None


def _execute(py_code: str, session_vars: dict):
    """
    py_code を exec し、Main().run() を呼んで
    (updated_session_vars, error_str) を返す。
    """
    ns = {}
    try:
        exec(py_code, ns)
    except Exception as e:
        return session_vars, f"Compile error: {e}"

    if "Main" not in ns:
        return session_vars, "Main クラスが見つかりません"

    instance = ns["Main"]()

    # セッション変数を注入（Python で直接 self.xxx = ... しているので
    # ここでは不要だが、念のため属性を上書きしておく）
    for k, v in session_vars.items():
        setattr(instance, k, v)

    try:
        instance.run()
    except Exception as e:
        return session_vars, f"Runtime error: {e}"

    updated = _extract_vars(instance)
    return updated, None


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
                    print(f"  {k} = {v!r}")
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

        # ブロックが開いている間は続けて読む
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

        # ── parse & codegen ───────────────────
        py_code, err = _to_py(source, session_vars)
        if err:
            print(err)
            continue

        last_py_code = py_code

        # ── 実行 ─────────────────────────────
        session_vars, err = _execute(py_code, session_vars)
        if err:
            print(err)


if __name__ == "__main__":
    run_repl()
