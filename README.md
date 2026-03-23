# SyscomScript

SyscomScript is a high-level, experimental programming language designed with simplicity, readability, and educational purposes in mind. Its primary goal is to provide a clear and intuitive syntax that allows beginners to grasp core programming concepts without being overwhelmed by complex boilerplate code or verbose language rules. At the same time, SyscomScript retains enough expressiveness to implement basic algorithms, control structures, and modular designs, making it a useful tool for learning, prototyping, and small-scale projects.

One of the key features of SyscomScript is its class-based structure. Programs are organized into classes, each containing methods and variables. This object-oriented approach helps users understand encapsulation, method scoping, and the interaction between objects, all while maintaining a lightweight and approachable syntax. Unlike traditional languages like Java or C++, SyscomScript minimizes syntactic overhead by avoiding excessive punctuation, enforcing a minimalistic block structure, and using keywords that closely resemble natural language.

Control flow in SyscomScript is straightforward and highly readable. The language supports standard constructs such as conditional statements (if, else), loops (while), and simple function definitions. Expressions use familiar operators for arithmetic, comparison, and logical operations, which reduces the learning curve for newcomers. Additionally, SyscomScript includes a built-in print functionality for easy output, allowing users to quickly see the results of their code during experimentation and learning.

Another important aspect of SyscomScript is its compilation and execution model. Rather than running natively, SyscomScript is designed to be transpiled into Python code. This approach leverages Python’s runtime environment for execution, enabling cross-platform compatibility, access to Python libraries, and a smooth development workflow without requiring a dedicated compiler. The transpiler parses the SyscomScript source code, transforms it into equivalent Python code, and executes it directly, providing immediate feedback and debugging information.

From an educational perspective, SyscomScript is particularly valuable. By combining object-oriented principles, control structures, and easy-to-read syntax, it encourages learners to focus on logical thinking, problem solving, and code organization. Its simplicity makes it ideal for teaching programming fundamentals, experimenting with algorithms, and introducing the concept of transpilers and language design. Furthermore, since SyscomScript translates to Python, learners can gradually transition to full Python programming while retaining familiarity with the constructs they have already mastered.

In summary, SyscomScript is an accessible, beginner-friendly programming language that balances readability, functionality, and educational utility. Its class-based design, intuitive syntax, and Python-based execution model make it an excellent tool for learners, educators, and hobbyist programmers seeking to explore programming concepts without the initial complexity of mainstream languages. While it is not intended for large-scale software development, SyscomScript provides a solid foundation for understanding programming principles and building confidence in coding through experimentation and structured learning.

## Features
- Simple class-based syntax
- Compiles to Python
- Runs immediately without build steps
- Designed for learning language and IDE development

## Example

```scs
class Main {
    run() {
        print("Hello")
    }
}
```

## How to use IDE

➀ Move to the syscom folder in the command prompt.

➁ Run "python ide.py" in the command prompt.

If you add "--debug-python" to the command, the Python code will be displayed (example: python syscom.py examples/hello.scs --debug-python)

## How to execute

➀ Move to the syscom folder in the command prompt.

➁ Run "python syscom.py code\\(file-name).scs" in the command prompt.

# SyscomScript Language Reference

SyscomScript is a class-based, educational programming language that transpiles to Python. Every `.scs` file is parsed, converted to Python code, and executed immediately — no separate compile step required.

---

## Table of Contents

