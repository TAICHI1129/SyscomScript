from lark import Lark
from pathlib import Path

grammar_path = Path(__file__).parent.parent / "grammar" / "syscom.lark"
grammar = grammar_path.read_text(encoding="utf-8")

_parser = Lark(grammar, parser="lalr", propagate_positions=True)

def parse(code: str):
    return _parser.parse(code)
