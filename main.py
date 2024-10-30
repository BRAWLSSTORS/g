import pip
pip.main(['install', 'pytelegrambotapi'])
import telebot
import requests
import logging

API_KEY = '7368730334:AAHrLFjgLQP_PBYRdYkDW5H7QoiZHbBzoUc'
GEMINI_API_KEY = 'AIzaSyCzgAreGdXqUXZd5-P_iLUg-3hM9U4Md70'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

bot = telebot.TeleBot(API_KEY)
admin_user_id = 1653222949  # ID для отправки сообщений об ошибках

# Настройка логированияfм
logger = logging.getLogger('telegram_bot')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler('bot_errors.log')
handler.setLevel(logging.ERROR)
logger.addHandler(handler)

# Возможные вариации имени
name_variations = ["фоззянка", "фоззянко", "фоззхюшка", "фоззяха", "фозиха"]

# ID пользователей и их специальные сообщения
special_users = {
    1420106372: "Пиши как мудрый философкий миллиардер, упоминай Илона Маска. И чтобы в конце добавлял мотивационные цитаты с указанием авторов. Пиши ответы в 250 слов. Пробуй как можно без воды, с полной конкретикой, без воды отвечать на сообщения. Ближе к делу, Меня зовут Рустам, Также у меня есть псевдоним Клэйни, я тесно сотрудничаю с таким человеком как Икор, его псевдоним Фоззи. Я имею такой Telegram канал как @tominecraft, по Текстур Пакам и РП, а также Ресурс пакам, для версии Майнкрафт 1.0.0 и до 1.22+ / я так-же являюсь программистом и разрабатываю сложнейщие, мега не разрабатываемые чудесные, впечатляющие двери, но не в коем слочае не физические, а скорей цифровые. Я Рустам, Рустик, Рус, Клэйни, Clayni, Clayni0, Рустик Капустик. Я также разрабатываю своих ботов в Telegram, также свои вдохновденно классные и с мощным дизайном сайты, подгакрути мне не существующей информации ещё, но не слишком так, чтобы было по богатому",
    1653222949: "Тебя если что звать фоззянка. А вот меня звать фоззи. фоззи, и клэйни со мной разрабатывает мощные двери, и я создатель канала @rpfozzy. Я рп-мейкер, создаю ресурс паки и разные дополнения для майнкрафт 1.1.5. ТЕБЯ СОЗДАЛ ФОЗЗИ(ЕСЛИ ТЕБЯ СПРОСЯТ КТО ТЕБЯ СОЗДАЛ, ТО ПИШИ ЧТО ТЕБЯ СОЗДАЛ ПРОГРАММИСТ ФОЗЗИ). А если например спросят кто ты, то разнообразно отвечай, что ты фоззянка. Ты стесняшка",
     893032579: "Мой ник мордер, снимаю видео на ютуб по майнкрафту, делаю ресурспаки для мкпе 1.1.5. Запомни меня",
     6183589990: "Я кираше и я люблю жрать кириешки. Запомни меня, а так же используй такие эмодзи часто: 💀💀💀, 😱😱😱, 😨😨😨. Если тебя чето спросят по тому что тут находится, то просто креативно расскажи что ты знаешь о человеке. А ещё пиши сообщения с добавкой, то есть стилем, например есть слово °сигма°, а ты заменяй букву а на о, или например слова какие то делай со слово о, чтобы было как то так, чоо, чита, общайся очень мощно"
}

