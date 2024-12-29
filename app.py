from flask import Flask, request, jsonify
import requests
import base64
import logging

app = Flask(__name__)

# Установите ваш API-ключ непосредственно здесь
API_KEY = "01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменная для хранения выбранного языка перевода
default_language = "hy"  # Армянский язык
user_languages = {}  # Словарь для хранения языка для каждого пользователя

# Функция для перевода текста на выбранный язык
def translate_text(text, target_language):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",  # Автоматическое определение исходного языка
        "tl": target_language,  # Целевой язык
        "dt": "t",
        "q": text
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            translation = response.json()[0][0][0]
            return translation
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка при разборе ответа перевода: {e}")
            return "Ошибка при переводе."
    else:
        logger.error(f"Ошибка перевода: {response.status_code}, {response.text}")
        return "Ошибка при переводе."

# Функция отправки сообщений пользователю
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
        logger.info(f"Сообщение успешно отправлено пользователю {chat_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")

# Функция для преобразования названия языка в код ISO-639-1
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

# Основной маршрут для вебхука
@app.route('/yoai:01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Получены данные: {data}")

    # Извлечение chat_id. Убедитесь, что используете правильный ключ из вашего вебхука.
    # Часто используется 'chatId', 'chat_id' или 'id'
    chat_id = data.get("chatId") or data.get("chat_id") or data.get("id")
    
    if not chat_id:
        logger.error("chat_id не найден в полученных данных.")
        return jsonify({"error": "chat_id не найден"}), 400

    encoded_text = data.get("text")
    if not encoded_text:
        logger.error(f"Текст не найден в полученных данных для chat_id {chat_id}.")
        return jsonify({"error": "Неверные данные"}), 400

    try:
        # Декодирование base64-строки
        decoded_bytes = base64.b64decode(encoded_text)
        decoded_text = decoded_bytes.decode('utf-8').strip()
        logger.info(f"Декодированное сообщение от {chat_id}: {decoded_text}")
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Ошибка декодирования для chat_id {chat_id}: {e}")
        send_message(chat_id, "Не удалось декодировать ваше сообщение. Пожалуйста, попробуйте снова.")
        return jsonify({"error": "Decoding failed"}), 400

    # Проверка, является ли сообщение командой (начинается с '/')
    if decoded_text.startswith('/'):
        # Извлечение команды без слеша и приведение к нижнему регистру
        command = decoded_text[1:].lower()
        logger.info(f"Получена команда от {chat_id}: {command}")

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
            user_languages[chat_id] = None  # Ожидание ввода языка
            logger.info(f"Ожидание ввода языка от пользователя {chat_id}.")
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
            logger.warning(f"Неизвестная команда '{command}' от пользователя {chat_id}.")
            return jsonify({"status": "ok"}), 200

    # Проверка, ожидается ли ввод языка после команды /switch
    if chat_id in user_languages and user_languages[chat_id] is None:
        target_language = get_language_code(decoded_text)
        if target_language:
            user_languages[chat_id] = target_language
            confirmation_message = f"Translation language has been set to {decoded_text.capitalize()}."
            send_message(chat_id, confirmation_message)
            logger.info(f"Пользователь {chat_id} установил язык перевода: {target_language}.")
        else:
            error_message = "Sorry, I couldn't recognize that language. Please try again."
            send_message(chat_id, error_message)
            logger.warning(f"Неизвестный язык '{decoded_text}' от пользователя {chat_id}.")
        return jsonify({"status": "ok"}), 200

    # Определение языка для перевода
    target_language = user_languages.get(chat_id, default_language)
    logger.info(f"Перевод сообщения от {chat_id} на язык {target_language}.")

    # Перевод сообщения
    translated_text = translate_text(decoded_text, target_language)
    logger.info(f"Переведенное сообщение для {chat_id}: {translated_text}")

    # Отправка переведенного текста обратно пользователю
    send_message(chat_id, translated_text)

    return jsonify({"status": "ok"}), 200

# Универсальный маршрут для отладки необработанных путей
@app.route('/<path:path>', methods=['POST'])
def catch_all(path):
    logger.warning(f"Необработанный путь: {path}")
    logger.warning(f"Получены данные: {request.json}")
    return jsonify({"status": "Unhandled path"}), 200

if __name__ == "__main__":
    # При развёртывании на сервере может потребоваться указать host='0.0.0.0'
    app.run(port=8888, debug=True)
