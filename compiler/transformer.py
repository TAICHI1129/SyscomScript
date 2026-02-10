from lark import Tree, Token

def to_python(tree: Tree) -> str:
    lines = []
    lines.append("class Main:")
    lines.append("    def run(self):")

    indent = "    "

    def walk(node, level=1):
        pad = indent * level

        if isinstance(node, Tree):
            # print文
            if node.data == "print_stmt":
                expr = node.children[0]
                lines.append(pad + "print(" + expr_to_py(expr) + ")")

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
                if len(node.children) == 3:  # elseあり
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

            # 子ノードを再帰
            for c in node.children:
                walk(c, level)

    walk(tree)

    if len(lines) == 2:
        lines.append(indent + "    pass")

    return "\n".join(lines)


def expr_to_py(expr):
    if isinstance(expr, Token):
        if expr.type == "STRING":
            return str(expr)
        else:
            return str(expr)
    raise TypeError(f"Unsupported expr node: {expr}")
