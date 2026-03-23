from lark import Tree, Token


def to_python(tree: Tree) -> str:
    import_lines: list[str] = []
    scs_imports:  list[str] = []
    class_lines:  list[str] = []

    for node in tree.children:
        if not isinstance(node, Tree):
            continue

        if node.data == "import_stmt":
            token = node.children[0]
            token_str = str(token)
            if token.type == "STRING":
                path = token_str.strip('"').strip("'")
                scs_imports.append(path)
            else:
                import_lines.append(f"import {token_str}")

        elif node.data == "class_def":
            _collect_class(node, class_lines)

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


def _collect_class(class_node: Tree, lines: list[str]):
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
        lines.append(f"{pad}print({expr_to_py(node.children[0])})")

    elif node.data == "assign":
        lines.append(f"{pad}{node.children[0]} = {expr_to_py(node.children[1])}")

    elif node.data == "if_stmt":
        cond       = node.children[0]
        then_block = node.children[1]
        chain      = node.children[2]

        lines.append(f"{pad}if {expr_to_py(cond)}:")
        walk_block(then_block, lines, indent, level + 1)

        chain_children = chain.children
        i = 0
        while i < len(chain_children):
            child = chain_children[i]
            if isinstance(child, Tree) and child.data == "block":
                lines.append(f"{pad}else:")
                walk_block(child, lines, indent, level + 1)
                i += 1
            else:
                elif_cond  = chain_children[i]
                elif_block = chain_children[i + 1]
                lines.append(f"{pad}elif {expr_to_py(elif_cond)}:")
                walk_block(elif_block, lines, indent, level + 1)
                i += 2

    elif node.data == "while_stmt":
        lines.append(f"{pad}while {expr_to_py(node.children[0])}:")
        walk_block(node.children[1], lines, indent, level + 1)

    elif node.data == "for_stmt":
        var  = str(node.children[0])
        end  = expr_to_py(node.children[1])
        body = node.children[2]
        lines.append(f"{pad}for {var} in range({end}):")
        walk_block(body, lines, indent, level + 1)

    elif node.data == "return_stmt":
        if node.children:
            lines.append(f"{pad}return {expr_to_py(node.children[0])}")
        else:
            lines.append(f"{pad}return")

    elif node.data == "func_call_stmt":
        # FIX: expr_to_py(func_call) は既に "self.foo(...)" を返すので
        #      ここで self. を付け直すと "self.self.foo(...)" になってしまう。
        #      func_call ノードを直接展開して self. を一度だけ付ける。
        fc = node.children[0]  # func_call ノード
        func_name = str(fc.children[0])
        args = []
        if len(fc.children) > 1 and isinstance(fc.children[1], Tree):
            args = [expr_to_py(a) for a in fc.children[1].children]
        lines.append(f"{pad}self.{func_name}({', '.join(args)})")

    else:
        for c in node.children:
            if isinstance(c, Tree):
                walk_stmt(c, lines, indent, level)


def expr_to_py(expr) -> str:
    if isinstance(expr, Token):
        return str(expr)

    if not isinstance(expr, Tree):
        raise TypeError(f"Unsupported expr type: {type(expr)}")

    BINOP = {
        "mul":      "*",
        "div":      "/",
        "mod":      "%",
        "add":      "+",
        "sub":      "-",
        "lt":       "<",
        "gt":       ">",
        "lte":      "<=",
        "gte":      ">=",
        "eq":       "==",
        "ne":       "!=",
        "and_expr": "and",
        "or_expr":  "or",
    }

    if expr.data in BINOP:
        op    = BINOP[expr.data]
        left  = expr_to_py(expr.children[0])
        right = expr_to_py(expr.children[1])
        return f"({left} {op} {right})"

    # py.path.to.func(args) → path.to.func(args)
    if expr.data == "py_call":
        py_path_node = expr.children[0]
        dotted = ".".join(str(t) for t in py_path_node.children)
        args = []
        if len(expr.children) > 1 and isinstance(expr.children[1], Tree):
            args = [expr_to_py(a) for a in expr.children[1].children]
        return f"{dotted}({', '.join(args)})"

    # obj.method(args) → variable.method(args)
    if expr.data == "obj_call":
        obj    = str(expr.children[0])
        method = str(expr.children[1])
        args   = []
        if len(expr.children) > 2 and isinstance(expr.children[2], Tree):
            args = [expr_to_py(a) for a in expr.children[2].children]
        return f"{obj}.{method}({', '.join(args)})"

    # 負数リテラル: -7 → (-7)
    if expr.data == "neg":
        return f"(-{str(expr.children[0])})"

    if expr.data == "not_expr":
        return f"(not {expr_to_py(expr.children[0])})"

    # 式中の関数呼び出し（右辺値）: foo(args) → self.foo(args)
    if expr.data == "func_call":
        func_name = str(expr.children[0])
        args = []
        if len(expr.children) > 1 and isinstance(expr.children[1], Tree):
            args = [expr_to_py(a) for a in expr.children[1].children]
        return f"self.{func_name}({', '.join(args)})"

    # リストリテラル: [1, 2, 3]
    if expr.data == "list_expr":
        if not expr.children:
            return "[]"
        items = [expr_to_py(item) for item in expr.children[0].children]
        return f"[{', '.join(items)}]"

    # インデックスアクセス: x[i]
    if expr.data == "index_expr":
        target = expr_to_py(expr.children[0])
        index  = expr_to_py(expr.children[1])
        return f"{target}[{index}]"

    raise TypeError(f"Unsupported expr node: {expr.data}")