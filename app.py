import tkinter as tk
from tkinter import ttk
import threading
import time
import google.generativeai as genai
import colorama
from colorama import Fore, Style
import speech_recognition as sr
import os
from datetime import datetime
import re
from gtts import gTTS
import pygame
import subprocess
import sys

# --- Configuration and Settings ---
def check_and_run(file_name, script_to_run):
    # Check if the file exists in the current directory
    if not os.path.exists(file_name):
        print(f"{file_name} does not exist. Running {script_to_run}...")
        
        # Run the entire .py script in the same directory
        subprocess.run([sys.executable, script_to_run])

        # Exit the current script
        sys.exit()
    else:
        print(f"{file_name} exists.")

check_and_run('settings.py', 'config.py')
import settings

# --- Global Variables ---
input_text = ""
output = ""
send = False
emotion = "none"
personality = settings.personality_text + (
        #Bot Configuration, PLEASE DO NOT CHANGE
        "never immediatly end a coversation"
        "you will be given your entire history, please do not bring it up in conversation unless prompted or required to for accuracy"
        "your name is aurora, you are a fully scentient robot that looks mostly humanoid with some now humanoid parts"
        "never prefix your response with AI:"
        "If the conversation ends, finish your reply with '@END'"
        "every message will contain a date and time, this is for you to know when the message was sent, please do not call upon this in a response"
        "at the start of the response always put your current emotion from these 6 choices '@E_SAD' '@E_HAPPY' '@E_MAD' '@E_NERVOUS' '@E_NEUTRAL' '@E_SCARED' without anything around it"
        "all messages in history and response has a time, use this to get proper time between respones and act accordingly"
    )

# Configure the Gemini AI API
api_key = settings.api  # Replace with your actual API key
def configure_gemini():
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash"), genai.GenerativeModel("gemini-1.5-flash")

model, end_detection_model = configure_gemini()

def choose_input_mode():
    """
    Automatically selects input mode based on settings.voice.
    Returns 'voice' if settings.voice is True, otherwise returns 'text'.
    """
    if settings.voice:
        print(Fore.GREEN + "Voice mode is enabled in settings. Automatically selecting Voice input." + Style.RESET_ALL)
        return "voice"
    else:
        print(Fore.GREEN + "Voice mode is disabled in settings. Automatically selecting Text input." + Style.RESET_ALL)
        return "text"
    
# Gemini AI Interaction
def get_response(history, model):
    """Sends the conversation history to Gemini AI and returns the response."""
    try:
        response = model.generate_content(history)
        return response.text.strip()  # Ensure clean response
    except Exception as e:
        return f"An error occurred: {e}"

def check_end_of_conversation(user_input, end_detection_model):
    """Sends user input to the end detection model and checks if it's ending the conversation."""
    try:
        prompt = f"Does this message indicate the conversation is ending? '{user_input}' Answer 'yes' or 'no'."
        response = end_detection_model.generate_content(prompt)
        return "yes" in response.text.lower()
    except Exception as e:
        print(f"An error occurred during end detection: {e}")
        return False

# Wake Word Listening and Input Handling
def wait_for_wake_word_or_input(interaction_mode, wake_word="aurora"):
    """Listens for a specific wake word or allows user to type input depending on the interaction mode."""
    recognizer = sr.Recognizer()

    if interaction_mode == '1':  # Text mode
        typed_input = "ready"
        return typed_input

    elif interaction_mode == '2':  # Voice mode
        print(Fore.YELLOW + f"Say '{wake_word}' to begin..." + Style.RESET_ALL)
        with sr.Microphone() as source:
            while True:
                try:
                    print(Fore.YELLOW + "Listening for the wake word..." + Style.RESET_ALL)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    detected_text = recognizer.recognize_google(audio).lower()
                    if wake_word in detected_text:
                        print(Fore.CYAN + "Wake word detected. Starting conversation..." + Style.RESET_ALL)
                        return ""  # Exit the loop once the wake word is detected
                except sr.UnknownValueError:
                    continue  # Ignore unrecognized input
                except sr.WaitTimeoutError:
                    continue  # Keep listening if no input detected
                except Exception as e:
                    print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)