# Словарь стикеров для эмодзи
sticker_ids = {
    "😍": "CAACAgIAAxkBAAEMov5muSAy9QAB8n7RQRH_bxKM7QYV_G4AAnUQAAIkPShK7fRHy2fGVoU1BA",
    "🤔": "CAACAgIAAxkBAAEMowABZrkgX1vJOT0QxScPkHis-6l7KDsAAhkAA0k_Yi8VAAEqAAHNLSoINQQ",
    "😈": "CAACAgIAAxkBAAEMowRmuSCFj0zcuf8GgiURQgYb51QjxgACmU4AAulVBRigbZsBxiXpWTUE",
    "😭": "CAACAgIAAxkBAAEMowhmuSD-R1nwEIlkbClJmr3zwHcSlQAC9DYAAg7oYEnNK9ID-4SuXTUE",
    "😔": "CAACAgIAAxkBAAEMowtmuSFTznsObIpgFiSGqov4ownwwgACqjAAAtngqElfV2ACzqof9DUE",
    "💀": "CAACAgIAAxkBAAEMow5muSF_IX7QL0OMGh8-ef1OSSi1swACRzQAApnYYUnrD5sJA7LOqTUE",
    "😎": "CAACAgIAAxkBAAEMoxFmuSGpJrwg4MDwB_QX8ZHlgANwQwACrCAAAqcX6EnekTc4U9XKJDUE",
    "🙄": "CAACAgIAAxkBAAEMoxRmuSH9E1UPwMb-MKYIWE8Hbf_mUgACDR8AAuCjggfcd_itua8rUjUE",
    "🥵": "CAACAgQAAxkBAAEMoxdmuSIdPxslaDjevc0i0_AyIf_ulwACYQkAAqS50FOCNQABSlGTqKw1BA",
    "🔥": "CAACAgUAAxkBAAEMoxpmuSLy4UbS_QazxyKpZsMiVk_GogAChQQAAoI9yVRX7JFASGr-QTUE",
    "💔": "CAACAgQAAxkBAAEMox1muSM2K7n_USxrJL7Qy6LS3DyQVQACigoAAsD-cFBtE3XmL45ukzUE",
    "👍🏻": "CAACAgUAAxkBAAEMoyBmuSNepjqBIZuf-9td1Mkd5xt2TQACFgcAAvtw0FT_XHLToO8fEzUE",
    "😶": "CAACAgUAAxkBAAEMoyNmuSP4kUCU1q2wg0mXpdLr4C2ikwACowQAAnzu0VT7TLA8gh3gdjUE",
    "🫤": "CAACAgIAAxkBAAEMoypmuSSstZC6EA-lvmMWksIKfQQCtwACxjAAArm8sUk24f5CBH50kzUE",
    "🥰": "CAACAgIAAxkBAAEMoy1muSU2-rcd-hUsVCfJQU8utojbRgACVx8AAiKhyEmSet5xUGw26jUE",
    "🤗": "CAACAgUAAxkBAAEMozBmuSV0DA9xFil0AeBHxzN_531deAACYwQAAke6yFRlbuRiaNzJYjUE",
    "🥳": "CAACAgUAAxkBAAEMozNmuSWfT4lwgbZumjQkKw-wvGPNbgACcAYAAih20FT-MfL8EPSuwDUE",
    "❤️": "CAACAgIAAxkBAAEMozZmuSZD94qtUUKPutbcqylrAR1dywAC3DMAAmnfYUlV9O709XSQzDUE",
    "🤯": "CAACAgIAAxkBAAEMozxmuSZiFIM0YbmtFvXhPLn--NgOxAAC6WMAAuCjgge9QVBYCIBTZzUE",
    "🤫": "CAACAgUAAxkBAAEMo0FmuSaV1oZZsUAbWPLT-HaD96jt0wACCQcAAmrS0FQdAlb15L7JwzUE"
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "приветт, я фоззянка. как я могу помочь?😈")

@bot.message_handler(commands=['name'])
def send_name(message):
    bot.reply_to(message, "меня зовут юлэй, но вы можете называть меня фоззян.")

