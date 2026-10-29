#!/usr/bin/env python3
"""
AI Video Studio - Prototype Launcher
Starts the FastAPI backend and serves the React frontend at http://127.0.0.1:8000
"""

import sys
import webbrowser
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from sample_media.generate_samples import generate_sample_assets

def main():
    print("=" * 60)
    print("      AI Video Studio - Intelligent Video Editor")
    print("=" * 60)
    print("[1/2] Verifying sample media assets...")
    try:
        generate_sample_assets()
        print("      Sample assets ready in backend/sample_media/")
    except Exception as e:
        print(f"      Notice: {e}")

    print("[2/2] Starting application server...")
    print("      URL: http://127.0.0.1:8000")
    print("      Press Ctrl+C to terminate.")
    print("=" * 60)

    # Automatically open browser after 1 second
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
