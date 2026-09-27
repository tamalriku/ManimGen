# 🎬 Manim Render Studio

**Manim Render Studio** is a fully local, browser-based desktop application designed to write, preview, and render high-quality mathematical and programmatic animations using [Manim Community Edition](https://www.manim.community/).

Designed specifically for local execution with **zero timeouts**, **unlimited render lengths**, and **100% privacy**.

---

## ✨ Features

- **In-Browser Code Editor**: Fixed-height editor with internal scrollbars and syntax highlighting—no infinite page scrolling when pasting long code.
- **1-Click Local Launcher**: Includes `run_studio.bat` for automated 1-click Windows setup, virtual environment creation, and instant browser launching.
- **Unlimited Local Rendering**: Zero timeouts—render complex, multi-minute scenes at high FPS without cloud restrictions.
- **Robust LaTeX & Fallback Engine**:
  - Native LaTeX equation rendering (`MathTex` & `Tex`) via MiKTeX / TeX Live.
  - Automatic `SafeMathTex` polyfill fallback to `Text(...)` if LaTeX is not installed on the system, preventing render crashes.
- **Customizable Render Profiles**:
  - **Aspect Ratios**: `16:9` (Widescreen), `9:16` (Reels/Shorts/TikTok), `1:1` (Instagram), `3:2`, `4:3`, `5:4`, `21:9` (Ultrawide).
  - **Resolutions**: `720p`, `1080p`, and `4K`.
  - **Frame Rates**: `24 fps` (cinematic), `30 fps` (standard), `60 fps` (ultra-smooth).
  - **Backgrounds**: Solid colors, 2-color gradients (Vertical, Horizontal, Diagonal), and Alpha Transparency (.mov).
- **Direct Base64 Video Downloads**: Fast client-side video downloading directly from your local server.
- **Automatic Scene Detection**: Auto-detects `Scene` class names in uploaded or pasted Python scripts.

---

## 💻 Local Windows Installation & Quick Start

Running locally gives you **unlimited render length**, **zero quota constraints**, and **100% private rendering**.

### Method 1: Automated 1-Click Launcher (Recommended for Windows)

1. **Clone the Repository**:
   ```cmd
   git clone https://github.com/tamalriku/ManimGen.git
   cd ManimGen
   ```

2. **Run the Batch Script**:
   Double-click `run_studio.bat` (or run it in Command Prompt):
   ```cmd
   run_studio.bat
   ```

   **What `run_studio.bat` does automatically**:
   - Detects Python 3.10+ on your system PATH.
   - Creates a Python virtual environment (`venv`) on first run.
   - Installs all dependencies (`manim`, `gradio`, `imageio-ffmpeg`, `pillow`, `numpy`).
   - Automatically opens your default web browser to **`http://localhost:7860`**.

> [!IMPORTANT]
> Keep the black Command Prompt window open while using the Studio. Closing the window stops the local server.

---

### Method 2: Manual Terminal Setup

1. **Clone & Navigate**:
   ```bash
   git clone https://github.com/tamalriku/ManimGen.git
   cd ManimGen
   ```

2. **Create & Activate Virtual Environment**:
   - **Windows (CMD/PowerShell)**:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Studio**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://localhost:7860`.

---

## 📐 LaTeX Support & Setup

Manim Render Studio supports mathematical formula rendering using `MathTex` and `Tex`.

### Installing LaTeX on Windows (Native MathTex)

For full LaTeX math rendering locally, install **MiKTeX**:
1. Open Command Prompt and run:
   ```cmd
   winget install --id MiKTeX.MiKTeX
   ```
2. Or download the installer from [miktex.org/download](https://miktex.org/download).
3. `app.py` automatically detects MiKTeX at `~\AppData\Local\Programs\MiKTeX\miktex\bin\x64` and adds `latex.exe` and `dvisvgm.exe` to PATH.

### Automatic Fallback (No LaTeX Installed)

If LaTeX is not installed on your system, **Manim Render Studio will NOT crash**. 
It includes a built-in `SafeMathTex` polyfill that automatically converts LaTeX math strings (e.g. `\text{Duty Cycle} = \frac{T_{ON}}{T_{period}} \times 100\%`) into readable text format and renders them using standard system fonts via `Text(...)`.

---

## 🚀 Usage Guide

1. **Paste or Upload Code**:
   Paste your Python script into the code editor or click **Upload .py File**.
2. **Select Scene Class**:
   Choose your target `Scene` class from the dropdown next to the render button.
3. **Configure Options**:
   Open **⚙️ Render Settings** to customize aspect ratio, resolution (720p/1080p/4K), frame rate (24/30/60 FPS), and background mode.
4. **Render & Download**:
   Click **🚀 Render Video**. When rendering completes, watch the preview and click **📥 Direct Download**.

---

## ⚙️ Supported Render Profiles

| Setting | Options | Description |
| :--- | :--- | :--- |
| **Aspect Ratios** | `16:9` · `9:16` · `1:1` · `3:2` · `4:3` · `5:4` · `21:9` | Widescreen, Shorts/Reels/TikTok, Instagram post, and Ultrawide. |
| **Resolutions** | `720p` · `1080p` · `4K` | Resolution scaling for target aspect ratio. |
| **Frame Rates** | `24 fps` · `30 fps` · `60 fps` | Cinematic (24), Web standard (30), Ultra-smooth (60). |
| **Background Modes** | **Solid Color** · **Gradient** · **Transparent** | Custom background color picker, 2-color gradient compositing via FFmpeg, or alpha MOV. |

---

## 🛠️ Tech Stack

- **[Python](https://www.python.org/)** (v3.10+) – Core engine
- **[Gradio](https://www.gradio.app/)** (v5.0+) – Web interface
- **[Manim Community Edition](https://www.manim.community/)** – Explanatory math animation engine
- **[FFmpeg](https://ffmpeg.org/)** (via `imageio-ffmpeg`) – Video encoding & gradient compositing
- **[MiKTeX / TeX Live](https://miktex.org/)** – LaTeX formula typesetting
- **[Pillow & NumPy](https://python-pillow.org/)** – Texture generation and image processing
