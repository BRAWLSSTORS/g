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

def is_cadastral_number(text):
    return ':' in text and any(char.isdigit() for char in text) and not text.startswith(('http://', 'https://'))

def is_coordinates(text):
    parts = text.split(',')
    if len(parts) != 2:
        return False
    try:
        lat, lon = float(parts[0]), float(parts[1])
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except ValueError:
        return False

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

@bot.message_handler(commands=['geoint'])
def request_input(message):
    markup = InlineKeyboardMarkup()
    button_coordinates = InlineKeyboardButton("ПО КООРДИНАТАМ", callback_data="request_coordinates")
    button_cadastral = InlineKeyboardButton("КАДАСТРОВЫЙ НОМЕР 🇺🇦", callback_data="request_cadastral")
    markup.add(button_coordinates)
    markup.add(button_cadastral)
    bot.send_message(message.chat.id, "Выберите тип ввода:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "request_coordinates")
def callback_coordinates(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите координаты в формате:  40.75926,-73.98052\n\nЧтобы получить координаты, откройте Google Maps, зажмите нужную точку на карте, затем нажмите на появившиеся координаты и скопируйте их")

@bot.callback_query_handler(func=lambda call: call.data == "request_cadastral")
def callback_cadastral(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите кадастровый номер\n\nЧтобы получить кадастровый номер, вам потребуется зайти на украинский сайт kadastr.live, затем нажать на любой объект и найти 'Номер' и вставить его мне")

@bot.message_handler(func=lambda message: is_coordinates(message.text))
def handle_coordinates(message):
    coordinates = message.text.strip()
    lat, lon = map(float, coordinates.split(','))

    driver = init_driver()
    try:
        location_info = get_location_info(lat, lon, driver)

        if location_info:
            photo = io.BytesIO(location_info['screenshot'])
            
            # Создаем ссылки для карт
            google_maps_url = f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}&hl=en&t=m&z=15"
            bing_maps_url = f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15&sp=Point.{lat}_{lon}____"
            apple_maps_url = f"https://maps.apple.com/maps?ll={lat},{lon}&q={lat},{lon}&t=m"
            yandex_maps_url = f"https://maps.yandex.com/?ll={lon},{lat}&spn=0.01,0.01&l=sat,skl&pt={lon},{lat}"
            
            # Создаем разметку для кнопок
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("Google Maps", url=google_maps_url),
                InlineKeyboardButton("Bing Maps", url=bing_maps_url),
                InlineKeyboardButton("Apple Maps", url=apple_maps_url),
                InlineKeyboardButton("Yandex Maps", url=yandex_maps_url)
            )
            
            # Отправляем фото с сообщением, адресом и кнопками
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"📍 Адрес: {location_info['address']}\n\nПо данным координатам найдены такие результаты:",
                reply_markup=markup
            )
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при получении информации о местоположении: {str(e)}")
    finally:
        driver.quit()

    send_photos_with_buttons(message.chat.id, lat, lon)

def send_photos_with_buttons(chat_id, lat, lon):
    # Все предыдущие сообщения с кнопками остаются без изменений
    # ... [Весь остальной код функции send_photos_with_buttons остается таким же]
    image_url = "https://i.postimg.cc/t4LXnfqX/1000474879.png"
    caption = "Дополнительные ресурсы:"
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Arcgis", url=f"https://livingatlas.arcgis.com/wayback/#localChangesOnly=true&ext={lon},{lat},{lon},{lat}"),
        InlineKeyboardButton("EarthEngine", url=f"https://earthengine.google.com/timelapse/#v={lat},{lon},15,latLng&t=3.04"),
        InlineKeyboardButton("Sentinel", url=f"https://apps.sentinel-hub.com/sentinel-playground/?source=S2L2A&lat={lat}&lng={lon}")
    )
    bot.send_photo(chat_id, image_url, caption=caption, reply_markup=markup)
    
    # Продолжение кода с остальными сообщениями...
    # [Оставшаяся часть функции send_photos_with_buttons остается без изменений]

@bot.message_handler(func=lambda message: is_cadastral_number(message.text))
def handle_cadastral_number(message):
    cadastral_number = message.text.strip()
    url = f'https://opendatabot.ua/l/{cadastral_number}?from=search'
    bot.send_message(message.chat.id, f"Обрабатываю данные по кадастровому номеру: {cadastral_number}")
    
    driver = init_driver()
    try:
        driver.get(url)
        time.sleep(3)  # Даем время для загрузки страницы
        screenshot = driver.get_screenshot_as_png()
        photo = io.BytesIO(screenshot)
        bot.send_photo(message.chat.id, photo, caption=f"Информация по кадастровому номеру {cadastral_number}")
    except Exception as e:
        bot.send_message(message.chat.id, "Не удалось получить информацию по указанному кадастровому номеру.")
        logger.error(f"Error in handle_cadastral_number: {str(e)}")
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
