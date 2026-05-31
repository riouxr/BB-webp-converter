import os
import sys
import threading
from pathlib import Path
from tkinter import *
from tkinter import font
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image

# All extensions Pillow can read, built at import time (e.g. .webp, .tga, .bmp, …)
SUPPORTED_EXTS: frozenset[str] = frozenset(Image.registered_extensions().keys())

# Output formats: name -> (file_ext, pillow_format, flatten_alpha, default_save_kwargs)
#   flatten_alpha=True  → transparency is composited onto a white background
#   flatten_alpha=False → alpha channel is preserved as-is
OUTPUT_FORMATS: dict[str, tuple[str, str, bool, dict]] = {
    "PNG":  (".png",  "PNG",  False, {}),
    "JPEG": (".jpg",  "JPEG", True,  {"quality": 95}),
    "WebP": (".webp", "WEBP", False, {"quality": 95}),
    "BMP":  (".bmp",  "BMP",  True,  {}),
    "TIFF": (".tiff", "TIFF", False, {}),
    "TGA":  (".tga",  "TGA",  False, {}),
    "GIF":  (".gif",  "GIF",  True,  {}),
}

# Formats that expose compression controls in the UI
COMP_FORMATS = {"JPEG", "WebP", "PNG", "TIFF"}


# ── helpers ────────────────────────────────────────────────────────────────────

def collect_files(paths: list[Path], recursive: bool) -> list[Path]:
    """Expand a mixed list of files and folders into supported image files."""
    result = []
    for p in paths:
        if p.is_dir():
            pattern = "**/*" if recursive else "*"
            for f in sorted(p.glob(pattern)):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    result.append(f)
        elif p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            result.append(p)
    return result


