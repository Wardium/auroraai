import tkinter as tk
from tkinter import messagebox
import pygame
import os
import threading
from PIL import Image, ImageTk
import settings
import google.generativeai as genai
stop_event = threading.Event()

def music_player(music_file):
    # Initialize pygame mixer for music playing
    pygame.mixer.init()
    
    def name(name):
        """
        Simplifies a conversation history using Gemini AI, extracting the key information (i.e., the file name).
        """
        name_file = "Unknown"
        
        # Prepare the prompt for AI
        prompt_template = (
            "Only respond with the name of the file that you would assume. "
            "Please, for the following message, return what you would assume is the real name of the file name (e.g., 'hi_sound.mp3' = 'hi'):\n\n" + name
        )

        # Configure and initialize the model
        genai.configure(api_key=settings.api)
        model = genai.GenerativeModel('gemini-1.5-flash')
    
        # Use the AI model to generate content
        simplified_message = model.generate_content(prompt_template)

        # Extract the text from the response object and strip any extra whitespace
        simplified_text = simplified_message.text.strip()

        # Return the AI-generated name
        return simplified_text
    
    name_file = name(os.path.basename(music_file))

    if not os.path.isfile(music_file):
        messagebox.showerror("Error", "Invalid music file.")
        return

    # Load the music
    pygame.mixer.music.load(music_file)

    # Create the main window
    root = tk.Tk()
    root.title("Music Player")
    root.geometry("170x75+25+75")  # Slightly larger to center items neatly
    root.overrideredirect(True)  # Removes the window frame
    root.attributes("-topmost", True)  # Keep the window always on top

    # Playing status and controls
    is_paused = False
    is_muted = False

    def toggle_play_pause():
        nonlocal is_paused
        if is_paused:
            pygame.mixer.music.unpause()
            root.after(0, play_pause_button.config, {"image": pause_img})  # Schedule update in main thread
        else:
            pygame.mixer.music.pause()
            root.after(0, play_pause_button.config, {"image": play_img})  # Schedule update in main thread
        is_paused = not is_paused

    def stop_music():
        stop_event.set()  # Signal the thread to stop
        pygame.mixer.init()
        pygame.mixer.music.stop()
        root.quit()

    def toggle_mute():
        nonlocal is_muted
        if is_muted:
            pygame.mixer.music.set_volume(1)
            root.after(0, mute_button.config, {"image": mute_img})  # Schedule update in main thread
        else:
            pygame.mixer.music.set_volume(0)
            root.after(0, mute_button.config, {"image": unmute_img})  # Schedule update in main thread
        is_muted = not is_muted

    def monitor_music():
        while True:
            if not pygame.mixer.music.get_busy() and not is_paused:
                stop_event.set()  # Signal the thread to stop
                root.quit()
                break
            threading.Event().wait(1)

    # Load images
    def load_image(path, size=(32, 32)):
        img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    play_img = load_image("src/musicplayer/play.png")
    pause_img = load_image("src/musicplayer/pause.png")
    stop_img = load_image("src/musicplayer/stop.png")
    mute_img = load_image("src/musicplayer/mute.png")
    unmute_img = load_image("src/musicplayer/unmute.png")

    # Rounded canvas background
    canvas = tk.Canvas(root, width=220, height=120, bg="black", highlightthickness=0)
    canvas.place(x=0, y=0)

    # Function to draw a rounded rectangle
    def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius, fill_color):
        canvas.create_arc(x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, fill=fill_color, outline="")
        canvas.create_arc(x2 - radius * 2, y1, x2, y1 + radius * 2, start=0, extent=90, fill=fill_color, outline="")
        canvas.create_arc(x1, y2 - radius * 2, x1 + radius * 2, y2, start=180, extent=90, fill=fill_color, outline="")
        canvas.create_arc(x2 - radius * 2, y2 - radius * 2, x2, y2, start=270, extent=90, fill=fill_color, outline="")
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill_color, outline="")
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill_color, outline="")

    # Draw the rounded rectangle for the canvas
    draw_rounded_rectangle(canvas, 0, 0, 220, 120, radius=20, fill_color="black")

    # Set up the text and buttons
    filename_label = tk.Label(
        root, 
        text=name_file, 
        bg="black", 
        fg="white", 
        font=("Arial", 10),
        anchor="center"
    )
    filename_label.place(relx=0.5, rely=0.2, anchor="center")

    stop_button = tk.Button(
        root, 
        image=stop_img, 
        command=stop_music, 
        bg="black", 
        bd=0, 
        activebackground="black", 
        highlightthickness=0
    )
    stop_button.place(relx=0.2, rely=0.6, anchor="center")

    play_pause_button = tk.Button(
        root, 
        image=pause_img, 
        command=toggle_play_pause, 
        bg="black", 
        bd=0, 
        activebackground="black", 
        highlightthickness=0
    )
    play_pause_button.place(relx=0.5, rely=0.6, anchor="center")

    mute_button = tk.Button(
        root, 
        image=mute_img, 
        command=toggle_mute, 
        bg="black", 
        bd=0, 
        activebackground="black", 
        highlightthickness=0
    )
    mute_button.place(relx=0.8, rely=0.6, anchor="center")

    # Start playing the music
    pygame.mixer.music.play()

    # Start a thread to monitor the music status
    threading.Thread(target=monitor_music, daemon=True).start()

    # Start the GUI loop
    root.mainloop()

# Example usage
# music_player("path/to/your/music/file.mp3")

# To call the function with the file path
# Example: music_player("path/to/your/music/file.mp3")
