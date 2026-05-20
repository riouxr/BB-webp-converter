# BB Image Converter

A lightweight drag-and-drop desktop app for converting images on Windows. Accepts any format Pillow can read (WebP, AVIF, TGA, BMP, GIF, TIFF, PSD, ICO, and more) and outputs to **PNG, JPEG, WebP, BMP, TIFF, TGA or GIF**. No FFmpeg, no dependencies, no installation required for end users.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

- **Drag & drop** — drop one or many image files at once
- **7 output formats** — PNG, JPEG, WebP, BMP, TIFF, TGA, GIF, selectable via a button row
- **Saves in place** — output files are written next to the originals, same filename, new extension
- **Transparency-aware** — formats that don't support alpha (JPEG, BMP, GIF) automatically flatten transparent areas onto a white background
- **Conversion log** — live feed of every file processed with success/error counts
- **Zero install for end users** — ships as a single `.exe`, nothing else needed

---

## Screenshot

![BB Image Converter](screenshot.png)

---

## Getting the app

### Option A — Download the latest release (easiest)

Head to the [**Releases page**](https://github.com/riouxr/BB-webp-converter/releases/latest) and download **`BBImageConverter.exe`** from the latest release. That's it — no installation, no Python needed. Just run it.

### Option B — Build it yourself

You need **Python 3.9+** installed. That's it.

1. Clone or download this repo
2. Double-click **`build_exe.bat`**
3. Find your app at **`dist\BBImageConverter.exe`**

The `.exe` is fully self-contained — copy it anywhere, share it with anyone.

### Option C — Run from source

```bash
pip install -r requirements.txt
python bb_image_converter.py
```

---

## Building from source

`build_exe.bat` handles everything automatically:

```
1. Verifies Python is available
2. pip installs all dependencies
3. Calls PyInstaller with the correct flags
4. Outputs dist\BBImageConverter.exe
```

Build time is roughly 30–60 seconds. The resulting `.exe` is ~15–20 MB (Python runtime + Pillow bundled in).

---

## How it works

- **No FFmpeg** — conversion is handled entirely by [Pillow](https://python-pillow.org/), which supports a wide range of formats out of the box. Supported input formats are detected automatically at runtime via `Image.registered_extensions()`.
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
├── bb_image_converter.py   # Application source
├── BBImageConverter.spec   # PyInstaller spec file
├── build_exe.bat           # One-click Windows build script
├── requirements.txt        # Python dependencies
└── README.md
```

---

## License

MIT — do whatever you want with it.
