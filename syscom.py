import sys
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main

def main():
    if len(sys.argv) < 2:
        print("Usage: python syscom.py <file.scc>")
        return

    path = sys.argv[1]

    with open(path, encoding="utf-8") as f:
        source = f.read()

    tree = parse(source)
    py_code = to_python(tree)

    # デバッグ用（消してもいい）
    print("=== Generated Python ===")
    print(py_code)
    print("========================")

    run_main(py_code)

if __name__ == "__main__":
    main()
