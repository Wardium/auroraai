import threading
import subprocess
import os
import signal
import colorama
from colorama import Fore, Style
from colorama import just_fix_windows_console
just_fix_windows_console()
import keyboard  # Install using `pip install keyboard`

# List to track subprocesses
subprocesses = []

def run_script(script_name):
    # Start a subprocess and append it to the list
    process = subprocess.Popen(["python", script_name])
    subprocesses.append(process)
    process.wait()  # Wait for this process to finish (keeps thread alive)

def terminate_processes():
    # Safely terminate all tracked processes
    for process in subprocesses:
        try:
            os.kill(process.pid, signal.SIGTERM)  # Send terminate signal
            process.wait()  # Ensure the process is terminated
            print(Fore.RED + f"Terminated process {process.pid} for {process.args[1]}" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Failed to terminate process {process.pid}: {e}" + Style.RESET_ALL)

def esc_listener():
    # Listen for Escape key to terminate processes
    keyboard.wait("esc")  # Block until 'esc' key is pressed
    print(Fore.RED + "Escape key pressed! Terminating Aurora..." + Style.RESET_ALL)
    terminate_processes()  # Stop all subprocesses safely
    os._exit(0)  # Exit the main script immediately

if __name__ == "__main__":
    try:
        # Start listener thread for Escape key
        esc_thread = threading.Thread(target=esc_listener, daemon=True)
        esc_thread.start()

        # Start both scripts as threads
        script1_thread = threading.Thread(target=run_script, args=("aurora.py",))
        script2_thread = threading.Thread(target=run_script, args=("gui.py",))
        
        script1_thread.start()
        script2_thread.start()

        print(Fore.GREEN + "Aurora is running. Press 'Escape' or 'Ctrl+C' to stop." + Style.RESET_ALL)
        
        # Keep the main thread running (could replace this with UI or other logic)
        script1_thread.join()
        script2_thread.join()

    except KeyboardInterrupt:
        print(Fore.RED + "Interrupt received. Terminating Aurora..." + Style.RESET_ALL)
        terminate_processes()  # Stop all subprocesses safely
        print(Fore.RED + "All subprocesses terminated. Exiting Aurora." + Style.RESET_ALL)