1. [Program Structure](#1-program-structure)
2. [Import](#2-import)
3. [Classes](#3-classes)
4. [Methods and Functions](#4-methods-and-functions)
5. [Statements](#5-statements)
6. [Expressions and Operators](#6-expressions-and-operators)
7. [Types and Literals](#7-types-and-literals)
8. [Complete Examples](#8-complete-examples)
9. [Formal Grammar (EBNF)](#9-formal-grammar-ebnf)

---

## 1. Program Structure

A SyscomScript file consists of zero or more `import` statements followed by one or more class definitions. Execution always begins from `class Main` — specifically its `run()` method.

```
program
  ├── import_stmt*
  └── class_def+
        └── (method_def | func_def)*
```

**Minimal program:**

```scs
class Main {
    run() {
        print("Hello, World!")
    }
}
```

> `run()` in `Main` is the entry point. It must exist and take no arguments.

---

## 2. Import

### 2-1. Python standard library

```scs
import math
import random
```

Transpiles directly to a Python `import` statement placed at the top of the generated code. All attributes of the imported module become available in the execution namespace.

### 2-2. Another `.scs` file

```scs
import "utils.scs"
import "lib/mathlib.scs"
```

The path is resolved **relative to the current file**. SyscomScript parses the target file, transpiles it to Python, and merges its class definitions into the same namespace before execution.

**Rules:**
- Circular imports are detected and raise a `SyscomRuntimeError`.
- Transitive imports are supported: `a.scs` imports `b.scs` which imports `c.scs`.
- The imported file may not define a `Main` class — only utility classes are expected.

---

## 3. Classes

```scs
class ClassName {
    // methods and functions go here
}
```

A class body contains any number of `method_def` and `func_def` entries in any order.

| Concept | Syntax | Notes |
|---|---|---|
| Class definition | `class Name { ... }` | Name must start with a letter |
| Entry point class | `class Main { ... }` | Required in every executable file |
| Utility class | Any other class name | Used by `Main` or other classes |

**Instantiating a class inside a method:**

```scs
class Main {
    run() {
        lib = MathLib()
        result = lib.square(5)
        print(result)
    }
}
```

> The assignment `lib = MathLib()` stores the instance in a variable. Method calls use the `name.method(args)` syntax. Currently only `func_call` expressions are supported; property access (dot notation outside of calls) is not yet available.

---

## 4. Methods and Functions

### 4-1. Method definition

A **method** takes no parameters. It is the top-level callable within a class — the entry point `run()` is a method.

```scs
class Main {
    run() {
        // statements
    }
}
```

### 4-2. Function definition

A **function** takes zero or more named parameters, declared with the `func` keyword.

```scs
class Main {
    func add(a, b) {
        return a + b
    }

    func greet(name) {
        print(name)
    }

    func reset() {
        return
    }
}
```

**Calling a function from the same class:**

```scs
result = add(3, 4)
greet("Alice")
```

> Within a class, function calls do not require `self.` in source code. The transpiler injects `self.` automatically.

**Parameter rules:**
- Parameters are positional only.
- Default values are not supported.
- Variadic parameters (`*args`) are not supported.

---

## 5. Statements

All statements appear inside a `block` — a `{ }` delimited body.

### 5-1. Assignment

```scs
x = 10
message = "hello"
result = add(x, 3)
```

- The right-hand side is any expression.
- Variables are dynamically typed; no declaration keyword is needed.
- Reassignment to an existing variable is allowed.

### 5-2. Print

```scs
print(x)
print("value is")
print(add(1, 2))
```

Accepts exactly one expression. The result is printed to standard output followed by a newline.

### 5-3. If / Else

```scs
if (condition) {
    // then branch
}

if (condition) {
    // then branch
} else {
    // else branch
}
```

- The condition must be wrapped in parentheses.
- The `else` branch is optional.
- `else if` chaining is not supported directly — nest another `if` inside the `else` block.

### 5-4. While loop

```scs
while (condition) {
    // loop body
}
```

- The condition must be wrapped in parentheses.
- Executes as long as the condition is truthy.
- `break` and `continue` are not supported.

### 5-5. Return

```scs
return expr    // return a value
return         // return without a value (None)
```

Exits the current function or method. A `return` at the end of `run()` simply ends execution.

### 5-6. Function call statement

```scs
print_msg("done")
reset()
```

A bare function call used as a statement (return value discarded).

---

## 6. Expressions and Operators

### Arithmetic

| Operator | Meaning | Example |
|---|---|---|
| `+` | Addition (numbers) or concatenation (strings) | `x + 1` |
| `-` | Subtraction | `x - 1` |

### Comparison

| Operator | Meaning | Example |
|---|---|---|
| `<` | Less than | `x < 10` |
| `>` | Greater than | `x > 0` |
| `==` | Equal to | `x == 3` |

> `<=`, `>=`, and `!=` are not yet in the grammar. They are planned for Phase 1 of the roadmap.

### Operator precedence

Operators are left-associative at the same level. Arithmetic binds more tightly than comparison. Use parentheses to enforce a specific evaluation order:

```scs
result = (a + b) * 2   // not yet supported — * is not in the grammar
if ((x + 1) > y) { }   // extra parens to clarify intent
```

> Currently only `+` and `-` are arithmetic operators. `*`, `/`, and `%` are planned.

### Function call as expression

A function call can appear anywhere an expression is expected:

```scs
result = add(x, y)
print(add(1, 2))
if (is_valid(x)) { }
```

---

## 7. Types and Literals

SyscomScript is dynamically typed. The following literal forms are recognised by the parser:

| Type | Literal syntax | Examples |
|---|---|---|
| Integer | Digits | `0`, `42`, `100` |
| Float | Digits with decimal point | `3.14`, `0.5` |
| String | Double-quoted | `"hello"`, `"world"` |
| Variable | Identifier | `x`, `count`, `myVar` |

**String notes:**
- Only double-quoted strings (`"..."`) are supported.
- Escape sequences follow Python rules: `\"`, `\\`, `\n`, `\t`.

**Number notes:**
- Negative number literals are not directly supported. Use subtraction: `0 - 7` instead of `-7`.

---

## 8. Complete Examples

### Hello World

```scs
class Main {
    run() {
        print("Hello, World!")
    }
}
```

### Variables and control flow

```scs
class Main {
    run() {
        x = 0
        while (x < 3) {
            print(x)
            x = x + 1
        }
        if (x == 3) {
            print("done")
        }
        return
    }
}
```

**Output:**
```
0
1
2
done
```

### Functions with parameters

```scs
class Main {
    run() {
        x = 5
        y = 7
        sum_result = add(x, y)
        print(sum_result)
        print_msg("finished")
    }

    func add(a, b) {
        return a + b
    }

    func print_msg(msg) {
        print(msg)
    }
}
```

**Output:**
```
12
finished
```

### Multi-class with import

```scs
// mathlib.scs
class MathLib {
    func square(n) {
        return n * n
    }

    func abs_val(n) {
        if (n < 0) {
            return 0 - n
        }
        return n
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
        print(lib.abs_val(0 - 7))
    }
}
```

**Output:**
```
25
7
```

---

## 9. Formal Grammar (EBNF)

The grammar is defined using [Lark](https://github.com/lark-parser/lark) notation. `?rule` means the rule is transparent (its node is inlined into the parent).

```lark
?start: program

program: (import_stmt | class_def)+

import_stmt: "import" (NAME | STRING)

class_def: "class" NAME "{" class_body "}"

class_body: (method_def | func_def)*

method_def: NAME "(" ")" block

func_def: "func" NAME "(" [param_list] ")" block
param_list: NAME ("," NAME)*

block: "{" stmt* "}"

stmt: assign
    | print_stmt
    | if_stmt
    | while_stmt
    | return_stmt
    | func_call_stmt

assign:        NAME "=" expr
print_stmt:    "print" "(" expr ")"
if_stmt:       "if" "(" expr ")" block ("else" block)?
while_stmt:    "while" "(" expr ")" block
return_stmt:   "return" expr?
func_call_stmt: func_call

func_call: NAME "(" [arg_list] ")"
arg_list:  expr ("," expr)*

?expr: STRING
     | NUMBER
     | NAME
     | func_call
     | expr "<"  expr  -> lt
     | expr ">"  expr  -> gt
     | expr "==" expr  -> eq
     | expr "+"  expr  -> add
     | expr "-"  expr  -> sub

%import common.CNAME          -> NAME
%import common.NUMBER
%import common.ESCAPED_STRING -> STRING
%import common.WS
%ignore WS
```

### Terminal definitions

| Terminal | Pattern | Description |
|---|---|---|
| `NAME` | `[a-zA-Z_][a-zA-Z0-9_]*` | Identifier (CNAME from Lark common grammar) |
| `NUMBER` | Integer or float literal | Lark common NUMBER |
| `STRING` | `"..."` | Double-quoted escaped string |
| `WS` | Whitespace | Ignored everywhere |

---

## Appendix: Execution pipeline

```
.scs source
  → parser.py       parse via Lark LALR → AST (Tree)
  → transformer.py  walk AST → Python source string
  → bootstrap.py    resolve .scs imports → exec() → Main().run()
```

**CLI usage:**

```bash
# Run a file
python syscom.py examples/hello.scs

# Show generated Python code
python syscom.py examples/hello.scs --debug-python

# Start interactive REPL
python syscom.py --repl
```