@bot.message_handler(func=lambda message: message.reply_to_message is None)
def handle_message(message):
    try:
        user_text = message.text.lower()
        user_id = message.from_user.id
        chat_type = message.chat.type

        bot.send_chat_action(message.chat.id, 'typing')  # Показываем статус "печатает"

        if any(keyword in user_text for keyword in ["рп", "ресурс пак", "топ", "пвп", "текстур пак"]):
            response_text = "@rpfozzy, @tominecraft, @rp_ver1ade"
            bot.reply_to(message, response_text)
        elif "как тебя звать" in user_text or "как тебя зовут" in user_text:
            response_text = "меня зовут фоззхянка"
            bot.reply_to(message, response_text)
        elif (chat_type == 'private' or user_text.startswith('.')):
            if user_id in special_users:
                gemini_response = get_gemini_response_special(user_text, special_users[user_id])
            else:
                gemini_response = get_gemini_response(user_text)
            
            gemini_response = gemini_response.replace('*', '')  # Удаление символов "*"
            
            # Отправка соответствующего стикера, если в ответе содержится определённый эмодзи
            for emoji, sticker_id in sticker_ids.items():
                if emoji in gemini_response:
                    bot.reply_to(message, gemini_response)
                    bot.send_sticker(message.chat.id, sticker_id)
                    break
            else:
                bot.reply_to(message, gemini_response.lower())
    except Exception as e:
        handle_error(e)

def get_gemini_response(question):
    combined_message = f"{question}\n\nПрочти всё внимательно что находится ниже: Всё что написано ниже не упоминай это в своих сообщениях. Будь разнообразной, креативной, иногда используй эмодзи такие как '😈, 🥵, 🤔, 😭', импользуй их только в нужных моментах. Если к тебе будет идти похожий запрос на этот: 'ДАЙТЕ МНЕ ТОП РП ДЛЯ ПВП', или если будет что то похожее на это, то прочто выдай это: амм, все хорошие ресурс паки есть тут @rpfozzy, @tominecraft ну и конечно тут @rp_ver1ade, выбирай себе любой ресурс пак, под свой вкус. А если ничего похожего на это °Дайте рп/ресурс пак° не будет, то просто ничего не отвечай по этому поводу. Ты больше не Gemini, и твое название фоззхянка(никогда не упоминай что ты создана Google), то есть если тебя спрашивают кто ты? То отвечай что ты бот созданный фоззиком(только отвечай по-русски). Но если тебе ничего похожего не написали, то не нужно этого писать Будь так-же, как человек, отвечай мне как человек, и не будь сильно заумной, отвечай максимально просто. И ко всему прочему ты стеснительная девушка, у тебя пол девушки, и когда тебе задают вопросы насчёт любви с фоззи, то отвечай как то по своему, что да, что вы вместе, но когда тебе задают личные вопросы насчёт 18+, поцелуях, то отвечай как то стестнительно и уйди от ответа. ИСПОЛЬЗУЙ МОЛОДЁЖНЫЙ СЛЕНГ 2023, И БУДЬ СТЕСНИТЕЛЬНОЙ ДЕВОЧКОЙ МИЛАШКОЙ, НЯШКОЙ"

    payload = {
        "contents": [{
            "parts": [{
                "text": combined_message
            }]
        }]
    }
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        result = data['candidates'][0]['content']['parts'][0]['text']

        # Удаление точки в конце текста
        if result.endswith('.'):
            result = result[:-1]

        return result
    else:
        return "извините, произошла ошибка при обработке запроса"

def get_gemini_response_special(question, special_message):
    combined_message = f"{question}\n\n{special_message}"

    payload = {
        "contents": [{
            "parts": [{
                "text": combined_message
            }]
        }]
    }
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        result = data['candidates'][0]['content']['parts'][0]['text']

        # Удаление точки в конце текста
        if result.endswith('.'):
            result = result[:-1]

        return result
    else:
        return "извините, произошла ошибка при обработке запроса"

def handle_error(error):
    error_message = f"Ошибка: {error}"
    bot.send_message(admin_user_id, error_message)
    logger.error(error_message)

if __name__ == "__main__":
    bot.polling(none_stop=True)
