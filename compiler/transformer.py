from lark import Tree, Token

def to_python(tree: Tree) -> str:
    lines = []
    lines.append("class Main:")
    lines.append("    def run(self):")

    def walk(node):
        if isinstance(node, Tree):
            # print文
            if node.data == "print_stmt":
                expr = node.children[0]
                lines.append("        print(" + expr_to_py(expr) + ")")

            # 代入文
            elif node.data == "assign":
                name = node.children[0]
                expr = node.children[1]
                lines.append(f"        {name} = {expr_to_py(expr)}")

            for c in node.children:
                walk(c)

    walk(tree)

    if len(lines) == 2:
        lines.append("        pass")

    return "\n".join(lines)


def expr_to_py(expr):
    if isinstance(expr, Token):
        return str(expr)
    raise TypeError(f"Unsupported expr node: {expr}")
