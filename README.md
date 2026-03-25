# SyscomScript

SyscomScript is a class-based, educational programming language that transpiles to Python. Write `.scs` files and run them immediately — no separate compile step required.

## Features

- Simple class-based syntax
- Transpiles to Python and runs immediately
- REPL (interactive mode) for quick experimentation
- Web-based IDE (`ide.py`)
- Import Python standard libraries (`import math`) and call them via `py.module.func()`
- Call deeply nested Python APIs with `py.os.path.join()`, `py.subprocess.run()`, etc.
- Import other `.scs` files (`import "utils.scs"`) and call methods via `obj.method()`
- `--debug-python` flag to inspect generated Python code

## Requirements

- Python 3.10 or later
- [lark](https://github.com/lark-parser/lark) (`pip install lark`)
- [flask](https://flask.palletsprojects.com/) (`pip install flask`) — required for the IDE
- [waitress](https://docs.pylonsproject.org/projects/waitress/) (`pip install waitress`) — required for the IDE (production-grade server for Flask)

## Installation

```bat
git clone https://github.com/TAICHI1129/SyscomScript.git
cd SyscomScript
pip install lark flask waitress
```

Running version_update.bat will replace it with the latest version.

## How to Run a File

**Option 1 — Double-click `run.bat`**

Place your `.scs` file in the `code\` folder, then double-click `run.bat`. Available files are listed automatically — just type the file name and press Enter.

```
================================
   SyscomScript Runner
================================

Available files in code\:

  hello.scs
  myprogram.scs

Enter file name (e.g. hello.scs): hello.scs

Running code\hello.scs ...
--------------------------------
Hello
--------------------------------
```

**Option 2 — Command line**

```bat
python syscom.py code\(file-name).scs
```

Example:

```bat
python syscom.py examples\hello.scs
```

To inspect the generated Python code, add `--debug-python`:

```bat
python syscom.py examples\hello.scs --debug-python
```

## How to Use the IDE

```bat
python ide.py
```

Then open http://localhost:8000 in your browser.

- Write SyscomScript in the left editor pane
- Click **Run** (or press `Ctrl+Enter`) to execute
- Output appears in the right pane
- Check **Show Python** to inspect the generated Python code
- `Tab` inserts 4 spaces for indentation

## How to Use the REPL

Launch the interactive mode by running with no arguments or with `--repl`:

```bat
python syscom.py
python syscom.py --repl
```

REPL commands:

| Command  | Description                        |
|----------|------------------------------------|
| `:vars`  | Show all current session variables |
| `:clear` | Reset the session                  |
| `:debug` | Show last generated Python code    |
| `:help`  | Show help                          |
| `exit`   | Quit the REPL                      |

## Language Overview

Every program starts from `class Main` and its `run()` method.

```scs
class Main {
    run() {
        print("Hello, World!")
    }
}
```

### Variables and arithmetic

```scs
class Main {
    run() {
        x = 10
        y = 3
        print(x + y)
        print(x - y)
        print(x * y)
        print(x / y)
        print(x % y)
    }
}
```

### Negative numbers

```scs
class Main {
    run() {
        x = -5
        print(x)
    }
}
```

### If / Else if / Else

```scs
class Main {
    run() {
        x = 5
        if (x > 10) {
            print("big")
        } else if (x > 3) {
            print("medium")
        } else {
            print("small")
        }
    }
}
```

### While loop

```scs
class Main {
    run() {
        x = 0
        while (x < 3) {
            print(x)
            x = x + 1
        }
    }
}
```

### For loop

```scs
class Main {
    run() {
        for i in range(5) {
            print(i)
        }
    }
}
```

### Lists

```scs
class Main {
    run() {
        nums = [10, 20, 30]
        print(nums[0])

        for i in range(3) {
            print(nums[i])
        }
    }
}
```

### Operators

```scs
class Main {
    run() {
        x = 5
        if (x >= 3 and x <= 10) {
            print("in range")
        }
        if (x != 0) {
            print("not zero")
        }
        if (not x == 0) {
            print("also not zero")
        }
    }
}
```

### Functions

```scs
class Main {
    run() {
        result = add(3, 4)
        print(result)
    }

    func add(a, b) {
        return a + b
    }
}
```

### Import a Python standard library

Use `import` to load a Python module, then call its functions with `py.<path>(<args>)`.
The path can be any number of dot-separated names, so you can reach nested APIs like `os.path.join`.

```scs
import math

class Main {
    run() {
        x = py.math.sqrt(16)
        print(x)

        y = py.math.floor(3.7)
        print(y)
    }
}
```

**Deeply nested calls (3+ segments):**

```scs
import os

class Main {
    run() {
        joined = py.os.path.join("mydir", "file.txt")
        print(joined)

        cwd = py.os.getcwd()
        print(cwd)
    }
}
```

**File I/O:**

```scs
class Main {
    run() {
        f = py.open("hello.txt", "w")
        f.write("Hello from SyscomScript!")
        f.close()
    }
}
```

**Running system commands:**

```scs
import subprocess

class Main {
    run() {
        py.subprocess.run(["echo", "hello"])
    }
}
```

### Import another `.scs` file

Define classes in a separate `.scs` file, import it, and call methods with `obj.method(args)`.

```scs
// mathlib.scs
class MathLib {
    func square(n) {
        return n * n
    }
}
```

```scs
// main.scs
import "mathlib.scs"

class Main {
    run() {
        lib = MathLib()
        print(lib.square(5))
    }
}
```

## Project Structure

```
SyscomScript/
├── syscom.py              # Entry point
├── run.bat                # Double-click runner
├── ide.py                 # IDE server (Flask + waitress)
├── syscom.html            # IDE frontend
├── repl.py                # Interactive REPL
├── grammar/
│   └── syscom.lark        # Language grammar (Lark EBNF)
├── compiler/
│   ├── parser.py          # Parses .scs source into AST
│   ├── transformer.py     # Converts AST to Python code
│   └── error.py           # Custom error classes
├── runtime/
│   └── bootstrap.py       # Resolves imports and executes generated code
├── examples/
│   ├── hello.scs
│   ├── test.scs
│   ├── testb.scs
│   ├── mathlib.scs
│   ├── use_import.scs
│   ├── for_loop.scs
│   ├── operators.scs
│   └── lists.scs
└── code/                  # Place your .scs files here
```

## Execution Pipeline

```
.scs source
  → compiler/parser.py       parse via Lark LALR → AST
  → compiler/transformer.py  walk AST → Python source string
  → runtime/bootstrap.py     resolve imports → exec() → Main().run()
```

## How to use the SyscomScript extension in VS Code

### Installation
 1. Clone or download SyscomScript
 2. Download [syscomscript-0.1.0.vsix](VScodeExtension/syscomscript-0.1.0.vsix) below
 3. In VSCode: Ctrl+Shift+P → "Install from VSIX" → select the file

## License

See [LICENSE.txt](LICENSE.txt).
