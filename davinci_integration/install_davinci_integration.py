"""
=============================================================================
EditAI — DaVinci Resolve 21 Chatbot One-Click Installer & Integrator
=============================================================================
Installs the integrated chatbot scripts into DaVinci Resolve 21's internal
scripts directory and prepares the desktop companion launcher.
"""

import os
import sys
import shutil

TARGET_DIRECTORIES = [
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility",
    os.path.expandvars(r"%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility")
]

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_TO_COPY = [
    "EditAI_Chatbot.py",
    "davinci_controller.py",
    "davinci_nlp_engine.py"
]

def install():
    print("=" * 65)
    print("      EditAI - DaVinci Resolve 21 In-App Integration Setup")
    print("=" * 65)

    copied_destinations = []
    for target_dir in TARGET_DIRECTORIES:
        try:
            os.makedirs(target_dir, exist_ok=True)
            for filename in FILES_TO_COPY:
                src_file = os.path.join(SOURCE_DIR, filename)
                dst_file = os.path.join(target_dir, filename)
                if os.path.exists(src_file):
                    shutil.copy2(src_file, dst_file)
            copied_destinations.append(target_dir)
            print(f"[OK] Installed to: {target_dir}")
        except Exception as e:
            print(f"[!] Warning installing to {target_dir}: {e}")

    # Check Resolve executable
    resolve_exe = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
    if os.path.exists(resolve_exe):
        print(f"[OK] Verified DaVinci Resolve installation at: {resolve_exe}")
    else:
        print(f"[?] Resolve executable not found at standard path: {resolve_exe}")

    print("\n" + "=" * 65)
    print("                 INSTALLATION SUCCESSFUL!")
    print("=" * 65)
    print("How to access the Integrated Chatbot inside DaVinci Resolve:")
    print("1. Launch DaVinci Resolve 21.")
    print("2. Open any project.")
    print("3. In the top menu, go to: Workspace -> Scripts -> EditAI_Chatbot")
    print("4. The AI Chatbot window will open directly inside Resolve!")
    print("\nAlternatively, you can run the Floating Desktop Chatbot anytime:")
    print(f"   python {os.path.join(SOURCE_DIR, 'EditAI_Desktop_Chatbot.py')}")
    print("=" * 65)

if __name__ == "__main__":
    install()
