from lark import Lark, UnexpectedToken, UnexpectedCharacters
from pathlib import Path
from compiler.error import SyscomSyntaxError

_GRAMMAR_PATH = Path(__file__).parent.parent / "grammar" / "syscom.lark"

# パーサを遅延初期化する（テスト等でカレントディレクトリが変わっても安全）
_parser: Lark | None = None


def _get_parser() -> Lark:
    global _parser
    if _parser is None:
        grammar = _GRAMMAR_PATH.read_text(encoding="utf-8")
        _parser = Lark(grammar, parser="lalr", propagate_positions=True)
    return _parser


def parse(code: str):
    try:
        return _get_parser().parse(code)
    except UnexpectedToken as e:
        raise SyscomSyntaxError(
            message=f"Unexpected token '{e.token}'",
            line=e.line,
            column=e.column,
        )
    except UnexpectedCharacters as e:
        raise SyscomSyntaxError(
            message=f"Unexpected character '{e.char}'",
            line=e.line,
            column=e.column,
        )