def convert_file(src: Path, fmt: str,
                 delete_original: bool = False,
                 save_kwargs: dict | None = None) -> tuple[bool, str]:
    """Convert any Pillow-readable image to the chosen output format."""
    if src.suffix.lower() not in SUPPORTED_EXTS:
        return False, f"Skipped (unsupported format): {src.name}"

    ext, pil_fmt, flatten, default_kwargs = OUTPUT_FORMATS[fmt]

    # Skip if the file is already in the target format
    if src.suffix.lower() == ext:
        return False, f"Skipped (already {fmt}): {src.name}"

    # UI-provided kwargs override the defaults
    kwargs = {**default_kwargs, **(save_kwargs or {})}
    dst = src.with_suffix(ext)

    try:
        with Image.open(src) as img:
            if flatten:
                # Flatten transparency onto a white background
                if img.mode == "P":
                    img = img.convert("RGBA")
                if img.mode in ("RGBA", "LA", "PA"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")
            img.save(dst, pil_fmt, **kwargs)

        if delete_original:
            src.unlink()
            return True, f"✓  {src.name}  →  {dst.name}  (original deleted)"

        return True, f"✓  {src.name}  →  {dst.name}"
    except Exception as e:
        return False, f"✗  {src.name}  —  {e}"


def parse_dropped(data: str) -> list[Path]:
    """Parse the string returned by tkdnd (handles spaces in filenames).
    Returns both folders and supported image files."""
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
    return [p for p in paths
            if p.is_dir() or p.suffix.lower() in SUPPORTED_EXTS]


# ── UI ─────────────────────────────────────────────────────────────────────────

class App(TkinterDnD.Tk):
    DARK   = "#0f0f17"
    PANEL  = "#17172a"
    CARD   = "#1e1e35"
    ACCENT = "#7c3aed"
    GREEN  = "#4ade80"
    RED    = "#f87171"
    YELLOW = "#fbbf24"
    TEXT   = "#f1f5f9"
    MUTED  = "#64748b"
    BORDER = "#2d2d4e"
    HOVER  = "#252545"

    def __init__(self):
        super().__init__()
        self.title("BB Image Converter")
        self.geometry("640x660")
        self.minsize(520, 500)
        self.configure(bg=self.DARK)
        self.resizable(True, True)

        # ── format ──────────────────────────────────────────────────────────
        self._fmt         = StringVar(value="PNG")

        # ── compression state ───────────────────────────────────────────────
        self._jpeg_quality    = IntVar(value=95)  # 95 is the sweet spot; 96–100 = near-lossless but huge files
        self._webp_quality    = IntVar(value=95)
        self._webp_lossless   = BooleanVar(value=False)
        self._png_compression = IntVar(value=6)
        self._tiff_compression = StringVar(value="tiff_lzw")

        # ── options ─────────────────────────────────────────────────────────
        self._recursive   = BooleanVar(value=False)
        self._delete_orig = BooleanVar(value=False)

        # widget refs rebuilt on format change
        self._tiff_btns: dict[str, Label] = {}

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 640) // 2
        y = (self.winfo_screenheight() - 660) // 2
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
        hdr_left.pack(side=LEFT, padx=20, fill=Y)

        dot = Canvas(hdr_left, width=10, height=10, bg=self.PANEL,
                     highlightthickness=0)
        dot.pack(side=LEFT, padx=(0, 9))
        dot.create_oval(0, 0, 10, 10, fill=self.ACCENT, outline="")

        Label(hdr_left, text="BB Image Converter",
              bg=self.PANEL, fg=self.TEXT,
              font=("Segoe UI", 14, "bold")).pack(side=LEFT)

        # ── format bar ──────────────────────────────────────────────────────
        self._fmt_bar = Frame(self, bg=self.PANEL)
        self._fmt_bar.pack(fill=X)

        Label(self._fmt_bar, text="Output format",
              bg=self.PANEL, fg=self.MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(22, 10), pady=(0, 8))

        pill = Frame(self._fmt_bar, bg=self.BORDER, padx=2, pady=2)
        pill.pack(side=LEFT, pady=(0, 8))

        self._fmt_btns: dict[str, Label] = {}
        for name in OUTPUT_FORMATS:
            btn = Label(pill, text=f"  {name}  ",
                        font=("Segoe UI", 9, "bold"),
                        pady=4, cursor="hand2")
            btn.pack(side=LEFT)
            btn.bind("<Button-1>", lambda _, n=name: self._set_fmt(n))
            self._fmt_btns[name] = btn

        self._refresh_fmt_btns()

        # ── compression options (dynamic, shown for JPEG/WebP/PNG/TIFF) ─────
        self._comp_frame = Frame(self, bg=self.PANEL, padx=22)
        # initial build — will pack itself if the default format needs it
        self._update_comp_ui()

        # accent line
        self._accent_line = Frame(self, bg=self.ACCENT, height=2)
        self._accent_line.pack(fill=X)

        # ── options row ─────────────────────────────────────────────────────
        opts = Frame(self, bg=self.DARK)
        opts.pack(fill=X, **pad, pady=(12, 0))

        cb_kw = dict(
            bg=self.DARK, fg=self.MUTED,
            activebackground=self.DARK, activeforeground=self.TEXT,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
            bd=0, highlightthickness=0,
            cursor="hand2",
        )
        Checkbutton(opts, text="Include subfolders",
                    variable=self._recursive, **cb_kw).pack(side=LEFT)
        Checkbutton(opts, text="Delete originals after conversion",
                    variable=self._delete_orig, **cb_kw).pack(side=LEFT, padx=(24, 0))

        # ── drop zone ───────────────────────────────────────────────────────
        dz_wrap = Frame(self, bg=self.DARK)
        dz_wrap.pack(fill=X, **pad, pady=(10, 0))

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
                                 text="Drop images or folders here",
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
        self._log("Ready — drop images or folders above.", "info")

    # ── format selector ─────────────────────────────────────────────────────

    def _set_fmt(self, fmt: str):
        self._fmt.set(fmt)
        ext = OUTPUT_FORMATS[fmt][0]
        self._drop_sub.configure(text=f"{ext} saved next to originals")
        self._refresh_fmt_btns()
        self._update_comp_ui()

    def _refresh_fmt_btns(self):
        current = self._fmt.get()
        for name, btn in self._fmt_btns.items():
            active = name == current
            btn.configure(
                bg=self.ACCENT if active else self.CARD,
                fg=self.TEXT   if active else self.MUTED,
            )

    # ── compression UI ──────────────────────────────────────────────────────

    def _update_comp_ui(self):
        """Rebuild the compression row for the current format."""
        for w in self._comp_frame.winfo_children():
            w.destroy()
        self._tiff_btns = {}

        fmt = self._fmt.get()
        builders = {
            "JPEG": self._build_jpeg_comp,
            "WebP": self._build_webp_comp,
            "PNG":  self._build_png_comp,
            "TIFF": self._build_tiff_comp,
        }

        if fmt in builders:
            builders[fmt](self._comp_frame)
            if not self._comp_frame.winfo_ismapped():
                self._comp_frame.pack(after=self._fmt_bar, fill=X, pady=(0, 4))
        else:
            self._comp_frame.pack_forget()

    def _make_slider(self, parent, label: str,
                     var: IntVar, lo: int, hi: int) -> tuple[Frame, Scale, Label]:
        """Create a labelled horizontal slider. Returns (row, scale, value_label)."""
        row = Frame(parent, bg=self.PANEL)
        row.pack(side=LEFT, padx=(0, 20))

        Label(row, text=label, bg=self.PANEL, fg=self.MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(0, 8))

        sc = Scale(row, variable=var, from_=lo, to=hi,
                   orient=HORIZONTAL, length=150, sliderlength=14,
                   showvalue=False,
                   bg=self.PANEL, troughcolor=self.BORDER,
                   activebackground=self.ACCENT,
                   highlightthickness=0, bd=0, relief=FLAT)
        sc.pack(side=LEFT)

        val_lbl = Label(row, text=str(var.get()), width=3, anchor=W,
                        bg=self.PANEL, fg=self.TEXT,
                        font=("Segoe UI", 9, "bold"))
        val_lbl.pack(side=LEFT, padx=(6, 0))
        var.trace_add("write", lambda *_: val_lbl.configure(text=str(var.get())))

        return row, sc, val_lbl

    def _build_jpeg_comp(self, parent):
        inner = Frame(parent, bg=self.PANEL)
        inner.pack(fill=X, pady=6)
        self._make_slider(inner, "Quality", self._jpeg_quality, 1, 100)

    def _build_webp_comp(self, parent):
        inner = Frame(parent, bg=self.PANEL)
        inner.pack(fill=X, pady=6)

        cb_kw = dict(bg=self.PANEL, fg=self.MUTED,
                     activebackground=self.PANEL, activeforeground=self.TEXT,
                     selectcolor=self.CARD, font=("Segoe UI", 9),
                     bd=0, highlightthickness=0, cursor="hand2")

        _, sc, val_lbl = self._make_slider(
            inner, "Quality", self._webp_quality, 1, 100)

        def _toggle_lossless():
            is_lossless = self._webp_lossless.get()
            sc.configure(state=DISABLED if is_lossless else NORMAL)
            val_lbl.configure(fg=self.MUTED if is_lossless else self.TEXT)

        Checkbutton(inner, text="Lossless",
                    variable=self._webp_lossless,
                    command=_toggle_lossless,
                    **cb_kw).pack(side=LEFT, padx=(0, 4))

        _toggle_lossless()  # apply initial state

    def _build_png_comp(self, parent):
        inner = Frame(parent, bg=self.PANEL)
        inner.pack(fill=X, pady=6)
        self._make_slider(inner, "Compression", self._png_compression, 0, 9)
        Label(inner, text="0 = fast   9 = smallest",
              bg=self.PANEL, fg=self.MUTED,
              font=("Segoe UI", 7)).pack(side=LEFT, padx=(4, 0))

    def _build_tiff_comp(self, parent):
        inner = Frame(parent, bg=self.PANEL)
        inner.pack(fill=X, pady=6)

        Label(inner, text="Compression",
              bg=self.PANEL, fg=self.MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(0, 10))

        pill = Frame(inner, bg=self.BORDER, padx=2, pady=2)
        pill.pack(side=LEFT)

        options = [("None", "raw"), ("LZW", "tiff_lzw"), ("Deflate", "tiff_deflate")]
        self._tiff_btns = {}
        for label, value in options:
            btn = Label(pill, text=f"  {label}  ",
                        font=("Segoe UI", 9, "bold"),
                        pady=3, cursor="hand2")
            btn.pack(side=LEFT)
            btn.bind("<Button-1>", lambda _, v=value: self._set_tiff_compression(v))
            self._tiff_btns[value] = btn

        self._refresh_tiff_btns()

    def _set_tiff_compression(self, value: str):
        self._tiff_compression.set(value)
        self._refresh_tiff_btns()

    def _refresh_tiff_btns(self):
        current = self._tiff_compression.get()
        for value, btn in self._tiff_btns.items():
            active = value == current
            btn.configure(
                bg=self.ACCENT if active else self.CARD,
                fg=self.TEXT   if active else self.MUTED,
            )

    def _get_save_kwargs(self, fmt: str) -> dict:
        """Build save kwargs from current UI state for the given format."""
        if fmt == "JPEG":
            return {"quality": self._jpeg_quality.get()}
        if fmt == "WebP":
            if self._webp_lossless.get():
                return {"lossless": True}
            return {"quality": self._webp_quality.get(), "lossless": False}
        if fmt == "PNG":
            return {"compress_level": self._png_compression.get()}
        if fmt == "TIFF":
            return {"compression": self._tiff_compression.get()}
        return {}

    # ── drag feedback ────────────────────────────────────────────────────────

    def _drop_widgets(self):
        kids = list(self.drop_zone.winfo_children())
        for c in list(kids):
            kids += list(c.winfo_children())
        return [self.drop_zone] + kids

    def _on_enter(self, event):
        self.drop_zone.configure(highlightbackground=self.ACCENT)
        for w in self._drop_widgets():
            try: w.configure(bg=self.HOVER)
            except: pass
        self._arrow.configure(fg=self.ACCENT)

    def _on_leave(self, event):
        self.drop_zone.configure(highlightbackground=self.BORDER)
        for w in self._drop_widgets():
            try: w.configure(bg=self.CARD)
            except: pass
        self._arrow.configure(fg=self.ACCENT)

    # ── drop handler ─────────────────────────────────────────────────────────

    def _on_drop(self, event):
        self._on_leave(event)
        raw = parse_dropped(event.data)
        files = collect_files(raw, self._recursive.get())
        if not files:
            self._log("No supported image files found in drop.", "info")
            return
        fmt    = self._fmt.get()
        delete = self._delete_orig.get()
        kwargs = self._get_save_kwargs(fmt)
        threading.Thread(
            target=self._convert_batch,
            args=(files, fmt, delete, kwargs),
            daemon=True
        ).start()

    def _convert_batch(self, files: list[Path], fmt: str,
                       delete_original: bool, save_kwargs: dict):
        self.after(0, self._log,
                   f"── Converting {len(files)} file(s) to {fmt} ──", "head")
        for path in files:
            ok, msg = convert_file(path, fmt, delete_original, save_kwargs)
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
