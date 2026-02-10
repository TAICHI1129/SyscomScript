
### ide.py（最小構成・動く）
import tkinter as tk
import subprocess
import tempfile
import os

def run_code():
    code = text.get("1.0", tk.END)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".scc", mode="w", encoding="utf-8") as f:
        f.write(code)
        path = f.name

    result = subprocess.run(
        ["python", "syscom.py", path],
        capture_output=True,
        text=True
    )

    output.delete("1.0", tk.END)
    output.insert(tk.END, result.stdout + result.stderr)

root = tk.Tk()
root.title("SyscomScript IDE")

text = tk.Text(root, height=15)
text.pack(fill="both", expand=True)

btn = tk.Button(root, text="Run", command=run_code)
btn.pack()

output = tk.Text(root, height=10, bg="#111", fg="#0f0")
output.pack(fill="both", expand=True)

root.mainloop()
