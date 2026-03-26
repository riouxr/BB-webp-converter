import os
import sys
import threading
from pathlib import Path
from tkinter import *
from tkinter import font
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image


# ── helpers ────────────────────────────────────────────────────────────────────

def convert_file(src: Path, fmt: str) -> tuple[bool, str]:
    """Convert a single WebP file to PNG or JPG. Returns (success, message)."""
    if src.suffix.lower() != ".webp":
        return False, f"Skipped (not .webp): {src.name}"
    ext = ".jpg" if fmt == "JPG" else ".png"
    dst = src.with_suffix(ext)
    try:
        with Image.open(src) as img:
            if fmt == "JPG":
                # JPG doesn't support transparency — flatten onto white bg
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg
                else:
                    img = img.convert("RGB")
                img.save(dst, "JPEG", quality=95)
            else:
                img.save(dst, "PNG")
        return True, f"✓  {src.name}  →  {dst.name}"
    except Exception as e:
        return False, f"✗  {src.name}  —  {e}"


def parse_dropped(data: str) -> list[Path]:
    """Parse the string returned by tkdnd (handles spaces in filenames)."""
    paths = []
    raw = data.strip()
    i = 0
    while i < len(raw):
        if raw[i] == "{":
            end = raw.index("}", i)
            paths.append(Path(raw[i + 1:end]))
            i = end + 2
        else:
            end = raw.find(" ", i)
            if end == -1:
                paths.append(Path(raw[i:]))
                break
            paths.append(Path(raw[i:end]))
            i = end + 1
    return [p for p in paths if p.suffix.lower() == ".webp"]


# ── UI ─────────────────────────────────────────────────────────────────────────

