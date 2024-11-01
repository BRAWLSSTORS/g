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
import requests
import zipfile
import io
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API токен бота
API_TOKEN = '7067233375:AAEVxtJ91HWZfpttqTouMjTzX8JePKE8HkI'
bot = telebot.TeleBot(API_TOKEN)

def setup_ublock():
    """Скачивает и подготавливает последнюю версию uBlock Origin."""
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
    """Инициализация Chrome с блокировщиком рекламы."""
    ublock_path = setup_ublock()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    if ublock_path:
        chrome_options.add_argument(f"--load-extension={ublock_path}")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@bot.message_handler(func=lambda message: ',' in message.text)
def handle_coordinates(message):
    try:
        lat, lon = map(float, message.text.split(','))
        
        # Инициализация браузера
        driver = init_driver()
        
        driver.get("https://gps-coordinates.org/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "latitude"))).send_keys(str(lat))
        driver.find_element(By.ID, "longitude").send_keys(str(lon))
        driver.find_element(By.ID, "btnGetAddressByCoordinates").click()
        time.sleep(2)
        
        address = driver.find_element(By.ID, "address").get_attribute("value")
        
        # Отправка фото и адреса
        bot.send_photo(
            message.chat.id,
            "https://i.postimg.cc/t4LXnfqX/1000474879.png",  # Замените на изображение карты
            caption=f"📍 Адрес: {address}\n\nПо данным координатам найдены такие результаты:"
        )
        
        # Генерация кнопок карт
        google_maps_url = f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}"
        bing_maps_url = f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15"
        apple_maps_url = f"https://maps.apple.com/maps?ll={lat},{lon}&q={lat},{lon}"
        yandex_maps_url = f"https://maps.yandex.com/?ll={lon},{lat}&spn=0.01,0.01"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Google Maps", url=google_maps_url))
        markup.add(InlineKeyboardButton("Bing Maps", url=bing_maps_url))
        markup.add(InlineKeyboardButton("Apple Maps", url=apple_maps_url))
        markup.add(InlineKeyboardButton("Yandex Maps", url=yandex_maps_url))
        
        bot.send_message(message.chat.id, "Выберите карту:", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")
    finally:
        driver.quit()

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
