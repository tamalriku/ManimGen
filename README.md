---
title: Manim Render Studio
emoji: 🎬
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 5.29.0
python_version: 3.11.0
app_file: app.py
pinned: false
license: mit
short_description: Render Manim animations in your browser
---

# 🎬 Manim Render Studio

**Manim Render Studio** is a browser-based, interactive environment designed to write, preview, and render high-quality mathematical and programmatic animations using [Manim Community Edition](https://www.manim.community/). 

Built with Gradio and deployed as a Hugging Face Space, this studio enables rapid prototyping of educational content, scientific visualizations, and social media clips without needing a local Python and TeX Live installation.

---

## ✨ Features

- **In-Browser Code Editing**: Write or paste Manim Python code directly with syntax-friendly formatting.
- **Customizable Render Profiles**: Tailor aspect ratio, resolution, frame rate, and background styling to your target platform.
- **LaTeX Math Rendering**: Native support for beautiful equations and typography via TeX Live.
- **Real-Time Render Logs**: Live terminal/stdout streaming to monitor progress and debug compilation errors.
- **Instant Video Playback**: Immediate video playback once rendering finishes.
- **One-Click Download**: Direct download link for high-quality MP4 exports.
- **Mobile & Social Presets**: Quick switching between standard widescreen (16:9) and vertical reels/shorts (9:16).

---

## 🚀 Usage Instructions

1. **Write Your Scene Code**:
   In the editor, define your scene by subclassing `Scene` (or `ThreeDScene`, `MovingCameraScene`, etc.):
   ```python
   from manim import *

   class InteractiveDemo(Scene):
       def construct(self):
           title = Title("Manim Render Studio")
           formula = MathTex(r"\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}")
           
           self.play(Write(title))
           self.wait(0.5)
           self.play(FadeIn(formula, shift=UP))
           self.play(formula.animate.scale(1.2).set_color(YELLOW))
           self.wait(1)
   ```

2. **Select Scene Name**:
   Enter the exact class name of the scene you want to render (e.g., `InteractiveDemo`).

3. **Configure Render Options**:
   - Choose your preferred resolution (e.g., `720p` for quick tests, `1080p` for final export).
   - Choose the target aspect ratio (16:9, 9:16, 1:1, etc.).
   - Set the frame rate (FPS) and background color.

4. **Click "Render Animation"**:
   Watch the live console output for Manim compilation and FFmpeg processing.

5. **Preview & Download**:
   Review the rendered video in the output video player and click the download button to save the MP4 file.

---

## ⚙️ Supported Render Options

| Setting | Options / Presets | Description |
| :--- | :--- | :--- |
| **Aspect Ratios** | `16:9` · `9:16` · `1:1` · `3:2` · `4:3` · `5:4` · `21:9` | Covers widescreen, vertical (Shorts/Reels), square (Instagram), and ultra-wide formats. |
| **Resolutions** | `720p` (e.g. 1280×720)<br>`1080p` (e.g. 1920×1080)<br>`4K` (e.g. 3840×2160) | Exact pixel dimensions depend on the chosen aspect ratio. A full lookup table is built in. |
| **Frame Rates** | `24 fps` · `30 fps` · `60 fps` | 24 fps for cinematic feel, 30 fps for standard web video (default), 60 fps for ultra-smooth motion. |
| **Background** | **Solid Color** (color picker)<br>**Gradient** (two colors + direction)<br>**Transparent** (alpha .mov) | Gradient composites a PIL-generated image under a transparent render via FFmpeg. |

---

## 📐 LaTeX Support

Manim Render Studio supports `Tex` and `MathTex` objects using system TeX Live installations.

### Pre-installed Packages
The Space environment comes pre-configured (via `packages.txt`) with essential TeX packages, including:
- `texlive-latex-base`
- `texlive-latex-extra`
- `texlive-fonts-recommended`
- `texlive-science` (provides `amsmath`, `amssymb`, `physics`, `mathtools`, and more)
- `texlive-latex-recommended`
- `dvisvgm`, `cm-super`, `ghostscript`

### Custom LaTeX Packages
If your scenes require specialized LaTeX packages (such as `tikz`, `chemfig`, or custom font packages), add them to `packages.txt` in the repo root:
```text
texlive-publishers
texlive-pstricks
```

---

## ⏱️ Resource & Timeout Limits

Please keep in mind the operational constraints of the Hugging Face Spaces environment:

- **Free-Tier Hardware Specs**: Free-tier Spaces run on **2 vCPUs** and **16 GB RAM**.
- **Execution Timeout**: Renders have a maximum processing timeout of **120 seconds (2 minutes)**.
- **Complex Scenes**: Scenes involving thousands of mathematical objects, extensive 3D meshes, raymarching, or high-density particle animations rendered at 4K may exceed the 120-second timeout.
- **Recommended Workflow**:
  1. Always verify and preview your animation at **720p / 24 fps** first for quick iteration.
  2. Once animation timing and positioning are confirmed, render at **1080p / 30 fps** or higher.
- **Ephemeral Storage**: Rendered outputs and cached video fragments are stored temporarily in a scratch directory and automatically pruned after download or session expiration to prevent disk exhaustion.

---

## 🔒 Security Notice

> [!WARNING]
> **Arbitrary Code Execution**: Manim scripts are executed as dynamic Python code. While the application runs inside an isolated HF Space environment, executing untrusted or arbitrary scripts poses inherent security risks. When deploying this space publicly, ensure strict sandboxing, avoid exposing secret environment variables, and monitor resource usage.

---

## 🛠️ Tech Stack

- **[Python](https://www.python.org/)** (v3.10+) – Core runtime environment
- **[Gradio](https://www.gradio.app/)** – Modern web UI and streaming response pipeline
- **[Manim Community](https://www.manim.community/)** – Python library for explanatory math animations
- **[FFmpeg](https://ffmpeg.org/)** – High-performance video encoding and post-processing
- **[TeX Live](https://www.tug.org/texlive/)** – Comprehensive TeX system for typesetting mathematical notation
- **[Pillow (PIL)](https://python-pillow.org/)** – Image processing, raster manipulation, and texture handling
