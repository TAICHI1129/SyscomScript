# compiler/error.py

class SyscomError(Exception):
    """
    SyscomScript 専用のエラークラス。
    line, column を指定するとどこで起きたかもわかる。
    """
    def __init__(self, message: str, line: int = None, column: int = None):
        super().__init__(message)
        self.line = line
        self.column = column

    def __str__(self):
        loc = ""
        if self.line is not None and self.column is not None:
            loc = f" at line {self.line}, column {self.column}"
        elif self.line is not None:
            loc = f" at line {self.line}"
        return f"SyscomError{loc}: {self.args[0]}"


# 例：構文エラー専用
class SyscomSyntaxError(SyscomError):
    """構文解析で発生するエラー"""
    pass


# 例：実行時エラー専用
class SyscomRuntimeError(SyscomError):
    """実行時に発生するエラー"""
    pass
