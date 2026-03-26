# BB Webp Converter

A lightweight drag-and-drop desktop app for converting `.webp` and `.avif` images to **PNG** or **JPG** on Windows — no FFmpeg, no dependencies, no installation required for end users.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

- **Drag & drop** — drop one or many `.webp` or `.avif` files at once
- **PNG or JPG output** — toggle between formats in one click
- **Saves in place** — output files are written next to the originals, same filename, new extension
- **Transparency-aware** — JPG conversions automatically flatten transparent areas onto a white background
- **Conversion log** — live feed of every file processed with success/error counts
- **Zero install for end users** — ships as a single `.exe`, nothing else needed

---

## Screenshot

```
┌─────────────────────────────────────────────┐
│  ● BB Webp Converter          Output format │
│                               [ PNG ][ JPG ]│
├─────────────────────────────────────────────┤
│                                             │
│                    ⬇                        │
│           Drop .webp or .avif files here    │
│       .png saved next to originals          │
│                                             │
├─────────────────────────────────────────────┤
│  ✓ 3 converted   ✗ 0 errors        Clear   │
├─────────────────────────────────────────────┤
│  Ready — drop some .webp files above.       │
│  ── Converting 3 file(s) to PNG ──          │
│  ✓  photo1.webp  →  photo1.png              │
│  ✓  banner.webp  →  banner.png              │
│  ✓  icon.webp    →  icon.png                │
│  ── Done ──                                 │
└─────────────────────────────────────────────┘
```

---

## Getting the app

### Option A — Build it yourself (recommended)

You need **Python 3.9+** installed. That's it.

1. Clone or download this repo
2. Double-click **`build_exe.bat`**
3. Find your app at **`dist\BBWebpConverter.exe`**

The `.exe` is fully self-contained — copy it anywhere, share it with anyone.

### Option B — Run from source

```bash
pip install -r requirements.txt
python webp2png.py
```

---

## Building from source

`build_exe.bat` handles everything automatically:

```
1. Verifies Python is available
2. pip installs all dependencies
3. Calls PyInstaller with the correct flags
4. Outputs dist\BBWebpConverter.exe
```

Build time is roughly 30–60 seconds. The resulting `.exe` is ~15–20 MB (Python runtime + Pillow bundled in).

---

## How it works

- **No FFmpeg** — conversion is handled entirely by [Pillow](https://python-pillow.org/), which supports WebP (lossy, lossless, animated) and AVIF via the `pillow-avif-plugin` or Pillow's built-in AVIF support (Pillow ≥ 9.1 with libavif)
- **Drag & drop** — powered by [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2), wrapping the TkDnD2 Tcl extension
- **Packaging** — [PyInstaller](https://pyinstaller.org/) bundles Python, Pillow, tkinterdnd2, and the Tcl/Tk runtime into a single executable

---

## Requirements (build machine only)

| Requirement | Version |
|---|---|
| Python | 3.9 or newer |
| Pillow | ≥ 10.0 |
| tkinterdnd2 | ≥ 0.3 |
| PyInstaller | ≥ 6.0 |

End users need **nothing** installed.

---

## Project structure

```
bb-webp-converter/
├── webp2png.py          # Application source
├── build_exe.bat        # One-click Windows build script
├── requirements.txt     # Python dependencies
└── README.md
```

---

## License

MIT — do whatever you want with it.
