from flask import Flask, request, jsonify, send_from_directory
import io
import sys
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main
from compiler.error import SyscomSyntaxError, SyscomRuntimeError

app = Flask(__name__, static_folder=".")

@app.route("/")
def index():
    return send_from_directory(".", "syscom.html")

@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "")
    debug = data.get("debug", False)

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()

    try:
        tree = parse(code)
        py_code = to_python(tree)

        if debug:
            buf.write("=== Generated Python ===\n")
            buf.write(py_code + "\n")
            buf.write("========================\n")

        run_main(py_code)

    except (SyscomSyntaxError, SyscomRuntimeError) as e:
        buf.write(str(e) + "\n")

    except Exception as e:
        buf.write(f"Unexpected error: {e}\n")

    finally:
        sys.stdout = old_stdout

    return jsonify(output=buf.getvalue())


if __name__ == "__main__":
    # waitress がインストールされていればそちらを使う（警告なし・安定）
    # インストール: pip install waitress
    try:
        from waitress import serve
        print("SyscomScript IDE running at http://localhost:8000")
        print("Press Ctrl + C to stop.")
        serve(app, host="127.0.0.1", port=8000)
    except ImportError:
        # waitress がなければ Flask の開発サーバーにフォールバック
        import logging
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        print("SyscomScript IDE running at http://localhost:8000")
        print("Press Ctrl + C to stop.")
        print("(tip: pip install waitress to suppress this fallback)")
        app.run(port=8000)
