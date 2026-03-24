import re
from pathlib import Path
from compiler.error import SyscomRuntimeError, friendly_runtime_error

_SCS_IMPORT_RE = re.compile(r"^# __scs_import__: (.+)$", re.MULTILINE)


def _resolve_scs_imports(
    py_code: str,
    base_dir: Path,
    namespace: dict,
    visited: set,
) -> None:
    from compiler.parser import parse
    from compiler.transformer import to_python

    for match in _SCS_IMPORT_RE.finditer(py_code):
        rel_path = match.group(1).strip()
        abs_path = (base_dir / rel_path).resolve()
        path_key = str(abs_path)

        if path_key in visited:
            raise SyscomRuntimeError(
                message=f"circular import detected: {rel_path}"
            )
        visited.add(path_key)

        if not abs_path.exists():
            raise SyscomRuntimeError(
                message=f"import file not found: {rel_path}"
            )

        source = abs_path.read_text(encoding="utf-8")

        try:
            tree = parse(source)
        except Exception as e:
            raise SyscomRuntimeError(
                message=f"syntax error in '{rel_path}': {e}"
            )

        dep_py_code = to_python(tree)
        _resolve_scs_imports(dep_py_code, abs_path.parent, namespace, visited)

        try:
            exec(dep_py_code, namespace)
        except Exception as e:
            raise friendly_runtime_error(e)


def run_main(
    py_code: str,
    source_path: str = None,
    session_vars: dict = None,
) -> dict:
    """
    py_code を実行して Main().run() を呼ぶ。

    session_vars:
        REPL から渡されるセッション変数辞書。
        None の場合は通常実行（変数の引き継ぎなし）。
        渡された場合は run() 前に setattr() で注入し、
        実行後に instance.__dict__ を返す。

    戻り値:
        実行後のセッション変数辞書（session_vars=None の場合は空辞書）
    """
    namespace: dict = {}

    base_dir = Path(source_path).parent if source_path else Path.cwd()
    _resolve_scs_imports(py_code, base_dir, namespace, visited=set())

    try:
        exec(py_code, namespace)
    except SyscomRuntimeError:
        raise
    except Exception as e:
        raise friendly_runtime_error(e)

    if "Main" not in namespace:
        raise SyscomRuntimeError("class 'Main' not found")

    main = namespace["Main"]()

    if not hasattr(main, "run"):
        raise SyscomRuntimeError("method 'run()' not found in class Main")

    # REPL セッション変数を setattr で注入（repr 不要・オブジェクトも安全）
    if session_vars:
        for k, v in session_vars.items():
            setattr(main, k, v)

    try:
        main.run()
    except SyscomRuntimeError:
        raise
    except Exception as e:
        raise friendly_runtime_error(e)

    # 実行後の変数を返す（_ で始まらないものすべて）
    if session_vars is not None:
        return {k: v for k, v in main.__dict__.items() if not k.startswith("_")}
    return {}