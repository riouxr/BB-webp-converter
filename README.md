# WebP → PNG Converter

A simple drag-and-drop desktop app that converts `.webp` images to `.png`.
- **No FFmpeg required** — uses Python's Pillow library directly
- **Standalone** — runs as a single `.exe`, no installation needed
- Saves the `.png` next to the original with the same filename

---

## Build the .exe (one-time setup)

You only need Python installed on YOUR PC to build the app.
After building, you can share `WebP2PNG.exe` with anyone — they need nothing installed.

**Steps:**

1. Install Python 3.9+ from https://www.python.org/downloads/
   _(Check "Add Python to PATH" during setup)_

2. Double-click **`build_exe.bat`**

3. Find your app at **`dist\WebP2PNG.exe`**

That's it. Copy the `.exe` anywhere you like.

---

## Usage

1. Launch `WebP2PNG.exe`
2. Drag one or more `.webp` files onto the drop zone
3. The converted `.png` files appear next to the originals instantly

---

## Technical notes

- Conversion via [Pillow](https://python-pillow.org/) — handles all WebP variants (lossy, lossless, animated first-frame)
- DnD via [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2)
- Packaged with [PyInstaller](https://pyinstaller.org/)
