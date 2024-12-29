from flask import Flask, request, jsonify
import requests
import base64
import logging
from deep_translator import GoogleTranslator, exceptions

app = Flask(__name__)

# Установите ваш API-ключ YoAI непосредственно здесь
YOAI_API_KEY = "01940f1b-72c5-7ac6-ab4b-b86c5e6f8964:becf17a8df9847da0e394bfbd57fffd05f3cbd2b1ab88065193fcc74aed329a9"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменная для хранения выбранного языка перевода по умолчанию
default_language = "hy"  # Армянский язык (код ISO-639-1)

# Словари для хранения настроек каждого пользователя
user_languages = {}  # {'chat_id': 'en'}
user_states = {}     # {'chat_id': 'awaiting_language'}

# Функция отправки сообщений пользователю через YoAI
def send_message(chat_id, text):
    url = "https://yoai.yophone.com/api/pub/sendMessage"
    headers = {
        "Content-Type": "application/json",
        "X-YoAI-API-Key": YOAI_API_KEY
    }
    payload = {
        "to": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Сообщение успешно отправлено пользователю {chat_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")

# Функция для преобразования названия языка в код ISO-639-1
def get_language_code(language_name):
    return GoogleTranslator.get_supported_languages(as_dict=True).get(language_name.lower())

# Функция для перевода текста на выбранный язык с использованием deep_translator
def translate_text(text, target_language):
    try:
        translator = GoogleTranslator(source='auto', target=target_language.lower())
        translated = translator.translate(text)
        return translated
    except exceptions.LanguageNotSupportedException:
        logger.error(f"Язык '{target_language}' не поддерживается.")
        return "Ошибка: выбранный язык не поддерживается."
    except exceptions.NotValidPayload:
        logger.error("Неверный формат текста для перевода.")
        return "Ошибка: неверный формат текста."
    except Exception as e:
        logger.error(f"Неизвестная ошибка при переводе: {e}")
        return "Ошибка при переводе."

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

    # Проверка, находится ли пользователь в состоянии ожидания ввода языка
    if user_states.get(chat_id) == 'awaiting_language':
        language_code = get_language_code(decoded_text)
        if language_code:
            user_languages[chat_id] = language_code
            user_states.pop(chat_id)  # Сброс состояния
            confirmation_message = f"Язык перевода установлен на {decoded_text.capitalize()}."
            send_message(chat_id, confirmation_message)
            logger.info(f"Пользователь {chat_id} установил язык перевода: {language_code}.")
        else:
            error_message = "Извините, я не распознал этот язык. Пожалуйста, попробуйте снова."
            send_message(chat_id, error_message)
            logger.warning(f"Неизвестный язык '{decoded_text}' от пользователя {chat_id}.")
        return jsonify({"status": "ok"}), 200

    # Проверка, является ли сообщение командой (начинается с '/')
    if decoded_text.startswith('/'):
        # Извлечение команды без слеша и приведение к нижнему регистру
        command = decoded_text[1:].lower()
        logger.info(f"Получена команда '{command}' от пользователя {chat_id}.")

        if command == "start":
            welcome_message = (
                "Добро пожаловать! Я могу переводить ваши сообщения.\n\n"
                "Команды:\n"
                "/switch - Изменить язык перевода.\n"
                "/help - Показать это сообщение.\n"
                "Просто напишите любое сообщение, и я переведу его."
            )
            send_message(chat_id, welcome_message)
            return jsonify({"status": "ok"}), 200

        elif command == "switch":
            switch_message = (
                "Пожалуйста, введите язык, на который хотите перевести (на английском, например, 'English', 'Russian', 'Spanish' и т.д.)."
            )
            send_message(chat_id, switch_message)
            user_states[chat_id] = 'awaiting_language'
            logger.info(f"Ожидание ввода языка от пользователя {chat_id}.")
            return jsonify({"status": "ok"}), 200

        elif command == "help":
            help_message = (
                "Вот доступные команды:\n"
                "/start - Начать работу с ботом и увидеть приветственное сообщение.\n"
                "/switch - Изменить язык перевода.\n"
                "/help - Показать это сообщение."
            )
            send_message(chat_id, help_message)
            return jsonify({"status": "ok"}), 200

        else:
            unknown_command_message = "Неизвестная команда. Введите /help для просмотра доступных команд."
            send_message(chat_id, unknown_command_message)
            logger.warning(f"Неизвестная команда '{command}' от пользователя {chat_id}.")
            return jsonify({"status": "ok"}), 200

    # Если сообщение не является командой и не ожидается ввод языка, выполнить перевод
    target_language = user_languages.get(chat_id, default_language)
    logger.info(f"Перевод сообщения от {chat_id} на язык '{target_language}'.")

    translated_text = translate_text(decoded_text, target_language)
    logger.info(f"Переведённое сообщение для {chat_id}: {translated_text}")

    send_message(chat_id, translated_text)

    return jsonify({"status": "ok"}), 200

# Универсальный маршрут для отладки необработанных путей
@app.route('/<path:path>', methods=['POST'])
def catch_all(path):
    data = request.json
    logger.warning(f"Необработанный путь: {path}")
    logger.warning(f"Получены данные: {data}")
    return jsonify({"status": "Unhandled path"}), 200

if __name__ == "__main__":
    # Запуск Flask-приложения
    app.run(port=8888, debug=True)
