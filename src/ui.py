#!/usr/bin/env python3
"""
A small fancy-looking Tkinter UI that reads from STDIN (if piped) and
lets the user send edited text to STDOUT. Designed to be used in a
pipe-friendly way: run a producer that pipes into this program, edit or
review the data, then press 'Send to STDOUT' to emit it downstream.

Usage examples:
  cat file.txt | python ui.py    # shows file.txt contents; click Send to STDOUT
  python ui.py                   # empty editor

"""
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk


def read_stdin():
    try:
        if not sys.stdin or sys.stdin.isatty():
            return ""
        # Read everything from stdin (blocking only if there's data piped)
        return sys.stdin.read()
    except Exception:
        return ""


def write_stdout(text):
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except Exception:
        pass


def main():
    root = tk.Tk()
    root.title("Murder at the Peak Vista Lodge")
    root.geometry("900x600")
    root.configure(bg="#1e1e2f")

    style = ttk.Style()
    style.theme_use("default")
    style.configure("TFrame", background="#1e1e2f")
    style.configure("TLabel", background="#1e1e2f", foreground="#d6deff", font=("Helvetica", 12))
    style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), foreground="#ffd479")
    style.configure("TButton", font=("Helvetica", 11))

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill=tk.BOTH, expand=True)

    header = ttk.Label(frame, text="Murder at the Peak Vista Lodge", style="Header.TLabel")
    header.pack(anchor=tk.W, pady=(0, 8))

    subtitle = ttk.Label(frame, text="Give specific instructions for the AI to follow")
    subtitle.pack(anchor=tk.W, pady=(0, 12))

    panes = ttk.Panedwindow(frame, orient=tk.HORIZONTAL)
    panes.pack(fill=tk.BOTH, expand=True)

    # Left: editable input area
    left = ttk.Frame(panes)
    panes.add(left, weight=3)

    lbl_in = ttk.Label(left, text="Input what you want to do here:")
    lbl_in.pack(anchor=tk.W)

    txt_in = tk.Text(left, wrap=tk.WORD, bg="#0f1724", fg="#e6eef8", insertbackground="#ffffff",
                     font=("Consolas", 12), relief=tk.FLAT)
    txt_in.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

    # Right: preview / actions
    right = ttk.Frame(panes, width=260)
    panes.add(right, weight=1)

    lbl_preview = ttk.Label(right, text="Preview / Actions:")
    lbl_preview.pack(anchor=tk.W)

    latest_response = tk.Text(right, height=10, wrap=tk.WORD, bg="#081028", fg="#cfe8ff",
                              font=("Consolas", 11), relief=tk.SUNKEN)
    latest_response.pack(fill=tk.BOTH, expand=False, pady=(6, 8))
    latest_response.configure(state=tk.DISABLED)

    lbl_history = ttk.Label(right, text="All Returned Messages:")
    lbl_history.pack(anchor=tk.W, pady=(0, 4))

    history_frame = ttk.Frame(right)
    history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

    history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL)
    history_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    history_list = tk.Listbox(history_frame, yscrollcommand=history_scroll.set,
                              bg="#0f1724", fg="#e6eef8", font=("Consolas", 10),
                              selectbackground="#253a5a", relief=tk.FLAT)
    history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    history_scroll.config(command=history_list.yview)

    btn_frame = ttk.Frame(right)
    btn_frame.pack(fill=tk.X)

    responses = []
    response_queue = queue.Queue()

    def show_latest_response(text):
        latest_response.configure(state=tk.NORMAL)
        latest_response.delete("1.0", tk.END)
        latest_response.insert(tk.END, text)
        latest_response.configure(state=tk.DISABLED)

    def add_response(text):
        message = text.strip()
        if not message:
            return
        responses.append(message)
        show_latest_response(message)
        summary = message.splitlines()[0][:80]
        history_list.insert(tk.END, f"{len(responses)}. {summary}")
        history_list.yview_moveto(1)

    def show_selected_response(event=None):
        sel = history_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(responses):
            show_latest_response(responses[idx])

    def update_preview(event=None):
        # Keep latest response visible; input editing no longer overwrites it.
        pass

    def send_stdout():
        data = txt_in.get("1.0", tk.END)
        write_stdout(data)

    def copy_clipboard():
        root.clipboard_clear()
        root.clipboard_append(txt_in.get("1.0", tk.END))

    def clear_input():
        txt_in.delete("1.0", tk.END)

    def stdin_listener():
        try:
            if not sys.stdin or sys.stdin.isatty():
                return
            for line in sys.stdin:
                response_queue.put(line)
        except Exception:
            pass

    def poll_responses():
        try:
            while True:
                add_response(response_queue.get_nowait())
        except queue.Empty:
            pass
        root.after(100, poll_responses)

    btn_send = ttk.Button(btn_frame, text="Send to STDOUT", command=send_stdout)
    btn_send.pack(fill=tk.X, pady=4)

    btn_copy = ttk.Button(btn_frame, text="Copy to Clipboard", command=copy_clipboard)
    btn_copy.pack(fill=tk.X, pady=4)

    btn_clear = ttk.Button(btn_frame, text="Clear Input", command=clear_input)
    btn_clear.pack(fill=tk.X, pady=4)

    btn_exit = ttk.Button(btn_frame, text="Exit", command=root.quit)
    btn_exit.pack(fill=tk.X, pady=4)

    # Keyboard shortcuts
    root.bind("<Control-Return>", lambda e: send_stdout())
    root.bind("<Control-c>", lambda e: copy_clipboard())
    root.bind("<Control-q>", lambda e: root.quit())
    txt_in.bind("<KeyRelease>", update_preview)
    history_list.bind("<<ListboxSelect>>", show_selected_response)

    # Start async stdin listener for returned LLM messages
    threading.Thread(target=stdin_listener, daemon=True).start()
    poll_responses()

    # Small footer
    footer = ttk.Label(frame, text="Shortcuts: Ctrl+Enter=Send  Ctrl+C=Copy  Ctrl+Q=Exit", font=("Helvetica", 10))
    footer.pack(anchor=tk.W, pady=(8, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
