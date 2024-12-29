from flask import Flask, request, jsonify
import requests
import base64
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Securely load API key from environment variable
API_KEY = os.getenv("01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9")
if not API_KEY:
    logger.error("API_KEY is not set. Please set the YOAI_API_KEY environment variable.")
    raise EnvironmentError("API_KEY not found.")

# Default translation language
default_language = "hy"  # Armenian
user_languages = {}  # Dictionary to store each user's selected language

# Function to translate text to the target language
def translate_text(text, target_language):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",  # Auto-detect source language
        "tl": target_language,  # Target language
        "dt": "t",
        "q": text
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            translation = response.json()[0][0][0]
            return translation
        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing translation response: {e}")
            return "Translation error."
    else:
        logger.error(f"Translation error: {response.status_code}, {response.text}")
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
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Message sent successfully to {chat_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message to {chat_id}: {e}")

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

    # Identify the correct key for chat ID
    # Common keys could be 'chatId', 'chat_id', 'id', etc.
    # Adjust based on your actual webhook payload
    chat_id = data.get("chatId") or data.get("chat_id") or data.get("id")
    
    if not chat_id:
        logger.error("chat_id not found in the incoming data.")
        return jsonify({"error": "chat_id not found"}), 400

    encoded_text = data.get("text")
    if not encoded_text:
        logger.error(f"Text not found in the incoming data for chat_id {chat_id}.")
        return jsonify({"error": "Invalid data"}), 400

    try:
        # Decode the base64-encoded text
        decoded_bytes = base64.b64decode(encoded_text)
        decoded_text = decoded_bytes.decode('utf-8').strip()
        logger.info(f"Decoded message from {chat_id}: {decoded_text}")
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Decoding error for chat_id {chat_id}: {e}")
        send_message(chat_id, "Failed to decode your message. Please try again.")
        return jsonify({"error": "Decoding failed"}), 400

    # Check if the message is a command (starts with '/')
    if decoded_text.startswith('/'):
        # Extract the command by removing the leading slash and convert to lowercase
        command = decoded_text[1:].lower()
        logger.info(f"Command received from {chat_id}: {command}")

        if command == "start":
            welcome_message = (
                "Welcome! I can translate your messages.\n\n"
                "Commands:\n"
                "/switch - Change the translation language.\n"
                "Simply type any message, and I will translate it."
            )
            send_message(chat_id, welcome_message)
            return jsonify({"status": "ok"}), 200

        elif command == "switch":
            switch_message = (
                "Please enter the language you want to translate to (in English, e.g., 'Spanish', 'French', etc.)."
            )
            send_message(chat_id, switch_message)
            user_languages[chat_id] = None  # Awaiting language input
            logger.info(f"Awaiting language input from {chat_id}.")
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
            logger.warning(f"Unknown command '{command}' received from {chat_id}.")
            return jsonify({"status": "ok"}), 200

    # Check if user is expected to input a language after /switch
    if chat_id in user_languages and user_languages[chat_id] is None:
        target_language = get_language_code(decoded_text)
        if target_language:
            user_languages[chat_id] = target_language
            confirmation_message = f"Translation language has been set to {decoded_text.capitalize()}."
            send_message(chat_id, confirmation_message)
            logger.info(f"User {chat_id} switched language to {target_language}.")
        else:
            error_message = "Sorry, I couldn't recognize that language. Please try again."
            send_message(chat_id, error_message)
            logger.warning(f"Unrecognized language '{decoded_text}' from {chat_id}.")
        return jsonify({"status": "ok"}), 200

    # Determine the target language for translation
    target_language = user_languages.get(chat_id, default_language)
    logger.info(f"Translating message from {chat_id} to {target_language}.")

    # Translate the incoming message
    translated_text = translate_text(decoded_text, target_language)
    logger.info(f"Translated message for {chat_id}: {translated_text}")

    # Send the translated message back to the user
    send_message(chat_id, translated_text)

    return jsonify({"status": "ok"}), 200

# Catch-all route for debugging unhandled paths
@app.route('/<path:path>', methods=['POST'])
def catch_all(path):
    logger.warning(f"Unhandled path: {path}")
    logger.warning(f"Received data: {request.json}")
    return jsonify({"status": "Unhandled path"}), 200

if __name__ == "__main__":
    # It's better to specify host='0.0.0.0' if deploying
    app.run(port=8888, debug=True)
