from flask import Flask, request, jsonify
import sys
import io
from contextlib import redirect_stdout
from syscom import main as syscom_main, SyscomError

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    code = data.get("code", "")
    debug = data.get("debug", False)

    f = io.StringIO()
    try:
        # ここで syscom_main を直接呼ぶのは難しいので
        # parse+to_python+run_main を分けて呼ぶのが安全
        from compiler.parser import parse
        from compiler.transformer import to_python
        from runtime.bootstrap import run_main

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
