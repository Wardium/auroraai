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


emotion = ""
GUI = False
output = ""
send = False
personality = settings.personality_text + (
        #Bot Configuration, PLEASE DO NOT CHANGE
        "The Users name is: " + settings.name + " "
        "If Prompted with the text '@RANDOM', please respond with a coversation starter, please do not reuse the same ones, be broad, this is not a date."
        "Use the last emotion in hostory to set your current emotion, this may not be the same as your set presonality"
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

def playsound(sound_file):
    """Plays a sound asynchronously using pygame."""
    pygame.mixer.init()
    pygame.mixer.Sound(sound_file).play()

def write_to_api(variable_name, variable_state):
    """Writes or updates a variable and its state in api.py."""
    api_file = "api.py"
    updated = False
    lines = []

    # Read existing lines from the file if it exists
    try:
        with open(api_file, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        pass

    # Update the variable if it exists
    for i, line in enumerate(lines):
        if line.startswith(f"{variable_name} ="):
            if isinstance(variable_state, str):
                lines[i] = f"{variable_name} = \"{variable_state}\"\n"
            else:
                lines[i] = f"{variable_name} = {variable_state}\n"
            updated = True
            break

    # Add the variable if it wasn't updated
    if not updated:
        if isinstance(variable_state, str):
            lines.append(f"{variable_name} = \"{variable_state}\"\n")
        else:
            lines.append(f"{variable_name} = {variable_state}\n")

    # Write back the updated lines
    with open(api_file, "w") as file:
        file.writelines(lines)

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
        response = model.generate_content(history)
        write_to_api("waiting_for_response", "no")
        return response.text.strip()  # Ensure clean response
    except Exception as e:
        write_to_api("waiting_for_response", "no")
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
                        playsound("src/listen.mp3")
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
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=150)
            print(Fore.CYAN + "Processing your input..." + Style.RESET_ALL)
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            print(Fore.RED + "No input detected. Switching to wake word detection..." + Style.RESET_ALL)
            playsound("src/wait.mp3")
            wait_for_wake_word_or_input(interaction_mode, wake_word="aurora")
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
    """Main loop to handle the conversation."""
    if interaction_mode == '2':
        print(Fore.YELLOW + "Listening for the wake word 'aurora'..." + Style.RESET_ALL)
    

    lasttime = "never"
    conversation_history = get_all_words_from_files_in_folder("logs") + "\n" + personality + "\n" + "\n"
    write_to_api("waiting_for_input", "yes")
    while True:
        if interaction_mode == '1':
            output = "none"
            user_input = get_input()
        elif interaction_mode == '2':
            user_input = get_voice_input().strip()
        else:
            user_input = ""  # Fallback in case of an unexpected error
            
            
        user_input = "[AI LAST MESSAGE: " + lasttime + " CURRENT TIME: " + datetime.now().strftime("[%Y-%m-%d %H:%M:%S]]") + user_input

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
            make_voice(voice_text=output, rate=1.3)
            save_conversation_to_file(conversation_history)
            break

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
        #Print AI's response because it needds to be printed!
        print(Fore.GREEN + output + Style.RESET_ALL)
        print()
        make_voice(voice_text=output, rate=1.3)

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
# Main Execution
if __name__ == "__main__":
    check_and_run('settings.py', 'config.py')  # Ensure settings.py exists

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
    wait_for_wake_word_or_input(interaction_mode, wake_word="aurora")
    conversation_loop()
