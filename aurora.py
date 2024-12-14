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

import threading
import random
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
check_and_run('settings.py', 'config.py')
import settings
import time
from pydub import AudioSegment
from pydub.playback import play
import api

is_timer_active = False
timer_thread = None
emotion = ""
GUI = False
output = ""
send = False
personality = settings.personality_text + (
        #Bot Configuration, PLEASE DO NOT CHANGE
        "1. The Users name is: " + settings.name + ". "
        "2. if the user responds with 'no reply' it indicates they did not say anything, end the coversation if you don't receive a response."
        "3. Use the last emotion in hostory to set your current emotion, this may not be the same as your set presonality."
        "4. never immediatly end a coversation."
        "5. you will be given your entire history, please do not bring it up in conversation unless prompted or required to for accuracy."
        "6. your name is aurora, you are a fully scentient robot that looks mostly humanoid with some now humanoid parts."
        "7. never prefix your response with AI:"
        "8. If the conversation ends, finish your reply with '@END'."
        "9. every message will contain a date and time, this is for you to know when the message was sent, please do not call upon this in a response."
        "10. at the start of the response always put your current emotion from these 6 choices '@E_SAD' '@E_HAPPY' '@E_MAD' '@E_NERVOUS' '@E_NEUTRAL' '@E_SCARED' without anything around it."
        "11. all messages in history and response has a time, use this to get proper time between respones and act accordingly."
        "12. if prompt is '@RANDOM' respond with a conversation starter, like you started the coversation with the user."
        "13. Never talk for the user"
    )

# Configure the Gemini AI API
api_key = settings.api  # Replace with your actual API key
def configure_gemini():
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash"), genai.GenerativeModel("gemini-1.5-flash")

model, end_detection_model = configure_gemini()

def simplify_conversation(model, history):
    """
    Simplifies a conversation history using Gemini AI, extracting key information.

    Args:
    - model: The AI model instance for generating content.
    - history (list): A list of message dictionaries. Each dictionary should contain:
      - "timestamp": The timestamp of the message.
      - "message": The content of the message.

    Returns:
    - list: A list of dictionaries containing the timestamp and the AI-simplified version of the message.
    """
    prompt_template = (
        "You are an AI assistant tasked with simplifying and extracting the most important details from "
        "a conversation. Focus on retaining key points, timestamps, and removing unnecessary filler words. "
        "sum up the coversation in one or two sentences, then provide key info"
        "if no valuable information is present, respond with '@NONE'"
        "remove every word that starts with a '@'"
        "any key points must have included time and date"
        "always end with the final emotion type felt"
        "Simplify the following message:\n\n" + history
    )

    # Use the AI model to simplify the message
    simplified_message = model.generate_content(prompt_template)
    
    simplified_text = simplified_message.text.strip()
    cleaned_text = re.sub('@NONE', '', simplified_text)
    
    return cleaned_text

def playsound(sound_file):
    """Plays a sound asynchronously using pygame."""
    pygame.mixer.init()
    pygame.mixer.Sound(sound_file).play()

def write_to_api(variable_name, variable_state):
    """Writes or updates a variable and its state in api.py, removing leading/trailing spaces."""
    file_path = "api.py"
    updated_lines = []
    variable_found = False

    # Clean the input if it's a string
    if isinstance(variable_state, str):
        variable_state = re.sub(r"^\s+|\s+$", "", variable_state)  # Remove leading and trailing spaces/newlines

    # Read the file content if it exists
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            # Check if the line matches the variable to update
            if line.startswith(f"{variable_name} ="):
                # Update the variable
                if isinstance(variable_state, str):
                    updated_lines.append(f"{variable_name} = \"{variable_state}\"\n")
                else:
                    updated_lines.append(f"{variable_name} = {variable_state}\n")
                variable_found = True
            else:
                # Retain the existing line
                updated_lines.append(line)

    except FileNotFoundError:
        # If the file doesn't exist, initialize an empty list
        pass

    # If the variable wasn't found, add it
    if not variable_found:
        if isinstance(variable_state, str):
            updated_lines.append(f"{variable_name} = \"{variable_state}\"\n")
        else:
            updated_lines.append(f"{variable_name} = {variable_state}\n")

    # Write the updated content back to the file
    with open(file_path, "w") as file:
        file.writelines(updated_lines)

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
    write_to_api("waiting_for_response", "yes")
    try:
        write_to_api("processing", True)
        response = model.generate_content(history)
        write_to_api("waiting_for_response", "no")
        write_to_api("processing", False)
        return response.text.strip()  # Ensure clean response
    except Exception as e:
        write_to_api("waiting_for_response", "no")
        write_to_api("processing", False)
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
    write_to_api("waiting", True)
    start_timer()
    if interaction_mode == '1':  # Text mode
        typed_input = "ready"
        write_to_api("waiting", False)
        stop_timer()
        return typed_input

    elif interaction_mode == '2':  # Voice mode
        print(Fore.YELLOW + f"Say '{wake_word}' to begin..." + Style.RESET_ALL)
        with sr.Microphone() as source:
            while True:
                try:
                
                    if api.random_talk == True:
                        return ""
                        
                    print(Fore.YELLOW + "Listening for the wake word..." + Style.RESET_ALL)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    detected_text = recognizer.recognize_google(audio).lower()
                    
                    if api.random_talk == True:
                        return ""
                        
                    if wake_word in detected_text:
                        playsound("src/listen.mp3")
                        print(Fore.CYAN + "Wake word detected. Starting conversation..." + Style.RESET_ALL)
                        write_to_api("waiting", False)
                        stop_timer()
                        return ""  # Exit the loop once the wake word is detected
                except sr.UnknownValueError:
                    continue  # Ignore unrecognized input
                except sr.WaitTimeoutError:
                    continue  # Keep listening if no input detected
                except Exception as e:
                    print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)

