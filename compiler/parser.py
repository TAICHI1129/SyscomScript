from lark import Lark, UnexpectedToken, UnexpectedCharacters
from pathlib import Path
from compiler.error import SyscomSyntaxError  # 新しく作ったエラークラス

# grammar 読み込み
grammar_path = Path(__file__).parent.parent / "grammar" / "syscom.lark"
grammar = grammar_path.read_text(encoding="utf-8")

_parser = Lark(grammar, parser="lalr", propagate_positions=True)

def parse(code: str):
    try:
        return _parser.parse(code)
    except UnexpectedToken as e:
        # トークンが予期せぬものだった場合
        raise SyscomSyntaxError(
            message=f"Unexpected token '{e.token}'",
            line=e.line,
            column=e.column
        )
    except UnexpectedCharacters as e:
        # 文字が予期せぬものだった場合
        raise SyscomSyntaxError(
            message=f"Unexpected character '{e.char}'",
            line=e.line,
            column=e.column
        )