# Voice Input Handling
def get_voice_input():
    """Captures voice input using the SpeechRecognition library."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(Fore.YELLOW + "Listening..." + Style.RESET_ALL)
        try:
            audio = recognizer.listen(source, timeout=20, phrase_time_limit=150)
            print(Fore.CYAN + "Processing your input..." + Style.RESET_ALL)
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            print(Fore.RED + "No input detected. Try again." + Style.RESET_ALL)
            return ""
        except sr.UnknownValueError:
            print(Fore.RED + "Sorry, I couldn't understand you." + Style.RESET_ALL)
            return ""
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)
            return ""

def get_all_words_from_files_in_folder(folder_path):
    """
    Reads all files in the specified folder, extracts their contents,
    and returns the combined text as a single string.

    Args:
        folder_path (str): Path to the folder containing text files.

    Returns:
        str: Combined content of all files in the folder.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist or is not a directory.")
        return ""

    all_text = []

    try:
        # Iterate over all files in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)

            # Ensure it's a file before reading
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = "[PAST HISTORY: " + "/n" + file.read() + "/n" +" END OF HISTORY]"
                        all_text.append(content)
                except Exception as e:
                    print(f"Error reading file '{file_path}': {e}")
    except Exception as e:
        print(f"Error accessing folder '{folder_path}': {e}")
        return ""

    # Join all file contents into a single string
    return "\n".join(all_text)

def send_output(text):
    global output
    output = text

def get_input():
    global input_text, send
    while (send == False):
        input_text = ""
        time.sleep(0.1) #Check every 100 ms
    send = False
    return()

# Conversation Loop
def conversation_loop():
    """Main loop to handle the conversation."""
    if interaction_mode == '2':
        print(Fore.YELLOW + "Listening for the wake word 'aurora'..." + Style.RESET_ALL)

    print(Fore.GREEN + "Wake word detected. Starting conversation..." + Style.RESET_ALL)
    

    lasttime = "never"
    conversation_history = get_all_words_from_files_in_folder("logs") + personality + "\n" + "\n"

    while True:
        global input_text, send, output, emotion
        if interaction_mode == '1':
            output = "none"
            get_input()
            user_input = input_text
        elif interaction_mode == '2':
            user_input = get_voice_input().strip()
        else:
            user_input = ""  # Fallback in case of an unexpected error
            
            
        user_input = "[AI LAST MESSAGE: " + lasttime + " CURRENT TIME: " + datetime.now().strftime("[%Y-%m-%d %H:%M:%S]]") + user_input

        if not user_input:
            continue

        conversation_history = add_message_to_history(conversation_history, "User", user_input)
        output = get_response(conversation_history, model)
        output = re.sub(r"AI:\s*", "", output)
        conversation_history = add_message_to_history(conversation_history, "AI", output)

        if "@E_SAD" in output:
            emotion = "sad"
        if "@E_HAPPY" in output:
            emotion = "happy"
        if "@E_MAD" in output:
            emotion = "mad"
        if "@E_NERVOUS" in output:
            emotion = "nervous"
        if "@E_NEUTRAL" in output:
            emotion = "neutral"
        if "@E_SCARED" in output:
            emotion = "scared"
        
        #Set up removing date and stuff from the AI
        lasttime = datetime.now().strftime("[%Y-%m-%d %H:%M:%S],")
        output_to_send = re.sub(r"[\(\[].*?[\)\]]", "", output)
        output_to_send = re.sub('@E_SAD', '', output_to_send)
        output_to_send = re.sub('@E_HAPPY', '', output_to_send)
        output_to_send = re.sub('@E_MAD', '', output_to_send)
        output_to_send = re.sub('@E_NERVOUS', '', output_to_send)
        output_to_send = re.sub('@E_NEUTRAL', '', output_to_send)
        output_to_send = re.sub('@E_SCARED', '', output_to_send)
        output_to_send = re.sub('@END', '', output_to_send)
        
        #Print AI's response because it needs to be printed!
        print(Fore.GREEN + output_to_send + Style.RESET_ALL)
        print()

        send_output(output_to_send) # Send it to the gui

        make_voice(voice_text=output_to_send)

        if "@END" in output:
            
            save_conversation_to_file(conversation_history)
            break


