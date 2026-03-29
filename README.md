# SyscomScript

SyscomScript is a class-based, educational programming language that transpiles to Python. Write `.scs` files and run them immediately — no separate compile step required.

## Features

- Simple class-based syntax
- Transpiles to Python and runs immediately
- REPL (interactive mode) for quick experimentation
- Web-based IDE (`ide.py`)
- Import Python standard libraries and call them via `py.module.func()`
- Call deeply nested Python APIs with `py.os.path.join()`, `py.subprocess.run()`, etc.
- Import other `.scs` files (`import "utils.scs"`) and call methods via `obj.method()`
- GUI application development via the **SCS_APP** framework (tkinter-based)
- `--debug-python` flag to inspect generated Python code

## Requirements

- Python 3.10 or later
- [lark](https://github.com/lark-parser/lark) (`pip install lark`)
- [flask](https://flask.palletsprojects.com/) (`pip install flask`) — required for the IDE
- [waitress](https://docs.pylonsproject.org/projects/waitress/) (`pip install waitress`) — required for the IDE

## Installation

```bat
git clone https://github.com/TAICHI1129/SyscomScript.git
cd SyscomScript
pip install lark flask waitress
```

Running `version_update.bat` will replace it with the latest version.

## How to Run a File

**Option 1 — Double-click `run.bat`**

Place your `.scs` file in the `code\` folder, then double-click `run.bat`.

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

## How to Use the REPL

```bat
python syscom.py
python syscom.py --repl
```

| Command  | Description                        |
|----------|------------------------------------|
| `:vars`  | Show all current session variables |
| `:clear` | Reset the session                  |
| `:debug` | Show last generated Python code    |
| `:help`  | Show help                          |
| `exit`   | Quit the REPL                      |

---

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

`range()` accepts 1, 2, or 3 arguments (end / start+end / start+end+step).

```scs
class Main {
    run() {
        for i in range(5) {
            print(i)
        }

        for i in range(1, 10, 2) {
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

### Dictionaries

```scs
class Main {
    run() {
        d = {"name": "Alice", "age": 20}
        print(d["name"])
    }
}
```

### Boolean and type casting

```scs
class Main {
    run() {
        flag = True
        n = int("42")
        s = str(100)
        f = float("3.14")
        b = bool(0)
        print(n)
        print(s)
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

### Comments

```scs
// This is a single-line comment

/* This is
   a multi-line comment */
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

### Import another `.scs` file

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

---

## Python Standard Library

SyscomScript can call any Python standard library function using the `py.` prefix. Common modules (`os`, `math`, `random`, `json`, `subprocess`, `time`, `datetime`) are available without an explicit `import` statement. For other modules, use `import` first.

### Built-in functions (no import needed)

```scs
class Main {
    run() {
        // File I/O
        f = py.open("hello.txt", "w")
        f.write("Hello from SyscomScript!")
        f.close()

        // Read back
        f = py.open("hello.txt", "r")
        content = f.read()
        f.close()
        print(content)
    }
}
```

### Math

```scs
class Main {
    run() {
        x = py.math.sqrt(16)
        print(x)

        y = py.math.floor(3.7)
        print(y)

        z = py.math.ceil(3.2)
        print(z)
    }
}
```

### OS and file system

```scs
class Main {
    run() {
        cwd = py.os.getcwd()
        print(cwd)

        joined = py.os.path.join("mydir", "file.txt")
        print(joined)

        exists = py.os.path.exists("hello.txt")
        print(exists)
    }
}
```

### Random

```scs
class Main {
    run() {
        n = py.random.randint(1, 100)
        print(n)
    }
}
```

### JSON

```scs
class Main {
    run() {
        d = {"key": "value", "num": 42}
        s = py.json.dumps(d)
        print(s)
    }
}
```

### System commands

```scs
import subprocess

class Main {
    run() {
        py.subprocess.run(["echo", "hello"])
    }
}
```

### Deeply nested APIs

The `py.` prefix supports any number of dot-separated segments:

```scs
import os

class Main {
    run() {
        joined = py.os.path.join("dir", "sub", "file.txt")
        print(joined)
    }
}
```

---

## SCS_APP — GUI Framework

SCS_APP is a GUI application framework for SyscomScript, built on Python's standard `tkinter` library. No additional installation is required.

### Setup

Place the `SCS_APP/` folder in the same directory as your `.scs` file:

```
SyscomScript/
└── SCS_APP/
    ├── _scs_app_runtime.py
    └── app.scs
```

### Minimal example

```scs
import "SCS_APP/app.scs"

class Main {
    run() {
        app = App()
        win = app.window("My App", 400, 300)
        app.start()
    }
}
```

Run it:

```bat
python syscom.py SCS_APP/hello_app.scs
```

This opens a 400×300 window titled "My App".

### App API

| Method | Description |
|--------|-------------|
| `App()` | Create the application |
| `app.window(title, width, height)` | Create a window and return it |
| `app.start()` | Start the GUI event loop (blocks here) |
| `app.quit()` | Exit the application programmatically |

### Window API

| Method | Description |
|--------|-------------|
| `win.title(text)` | Change the window title |
| `win.resize(width, height)` | Resize the window |

### Planned widgets

The following widgets are planned for future releases:

| Widget | Description |
|--------|-------------|
| `win.label(text)` | Display text |
| `win.button(text)` | Clickable button |
| `win.input(placeholder)` | Text input field |

---

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
├── SCS_APP/               # GUI framework
│   ├── _scs_app_runtime.py
│   └── app.scs
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

1. Clone or download SyscomScript
2. Download [syscomscript-(VersionName).vsix](https://github.com/TAICHI1129/SyscomScript/tree/main/VScodeExtension)
3. Move the `.vscode` folder to `C:/Users/` root directory
4. In VSCode: `Ctrl+Shift+P` → "Install from VSIX" → select the file

## License

See [LICENSE.txt](LICENSE.txt).