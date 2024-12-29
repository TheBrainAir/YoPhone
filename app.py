from flask import Flask, request, jsonify
import requests
import base64
import logging

app = Flask(__name__)

# Set your API key directly in the code
API_KEY = "01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default translation language
default_language = "hy"  # Armenian

# Dictionaries to store user languages and states
user_languages = {}  # Stores the target language for each user
user_states = {}     # Stores the current state for each user (e.g., awaiting language input)

# Function to translate text to the target language
def translate_text(text, target_language):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",            # Auto-detect source language
        "tl": target_language,   # Target language
        "dt": "t",
        "q": text
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        translation = response.json()[0][0][0]
        return translation
    except requests.exceptions.RequestException as e:
        logger.error(f"Translation API request failed: {e}")
        return "Translation error."
    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing translation response: {e}")
        return "Translation error."

# Function to send messages to the user
def send_message(chat_id, text):
    url = "https://yoai.yophone.com/api/pub/sendMessage"
    headers = {
        "Content-Type": "application/json",
        "X-YoAI-API-Key": API_KEY
    }
    payload = {
        "to": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Message successfully sent to {chat_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")

# Function to convert language name to ISO-639-1 code
def get_language_code(language_name):
    language_map = {
        "english": "en",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "russian": "ru",
        "armenian": "hy",
        "chinese": "zh",
        "japanese": "ja",
        "arabic": "ar",
        "hindi": "hi",
        "italian": "it",
        "korean": "ko",
        "portuguese": "pt",
        "turkish": "tr",
        "dutch": "nl",
        "swedish": "sv",
        "polish": "pl",
        "greek": "el",
        "czech": "cs",
        "danish": "da",
        "finnish": "fi",
        "hungarian": "hu",
        "norwegian": "no",
        "thai": "th",
        "vietnamese": "vi",
        "hebrew": "he",
        "indonesian": "id",
        "malay": "ms",
        "filipino": "tl",
        "ukrainian": "uk",
        "bulgarian": "bg",
        "slovak": "sk",
        "croatian": "hr",
        "serbian": "sr",
        "lithuanian": "lt",
        "latvian": "lv",
        "estonian": "et",
        "slovenian": "sl",
        "macedonian": "mk",
        "icelandic": "is",
        "afrikaans": "af",
        "swahili": "sw"
    }
    return language_map.get(language_name.lower())

# Main webhook route
@app.route('/yoai:01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Received data: {data}")

    # Extract chat_id. Adjust the key based on your webhook's payload structure.
    chat_id = data.get("chatId") or data.get("chat_id") or data.get("id")
    
    if not chat_id:
        logger.error("chat_id not found in the incoming data.")
        return jsonify({"error": "chat_id not found"}), 400

    encoded_text = data.get("text")
    if not encoded_text:
        logger.error(f"Text not found in the incoming data for chat_id {chat_id}.")
        return jsonify({"error": "Invalid data"}), 400

    try:
        # Decode base64 string
        decoded_bytes = base64.b64decode(encoded_text)
        decoded_text = decoded_bytes.decode('utf-8').strip()
        logger.info(f"Decoded message from {chat_id}: {decoded_text}")
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Decoding error for chat_id {chat_id}: {e}")
        send_message(chat_id, "Failed to decode your message. Please try again.")
        return jsonify({"error": "Decoding failed"}), 400

    # Check if the user is in a specific state
    if user_states.get(chat_id) == 'awaiting_language':
        language_code = get_language_code(decoded_text)
        if language_code:
            user_languages[chat_id] = language_code
            user_states.pop(chat_id)  # Reset the state
            confirmation_message = f"Translation language has been set to {decoded_text.capitalize()}."
            send_message(chat_id, confirmation_message)
            logger.info(f"User {chat_id} set language to {language_code}.")
        else:
            error_message = "Sorry, I couldn't recognize that language. Please try again."
            send_message(chat_id, error_message)
            logger.warning(f"Unrecognized language '{decoded_text}' from user {chat_id}.")
        return jsonify({"status": "ok"}), 200

    # Check if the message is a command (starts with '/')
    if decoded_text.startswith('/'):
        # Extract the command without the slash and convert to lowercase
        command = decoded_text[1:].lower()
        logger.info(f"Received command '{command}' from user {chat_id}.")

        if command == "start":
            welcome_message = (
                "Welcome! I can translate your messages.\n\n"
                "Commands:\n"
                "/switch - Change the translation language.\n"
                "/help - Show this help message.\n"
                "Simply type any message, and I will translate it."
            )
            send_message(chat_id, welcome_message)
            return jsonify({"status": "ok"}), 200

        elif command == "switch":
            switch_message = (
                "Please enter the language you want to translate to (in English, e.g., 'Spanish', 'French', etc.)."
            )
            send_message(chat_id, switch_message)
            user_states[chat_id] = 'awaiting_language'
            logger.info(f"Set state 'awaiting_language' for user {chat_id}.")
            return jsonify({"status": "ok"}), 200

        elif command == "help":
            help_message = (
                "Here are the commands you can use:\n"
                "/start - Start the bot and see the welcome message.\n"
                "/switch - Change the translation language.\n"
                "/help - Show this help message."
            )
            send_message(chat_id, help_message)
            return jsonify({"status": "ok"}), 200

        else:
            unknown_command_message = "Unknown command. Type /help to see available commands."
            send_message(chat_id, unknown_command_message)
            logger.warning(f"Unknown command '{command}' from user {chat_id}.")
            return jsonify({"status": "ok"}), 200

    # If not a command and not awaiting language input, translate the message
    target_language = user_languages.get(chat_id, default_language)
    logger.info(f"Translating message from {chat_id} to language code '{target_language}'.")

    translated_text = translate_text(decoded_text, target_language)
    logger.info(f"Translated message for {chat_id}: {translated_text}")

    send_message(chat_id, translated_text)

    return jsonify({"status": "ok"}), 200

# Catch-all route for debugging unhandled paths
@app.route('/<path:path>', methods=['POST'])
def catch_all(path):
    data = request.json
    logger.warning(f"Unhandled path: {path}")
    logger.warning(f"Received data: {data}")
    return jsonify({"status": "Unhandled path"}), 200

if __name__ == "__main__":
    # Run the Flask app
    app.run(port=8888, debug=True)