class App(TkinterDnD.Tk):
    DARK   = "#0f0f17"
    PANEL  = "#17172a"
    CARD   = "#1e1e35"
    ACCENT = "#7c3aed"
    SEL_PNG= "#7c3aed"
    SEL_JPG= "#0ea5e9"
    GREEN  = "#4ade80"
    RED    = "#f87171"
    YELLOW = "#fbbf24"
    TEXT   = "#f1f5f9"
    MUTED  = "#64748b"
    BORDER = "#2d2d4e"
    HOVER  = "#252545"

    def __init__(self):
        super().__init__()
        self.title("BB Webp Converter")
        self.geometry("640x560")
        self.minsize(500, 420)
        self.configure(bg=self.DARK)
        self.resizable(True, True)

        self._fmt = StringVar(value="PNG")

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 640) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    # ── layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=22)

        # ── header ──────────────────────────────────────────────────────────
        hdr = Frame(self, bg=self.PANEL, height=62)
        hdr.pack(fill=X)
        hdr.pack_propagate(False)

        hdr_left = Frame(hdr, bg=self.PANEL)
        hdr_left.pack(side=LEFT, padx=20)

        dot = Canvas(hdr_left, width=10, height=10, bg=self.PANEL,
                     highlightthickness=0)
        dot.pack(side=LEFT, padx=(0, 9))
        dot.create_oval(0, 0, 10, 10, fill=self.ACCENT, outline="")

        Label(hdr_left, text="BB Webp Converter",
              bg=self.PANEL, fg=self.TEXT,
              font=("Segoe UI", 14, "bold")).pack(side=LEFT)

        # right: PNG / JPG toggle pill
        toggle_wrap = Frame(hdr, bg=self.PANEL)
        toggle_wrap.pack(side=RIGHT, padx=20)

        Label(toggle_wrap, text="Output format",
              bg=self.PANEL, fg=self.MUTED,
              font=("Segoe UI", 8)).pack(anchor=E)

        pill = Frame(toggle_wrap, bg=self.BORDER, padx=2, pady=2)
        pill.pack()

        self._btn_png = Label(pill, text="  PNG  ",
                              font=("Segoe UI", 9, "bold"),
                              pady=5, cursor="hand2")
        self._btn_png.pack(side=LEFT)

        self._btn_jpg = Label(pill, text="  JPG  ",
                              font=("Segoe UI", 9, "bold"),
                              pady=5, cursor="hand2")
        self._btn_jpg.pack(side=LEFT)

        self._btn_png.bind("<Button-1>", lambda _: self._set_fmt("PNG"))
        self._btn_jpg.bind("<Button-1>", lambda _: self._set_fmt("JPG"))
        self._refresh_toggle()

        # accent line
        self._accent_line = Frame(self, bg=self.ACCENT, height=2)
        self._accent_line.pack(fill=X)

        # ── drop zone ───────────────────────────────────────────────────────
        dz_wrap = Frame(self, bg=self.DARK)
        dz_wrap.pack(fill=X, **pad, pady=(20, 0))

        self.drop_zone = Frame(
            dz_wrap, bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=2,
        )
        self.drop_zone.pack(fill=X)

        inner = Frame(self.drop_zone, bg=self.CARD)
        inner.pack(fill=X, padx=4, pady=4)

        self._arrow = Label(inner, text="⬇", font=("Segoe UI", 32),
                            bg=self.CARD, fg=self.ACCENT)
        self._arrow.pack(pady=(20, 4))

        self._drop_title = Label(inner,
                                 text="Drop .webp files here",
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.CARD, fg=self.TEXT)
        self._drop_title.pack()

        self._drop_sub = Label(inner,
                               text=".png saved next to originals",
                               font=("Segoe UI", 8),
                               bg=self.CARD, fg=self.MUTED)
        self._drop_sub.pack(pady=(3, 20))

        # register DnD on zone and children
        dnd_targets = [self.drop_zone, inner,
                       self._arrow, self._drop_title, self._drop_sub]
        for w in dnd_targets:
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>",      self._on_drop)
            w.dnd_bind("<<DragEnter>>", self._on_enter)
            w.dnd_bind("<<DragLeave>>", self._on_leave)

        self._drop_inner = inner

        # ── stats row ───────────────────────────────────────────────────────
        stats = Frame(self, bg=self.DARK)
        stats.pack(fill=X, **pad, pady=(12, 0))

        self._lbl_ok  = Label(stats, text="✓  0 converted",
                              bg=self.DARK, fg=self.GREEN,
                              font=("Segoe UI", 9, "bold"))
        self._lbl_ok.pack(side=LEFT)

        self._lbl_err = Label(stats, text="✗  0 errors",
                              bg=self.DARK, fg=self.RED,
                              font=("Segoe UI", 9, "bold"))
        self._lbl_err.pack(side=LEFT, padx=16)

        btn_clear = Label(stats, text="Clear",
                          bg=self.DARK, fg=self.MUTED,
                          font=("Segoe UI", 9), cursor="hand2")
        btn_clear.pack(side=RIGHT)
        btn_clear.bind("<Button-1>", lambda _: self._clear_log())
        btn_clear.bind("<Enter>",    lambda _: btn_clear.configure(fg=self.TEXT))
        btn_clear.bind("<Leave>",    lambda _: btn_clear.configure(fg=self.MUTED))

        # ── log ─────────────────────────────────────────────────────────────
        log_wrap = Frame(self, bg=self.DARK)
        log_wrap.pack(fill=BOTH, expand=True, **pad, pady=(6, 18))

        log_border = Frame(log_wrap, bg=self.BORDER, padx=1, pady=1)
        log_border.pack(fill=BOTH, expand=True)

        log_inner = Frame(log_border, bg=self.CARD)
        log_inner.pack(fill=BOTH, expand=True)

        mono = ("Cascadia Code", 9) if self._font_exists("Cascadia Code") \
               else ("Consolas", 9)

        self._log_text = Text(
            log_inner,
            bg=self.CARD, fg=self.TEXT,
            font=mono, relief=FLAT, bd=0,
            padx=12, pady=10,
            state=DISABLED, wrap=NONE,
            selectbackground=self.ACCENT,
            insertbackground=self.TEXT,
        )
        sb = Scrollbar(log_inner, command=self._log_text.yview,
                       bg=self.CARD, troughcolor=self.CARD,
                       activebackground=self.BORDER, relief=FLAT)
        self._log_text.configure(yscrollcommand=sb.set)
        self._log_text.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        self._log_text.tag_config("ok",   foreground=self.GREEN)
        self._log_text.tag_config("err",  foreground=self.RED)
        self._log_text.tag_config("info", foreground=self.MUTED)
        self._log_text.tag_config("head", foreground=self.YELLOW)

        self._ok_count = self._err_count = 0
        self._log("Ready — drop some .webp files above.", "info")

    # ── toggle ──────────────────────────────────────────────────────────────

    def _set_fmt(self, fmt: str):
        self._fmt.set(fmt)
        self._refresh_toggle()
        self._drop_sub.configure(
            text=f".{fmt.lower()} saved next to originals"
        )

    def _refresh_toggle(self):
        fmt = self._fmt.get()
        active = self.SEL_PNG if fmt == "PNG" else self.SEL_JPG

        self._btn_png.configure(
            bg=active    if fmt == "PNG" else self.CARD,
            fg=self.TEXT if fmt == "PNG" else self.MUTED,
        )
        self._btn_jpg.configure(
            bg=active    if fmt == "JPG" else self.CARD,
            fg=self.TEXT if fmt == "JPG" else self.MUTED,
        )
        if hasattr(self, "_arrow"):
            self._arrow.configure(fg=active)
        if hasattr(self, "_accent_line"):
            self._accent_line.configure(bg=active)

    # ── drag feedback ────────────────────────────────────────────────────────

    def _drop_widgets(self):
        kids = list(self.drop_zone.winfo_children())
        for c in list(kids):
            kids += list(c.winfo_children())
        return [self.drop_zone] + kids

    def _on_enter(self, event):
        active = self.SEL_PNG if self._fmt.get() == "PNG" else self.SEL_JPG
        self.drop_zone.configure(highlightbackground=active)
        for w in self._drop_widgets():
            try: w.configure(bg=self.HOVER)
            except: pass
        self._arrow.configure(fg=active)

    def _on_leave(self, event):
        self.drop_zone.configure(highlightbackground=self.BORDER)
        for w in self._drop_widgets():
            try: w.configure(bg=self.CARD)
            except: pass
        active = self.SEL_PNG if self._fmt.get() == "PNG" else self.SEL_JPG
        self._arrow.configure(fg=active)

    # ── drop handler ─────────────────────────────────────────────────────────

    def _on_drop(self, event):
        self._on_leave(event)
        files = parse_dropped(event.data)
        if not files:
            self._log("No .webp files found in drop.", "info")
            return
        fmt = self._fmt.get()
        threading.Thread(
            target=self._convert_batch,
            args=(files, fmt),
            daemon=True
        ).start()

    def _convert_batch(self, files: list[Path], fmt: str):
        self.after(0, self._log,
                   f"── Converting {len(files)} file(s) to {fmt} ──", "head")
        for path in files:
            ok, msg = convert_file(path, fmt)
            self.after(0, self._log, msg, "ok" if ok else "err")
            self.after(0, self._bump, ok)
        self.after(0, self._log, "── Done ──", "info")

    # ── log helpers ──────────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        self._log_text.configure(state=NORMAL)
        self._log_text.insert(END, msg + "\n", tag)
        self._log_text.see(END)
        self._log_text.configure(state=DISABLED)

    def _clear_log(self):
        self._log_text.configure(state=NORMAL)
        self._log_text.delete("1.0", END)
        self._log_text.configure(state=DISABLED)
        self._ok_count = self._err_count = 0
        self._refresh_counts()

    def _bump(self, success: bool):
        if success: self._ok_count += 1
        else:        self._err_count += 1
        self._refresh_counts()

    def _refresh_counts(self):
        self._lbl_ok.configure(text=f"✓  {self._ok_count} converted")
        self._lbl_err.configure(text=f"✗  {self._err_count} errors")

    # ── util ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _font_exists(name: str) -> bool:
        try:
            f = font.Font(family=name)
            return f.actual("family").lower() == name.lower()
        except Exception:
            return False


if __name__ == "__main__":
    app = App()
    app.mainloop()
