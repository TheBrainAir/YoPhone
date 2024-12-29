from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

API_KEY = "01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9"

# Переменная для хранения выбранного языка перевода
default_language = "hy"  # Армянский язык
user_languages = {}  # Словарь для хранения языка для каждого пользователя

# Функция для перевода текста на выбранный язык
def translate_text(text, target_language):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",  # Определение исходного языка автоматически
        "tl": target_language,  # Целевой язык
        "dt": "t",
        "q": text
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        translation = response.json()[0][0][0]
        return translation
    else:
        print(f"Translation error: {response.status_code}, {response.text}")
        return "Translation error."

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YoTranslate</title>
    </head>
    <body>
        <h1>Welcome to YoTranslate!</h1>
        <p>This is the bot server for YoTranslate. If you see this page, the server is running successfully.</p>
    </body>
    </html>
    '''

# Основной маршрут для вебхука
@app.route('/yoai:01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9', methods=['POST'])
def webhook():
    data = request.json
    print("Received data:", data)

    chat_id = data.get("chatId")
    encoded_text = data.get("text")
    if not chat_id or not encoded_text:
        return jsonify({"error": "Invalid data"}), 400

    # Декодирование текста
    decoded_text = base64.b64decode(encoded_text).decode('utf-8').strip()
    print(f"Decoded message: {decoded_text}")

    # Обработка команды /start
    if decoded_text == "/Start":
        send_message(chat_id, "Welcome! I can translate your messages.\n\n" \
                               "Commands:\n" \
                               "/Switch - Change the translation language.\n" \
                               "Simply type any message, and I will translate it.")
        return jsonify({"status": "ok"}), 200

    # Обработка команды /Switch
    if decoded_text == "/Switch":
        send_message(chat_id, "Please enter the language you want to translate to (in English, e.g., 'Spanish', 'French', etc.).")
        user_languages[chat_id] = None  # Ожидание ввода языка
        return jsonify({"status": "ok"}), 200

    # Проверка ввода языка после /switch
    if chat_id in user_languages and user_languages[chat_id] is None:
        # Перевод введённого языка в целевой код языка (e.g., "French" -> "fr")
        target_language = get_language_code(decoded_text)
        if target_language:
            user_languages[chat_id] = target_language
            send_message(chat_id, f"Translation language has been set to {decoded_text}.")
        else:
            send_message(chat_id, "Sorry, I couldn't recognize the language. Please try again.")
        return jsonify({"status": "ok"}), 200

    # Определение языка для перевода
    target_language = user_languages.get(chat_id, default_language)

    # Перевод текста
    translated_text = translate_text(decoded_text, target_language)
    print(f"Translated message: {translated_text}")

    # Отправка переведённого текста
    send_message(chat_id, translated_text)

    return jsonify({"status": "ok"}), 200

# Функция отправки сообщений
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
    response = requests.post(url, headers=headers, json=payload)
    print("Sent message response:", response.json())

# Функция для преобразования языка в его код ISO-639-1
def get_language_code(language_name):
    language_map = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Russian": "ru",
        "Armenian": "hy",
        "Chinese": "zh",
        "Japanese": "ja",
        "Arabic": "ar",
        "Hindi": "hi",
        "Italian": "it",
        "Korean": "ko",
        "Portuguese": "pt",
        "Turkish": "tr",
        "Dutch": "nl",
        "Swedish": "sv",
        "Polish": "pl",
        "Greek": "el",
        "Czech": "cs",
        "Danish": "da",
        "Finnish": "fi",
        "Hungarian": "hu",
        "Norwegian": "no",
        "Thai": "th",
        "Vietnamese": "vi",
        "Hebrew": "he",
        "Indonesian": "id",
        "Malay": "ms",
        "Filipino": "tl",
        "Ukrainian": "uk",
        "Bulgarian": "bg",
        "Slovak": "sk",
        "Croatian": "hr",
        "Serbian": "sr",
        "Lithuanian": "lt",
        "Latvian": "lv",
        "Estonian": "et",
        "Slovenian": "sl",
        "Macedonian": "mk",
        "Icelandic": "is",
        "Afrikaans": "af",
        "Swahili": "sw"
    }
    return language_map.get(language_name.capitalize())

# Универсальный маршрут для отладки
@app.route('/<path:path>', methods=['POST'])
def catch_all(path):
    print(f"Unhandled path: {path}")
    print("Received data:", request.json)
    return jsonify({"status": "Unhandled path"}), 200

if __name__ == "__main__":
    app.run(port=8888)
