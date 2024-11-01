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
import zipfile
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7067233375:AAEVxtJ91HWZfpttqTouMjTzX8JePKE8HkI'
bot = telebot.TeleBot(API_TOKEN)

def setup_ublock():
    """Скачивает и подготавливает последнюю версию uBlock Origin"""
    extensions_dir = os.path.join(os.getcwd(), 'extensions')
    if not os.path.exists(extensions_dir):
        os.makedirs(extensions_dir)
    
    ublock_zip_path = os.path.join(extensions_dir, 'ublock.zip')
    ublock_dir = os.path.join(extensions_dir, 'ublock')
    
    ublock_url = "https://github.com/gorhill/uBlock/releases/download/1.60.1rc4/uBlock0_1.60.1rc4.chromium.zip"
    
    try:
        if not os.path.exists(ublock_dir):
            logger.info("Скачиваем uBlock Origin...")
            response = requests.get(ublock_url)
            response.raise_for_status()
            
            with open(ublock_zip_path, 'wb') as f:
                f.write(response.content)
            
            logger.info("Распаковываем uBlock Origin...")
            with zipfile.ZipFile(ublock_zip_path, 'r') as zip_ref:
                zip_ref.extractall(ublock_dir)
            
            os.remove(ublock_zip_path)
            logger.info("uBlock Origin успешно установлен")
        else:
            logger.info("uBlock Origin уже установлен")
    
    except Exception as e:
        logger.error(f"Ошибка при установке uBlock Origin: {e}")
        return None
    
    return ublock_dir

def init_driver():
    """Инициализация Chrome с блокировщиком рекламы"""
    ublock_path = setup_ublock()
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    if ublock_path:
        chrome_options.add_argument(f"--load-extension={ublock_path}")
    
    # Дополнительные настройки для блокировки рекламы
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-notifications')
    
    # Настройки приватности и безопасности
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values": {
            "ads": 2,
            "notifications": 2,
            "popups": 2
        }
    })
    
    # Блокируем рекламные домены
    blocked_domains = [
        "'*googlesyndication.com*'",
        "'*googleadservices.com*'",
        "'*doubleclick.net*'",
        "'*google-analytics.com*'",
        "'*adnxs.com*'",
        "'*advertising.com*'"
    ]
    chrome_options.add_argument('--host-rules=' + ','.join(['MAP ' + domain + ' 127.0.0.1' for domain in blocked_domains]))
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Включаем блокировку рекламных URL через CDP
    driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": [
        "*googlesyndication.com*",
        "*googleadservices.com*",
        "*doubleclick.net*",
        "*google-analytics.com*",
        "*adnxs.com*",
        "*advertising.com*"
    ]})
    driver.execute_cdp_cmd('Network.enable', {})
    
    return driver

def is_coordinates(text):
    parts = text.split(',')
    if len(parts) != 2:
        return False
    try:
        lat, lon = float(parts[0]), float(parts[1])
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except ValueError:
        return False

@bot.message_handler(func=lambda message: is_coordinates(message.text))
def handle_coordinates(message):
    coordinates = message.text.strip()
    lat, lon = map(float, coordinates.split(','))
    
    driver = init_driver()
    try:
        # Отправляем сообщение с адресом
        address = "Rockefeller Center, 67 W 49th St, New York, NY 10112, United States"
        bot.send_message(
            message.chat.id,
            f"📍 Адрес: {address}\n\nПо данным координатам найдены такие результаты:"
        )
        
        # Добавляем инлайн кнопки для карт
        google_maps_url = f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}&hl=en&t=m&z=15"
        bing_maps_url = f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15&sp=Point.{lat}_{lon}____"
        apple_maps_url = f"https://maps.apple.com/maps?ll={lat},{lon}&q={lat},{lon}&t=m"
        yandex_maps_url = f"https://maps.yandex.com/?ll={lon},{lat}&spn=0.01,0.01&l=sat,skl&pt={lon},{lat}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Google Maps", url=google_maps_url))
        markup.add(InlineKeyboardButton("Bing Maps", url=bing_maps_url))
        markup.add(InlineKeyboardButton("Apple Maps", url=apple_maps_url))
        markup.add(InlineKeyboardButton("Yandex Maps", url=yandex_maps_url))
        
        bot.send_message(message.chat.id, "Изображение", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при получении информации о местоположении: {str(e)}")
    finally:
        driver.quit()

# Запуск бота
if __name__ == "__main__":
    logger.info("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(5)
