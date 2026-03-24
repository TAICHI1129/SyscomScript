"""
compiler/transformer.py

Lark の Transformer 基底クラスを使い、ノード名でメソッドを自動ディスパッチする。
以前の手書き if/elif チェーンと比べて:
  - 新しいノードを追加するときはメソッドを一つ追加するだけでよい
  - 未知ノードは transformer_default() で即座に例外を出す
  - 引数取り出しロジックを _extract_args() に集約して重複を排除した
"""

from __future__ import annotations
from lark import Transformer, Token, Tree, v_args


# ──────────────────────────────────────────────────────────
# ヘルパー
# ──────────────────────────────────────────────────────────

def _extract_args(children: list, arg_index: int) -> list[str]:
    """children[arg_index] が arg_list ノードならその要素を返す。なければ空リスト。"""
    if arg_index < len(children) and isinstance(children[arg_index], Tree):
        return list(children[arg_index].children)
    return []


def _indent(level: int, indent: str = "    ") -> str:
    return indent * level


# ──────────────────────────────────────────────────────────
# 式トランスフォーマー（Lark Transformer を継承）
# ──────────────────────────────────────────────────────────
# v_args(inline=True) で children リストではなく *args として受け取る

@v_args(inline=True)
class _ExprTransformer(Transformer):
    """AST の式ノードを Python コード文字列へ変換する。"""

    # ── リテラル / 識別子 ──────────────────────────────

    def STRING(self, tok):   return str(tok)
    def NUMBER(self, tok):   return str(tok)
    def NAME(self, tok):     return str(tok)

    # ── 二項演算子 ────────────────────────────────────

    def mul(self, l, r):      return f"({l} * {r})"
    def div(self, l, r):      return f"({l} / {r})"
    def mod(self, l, r):      return f"({l} % {r})"
    def add(self, l, r):      return f"({l} + {r})"
    def sub(self, l, r):      return f"({l} - {r})"
    def lt(self, l, r):       return f"({l} < {r})"
    def gt(self, l, r):       return f"({l} > {r})"
    def lte(self, l, r):      return f"({l} <= {r})"
    def gte(self, l, r):      return f"({l} >= {r})"
    def eq(self, l, r):       return f"({l} == {r})"
    def ne(self, l, r):       return f"({l} != {r})"
    def and_expr(self, l, r): return f"({l} and {r})"
    def or_expr(self, l, r):  return f"({l} or {r})"

    # ── 単項演算子 ────────────────────────────────────

    def neg(self, num):       return f"(-{num})"
    def not_expr(self, expr): return f"(not {expr})"

    # ── 式中の関数呼び出し: foo(args) → self.foo(args) ──

    def func_call(self, name, *rest):
        # rest[0] は arg_list ノード（存在する場合）
        args = list(rest[0].children) if rest else []
        return f"self.{name}({', '.join(args)})"

    def arg_list(self, *args):
        # children はすでに文字列に変換済み
        return Tree("arg_list", list(args))

    # ── py.module.func(args) ──────────────────────────

    def py_call(self, py_path, *rest):
        dotted = ".".join(str(t) for t in py_path.children)
        args = list(rest[0].children) if rest else []
        return f"{dotted}({', '.join(args)})"

    def py_path(self, *names):
        return Tree("py_path", list(names))

    # ── obj.method(args) ─────────────────────────────

    def obj_call(self, obj, method, *rest):
        args = list(rest[0].children) if rest else []
        return f"{obj}.{method}({', '.join(args)})"

    # ── リスト ───────────────────────────────────────

    def list_expr(self, *rest):
        items = list(rest[0].children) if rest else []
        return f"[{', '.join(items)}]"

    def list_items(self, *items):
        return Tree("list_items", list(items))

    # ── インデックスアクセス ──────────────────────────

    def index_expr(self, target, index):
        return f"{target}[{index}]"

    # ── 未知ノードは即例外（サイレント無視を防ぐ） ──

    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"_ExprTransformer: unknown expr node '{data}'. "
            "文法を追加した場合は transformer.py にも対応メソッドを追加してください。"
        )


# ──────────────────────────────────────────────────────────
# 文・クラス生成（ウォーカー）
# ──────────────────────────────────────────────────────────

