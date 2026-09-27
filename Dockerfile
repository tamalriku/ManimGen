# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Metadata labels
LABEL maintainer="MANIMGEN" \
      description="Manim Render Studio Gradio App on Hugging Face Spaces" \
      version="1.0"

# Set environment variables for Python and Gradio
ENV PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for Manim, Cairo, Pango, and LaTeX rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    build-essential \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    texlive-latex-recommended \
    dvisvgm \
    cm-super \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with UID 1000 (standard for Hugging Face Spaces)
# and prepare a writable render cache directory
RUN useradd -m -u 1000 user && \
    mkdir -p /tmp/manim_renders && \
    chown -R user:user /tmp/manim_renders && \
    chmod 777 /tmp/manim_renders

# Set the working directory
WORKDIR /app

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies without cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files and grant ownership to the non-root user
COPY --chown=user:user app.py README.md /app/

# Ensure workspace ownership
RUN chown -R user:user /app

# Switch to the non-root user
USER user

# Expose the default Gradio port
EXPOSE 7860

# Define entrypoint command to run the Gradio app
CMD ["python", "app.py"]
