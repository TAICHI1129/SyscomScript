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
        lines.append(f"{pad}if {expr_to_py(node.children[0])}:")
        walk_block(node.children[1], lines, indent, level + 1)
        if len(node.children) == 3:
            lines.append(f"{pad}else:")
            walk_block(node.children[2], lines, indent, level + 1)

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
        lines.append(f"{pad}self.{expr_to_py(node.children[0])}")

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

    if expr.data == "not_expr":
        return f"(not {expr_to_py(expr.children[0])})"

    if expr.data == "func_call":
        func_name = expr.children[0]
        args = []
        if len(expr.children) > 1:
            args = [expr_to_py(a) for a in expr.children[1].children]
        return f"self.{func_name}({', '.join(args)})"

    raise TypeError(f"Unsupported expr node: {expr.data}")
