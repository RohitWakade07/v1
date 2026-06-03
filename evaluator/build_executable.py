import os
import sys
import subprocess

def build():
    print("==========================================================")
    print("            PACKAGING EVALUATOR CLI EXECUTABLE            ")
    print("==========================================================")
    
    # 1. Install pyinstaller if not already present
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing PyInstaller...")
        # Installs PyInstaller inside the active virtualenv
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller==6.6.0"], check=True)
        
    # 2. Package the binary
    # Determine correct path separator based on OS
    sep = ";" if os.name == "nt" else ":"
    
    # Target files and output options
    main_script = os.path.join("evaluator", "main.py")
    scripts_dir = os.path.join("evaluator", "scripts")
    
    pyinstaller_bin = "pyinstaller"
    if os.name == "nt":
        venv_scripts = os.path.join(os.path.dirname(sys.executable), "pyinstaller.exe")
        if os.path.exists(venv_scripts):
            pyinstaller_bin = venv_scripts
            
    args = [
        "--onefile",
        f"--add-data={scripts_dir}{sep}evaluator/scripts",
        "--paths=.",
        "--name=artifact_evaluator",
        main_script
    ]
    
    print(f"Running command: {pyinstaller_bin} {' '.join(args)}")
    subprocess.run([pyinstaller_bin] + args, check=True)
    
    print("\n==========================================================")
    print("[OK] SUCCESS: packed single-binary executable compiled!")
    binary_name = "artifact_evaluator.exe" if os.name == "nt" else "artifact_evaluator"
    print(f"Location: {os.path.abspath(os.path.join('dist', binary_name))}")
    print("==========================================================")

if __name__ == "__main__":
    build()
