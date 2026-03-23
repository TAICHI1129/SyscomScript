import sys
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main
from compiler.error import SyscomSyntaxError

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--repl":
        from repl import run_repl
        run_repl()
        return

    path = sys.argv[1]
    debug = "--debug-python" in sys.argv

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()

        tree = parse(source)
        py_code = to_python(tree)

        if debug:
            print("=== Generated Python ===")
            print(py_code)
            print("========================")

        # source_path を渡すことで .scs import の基準ディレクトリが確定する
        run_main(py_code, source_path=path)

    except SyscomSyntaxError as e:
        print(e)

    except FileNotFoundError:
        print(f"File not found: {path}")

    except Exception as e:
        print("Unexpected error:")
        raise e

if __name__ == "__main__":
    main()
