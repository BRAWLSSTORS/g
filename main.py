import telebot

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
TOKEN = '7368730334:AAHrLFjgLQP_PBYRdYkDW5H7QoiZHbBzoUc'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, '<b>Привет! Это жирное сообщение!</b>', parse_mode='HTML')

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
