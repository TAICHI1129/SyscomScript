from lark import Tree, Token

# Python 標準ライブラリの許可リスト
# これ以外のモジュール名が import されたときは .scs ファイルとして扱う
STDLIB_MODULES = {
    "math", "random", "sys", "os", "time", "datetime",
    "json", "re", "string", "collections", "itertools",
    "functools", "pathlib", "io",
}


def to_python(tree: Tree) -> str:
    """
    program ノードを受け取り Python コード文字列を返す。

    program は (import_stmt | class_def)+ で構成される。
    import_stmt は Python コードの先頭行に、class_def はその後ろに出力する。

    戻り値の構造:
        import math          ← Python stdlib の import
        import random        ← 同上
                             ← (blank line)
        class Util:          ← .scs から取り込んだクラス（bootstrap が注入）
            ...
        class Main:          ← メインクラス
            ...
    """
    import_lines: list[str] = []   # Python の import 文
    scs_imports:  list[str] = []   # .scs ファイルパス（bootstrap が処理する）
    class_lines:  list[str] = []   # クラス定義

    for node in tree.children:
        if not isinstance(node, Tree):
            continue

        if node.data == "import_stmt":
            token = node.children[0]
            token_str = str(token)

            if token.type == "STRING":
                # import "utils.scs" — .scs ファイルの import
                # 文字列リテラルの前後の " を除く
                path = token_str.strip('"').strip("'")
                scs_imports.append(path)
            else:
                # import math — Python 標準ライブラリの import
                module_name = token_str
                import_lines.append(f"import {module_name}")

        elif node.data == "class_def":
            _collect_class(node, class_lines)

    # 結合: import 行 + 空行 + クラス定義
    parts: list[str] = []
    if import_lines:
        parts.extend(import_lines)
        parts.append("")  # 空行

    # .scs ファイルのパスを特殊コメントとして埋め込む
    # bootstrap がこれを読み取って別ファイルを parse・注入する
    for path in scs_imports:
        parts.append(f"# __scs_import__: {path}")

    if scs_imports:
        parts.append("")

    parts.extend(class_lines)

    return "\n".join(parts)


def _collect_class(class_node: Tree, lines: list[str]):
    """class_def ノードを Python クラス定義に変換して lines に追加する"""
    indent = "    "
    class_name = str(class_node.children[0])
    lines.append(f"class {class_name}:")

    class_body = class_node.children[1]

    for item in class_body.children:
        if not isinstance(item, Tree):
            continue

        if item.data == "method_def":
            method_name = str(item.children[0])
            body = item.children[1]
            lines.append(f"{indent}def {method_name}(self):")
            walk_block(body, lines, indent, level=2)

        elif item.data == "func_def":
            func_name = str(item.children[0])
            param_node = item.children[1] if len(item.children) > 2 else None
            params = []
            if param_node and isinstance(param_node, Tree) and param_node.data == "param_list":
                params = [str(p) for p in param_node.children]
            body = item.children[-1]
            all_params = ["self"] + params
            lines.append(f"{indent}def {func_name}({', '.join(all_params)}):")
            walk_block(body, lines, indent, level=2)

    lines.append("")


def walk_block(block_node: Tree, lines: list, indent: str, level: int):
    pad = indent * level
    has_stmts = False

    for stmt in block_node.children:
        if isinstance(stmt, Tree):
            walk_stmt(stmt, lines, indent, level)
            has_stmts = True

    if not has_stmts:
        lines.append(f"{pad}pass")


def walk_stmt(node: Tree, lines: list, indent: str, level: int):
    pad = indent * level

    if node.data == "print_stmt":
        expr = node.children[0]
        lines.append(f"{pad}print({expr_to_py(expr)})")

    elif node.data == "assign":
        name = node.children[0]
        expr = node.children[1]
        lines.append(f"{pad}{name} = {expr_to_py(expr)}")

    elif node.data == "if_stmt":
        cond = node.children[0]
        then_block = node.children[1]
        lines.append(f"{pad}if {expr_to_py(cond)}:")
        walk_block(then_block, lines, indent, level + 1)
        if len(node.children) == 3:
            else_block = node.children[2]
            lines.append(f"{pad}else:")
            walk_block(else_block, lines, indent, level + 1)

    elif node.data == "while_stmt":
        cond = node.children[0]
        body = node.children[1]
        lines.append(f"{pad}while {expr_to_py(cond)}:")
        walk_block(body, lines, indent, level + 1)

    elif node.data == "return_stmt":
        if node.children:
            ret_expr = node.children[0]
            lines.append(f"{pad}return {expr_to_py(ret_expr)}")
        else:
            lines.append(f"{pad}return")

    elif node.data == "func_call_stmt":
        lines.append(f"{pad}self.{expr_to_py(node.children[0])}")

    else:
        for c in node.children:
            if isinstance(c, Tree):
                walk_stmt(c, lines, indent, level)


def expr_to_py(expr):
    if isinstance(expr, Token):
        return str(expr)
    elif isinstance(expr, Tree):
        if expr.data == "add":
            return f"({expr_to_py(expr.children[0])} + {expr_to_py(expr.children[1])})"
        elif expr.data == "sub":
            return f"({expr_to_py(expr.children[0])} - {expr_to_py(expr.children[1])})"
        elif expr.data == "lt":
            return f"({expr_to_py(expr.children[0])} < {expr_to_py(expr.children[1])})"
        elif expr.data == "gt":
            return f"({expr_to_py(expr.children[0])} > {expr_to_py(expr.children[1])})"
        elif expr.data == "eq":
            return f"({expr_to_py(expr.children[0])} == {expr_to_py(expr.children[1])})"
        elif expr.data == "func_call":
            func_name = expr.children[0]
            args = []
            if len(expr.children) > 1:
                args_node = expr.children[1]
                args = [expr_to_py(a) for a in args_node.children]
            return f"self.{func_name}({', '.join(args)})"
        else:
            raise TypeError(f"Unsupported expr node: {expr}")
    else:
        raise TypeError(f"Unsupported expr type: {type(expr)}")