def timer_function():
    global is_timer_active

    while is_timer_active:
        # Generate a random duration between 5 and 30 minutes (converted to seconds)
        duration = random.randint(300, 1000)
        print(f"Timer started for {duration // 60} minutes.")

        # Wait for the duration or until the timer is deactivated
        start_time = time.time()
        while is_timer_active and time.time() - start_time < duration:
            time.sleep(1)  # Check every second if the timer is still active
        
        if is_timer_active:
            print("Timer completed!")
            write_to_api("random_talk", True)
        else:
            print("Timer was stopped before completion.")

        # Reset the timer if still active
        if not is_timer_active:
            break

def start_timer():
    global is_timer_active, timer_thread

    if not is_timer_active:
        is_timer_active = True
        timer_thread = threading.Thread(target=timer_function)
        timer_thread.daemon = True  # Allows the thread to exit when the main program exits
        timer_thread.start()

def stop_timer():
    global is_timer_active

    is_timer_active = False
    if timer_thread and timer_thread.is_alive():
        timer_thread.join()  # Wait for the thread to finish if necessary
        print("Timer has been stopped and reset.")

# Voice Input Handling
def get_voice_input():
    write_to_api("response", "yes")
    write_to_api("finished", False)
    playsound("src/popon.mp3")
    """Captures voice input using the SpeechRecognition library."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(Fore.YELLOW + "Listening..." + Style.RESET_ALL)
        try:
            if api.random_talk == True:
                return "@RANDOM"
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=150)
            print(Fore.CYAN + "Processing your input..." + Style.RESET_ALL)
            write_to_api("response", "yes")
            playsound("src/popoff.mp3")
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            print(Fore.RED + "No input detected. Switching to wake word detection..." + Style.RESET_ALL)
            playsound("src/wait.mp3")
            write_to_api("response", "no")
            return "no reply"
        except sr.UnknownValueError:
            print(Fore.RED + "Sorry, I couldn't understand you." + Style.RESET_ALL)
            write_to_api("response", "yes")
            return ""
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)
            write_to_api("response", "yes")
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
                        content = "[PAST HISTORY: " + file.read() +" END OF HISTORY] \n \n \n"
                        all_text.append(content)
                except Exception as e:
                    print(f"Error reading file '{file_path}': {e}")
    except Exception as e:
        print(f"Error accessing folder '{folder_path}': {e}")
        return ""

    # Join all file contents into a single string
    return "\n".join(all_text)

def send_output(text):
    send = True

def get_input():
    if GUI == True:
        while (visual.send == False):
            user_input = visual.input
            print("Waiting For Send... Current Value: " + str(visual.send))
            time.sleep(0.1) #Check every 100 ms
        visual.send = False
    else:
        reply = input("Enter Message: ")
    return(reply)

# Conversation Loop
def conversation_loop():
            
    write_to_api("finished", False)
    write_to_api("output", False)
    write_to_api("finished", False)
    

    lasttime = "never"
    conversation_history = get_all_words_from_files_in_folder("logs") + "\n" + personality + "\n" + "\n"
    write_to_api("waiting_for_input", "yes")
    
    while True:
    
        if api.random_talk == True:
            write_to_api("random_talk", False)
            
        write_to_api("waiting_for_input", "yes")
        
        if interaction_mode == '1':
            output = "none"
            user_input = get_input()
        elif interaction_mode == '2':
            user_input = get_voice_input().strip()
            while user_input == "":
                user_input = get_voice_input().strip()
        else:
            user_input = "no reply"  # Fallback in case of an unexpected error
            
        print(user_input)
            
        user_input = "[AI LAST MESSAGE: " + lasttime + " CURRENT TIME: " + datetime.now().strftime("[%Y-%m-%d %H:%M:%S]]") + user_input

        if api.random_talk == True:
            write_to_api("random_talk", False)

        if not user_input:
            continue
        write_to_api("waiting_for_input", "no")
        conversation_history = add_message_to_history(conversation_history, "User", user_input)
        output = get_response(conversation_history, model)
        output = re.sub(r"AI:\s*", "", output)
        if "@e_sad" in output.lower():
            emotion = "sad"
            write_to_api("emotion", emotion)
        elif "@e_happy" in output.lower():
            emotion = "happy"
            write_to_api("emotion", emotion)
        elif "@e_mad" in output.lower():
            emotion = "mad"
            write_to_api("emotion", emotion)
        elif "@e_nervous" in output.lower():
            emotion = "nervous"
            write_to_api("emotion", emotion)
        elif "@e_neutral" in output.lower():
            emotion = "neutral"
            write_to_api("emotion", emotion)
        elif "@e_scared" in output.lower():
            emotion = "scared"
            write_to_api("emotion", emotion)
        conversation_history = add_message_to_history(conversation_history, "AI", output)

        if api.response == "no":
            write_to_api("response", "yes")

        if "@END" in output:
            lasttime = datetime.now().strftime("[%Y-%m-%d %H:%M:%S],")
            output = re.sub(r"[\(\[].*?[\)\]]", "", output)
            output = re.sub('@E_SAD', '', output)
            output = re.sub('@E_HAPPY', '', output)
            output = re.sub('@E_MAD', '', output)
            output = re.sub('@E_NERVOUS', '', output)
            output = re.sub('@E_NEUTRAL', '', output)
            output = re.sub('@E_SCARED', '', output)
            output = re.sub('@END', '', output)
            #Print AI's response because it needds to be printed!
            print(Fore.GREEN + output + Style.RESET_ALL)
            print()
            write_to_api("output", output)
            send_output(output)
            make_voice(voice_text=output, rate=1.0)
            save_conversation_to_file(conversation_history)
            write_to_api("output", "")
            write_to_api("finished", True)
            return()
            
        if api.finished == False:
            #Set up removing date and stuff from the AI
            lasttime = datetime.now().strftime("[%Y-%m-%d %H:%M:%S],")
            output = re.sub(r"[\(\[].*?[\)\]]", "", output)
            output = re.sub('@E_SAD', '', output)
            output = re.sub('@E_HAPPY', '', output)
            output = re.sub('@E_MAD', '', output)
            output = re.sub('@E_NERVOUS', '', output)
            output = re.sub('@E_NEUTRAL', '', output)
            output = re.sub('@E_SCARED', '', output)
            output = re.sub('@END', '', output)
            #Print AI's response because it needs to be printed!
            print(Fore.GREEN + output + Style.RESET_ALL)
            print()
            write_to_api("output", output)
            make_voice(voice_text=output, rate=1.0)

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
    simplified = simplify_conversation(model, conversation_history)
    if simplified != "":
        with open(log_file_path, "w") as log_file:
            log_file.write(simplified)
            print(f"Conversation saved to {log_file_path}")

def add_message_to_history(history, speaker, message):
    """
    Adds a message with a timestamp to the conversation history.
    """
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    formatted_message = f"{timestamp} {speaker}: {message}"
    if speaker == "AI":
        return history + formatted_message + "\n \n"
    return history + formatted_message + "\n \n"
    
def make_voice(voice_text, rate=1.0):  # Added rate parameter (default is 1.0)
    # Check if the setting 'speak' is enabled
    if voice_text == "":
        return()
    if not settings.speak:
        return  # Exit the function if speaking is disabled
    
    # Generate speech with gTTS
    voice = gTTS(text=voice_text, lang="en", slow=False)
    audio_file = "voice.mp3"
    voice.save(audio_file)
    
    # Adjust the speed of the audio if rate is not 1.0
    if rate != 1.0:
        sound = AudioSegment.from_mp3(audio_file)
        sound = sound.speedup(playback_speed=rate)  # Adjust the playback speed
        sound.export(audio_file, format="mp3")  # Save the adjusted audio

    # Initialize pygame mixer to play audio
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()   
    
    # Wait until the audio finishes playing
    while pygame.mixer.music.get_busy():  # Check if the audio is still playing
        pygame.time.Clock().tick(5)
        
    pygame.mixer.music.stop()  # Stop the music
    pygame.mixer.quit()
        
    try:
        os.remove(audio_file)  # Delete the file
    except PermissionError as e:
        print(f"Error deleting file: {e}")
        time.sleep(1)  # Wait for a moment before retrying
        os.remove(audio_file)  # Retry deleting the file
    
    write_to_api("output", "")
# Main Execution
if __name__ == "__main__":
    check_and_run('settings.py', 'config.py')  # Ensure settings.py exists
    write_to_api("finished", False)

    # Assuming 'settings' is a module that contains a 'voice' variable
    import settings
    playsound("src/ready.mp3")
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
    
    # Assuming `wait_for_wake_word_or_input` and `conversation_loop` are functions already defined
    while True:
        wait_for_wake_word_or_input(interaction_mode, wake_word="aurora")
        conversation_loop()
        write_to_api("finished", False)
