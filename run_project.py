import os
import sys
import subprocess

# Define relative paths
VENV_DIR = os.path.join(os.getcwd(), "venv")
REQ_FILE = os.path.join(os.getcwd(), "requirements.txt")
MAIN_SCRIPT = os.path.join(os.getcwd(), "main.py")

# Determine Python executable for virtual environment
PYTHON_EXEC = os.path.join(VENV_DIR, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(VENV_DIR, "bin", "python")

def create_venv():
    """Create virtual environment if it doesn't exist"""
    if not os.path.exists(VENV_DIR):
        print("📌 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    else:
        return True

def install_dependencies():
    """Ensure dependencies are installed and compatible"""
    print("📌 Upgrading pip and reinstalling core dependencies...")
    subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    # **Fix numpy & pandas incompatibility**
    print("⚠️ Forcing numpy installation to prevent binary issues...")
    subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "--no-cache-dir", "--force-reinstall", "numpy"], check=True)

    print("📌 Installing all dependencies from requirements.txt...")
    subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "--no-cache-dir", "-r", REQ_FILE], check=True)

def run_script():
    """Run the main script inside the virtual environment"""
    print("🚀 Running main.py...")
    subprocess.run([PYTHON_EXEC, MAIN_SCRIPT], check=True)

if __name__ == "__main__":
    try:
        if create_venv():
            pass
        else:
            install_dependencies()
        run_script()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