class _CodeGen:
    """変換済み式文字列を受け取り、Python コード行を生成する。"""

    INDENT = "    "

    def __init__(self):
        self._expr = _ExprTransformer()

    def expr(self, node) -> str:
        """式ノード（または Token）を Python 文字列に変換する。"""
        if isinstance(node, Token):
            return str(node)
        return self._expr.transform(Tree(node.data, node.children, node._meta
                                         if hasattr(node, "_meta") else None))

    # ── プログラム全体 ────────────────────────────────

    def program(self, tree) -> str:
        import_lines: list[str] = []
        scs_imports:  list[str] = []
        class_lines:  list[str] = []

        for node in tree.children:
            if not isinstance(node, Tree):
                continue
            if node.data == "import_stmt":
                tok = node.children[0]
                if tok.type == "STRING":
                    scs_imports.append(str(tok).strip('"').strip("'"))
                else:
                    import_lines.append(f"import {tok}")
            elif node.data == "class_def":
                self._collect_class(node, class_lines)

        parts: list[str] = []
        if import_lines:
            parts.extend(import_lines)
            parts.append("")
        for path in scs_imports:
            parts.append(f"# __scs_import__: {path}")
        if scs_imports:
            parts.append("")
        parts.extend(class_lines)
        return "\n".join(parts)

    # ── クラス ───────────────────────────────────────

    def _collect_class(self, class_node: Tree, lines: list[str]) -> None:
        pad = self.INDENT
        class_name = str(class_node.children[0])
        lines.append(f"class {class_name}:")

        for item in class_node.children[1].children:
            if not isinstance(item, Tree):
                continue
            if item.data == "method_def":
                method_name = str(item.children[0])
                lines.append(f"{pad}def {method_name}(self):")
                self._walk_block(item.children[1], lines, level=2)

            elif item.data == "func_def":
                func_name  = str(item.children[0])
                param_node = item.children[1] if len(item.children) > 2 else None
                params: list[str] = []
                if isinstance(param_node, Tree) and param_node.data == "param_list":
                    params = [str(p) for p in param_node.children]
                body = item.children[-1]
                all_params = ["self"] + params
                lines.append(f"{pad}def {func_name}({', '.join(all_params)}):")
                self._walk_block(body, lines, level=2)

            else:
                raise NotImplementedError(
                    f"_collect_class: unknown class body node '{item.data}'"
                )

        lines.append("")

    # ── ブロック ─────────────────────────────────────

    def _walk_block(self, block_node: Tree, lines: list[str], level: int) -> None:
        pad = _indent(level)
        stmts = [n for n in block_node.children if isinstance(n, Tree)]
        if not stmts:
            lines.append(f"{pad}pass")
            return
        for stmt in stmts:
            self._walk_stmt(stmt, lines, level)

    # ── 文 ───────────────────────────────────────────

    def _walk_stmt(self, node: Tree, lines: list[str], level: int) -> None:
        pad = _indent(level)

        match node.data:

            case "print_stmt":
                lines.append(f"{pad}print({self.expr(node.children[0])})")

            case "assign":
                lines.append(
                    f"{pad}{node.children[0]} = {self.expr(node.children[1])}"
                )

            case "if_stmt":
                cond, then_block, chain = (
                    node.children[0], node.children[1], node.children[2]
                )
                lines.append(f"{pad}if {self.expr(cond)}:")
                self._walk_block(then_block, lines, level + 1)
                self._walk_elif_chain(chain, lines, level)

            case "while_stmt":
                lines.append(f"{pad}while {self.expr(node.children[0])}:")
                self._walk_block(node.children[1], lines, level + 1)

            case "for_stmt":
                # range() 引数が可変長（1〜3個）に対応
                # children: [NAME, expr..., block]
                var   = str(node.children[0])
                body  = node.children[-1]
                range_args = [
                    self.expr(c)
                    for c in node.children[1:-1]
                    if isinstance(c, Tree) or isinstance(c, Token)
                ]
                lines.append(
                    f"{pad}for {var} in range({', '.join(range_args)}):"
                )
                self._walk_block(body, lines, level + 1)

            case "return_stmt":
                if node.children:
                    lines.append(f"{pad}return {self.expr(node.children[0])}")
                else:
                    lines.append(f"{pad}return")

            case "func_call_stmt":
                # expr_to_py に委譲して重複実装を排除（self. は expr 側で付く）
                fc = node.children[0]
                lines.append(f"{pad}{self.expr(fc)}")

            case _:
                raise NotImplementedError(
                    f"_walk_stmt: unknown stmt node '{node.data}'. "
                    "文法を追加した場合は transformer.py にも対応を追加してください。"
                )

    # ── elif チェーン ─────────────────────────────────

    def _walk_elif_chain(self, chain: Tree, lines: list[str], level: int) -> None:
        pad = _indent(level)
        ch  = chain.children
        i   = 0
        while i < len(ch):
            child = ch[i]
            if isinstance(child, Tree) and child.data == "block":
                lines.append(f"{pad}else:")
                self._walk_block(child, lines, level + 1)
                i += 1
            else:
                elif_cond  = ch[i]
                elif_block = ch[i + 1]
                lines.append(f"{pad}elif {self.expr(elif_cond)}:")
                self._walk_block(elif_block, lines, level + 1)
                i += 2


# ──────────────────────────────────────────────────────────
# 公開 API
# ──────────────────────────────────────────────────────────

def to_python(tree) -> str:
    """AST（Lark Tree）を Python ソースコード文字列に変換する。"""
    return _CodeGen().program(tree)