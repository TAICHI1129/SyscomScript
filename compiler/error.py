class SyscomError(Exception):
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


class SyscomSyntaxError(SyscomError):
    """Raised during parsing."""
    pass


class SyscomRuntimeError(SyscomError):
    """Raised during execution."""
    pass


def friendly_runtime_error(exc: Exception) -> SyscomRuntimeError:
    name = type(exc).__name__
    msg  = str(exc)

    if isinstance(exc, NameError):
        var = msg.replace("name ", "").replace(" is not defined", "").strip("'\" ")
        return SyscomRuntimeError(f"variable '{var}' is not defined")

    if isinstance(exc, TypeError):
        if "can only concatenate" in msg or "unsupported operand" in msg:
            return SyscomRuntimeError(
                f"type error: cannot apply operator to these types\n  detail: {msg}"
            )
        if "takes" in msg and "argument" in msg:
            return SyscomRuntimeError(f"wrong number of arguments: {msg}")
        return SyscomRuntimeError(f"type error: {msg}")

    if isinstance(exc, ZeroDivisionError):
        return SyscomRuntimeError("division by zero")

    if isinstance(exc, RecursionError):
        return SyscomRuntimeError("recursion limit exceeded (infinite loop or recursive call?)")

    if isinstance(exc, AttributeError):
        return SyscomRuntimeError(f"attribute error: {msg}")

    if isinstance(exc, IndexError):
        return SyscomRuntimeError(f"index out of range: {msg}")

    return SyscomRuntimeError(f"{name}: {msg}")
