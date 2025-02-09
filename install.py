import os
import sys
import subprocess
import platform

def run_command(command, check=True):
    """Runs a shell command safely."""
    try:
        subprocess.run(command, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")

def install_pip_packages():
    """Installs common Python dependencies."""
    print("Installing Python dependencies...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    run_command(f"{sys.executable} -m pip install -r requirements.txt")

    system = platform.system()
    if system == "Windows":
        run_command(f"{sys.executable} -m pip install psutil pywin32")
    elif system == "Linux":
        run_command(f"{sys.executable} -m pip install psutil")
        run_command("sudo apt install xdotool || sudo pacman -S xdotool || sudo dnf install xdotool")
    elif system == "Darwin":  # macOS
        run_command(f"{sys.executable} -m pip install psutil pyobjc-framework-AppKit")

def install_ffmpeg():
    """Guides the user to install FFmpeg."""
    print("\nFFmpeg is required for this project.")
    if platform.system() == "Windows":
        print("Download it from: https://www.ffmpeg.org")
    else:
        run_command("sudo apt install ffmpeg || sudo pacman -S ffmpeg || sudo dnf install ffmpeg || brew install ffmpeg")

def setup_repository():
    """Clones and sets up the Aurora AI repository."""
    repo_url = "https://github.com/Wardium/auroraai.git"
    repo_name = "auroraai"
    
    if not os.path.exists(repo_name):
        print("Cloning repository...")
        run_command(f"git clone {repo_url}")
    
    os.chdir(repo_name)

def main():
    print("Setting up Aurora AI...")
    
    time.sleep(3)
    
    # Step 2: Install FFmpeg
    install_ffmpeg()
    time.sleep(3)
    # Step 3: Install Python Dependencies
    install_pip_packages()
    time.sleep(1)
    print("\nInstallation complete! You may need to restart your terminal or system for changes to take effect.")

if __name__ == "__main__":
    main()
