import sys
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main
from compiler.error import SyscomSyntaxError

def main():
    if len(sys.argv) < 2:
        print("Usage: python syscom.py <file.scs> [--debug-python]")
        return

    path = sys.argv[1]
    debug = "--debug-python" in sys.argv

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()

        tree = parse(source)
        py_code = to_python(tree)

        # デバッグ用（--debug-python のときだけ表示）
        if debug:
            print("=== Generated Python ===")
            print(py_code)
            print("========================")

        run_main(py_code)

    except SyscomSyntaxError as e:
        # 旧 Lark の長い Traceback ではなく、1行でわかるエラー表示
        print(e)

    except FileNotFoundError:
        print(f"File not found: {path}")

    except Exception as e:
        # 想定外のエラーは通常 Traceback
        print("Unexpected error:")
        raise e

if __name__ == "__main__":
    main()
