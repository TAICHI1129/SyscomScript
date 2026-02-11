from flask import Flask, request, jsonify
import io
from contextlib import redirect_stdout
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main
import traceback

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
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

        with redirect_stdout(f):
            run_main(py_code)

    except Exception:
        f.write("ERROR:\n")
        f.write(traceback.format_exc())

    return jsonify(output=f.getvalue())

if __name__ == "__main__":
    app.run(port=8000)
