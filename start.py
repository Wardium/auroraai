import threading
import subprocess
import os
import signal
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
            print(f"Terminated process {process.pid} for {process.args[1]}")
        except Exception as e:
            print(f"Failed to terminate process {process.pid}: {e}")

def esc_listener():
    # Listen for Escape key to terminate processes
    print("Press 'Escape' to terminate all processes.")
    keyboard.wait("esc")  # Block until 'esc' key is pressed
    print("Escape key pressed! Terminating subprocesses...")
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

        print("Scripts are running. Press 'Escape' or 'Ctrl+C' to stop both.")
        
        # Keep the main thread running (could replace this with UI or other logic)
        script1_thread.join()
        script2_thread.join()

    except KeyboardInterrupt:
        print("Interrupt received. Terminating subprocesses...")
        terminate_processes()  # Stop all subprocesses safely
        print("All subprocesses terminated. Exiting program.")
