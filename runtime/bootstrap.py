# runtime/bootstrap.py
#
# 【import の解決フロー】
#
#   to_python() が生成したコードには、.scs ファイルの import が
#   特殊コメントとして埋め込まれている:
#
#       # __scs_import__: utils.scs
#
#   run_main() はこのコメントを検出し、
#   1. utils.scs を読み込む
#   2. parse → to_python で Python コードを生成する
#   3. そのコードを「依存コード」として本体の前に exec する
#   4. 循環 import を visited set で防ぐ
#
#   Python stdlib の import は通常の Python 文としてそのまま exec される。

import re
from pathlib import Path
from compiler.error import SyscomRuntimeError

# .scs import を示す特殊コメントのパターン
_SCS_IMPORT_RE = re.compile(r"^# __scs_import__: (.+)$", re.MULTILINE)


def _resolve_scs_imports(
    py_code: str,
    base_dir: Path,
    namespace: dict,
    visited: set[str],
) -> None:
    """
    py_code 内の # __scs_import__: <path> を再帰的に解決して namespace に注入する。
    visited: 循環 import を防ぐための既処理ファイルパスの集合
    """
    # ここで初めて compiler モジュールを import する（循環 import 回避のため遅延 import）
    from compiler.parser import parse
    from compiler.transformer import to_python

    for match in _SCS_IMPORT_RE.finditer(py_code):
        rel_path = match.group(1).strip()
        abs_path = (base_dir / rel_path).resolve()
        path_key = str(abs_path)

        if path_key in visited:
            raise SyscomRuntimeError(
                message=f"Circular import detected: {rel_path}",
            )
        visited.add(path_key)

        if not abs_path.exists():
            raise SyscomRuntimeError(
                message=f"Import file not found: {rel_path}",
            )

        source = abs_path.read_text(encoding="utf-8")

        try:
            tree = parse(source)
        except Exception as e:
            raise SyscomRuntimeError(
                message=f"Syntax error in {rel_path}: {e}",
            )

        dep_py_code = to_python(tree)

        # 依存ファイルも再帰的に解決する（依存の依存）
        dep_base_dir = abs_path.parent
        _resolve_scs_imports(dep_py_code, dep_base_dir, namespace, visited)

        # 依存コードを exec して namespace にクラスを登録する
        # __scs_import__ コメント行は Python として無害なのでそのまま exec できる
        try:
            exec(dep_py_code, namespace)
        except Exception as e:
            raise SyscomRuntimeError(
                message=f"Error executing {rel_path}: {e}",
            )


def run_main(py_code: str, source_path: str | None = None) -> None:
    """
    py_code を実行する。
    source_path が指定された場合、.scs import の解決に使うベースディレクトリを決定する。
    """
    namespace: dict = {}

    # ① .scs ファイルの import を解決して namespace にクラスを注入する
    base_dir = Path(source_path).parent if source_path else Path.cwd()
    visited: set[str] = set()
    _resolve_scs_imports(py_code, base_dir, namespace, visited)

    # ② メインコードを exec する（stdlib の import 文もここで処理される）
    try:
        exec(py_code, namespace)
    except Exception as e:
        raise RuntimeError(f"Execution error: {e}") from e

    # ③ Main クラスを取り出して run() を呼ぶ
    if "Main" not in namespace:
        raise RuntimeError("Main class not found")

    main = namespace["Main"]()

    if not hasattr(main, "run"):
        raise RuntimeError("run() not found in Main class")

    main.run()
