import os
import sys
import subprocess

# Define relative paths
VENV_DIR = os.path.join(os.getcwd(), "venv")
REQ_FILE = os.path.join(os.getcwd(), "requirements.txt")
MAIN_SCRIPT = os.path.join(os.getcwd(), "main.py")
CONNECTION_SCRIPT = os.path.join(os.getcwd(), "connection.py")


# Determine Python executable for virtual environment
PYTHON_EXEC = os.path.join(VENV_DIR, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(VENV_DIR, "bin", "python")

def pull_latest_changes():
    """Pull the latest changes from the main branch."""
    print("📥 Pulling latest changes from main branch...")
    subprocess.run(["git", "checkout", "main"], check=True)  # Ensure we are on the main branch
    subprocess.run(["git", "pull", "origin", "main"], check=True)  # Pull latest changes

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
    print("Press 1 to run job applications")
    print("Press 2 to run linkedin connection bot")
    choice = int(input())
    if choice == 1:
        print("🚀 Running job applications...")
        subprocess.run([PYTHON_EXEC, MAIN_SCRIPT], check=True)
    elif choice ==2:
        print("🚀 Running linkedin connection bot")
        subprocess.run([PYTHON_EXEC, CONNECTION_SCRIPT], check=True)
    else:
        print("Uhhh ohhhh!!! Wrong choice.")

if __name__ == "__main__":
    try:
        pull_latest_changes()  # Ensure we pull the latest changes before doing anything else
        if create_venv():
            pass
        else:
            install_dependencies()
        run_script()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
