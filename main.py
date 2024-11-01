import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from PIL import Image
import io
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7067233375:AAEVxtJ91HWZfpttqTouMjTzX8JePKE8HkI'
bot = telebot.TeleBot(API_TOKEN)

# Функция для проверки, является ли строка кадастровым номером
def is_cadastral_number(text):
    return ':' in text and any(char.isdigit() for char in text) and not text.startswith(('http://', 'https://'))

# Функция для проверки, являются ли введенные данные координатами
def is_coordinates(text):
    parts = text.split(',')
    if len(parts) != 2:
        return False
    try:
        lat, lon = float(parts[0]), float(parts[1])
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except ValueError:
        return False

# Инициализация драйвера Chrome
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Функция для получения информации о местоположении по координатам
def get_location_info(lat, lon, driver):
    try:
        driver.get("https://gps-coordinates.org/")
        
        lat_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "latitude"))
        )
        lat_input.clear()
        lat_input.send_keys(str(lat))
        
        lon_input = driver.find_element(By.ID, "longitude")
        lon_input.clear()
        lon_input.send_keys(str(lon))
        
        button = driver.find_element(By.ID, "btnGetAddressByCoordinates")
        button.click()
        
        time.sleep(2)
        
        address_input = driver.find_element(By.ID, "address")
        address = address_input.get_attribute("value")
        
        map_element = driver.find_element(By.ID, "map")
        screenshot = map_element.screenshot_as_png
        
        return {
            'address': address,
            'screenshot': screenshot
        }
    except Exception as e:
        logger.error(f"Error in get_location_info: {str(e)}")
        return None

# Обработчик команды /geoint
@bot.message_handler(commands=['geoint'])
def request_input(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("ПО КООРДИНАТАМ", callback_data="request_coordinates"))
    markup.add(InlineKeyboardButton("КАДАСТРОВЫЙ НОМЕР 🇺🇦", callback_data="request_cadastral"))
    bot.send_message(message.chat.id, "Выберите тип ввода:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "request_coordinates")
def callback_coordinates(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите координаты в формате:  40.75926,-73.98052")

@bot.callback_query_handler(func=lambda call: call.data == "request_cadastral")
def callback_cadastral(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите кадастровый номер")

# Обработчик ввода координат
@bot.message_handler(func=lambda message: is_coordinates(message.text))
def handle_coordinates(message):
    lat, lon = map(float, message.text.split(','))
    driver = init_driver()
    
    try:
        location_info = get_location_info(lat, lon, driver)
        
        if location_info:
            photo = io.BytesIO(location_info['screenshot'])
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"📍 Адрес: {location_info['address']}\n\nРезультаты по данным координатам:"
            )
        
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Google Maps", url=f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}&hl=en&t=m&z=15"))
            markup.add(InlineKeyboardButton("Bing Maps", url=f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15&sp=Point.{lat}_{lon}____"))
            bot.send_message(message.chat.id, "Дополнительные карты:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"Ошибка при получении информации о местоположении: {str(e)}")
    finally:
        driver.quit()

@bot.message_handler(func=lambda message: is_cadastral_number(message.text))
def handle_cadastral_number(message):
    cadastral_number = message.text.strip()
    bot.send_message(message.chat.id, f"Обрабатываю данные по кадастровому номеру: {cadastral_number}")

    # Вставьте ваш метод обработки кадастрового номера здесь

# Запуск бота
while True:
    try:
        logging.info("Бот запущен...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        time.sleep(5)
