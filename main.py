import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7067233375:AAEVxtJ91HWZfpttqTouMjTzX8JePKE8HkI'

bot = telebot.TeleBot(API_TOKEN)

# Настройки для запуска Chrome в headless режиме
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Функция для получения адреса и скриншота по координатам
def get_address_and_screenshot(lat, lon):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        driver.get("https://gps-coordinates.org")
        
        # Ввод координат в соответствующие поля
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "latitude"))).send_keys(str(lat))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "longitude"))).send_keys(str(lon))
        
        # Нажатие на кнопку для получения адреса
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnGetAddressByCoordinates")))
        button.click()
        
        # Ожидание получения адреса
        address = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "address"))).get_attribute("value")
        
        # Скриншот карты
        map_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "map")))
        screenshot_path = f"/tmp/map_screenshot_{lat}_{lon}.png"
        map_element.screenshot(screenshot_path)
        
        return address, screenshot_path
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return None, None
    finally:
        driver.quit()

# Обработчик ввода координат
@bot.message_handler(func=lambda message: is_coordinates(message.text))
def handle_coordinates(message):
    coordinates = message.text.strip()
    lat, lon = map(float, coordinates.split(','))

    # Получение адреса и скриншота
    address, screenshot_path = get_address_and_screenshot(lat, lon)
    
    if address and screenshot_path:
        # Отправка изображения и адреса пользователю
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file, caption=f"Адрес: {address}\nПо данным координатам найдены такие результаты:")
        os.remove(screenshot_path)
    else:
        bot.send_message(message.chat.id, "Не удалось получить информацию по указанным координатам.")
    
    # Дополнительные карты
    google_maps_url = f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}&hl=en&t=m&z=15"
    bing_maps_url = f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15&sp=Point.{lat}_{lon}____"
    apple_maps_url = f"https://maps.apple.com/maps?ll={lat},{lon}&q={lat},{lon}&t=m"
    yandex_maps_url = f"https://maps.yandex.com/?ll={lon},{lat}&spn=0.01,0.01&l=sat,skl&pt={lon},{lat}"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Google Maps", url=google_maps_url))
    markup.add(InlineKeyboardButton("Bing Maps", url=bing_maps_url))
    markup.add(InlineKeyboardButton("Apple Maps", url=apple_maps_url))
    markup.add(InlineKeyboardButton("Yandex Maps", url=yandex_maps_url))
    
    bot.send_message(message.chat.id, "Дополнительные результаты по координатам:", reply_markup=markup)

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

bot.polling(none_stop=True)
