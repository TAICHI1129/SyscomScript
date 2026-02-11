from flask import Flask, request, jsonify
import io
from compiler.parser import parse
from compiler.transformer import to_python
from runtime.bootstrap import run_main
from compiler.error import SyscomError

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    code = data.get("code", "")
    debug = data.get("debug", False)

    f = io.StringIO()
    try:
        # パースして Python コード生成
        tree = parse(code)
        py_code = to_python(tree)

        # デバッグ表示
        if debug:
            f.write("=== Generated Python ===\n")
            f.write(py_code + "\n")
            f.write("========================\n")

        # 実行
        run_main(py_code)
    except SyscomError as e:
        f.write(str(e) + "\n")
    except Exception as e:
        f.write(f"Unexpected Error: {e}\n")

    return jsonify(output=f.getvalue())

if __name__ == "__main__":
    app.run(port=8000)
