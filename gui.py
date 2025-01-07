import tkinter as tk
from PIL import Image, ImageTk
import random
import math
import threading
import time
import os
import importlib
import api
import subprocess
from datetime import datetime
import colorama

sleep_timer = False
blinking = False
do_once = False
current_time = datetime.now().time()
is_timer_active = False
is_blink_active = False
timer_thread = None
blink_thread = None
sleep = False
blink_image = "src/eyes/waiting/blink_waiting.png"
waiting_eyes = "src/eyes/waiting/waiting.png"

class FloatingImageApp:
    
    def fade_in(self):
        """Fades the application window in slowly."""
        alpha = 0.0  # Initial transparency value
        increment = 0.01  # Increase in transparency per frame
        delay = 10  # Time in ms between updates

        def increment_alpha():
            nonlocal alpha
            if alpha < 1.0:  # Maximum transparency level
                alpha += increment
                self.root.attributes('-alpha', alpha)
                self.root.after(delay, increment_alpha)

        increment_alpha()
    
    def __init__(self, root):
        
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        root.title("Aurora AI")  # Set the window title
        root.iconbitmap("src/icon.ico")
        
        # Initialize the transparency to 0 (fully transparent)
        self.root.attributes('-alpha', 0.0)

        # Call the fade-in effect
        self.fade_in()
        
        # Initialize previous content as None
        self.previous_content = None

        # Load the initial image
        self.image_path = 'src/eyes/eyes.png'
        self.image = Image.open(self.image_path).resize((500, 500), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)

        # Create a canvas to hold the image
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Add the image to the canvas
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.CENTER, image=self.photo)

        # Initialize position and velocity
        self.x_pos = self.root.winfo_screenwidth() // 2
        self.y_pos = self.root.winfo_screenheight() // 2
        self.x_velocity = random.uniform(-0.5, 0.5)  # Initial velocity for x
        self.y_velocity = random.uniform(-0.5, 0.5)  # Initial velocity for y
        self.radius = 100  # Radius to limit movement
        self.center_x = self.x_pos
        self.center_y = self.y_pos

        # Physics parameters
        self.friction = 0.98  # Simulate gradual slowing
        self.acceleration = 0.01  # Gradual acceleration to change direction
        self.min_velocity = 0.1  # Minimum velocity to prevent stopping

        # Additional UI elements
        self.loading_throbber = None
        self.text_output = None
        self.waiting_image_id = None

        # Start the animation
        self.animate()

        # Start the API monitoring thread
        self.monitor_api()

        # Bind escape key to exit full screen
        self.root.bind('<Escape>', lambda e: self.root.destroy())

    def blink_function(self):
        global sleep, blink_image, blinking, do_once, is_blink_active
        
        blink_image = "src/eyes/waiting/blink_waiting.png"
        
        if sleep == True:
            print("Sleeping")
            return()
        print(f"Sleep: {sleep}")
        
        if blinking == True:
            return()
            
        if self.api.waiting == True:
            try:
                blink_image = "src/eyes/waiting/blink_waiting.png"
            except FileNotFoundError:
                pass  # Ignore if the image doesn't exist
        else:
            try:
                blink_image = "src/eyes/blink.png"
            except FileNotFoundError:
                pass  # Ignore if the image doesn't exist
                
        if sleep == True:
            print("Sleeping")
            return()
        print(Style.DIM + f"Sleep: {sleep}")
                
                
        if hasattr(api, 'emotion'):
            try:
                new_image_path = f"src/eyes/{api.emotion}.png"
                waiting_eyes = f"src/eyes/waiting/{api.emotion}.png"
            except FileNotFoundError:
                pass  # Ignore if the image doesn't exist
        
        while is_blink_active:
        
            if sleep == True:
                print("Sleeping")
                return()
            print(f"Sleep: {sleep}")
            
            blinking = True
            # Generate a random duration between 2 and 10 seconds (converted to seconds)
            duration = random.randint(2, 10)

            # Wait for the duration or until the timer is deactivated
            start_time = time.time()
            while is_blink_active and time.time() - start_time < duration:
                time.sleep(1)  # Check every second if the timer is still active
        
            if is_blink_active:
                new_image = Image.open(blink_image).resize((500, 500), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(new_image)
                self.canvas.itemconfig(self.image_id, image=self.photo)
            else:
                print("Blink was stopped before completion.")
                
            time.sleep(random.uniform(0.1, 0.4))
            
            if self.api.waiting == True:
                try:
                    new_image = Image.open(f"src/eyes/waiting/{api.emotion}.png").resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                    blink_image = "src/eyes/waiting/blink_waiting.png"
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist
            else:
                try:
                    new_image = Image.open(f"src/eyes/{api.emotion}.png").resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                    blink_image = "src/eyes/blink.png"
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist

            # Reset the timer if still active
            if not is_blink_active:
                blinking = False
                do_once = False

    def blinking_timer(self):
        global blinking, do_once, is_blink_active, blink_thread

        if not is_blink_active:
            if blinking == True:
                return
            else:
                is_blink_active = True
                blink_thread = threading.Thread(target=self.blink_function)
                blink_thread.daemon = True  # Allows the thread to exit when the main program exits
                blink_thread.start()

    def timer_function(self):
        global is_timer_active

        while is_timer_active:
            # Generate a random duration between 5 and 30 minutes (converted to seconds)
            duration = random.randint(60, 120)
            print(f"Timer started for {duration // 60} minutes.")

            # Wait for the duration or until the timer is deactivated
            start_time = time.time()
            while is_timer_active and time.time() - start_time < duration:
                time.sleep(1)  # Check every second if the timer is still active
            
            if is_timer_active:
                print("Timer completed!")
                self.sleep()
            else:
                print("Timer was stopped before completion.")

            # Reset the timer if still active
            if not is_timer_active:
                break

    def load_api_variables(self):
        # Dynamically reload the api.py file to reflect changes
        importlib.reload(api)
        self.api = api  # Make api variables available

    def animate(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Update velocity with slight random acceleration
        self.x_velocity += random.uniform(-self.acceleration, self.acceleration)
        self.y_velocity += random.uniform(-self.acceleration, self.acceleration)

        # Apply friction to smooth the movement
        self.x_velocity *= self.friction
        self.y_velocity *= self.friction

        # Ensure minimum velocity
        if abs(self.x_velocity) < self.min_velocity:
            self.x_velocity = self.min_velocity * (1 if self.x_velocity > 0 else -1)
        if abs(self.y_velocity) < self.min_velocity:
            self.y_velocity = self.min_velocity * (1 if self.y_velocity > 0 else -1)

        # Update position
        self.x_pos += self.x_velocity
        self.y_pos += self.y_velocity

        # Bounce off boundaries within radius and screen limits
        if abs(self.x_pos - self.center_x) > self.radius or not (250 < self.x_pos < screen_width - 250):
            self.x_velocity *= -1
        if abs(self.y_pos - self.center_y) > self.radius or not (250 < self.y_pos < screen_height - 250):
            self.y_velocity *= -1

        # Move the image
        self.canvas.coords(self.image_id, self.x_pos, self.y_pos)

        # Schedule the next frame
        self.root.after(16, self.animate)  # 60 FPS (16 ms per frame)

    def read_api_file(self):
        # Path to the api.py file
        api_file_path = 'api.py'
        if os.path.exists(api_file_path):
            with open(api_file_path, 'r') as file:
                return file.read()
        return None

    def load_api(self):
        """Loads and returns the API object dynamically from api.py"""
        # Read the current content of api.py
        current_content = self.read_api_file()

        # Create a new empty namespace (object-like)
        api_namespace = type('api', (object,), {})()

        # Dynamically execute the content of api.py and populate the api_namespace
        exec(current_content, globals(), vars(api_namespace))

        # Return the dynamically created api object
        return api_namespace
    
    def start_timer(self):
        global sleep_timer, is_timer_active, timer_thread

        if not is_timer_active:
            if sleep_timer == False:
                is_timer_active = True
                timer_thread = threading.Thread(target=self.timer_function)
                timer_thread.daemon = True  # Allows the thread to exit when the main program exits
                timer_thread.start()

    def stop_timer(self):
        global is_timer_active
        
        if sleep_timer == True:
            is_timer_active = False
            if timer_thread and timer_thread.is_alive():
                timer_thread.join()  # Wait for the thread to finish if necessary
                print("Timer has been stopped and reset.")

    def sleep(self):
        global sleep
        start_night = datetime.strptime("20:00", "%H:%M").time()  # 8:00 PM
        end_night = datetime.strptime("07:00", "%H:%M").time()    # 7:00 AM

        if (current_time >= start_night or current_time <= end_night):
            sleep = True
            new_image_path = f"src/eyes/sleep.png"
            new_image = Image.open(new_image_path).resize((500, 500), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(new_image)
            self.canvas.itemconfig(self.image_id, image=self.photo)
        else:
            sleep = False
    
    def monitor_api(self):
        
        global blink_image, sleep, do_once
        
        self.load_api_variables()
        
        # Read current content of the api.py file
        current_content = self.read_api_file()

        if current_content != self.previous_content:
            # If content has changed, update the previous content and check for variables
            self.previous_content = current_content

            # Dynamically evaluate variables from api.py using exec
            exec(current_content, globals(), locals())

            if sleep == True:
                if self.api.waiting == False:
                    sleep = False
                else:
                    if do_once == False:
                        do_once = True
                        print("Did Once ")
                        self.blinking_timer()
                    return()


            # Check the 'processing' variable
            if self.api.processing:
                if not self.loading_throbber:
                    self.loading_throbber = self.canvas.create_text(
                        self.root.winfo_screenwidth() - 50, 50,
                        text="",
                        fill="Blue",
                        font=("Helvetica", 20),
                        anchor=tk.SE
                    )
            else:
                if self.loading_throbber:
                    self.canvas.delete(self.loading_throbber)
                    self.loading_throbber = None

            # Check the 'emotion' variable
            if hasattr(api, 'emotion'):
                try:
                    new_image_path = f"src/eyes/{api.emotion}.png"
                    waiting_eyes = f"src/eyes/waiting/{api.emotion}.png"
                    new_image = Image.open(new_image_path).resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist

            # Check the 'output' variable
            if hasattr(api, 'output'):
                if not self.text_output:
                    self.text_output = self.canvas.create_text(
                        self.root.winfo_screenwidth() // 2,
                        self.root.winfo_screenheight() - 50,
                        text=api.output,
                        fill="white",
                        font=("Helvetica", 16)
                    )
                else:
                    self.canvas.itemconfig(self.text_output, text=api.output)


            if self.api.waiting == True:
                try:
                    new_image = Image.open(waiting_eyes).resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                    blink_image = "src/eyes/waiting/blink_waiting.png"
                    self.start_timer()
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist
            else:
                try:
                    new_image = Image.open(new_image_path).resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                    blink_image = "src/eyes/blink.png"
                    self.stop_timer()
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist
                
        # Schedule the next check
        
        if do_once == False:
            do_once = True
            print("Did Once ")
            self.blinking_timer()
        self.root.after(100, self.monitor_api)  # Check for updates every 100ms

def start_timer():
    global is_timer_active, timer_thread

    if not is_timer_active:
        is_timer_active = True
        timer_thread = threading.Thread(target=timer_function)
        timer_thread.daemon = True  # Allows the thread to exit when the main program exits
        timer_thread.start()

if __name__ == "__main__":
    import colorama
    from colorama import Fore, Style
    from colorama import just_fix_windows_console
    just_fix_windows_console()
    print(Style.DIM + "GUI Started.")
    root = tk.Tk()
    app = FloatingImageApp(root)
    root.mainloop()