def save_conversation_to_file(conversation_history):
    """
    Saves the conversation history to a log file with timestamps for each message.
    """
    # Ensure the logs folder exists
    logs_folder = "logs"
    os.makedirs(logs_folder, exist_ok=True)

    # Format the timestamp for the file name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(logs_folder, f"conversation_{timestamp}.txt")

    # Write the conversation to the file
    with open(log_file_path, "w") as log_file:
        log_file.write(conversation_history)
        log_file.write("LAST EMOTION: " + emotion)

    print(f"Conversation saved to {log_file_path}")

def add_message_to_history(history, speaker, message):
    """
    Adds a message with a timestamp to the conversation history.
    """
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    formatted_message = f"{timestamp} {speaker}: {message}\n\n"
    return history + formatted_message
    
def make_voice(voice_text):
    # Check if the setting 'speak' is enabled
    if not settings.speak:
        return  # Exit the function if speaking is disabled
    
    voice = gTTS(text=voice_text, lang="en", slow=False)
    audio_file = "voice.mp3"
    voice.save(audio_file)
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()   
    
    while pygame.mixer.music.get_busy():  # Check if the audio is still playing
        pygame.time.Clock().tick(20)
        
    pygame.mixer.music.stop()  # Stop the music
    pygame.mixer.quit()
        
    try:
        os.remove(audio_file)  # Delete the file
    except PermissionError as e:
        print(f"Error deleting file: {e}")
        time.sleep(1)  # Wait for a moment before retrying
        os.remove(audio_file)  # Retry deleting the file

# --- Tkinter GUI ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter App")

        # Input Line
        ttk.Label(root, text="Enter Text:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.input_entry = ttk.Entry(root)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Output Label
        ttk.Label(root, text="Output:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.output_label = ttk.Label(root, text="Output will appear here...")
        self.output_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Button to Send Text
        send_button = ttk.Button(root, text="Send", command=self.send_input)
        send_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

        # Configure grid column to expand
        root.columnconfigure(1, weight=1)

        self.update_thread = threading.Thread(target=self.update_output_loop, daemon=True)
        self.update_thread.start()

    def send_input(self):
        global input_text, send
        input_text = self.input_entry.get()
        send = True
        self.output_label.config(text="Waiting for output...")


    def update_output_loop(self):
            global send, output
            while True:
                if send == False:
                    if output != "":
                         self.output_label.config(text=f"Output: {output}")
                time.sleep(0.1) #Check every 100 ms

# Main Execution
if __name__ == "__main__":
    root = tk.Tk()
    
    #Ensure settings.py Exists
    check_and_run('settings.py', 'config.py')
    
    # Assuming 'settings' is a module that contains a 'voice' variable
    import settings

    # Get interaction mode from settings, if set; otherwise, use input
    if hasattr(settings, 'voice') and settings.voice is not None:
        interaction_mode = '2' if settings.voice else '1'
    else:
        # Prompt user for input
        interaction_mode = input(
            Fore.CYAN + "Choose interaction mode: Type '1' for Text or '2' for Voice: " + Style.RESET_ALL
        ).strip()

        # Validate input and set default to '1' (Text mode) if invalid
        if interaction_mode not in ['1', '2']:
            print(Fore.RED + "Invalid choice. Defaulting to Text mode." + Style.RESET_ALL)
            interaction_mode = '1'  # Default to text mode

    print(f"Selected interaction mode: {'Voice' if interaction_mode == '2' else 'Text'}")
    wait_for_wake_word_or_input(interaction_mode, wake_word="aurora")


    app = App(root)
    
    # Start the conversation loop in a separate thread to avoid blocking the GUI
    conversation_thread = threading.Thread(target=conversation_loop, daemon=True)
    conversation_thread.start()


    root.mainloop()