from flask import Flask, request, jsonify, send_from_directory
import io
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main

app = Flask(__name__, static_folder=".")

# IDEを開くためのルート
@app.route("/")
def index():
    return send_from_directory(".", "ide.html")

# Syscomコードを実行するAPI
@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "")
    debug = data.get("debug", False)

    f = io.StringIO()
    try:
        tree = parse(code)
        py_code = to_python(tree)
        if debug:
            f.write("=== Generated Python ===\n")
            f.write(py_code + "\n")
            f.write("========================\n")
        run_main(py_code)
    except Exception as e:
        f.write(str(e))

    return jsonify(output=f.getvalue())

if __name__ == "__main__":
    app.run(port=8000)
