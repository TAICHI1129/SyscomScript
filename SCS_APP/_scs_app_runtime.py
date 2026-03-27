# SCS_APP/_scs_app_runtime.py
# SyscomScript GUI フレームワーク — tkinter バックエンド

import tkinter as tk


class _ScsApp:
    def __init__(self):
        self._root = tk.Tk()
        self._root.withdraw()
        self._windows = []

    def window(self, title="App", width=400, height=300):
        win = _ScsWindow(self._root, str(title), int(width), int(height))
        self._windows.append(win)
        return win

    def start(self):
        if self._windows:
            self._windows[0]._toplevel.deiconify()
        self._root.mainloop()

    def quit(self):
        self._root.quit()


class _ScsWindow:
    def __init__(self, root, title, width, height):
        self._toplevel = tk.Toplevel(root)
        self._toplevel.title(title)
        self._toplevel.geometry(f"{width}x{height}")
        self._toplevel.resizable(True, True)
        self._toplevel.protocol("WM_DELETE_WINDOW", root.quit)

        self._frame = tk.Frame(self._toplevel, padx=12, pady=12)
        self._frame.pack(fill="both", expand=True)

    def title(self, text):
        self._toplevel.title(str(text))

    def resize(self, width, height):
        self._toplevel.geometry(f"{int(width)}x{int(height)}")


def App():
    return _ScsApp()