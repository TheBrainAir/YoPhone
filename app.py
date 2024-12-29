from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

API_KEY = "01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9"

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
            print(f"Error parsing translation response: {e}")
            return "Translation error."
    else:
        print(f"Translation error: {response.status_code}, {response.text}")
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
        print("Message sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

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
    print("Received data:", data)

    chat_id = data.get("chatId")
    encoded_text = data.get("text")
    if not chat_id or not encoded_text:
        return jsonify({"error": "Invalid data"}), 400

    try:
        # Decode the base64-encoded text
        decoded_text = base64.b64decode(encoded_text).decode('utf-8').strip()
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        print(f"Decoding error: {e}")
        send_message(chat_id, "Failed to decode your message. Please try again.")
        return jsonify({"error": "Decoding failed"}), 400

    print(f"Decoded message: {decoded_text}")

    # Check if the message is a command (starts with '/')
    if decoded_text.startswith('/'):
        # Extract the command by removing the leading slash and convert to lowercase
        command = decoded_text[1:].lower()

        # Handle /start command
        if command == "start":
            welcome_message = (
                "Welcome! I can translate your messages.\n\n"
                "Commands:\n"
                "/switch - Change the translation language.\n"
                "Simply type any message, and I will translate it."
            )
            send_message(chat_id, welcome_message)
            return jsonify({"status": "ok"}), 200

        # Handle /switch command
        if command == "switch":
            switch_message = (
                "Please enter the language you want to translate to (in English, e.g., 'Spanish', 'French', etc.)."
            )
            send_message(chat_id, switch_message)
            user_languages[chat_id] = None  # Awaiting language input
            return jsonify({"status": "ok"}), 200
        
        
        if command == "help":
            help_message = (
                "Here are the commands you can use:\n"
                "/start - Start the bot and see the welcome message.\n"
                "/switch - Change the translation language.\n"
                "/help - Show this help message."
            )
            send_message(chat_id, help_message)
            return jsonify({"status": "ok"}), 200


        # You can add more command handlers here if needed

    # Check if user is expected to input a language after /switch
    if chat_id in user_languages and user_languages[chat_id] is None:
        target_language = get_language_code(decoded_text)
        if target_language:
            user_languages[chat_id] = target_language
            confirmation_message = f"Translation language has been set to {decoded_text.capitalize()}."
            send_message(chat_id, confirmation_message)
        else:
            error_message = "Sorry, I couldn't recognize that language. Please try again."
            send_message(chat_id, error_message)
        return jsonify({"status": "ok"}), 200

    # Determine the target language for translation
    target_language = user_languages.get(chat_id, default_language)

    # Translate the incoming message
    translated_text = translate_text(decoded_text, target_language)
    print(f"Translated message: {translated_text}")

    # Send the translated message back to the user
    send_message(chat_id, translated_text)

    return jsonify({"status": "ok"}), 200

# Catch-all route for debugging unhandled paths
@app.route('/<path:path>', methods=['POST'])
def catch_all(path):
    print(f"Unhandled path: {path}")
    print("Received data:", request.json)
    return jsonify({"status": "Unhandled path"}), 200

if __name__ == "__main__":
    app.run(port=8888)
