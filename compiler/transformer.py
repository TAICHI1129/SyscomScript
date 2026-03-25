"""
compiler/transformer.py
"""

from __future__ import annotations
from lark import Transformer, Token, Tree, v_args


def _indent(level: int, indent: str = "    ") -> str:
    return indent * level


@v_args(inline=True)
class _ExprTransformer(Transformer):
    """AST の式ノードを Python コード文字列へ変換する。"""

    # ── リテラル / 識別子 ──────────────────────────────

    def STRING(self, tok):    return str(tok)
    def NUMBER(self, tok):    return str(tok)
    def NAME(self, tok):      return str(tok)
    def bool_true(self):      return "True"
    def bool_false(self):     return "False"

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
    def neg(self, num):       return f"(-{num})"
    def not_expr(self, expr): return f"(not {expr})"

    # ── 型変換: int(x) str(x) float(x) bool(x) ──────

    def cast_expr(self, type_tok, expr_str):
        # grammar: ("int"|"str"|"float"|"bool") "(" expr ")"
        # type_tok = Token('__ANON', 'int') などのキーワードトークン
        return f"{type_tok}({expr_str})"

    # ── 式中の関数呼び出し ────────────────────────────

    def func_call(self, name, *rest):
        args = list(rest[0].children) if rest else []
        return f"self.{name}({', '.join(args)})"

    def arg_list(self, *args):
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

    # ── dict ─────────────────────────────────────────

    def dict_expr(self, *rest):
        if not rest:
            return "{}"
        pairs = rest[0].children  # dict_pair ノードのリスト
        items = [f"{p.children[0]}: {p.children[1]}" for p in pairs]
        return "{" + ", ".join(items) + "}"

    def dict_items(self, *pairs):
        return Tree("dict_items", list(pairs))

    def dict_pair(self, key, val):
        return Tree("dict_pair", [key, val])

    # ── インデックスアクセス ──────────────────────────

    def index_expr(self, target, index):
        return f"{target}[{index}]"

    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"_ExprTransformer: unknown expr node '{data}'."
        )


class _CodeGen:
    INDENT = "    "

    def __init__(self):
        self._expr = _ExprTransformer()

    def expr(self, node) -> str:
        if isinstance(node, Token):
            return str(node)
        return self._expr.transform(
            Tree(node.data, node.children,
                 node._meta if hasattr(node, "_meta") else None)
        )

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

    def _walk_block(self, block_node: Tree, lines: list[str], level: int) -> None:
        pad = _indent(level)
        stmts = [n for n in block_node.children if isinstance(n, Tree)]
        if not stmts:
            lines.append(f"{pad}pass")
            return
        for stmt in stmts:
            self._walk_stmt(stmt, lines, level)

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
                var  = str(node.children[0])
                body = node.children[-1]
                range_args = [
                    self.expr(c)
                    for c in node.children[1:-1]
                    if isinstance(c, (Tree, Token))
                ]
                lines.append(f"{pad}for {var} in range({', '.join(range_args)}):")
                self._walk_block(body, lines, level + 1)

            case "return_stmt":
                if node.children:
                    lines.append(f"{pad}return {self.expr(node.children[0])}")
                else:
                    lines.append(f"{pad}return")

            case "func_call_stmt":
                fc = node.children[0]
                lines.append(f"{pad}{self.expr(fc)}")

            case _:
                raise NotImplementedError(
                    f"_walk_stmt: unknown stmt node '{node.data}'."
                )

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


def to_python(tree) -> str:
    return _CodeGen().program(tree)