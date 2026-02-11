from lark import Tree, Token

def to_python(tree: Tree) -> str:
    lines = []
    indent = "    "
    lines.append("class Main:")
    lines.append(f"{indent}def run(self):")

    def walk(node, level=2):
        pad = indent * level

        if isinstance(node, Tree):
            # print文
            if node.data == "print_stmt":
                expr = node.children[0]
                lines.append(f"{pad}print({expr_to_py(expr)})")

            # 代入文
            elif node.data == "assign":
                name = node.children[0]
                expr = node.children[1]
                lines.append(f"{pad}{name} = {expr_to_py(expr)}")

            # if文
            elif node.data == "if_stmt":
                cond = node.children[0]
                then_block = node.children[1]
                lines.append(f"{pad}if {expr_to_py(cond)}:")
                walk(then_block, level + 1)
                if len(node.children) == 3:
                    else_block = node.children[2]
                    lines.append(f"{pad}else:")
                    walk(else_block, level + 1)

            # while文
            elif node.data == "while_stmt":
                cond = node.children[0]
                body = node.children[1]
                lines.append(f"{pad}while {expr_to_py(cond)}:")
                walk(body, level + 1)

            # return文
            elif node.data == "return_stmt":
                if node.children:
                    ret_expr = node.children[0]
                    lines.append(f"{pad}return {expr_to_py(ret_expr)}")
                else:
                    lines.append(f"{pad}return")

            # 関数定義
            elif node.data == "func_def":
                name = node.children[0]
                param_node = node.children[1] if len(node.children) > 2 else None
                params = []
                if param_node:
                    params = [str(p) for p in param_node.children]
                body = node.children[-1]
                lines.append(f"{pad}def {name}({', '.join(params)}):")
                walk(body, level + 1)

            # 関数呼び出し
            elif node.data == "func_call_stmt":
                lines.append(f"{pad}{expr_to_py(node.children[0])}")

            # 子ノードを再帰処理
            for c in node.children:
                if isinstance(c, Tree):
                    walk(c, level)

    walk(tree)

    if len(lines) == 2:
        lines.append(indent*2 + "pass")

    return "\n".join(lines)


def expr_to_py(expr):
    if isinstance(expr, Token):
        if expr.type == "STRING":
            return str(expr)
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
            return f"{func_name}({', '.join(args)})"
        else:
            raise TypeError(f"Unsupported expr node: {expr}")
    else:
        raise TypeError(f"Unsupported expr node: {expr}")
