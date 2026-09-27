"""
Manim Render Studio — A browser-based Manim animation renderer.

Deploy on Hugging Face Spaces (Docker SDK) to render Manim scenes
from user-submitted Python code.

SECURITY WARNING:
    This application executes arbitrary user-supplied Python code via the
    `manim` CLI. It is NOT safe for fully public, untrusted multi-tenant
    deployment without proper sandboxing (e.g. gVisor, nsjail, Firecracker).
    The denylist check below is a soft heuristic guard only — it is trivially
    bypassable and is NOT a substitute for real isolation.
    For a personal / portfolio Space this is acceptable.
"""

import os
import re
import time
import base64
import tempfile
import subprocess
import shutil
import gradio as gr
import numpy as np
from PIL import Image

OUTPUT_DIR = os.path.abspath("output_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Automatic ffmpeg fallback using imageio_ffmpeg if system ffmpeg is missing
if shutil.which("ffmpeg") is None:
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass

# ZeroGPU support: only enable when running ON Hugging Face Spaces environment
IS_ON_HF_SPACES = "SPACE_ID" in os.environ or "SYSTEM" in os.environ
if IS_ON_HF_SPACES:
    try:
        import spaces
        ZEROGPU_AVAILABLE = True
    except ImportError:
        ZEROGPU_AVAILABLE = False
else:
    ZEROGPU_AVAILABLE = False

# -------------------------------------------------------------------------
# CONSTANTS & CONFIGURATION
# -------------------------------------------------------------------------

RESOLUTION_MAP = {
    "16:9": {"720p": (1280, 720), "1080p": (1920, 1080), "4K": (3840, 2160)},
    "9:16": {"720p": (720, 1280), "1080p": (1080, 1920), "4K": (2160, 3840)},
    "1:1": {"720p": (720, 720), "1080p": (1080, 1080), "4K": (2160, 2160)},
    "3:2": {"720p": (1080, 720), "1080p": (1620, 1080), "4K": (3240, 2160)},
    "4:3": {"720p": (960, 720), "1080p": (1440, 1080), "4K": (2880, 2160)},
    "5:4": {"720p": (900, 720), "1080p": (1350, 1080), "4K": (2700, 2160)},
    "21:9": {"720p": (1680, 720), "1080p": (2520, 1080), "4K": (5040, 2160)}
}

# Soft-guard denylist: blocks obviously dangerous patterns.
# This is trivially bypassable and NOT a substitute for real sandboxing.
DENYLIST_PATTERNS = [
    r"\bos\.system\s*\(",
    r"\bsubprocess\b",
    r"\bsocket\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\b__import__\s*\(",
    r"\bimportlib\b",
    r"\bshutil\.rmtree\b",
]

DEFAULT_CODE = """from manim import *

class ManimRenderStudio(Scene):
    def construct(self):
        # Title
        title = Text("Manim Render Studio", font_size=48)
        title.set_color_by_gradient(BLUE, PURPLE)
        self.play(Write(title))
        self.wait(0.5)
        self.play(title.animate.to_edge(UP))

        # Animated circle
        circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        self.play(Create(circle))
        self.play(circle.animate.set_fill(PURPLE, opacity=0.6))

        # Math equation (Text works on all systems without LaTeX)
        equation = Text("e^(iπ) + 1 = 0", font_size=54)
        equation.next_to(circle, DOWN, buff=0.5)
        self.play(Write(equation))
        self.wait(1)

        # Transform
        square = Square(side_length=3, color=YELLOW, fill_opacity=0.3)
        self.play(Transform(circle, square))
        self.wait(1)
"""

# -------------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------------

def check_denylist(code: str) -> list:
    """Soft guard check against dangerous imports/calls (regex-based)."""
    found = []
    for pattern in DENYLIST_PATTERNS:
        if re.search(pattern, code):
            # Extract a human-readable label from the pattern
            label = pattern.replace(r"\b", "").replace(r"\s*\(", "()").replace(r"\(", "()")
            label = re.sub(r"\(\?<!.*?\)", "", label)  # strip lookbehind
            found.append(label)
    return found

def extract_scenes(code: str):
    """Auto-detect Scene class names using regex."""
    pattern = r"class\s+(\w+)\s*\(.*Scene.*\)"
    return re.findall(pattern, code)

def get_video_duration(video_path: str) -> float:
    """Get the duration of a video using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c + c for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_gradient_image(
    width: int, height: int, start_color: str, end_color: str, direction: str
) -> Image.Image:
    """Generate a gradient image using numpy and PIL."""
    start_rgb = np.array(hex_to_rgb(start_color), dtype=np.float64)
    end_rgb = np.array(hex_to_rgb(end_color), dtype=np.float64)

    if direction == "Vertical":
        # Interpolation factor varies along height (top=0, bottom=1)
        t = np.linspace(0, 1, height).reshape(height, 1, 1)
        gradient = (1 - t) * start_rgb + t * end_rgb               # (H, 1, 3)
        gradient = np.broadcast_to(gradient, (height, width, 3))    # (H, W, 3)
    elif direction == "Horizontal":
        t = np.linspace(0, 1, width).reshape(1, width, 1)
        gradient = (1 - t) * start_rgb + t * end_rgb               # (1, W, 3)
        gradient = np.broadcast_to(gradient, (height, width, 3))    # (H, W, 3)
    else:  # Diagonal
        tx = np.linspace(0, 1, width)
        ty = np.linspace(0, 1, height)
        xx, yy = np.meshgrid(tx, ty)
        t = ((xx + yy) / 2.0)[:, :, np.newaxis]                    # (H, W, 1)
        gradient = (1 - t) * start_rgb + t * end_rgb               # (H, W, 3)

    return Image.fromarray(np.clip(gradient, 0, 255).astype(np.uint8))

# -------------------------------------------------------------------------
# GRADIO EVENT HANDLERS
# -------------------------------------------------------------------------

def update_scene_dropdown(code: str):
    """Update dropdown choices based on parsed scenes in the code."""
    scenes = extract_scenes(code)
    if not scenes:
        return gr.update(choices=[], value=None)
    # Auto-select if only one
    val = scenes[0] if len(scenes) == 1 else scenes[0]
    return gr.update(choices=scenes, value=val)

def handle_file_upload(file_path):
    """Read uploaded .py file and populate the code editor.
    
    In Gradio 4.x+, file upload returns a string path, not a NamedString.
    """
    if file_path is None:
        return gr.update()
    # Gradio 4+ returns a file path string directly
    path = file_path if isinstance(file_path, str) else file_path.name
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def toggle_bg_options(bg_mode):
    """Show/hide background-specific options."""
    if bg_mode == "Solid Color":
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    elif bg_mode == "Gradient":
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)
    else: # Transparent
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

# Apply @spaces.GPU decorator only when running on ZeroGPU hardware.
# This requests a GPU allocation for the duration of the render call.
# Manim itself is CPU-based, but ZeroGPU requires at least one decorated function.
if ZEROGPU_AVAILABLE:
    @spaces.GPU(duration=120)
    def render_manim(code, scene_name, aspect_ratio, resolution, bg_mode, solid_color,
                     grad_start, grad_end, grad_dir, fps, progress=gr.Progress()):
        return _render_manim_impl(code, scene_name, aspect_ratio, resolution, bg_mode,
                                  solid_color, grad_start, grad_end, grad_dir, fps, progress)
else:
    def render_manim(code, scene_name, aspect_ratio, resolution, bg_mode, solid_color,
                     grad_start, grad_end, grad_dir, fps, progress=gr.Progress()):
        return _render_manim_impl(code, scene_name, aspect_ratio, resolution, bg_mode,
                                  solid_color, grad_start, grad_end, grad_dir, fps, progress)

def generate_download_html(file_path: str) -> str:
    """Generate a client-side Data URI download button for 100% reliable download in Private HF Spaces."""
    if not file_path or not os.path.exists(file_path):
        return ""
    
    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    mime = "video/mp4" if ext == ".mp4" else "video/quicktime"
    
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        data_uri = f"data:{mime};base64,{b64}"
        size_mb = len(file_bytes) / (1024 * 1024)
        
        return f"""
        <div style="margin: 12px 0;">
            <a href="{data_uri}" download="{filename}" style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: #ffffff;
                font-weight: 700;
                font-size: 16px;
                padding: 14px 28px;
                border-radius: 10px;
                text-decoration: none;
                box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
                transition: all 0.2s ease-in-out;
                width: 100%;
                box-sizing: border-box;
                text-align: center;
            ">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                📥 Direct Download ({filename} — {size_mb:.2f} MB)
            </a>
        </div>
        """
    except Exception as e:
        return f"<p style='color:red;'>Failed to generate direct download link: {e}</p>"

TEX_POLYFILL_HEADER = """# Automatic Safe Fallback for MathTex / Tex when LaTeX is not installed
import os
import re
import shutil
import manim

def _clean_tex_to_text(tex_str: str) -> str:
    s = str(tex_str)
    s = re.sub(r'\\\\text\{([^}]+)\}', r'\\1', s)
    s = re.sub(r'\\\\frac\{([^}]+)\}\{([^}]+)\}', r'(\\1 / \\2)', s)
    replacements = {
        '\\\\times': '×', '\\\\div': '÷', '\\\\%': '%', '\\\\approx': '≈',
        '\\\\neq': '≠', '\\\\leq': '≤', '\\\\geq': '≥', '\\\\infty': '∞',
        '\\\\pi': 'π', '\\\\theta': 'θ', '\\\\alpha': 'α', '\\\\beta': 'β',
        '\\\\gamma': 'γ', '\\\\delta': 'δ', '\\\\sigma': 'σ', '\\\\omega': 'ω',
        '\\\\,': ' ', '\\\\;': ' ', '\\\\quad': '  ', '\\\\{': '{', '\\\\}': '}',
        '\\\\cdot': '·', '\\\\pm': '±', '\\\\mp': '∓', '\\\\sqrt': '√'
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = re.sub(r'\\\\([a-zA-Z]+)', r'\\1', s)
    return s.strip()

if shutil.which("latex") is None and shutil.which("xelatex") is None:
    class SafeMathTex(manim.Text):
        def __init__(self, *tex_strings, font_size=48, color=None, **kwargs):
            kwargs.pop("tex_environment", None)
            kwargs.pop("tex_template", None)
            kwargs.pop("substrings_to_isolate", None)
            kwargs.pop("arg_separator", None)
            cleaned = [_clean_tex_to_text(s) for s in tex_strings]
            text_val = " ".join(cleaned) if cleaned else ""
            if not text_val:
                text_val = " "
            super().__init__(text_val, font_size=font_size, color=color, **kwargs)

    manim.MathTex = SafeMathTex
    manim.Tex = SafeMathTex
"""

def _render_manim_impl(code, scene_name, aspect_ratio, resolution, bg_mode, solid_color,
                       grad_start, grad_end, grad_dir, fps, progress=gr.Progress()):
    """Main rendering function."""
    # 1. Validation
    if not scene_name:
        return None, None, "", "Error: No Scene class selected. Please select one from the dropdown."
    
    denied = check_denylist(code)
    if denied:
        return None, None, "", f"Security Warning: Detected potentially dangerous keywords: {', '.join(denied)}. Rendering blocked."

    width, height = RESOLUTION_MAP[aspect_ratio][resolution]
    
    # 2. Setup Temporary Directory
    temp_dir = tempfile.mkdtemp(prefix="manim_render_")
    code_path = os.path.join(temp_dir, "scene.py")
    
    # Prepend LaTeX polyfill & background settings
    header = ""
    if shutil.which("latex") is None and shutil.which("xelatex") is None:
        header += TEX_POLYFILL_HEADER + "\n"
        
    if bg_mode == "Solid Color":
        header += f'from manim import config\nconfig.background_color = "{solid_color}"\n'
        
    processed_code = header + code
        
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(processed_code)

    # 3. Construct Manim CLI Command
    progress(0.2, desc="Starting Manim Render...")
    output_filename = "output.mov" if bg_mode == "Transparent" else "output.mp4"
    if bg_mode == "Gradient":
        output_filename = "transparent.mov"

    manim_cmd = [
        "manim", "render",
        "-r", f"{width},{height}",
        "--fps", str(fps),
        "-o", output_filename,
        code_path,
        scene_name
    ]
    
    if bg_mode in ["Transparent", "Gradient"]:
        manim_cmd.append("-t")

    # 4. Execute Manim
    progress(0.4, desc="Rendering Frames...")
    try:
        result = subprocess.run(manim_cmd, cwd=temp_dir, capture_output=True, text=True, timeout=120)
        log_output = result.stdout + "\n" + result.stderr
        if result.returncode != 0:
            if "tex_to_svg_file" in log_output or "latex" in log_output.lower() or "dvisvgm" in log_output.lower():
                log_output += (
                    "\n\n"
                    "===========================================================\n"
                    "💡 LATEX NOT INSTALLED NOTICE:\n"
                    "Your scene uses MathTex or Tex, which requires LaTeX (MiKTeX/TeX Live).\n"
                    "Options:\n"
                    "1. Install MiKTeX on Windows: run 'winget install MiKTeX.MiKTeX' in CMD.\n"
                    "2. Or replace MathTex(r'...') with standard Text('...') which works out-of-the-box!\n"
                    "===========================================================\n"
                )
            return None, None, "", f"Manim Error:\n{log_output}"
    except subprocess.TimeoutExpired as e:
        return None, None, "", f"Render timed out after 120 seconds:\n{e}"
    except Exception as e:
        return None, None, "", f"Execution failed:\n{e}"

    # Output paths inside manim's media folder
    generated_file = None
    for root, dirs, files in os.walk(temp_dir):
        if output_filename in files:
            generated_file = os.path.join(root, output_filename)
            break
            
    if not generated_file:
        return None, None, "", f"Error: Output file '{output_filename}' not found.\nLog:\n{log_output}"

    # 5. Handle Gradient Compositing
    final_output = generated_file
    if bg_mode == "Gradient":
        progress(0.8, desc="Compositing Gradient...")
        duration = get_video_duration(generated_file)
        grad_img_path = os.path.join(temp_dir, "gradient.png")
        grad_img = create_gradient_image(width, height, grad_start, grad_end, grad_dir)
        grad_img.save(grad_img_path)
        
        composited_file = os.path.join(temp_dir, "final_output.mp4")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", grad_img_path,
            "-i", generated_file,
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            composited_file
        ]
        
        try:
            ff_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
            if ff_result.returncode != 0:
                return None, None, "", f"FFmpeg Error:\n{ff_result.stderr}"
            final_output = composited_file
        except subprocess.TimeoutExpired as e:
            return None, None, "", f"FFmpeg timed out:\n{e}"

    # 6. Copy output to persistent allowed directory for Gradio file serving
    ext = os.path.splitext(final_output)[1]
    dest_filename = f"{scene_name}_{int(time.time())}{ext}"
    dest_path = os.path.join(OUTPUT_DIR, dest_filename)
    shutil.copy(final_output, dest_path)

    # Cleanup temporary build folder
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    html_download = generate_download_html(dest_path)
    progress(1.0, desc="Done!")
    return dest_path, dest_path, html_download, log_output

CUSTOM_CSS = """
/* Cap code input container height and enable internal scrolling */
.gr-code {
    max-height: 440px !important;
    overflow-y: auto !important;
}
.monaco-editor-container {
    max-height: 420px !important;
}
"""

# -------------------------------------------------------------------------
# GRADIO UI SETUP
# -------------------------------------------------------------------------

with gr.Blocks(title="Manim Render Studio", css=CUSTOM_CSS) as demo:
    gr.Markdown("# 🎬 Manim Render Studio\nWrite or upload Manim Python code to render beautiful mathematical animations!")
    gr.Markdown("*Note: This application executes user-provided code and is meant for local or trusted use only.*")
    
    with gr.Row():
        # LEFT COLUMN: Code Input & Controls
        with gr.Column(scale=1):
            code_input = gr.Code(
                value=DEFAULT_CODE,
                language="python",
                label="Manim Code",
                lines=16,
                max_lines=18
            )
            
            with gr.Row():
                scene_dropdown = gr.Dropdown(
                    label="Select Scene Class to Render",
                    choices=["ManimRenderStudio"],
                    value="ManimRenderStudio",
                    interactive=True,
                    scale=2
                )
                render_btn = gr.Button("🚀 Render Video", variant="primary", scale=1)
                
            file_upload = gr.File(
                label="Or Upload .py File", 
                file_types=[".py"]
            )
            
            with gr.Accordion("⚙️ Render Settings", open=True):
                with gr.Row():
                    aspect_ratio = gr.Dropdown(
                        label="Aspect Ratio",
                        choices=["16:9", "9:16", "1:1", "3:2", "4:3", "5:4", "21:9"],
                        value="16:9"
                    )
                    resolution = gr.Dropdown(
                        label="Resolution",
                        choices=["720p", "1080p", "4K"],
                        value="1080p"
                    )
                    fps = gr.Dropdown(
                        label="Frame Rate (fps)",
                        choices=["24", "30", "60"],
                        value="30"
                    )
                
                bg_mode = gr.Radio(
                    label="Background Mode",
                    choices=["Solid Color", "Gradient", "Transparent"],
                    value="Solid Color"
                )
                
                # Solid Color settings
                solid_color = gr.ColorPicker(label="Background Color", value="#000000", visible=True)
                
                # Gradient settings
                grad_start = gr.ColorPicker(label="Start Color", value="#1a1a2e", visible=False)
                grad_end = gr.ColorPicker(label="End Color", value="#16213e", visible=False)
                grad_dir = gr.Dropdown(
                    label="Gradient Direction", 
                    choices=["Vertical", "Horizontal", "Diagonal"], 
                    value="Vertical", 
                    visible=False
                )
            
        # RIGHT COLUMN: Output
        with gr.Column(scale=1):
            video_out = gr.Video(label="Rendered Video", interactive=False)
            download_html = gr.HTML(label="Direct Download Button")
            file_out = gr.File(label="Alternative File Link")
            
            with gr.Accordion("📋 Render Log", open=False):
                log_out = gr.Textbox(label="Console Output", lines=10, max_lines=20, interactive=False)
                
    # ---------------------------------------------------------------------
    # EVENT BINDING
    # ---------------------------------------------------------------------
    
    # When file uploaded, update code editor
    file_upload.upload(fn=handle_file_upload, inputs=file_upload, outputs=code_input)
    
    # When code changes, parse classes and update scene dropdown
    code_input.change(fn=update_scene_dropdown, inputs=code_input, outputs=scene_dropdown)
    
    # When background mode changes, toggle options
    bg_mode.change(
        fn=toggle_bg_options, 
        inputs=bg_mode, 
        outputs=[solid_color, grad_start, grad_end, grad_dir]
    )
    
    # Render button
    render_btn.click(
        fn=render_manim,
        inputs=[
            code_input, scene_dropdown, aspect_ratio, resolution, bg_mode, 
            solid_color, grad_start, grad_end, grad_dir, fps
        ],
        outputs=[video_out, file_out, download_html, log_out]
    )

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        allowed_paths=[OUTPUT_DIR, tempfile.gettempdir()]
    )
