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


## How to execute

➀ Move to the syscom folder in the command prompt.

➁ Run "python syscom.py code\\(file-name).scs" in the command prompt.