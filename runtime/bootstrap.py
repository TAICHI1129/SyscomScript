import re
from pathlib import Path
from compiler.error import SyscomRuntimeError, friendly_runtime_error

_SCS_IMPORT_RE    = re.compile(r"^# __scs_import__: (.+)$", re.MULTILINE)

# SCS_APP のファイルを検出する正規表現
# transformer が "SCS_APP/app.scs" → "app.scs" に短縮する場合も考慮し、
# app.scs / widgets.scs / events.scs のどれかにマッチすれば SCS_APP とみなす
_SCS_APP_IMPORT_RE = re.compile(
    r'^# __scs_import__: (?:SCS_APP/)?(?:app|widgets|events)\.scs$',
    re.MULTILINE,
)


def _load_scs_app_runtime(base_dir: Path, namespace: dict) -> None:
    """
    SCS_APP/_scs_app_runtime.py を探して namespace に exec する。
    見つからなければ SyscomRuntimeError を投げる。
    """
    candidates = [
        base_dir / "SCS_APP" / "_scs_app_runtime.py",
        Path.cwd() / "SCS_APP" / "_scs_app_runtime.py",
    ]
    for path in candidates:
        if path.exists():
            try:
                exec(path.read_text(encoding="utf-8"), namespace)
            except Exception as e:
                raise SyscomRuntimeError(
                    f"SCS_APP ランタイムの読み込みに失敗: {e}"
                )
            return
    raise SyscomRuntimeError(
        "SCS_APP/_scs_app_runtime.py が見つかりません。\n"
        "SCS_APP フォルダを .scs ファイルと同じ場所に置いてください。"
    )


def _resolve_scs_imports(
    py_code: str,
    base_dir: Path,
    namespace: dict,
    visited: set,
    scs_app_loaded: list,   # [bool] — 可変フラグ（リストで渡す）
) -> None:
    from compiler.parser import parse
    from compiler.transformer import to_python

    # SCS_APP/* の import が含まれていたらランタイムを一度だけロード
    if _SCS_APP_IMPORT_RE.search(py_code) and not scs_app_loaded[0]:
        _load_scs_app_runtime(base_dir, namespace)
        scs_app_loaded[0] = True

    for match in _SCS_IMPORT_RE.finditer(py_code):
        rel_path = match.group(1).strip()

        # SCS_APP の .scs ファイルはランタイムで処理済みなのでスキップ
        from pathlib import Path as _P
        if _P(rel_path).name in ("app.scs", "widgets.scs", "events.scs"):
            continue

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
        _resolve_scs_imports(
            dep_py_code, abs_path.parent, namespace, visited, scs_app_loaded
        )

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

    戻り値:
        実行後のセッション変数辞書（session_vars=None の場合は空辞書）
    """
    namespace: dict = {}

    base_dir = Path(source_path).parent if source_path else Path.cwd()
    _resolve_scs_imports(
        py_code, base_dir, namespace, visited=set(), scs_app_loaded=[False]
    )

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

    # REPL セッション変数を setattr で注入
    if session_vars:
        for k, v in session_vars.items():
            setattr(main, k, v)

    try:
        main.run()
    except SyscomRuntimeError:
        raise
    except Exception as e:
        raise friendly_runtime_error(e)

    # 実行後の変数を返す
    if session_vars is not None:
        return {k: v for k, v in main.__dict__.items() if not k.startswith("_")}
    return {}