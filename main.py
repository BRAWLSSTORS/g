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

# Initialize Chrome driver
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

# Function to get location info from coordinates
def get_location_info(lat, lon, driver):
    try:
        # Navigate to the website
        driver.get("https://gps-coordinates.org/")
        
        # Wait for latitude input field and enter value
        lat_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "latitude"))
        )
        lat_input.clear()
        lat_input.send_keys(str(lat))
        
        # Enter longitude
        lon_input = driver.find_element(By.ID, "longitude")
        lon_input.clear()
        lon_input.send_keys(str(lon))
        
        # Click the button to get address
        button = driver.find_element(By.ID, "btnGetAddressByCoordinates")
        button.click()
        
        # Wait for the address to be populated
        time.sleep(2)
        
        # Get the address
        address_input = driver.find_element(By.ID, "address")
        address = address_input.get_attribute("value")
        
        # Take screenshot of the map
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
    button_coordinates = InlineKeyboardButton("ПО КООРДИНАТАМ", callback_data="request_coordinates")
    button_cadastral = InlineKeyboardButton("КАДАСТРОВЫЙ НОМЕР 🇺🇦", callback_data="request_cadastral")
    markup.add(button_coordinates)
    markup.add(button_cadastral)
    bot.send_message(message.chat.id, "Выберите тип ввода:", reply_markup=markup)

# Обработчик callback-запроса для кнопки "ПО КООРДИНАТАМ"
@bot.callback_query_handler(func=lambda call: call.data == "request_coordinates")
def callback_coordinates(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите координаты в формате:  40.75926,-73.98052\n\nЧтобы получить координаты, откройте Google Maps, зажмите нужную точку на карте, затем нажмите на появившиеся координаты и скопируйте их")

# Обработчик callback-запроса для кнопки "КАДАСТРОВЫЙ НОМЕР"
@bot.callback_query_handler(func=lambda call: call.data == "request_cadastral")
def callback_cadastral(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите кадастровый номер\n\nЧтобы получить кадастровый номер, вам потребуется зайти на украинский сайт kadastr.live, затем нажать на любой объект и найти 'Номер' и вставить его мне")

# Обработчик ввода координат
@bot.message_handler(func=lambda message: is_coordinates(message.text))
def handle_coordinates(message):
    coordinates = message.text.strip()
    lat, lon = map(float, coordinates.split(','))
    
    # Get location info using Selenium
    driver = init_driver()
    try:
        location_info = get_location_info(lat, lon, driver)
        
        if location_info:
            # Send the map screenshot with address
            photo = io.BytesIO(location_info['screenshot'])
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"📍 Адрес: {location_info['address']}\n\nПо данным координатам найдены такие результаты:"
            )
        
        # Send additional map links
        google_maps_url = f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}&hl=en&t=m&z=15"
        bing_maps_url = f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15&sp=Point.{lat}_{lon}____"
        apple_maps_url = f"https://maps.apple.com/maps?ll={lat},{lon}&q={lat},{lon}&t=m"
        yandex_maps_url = f"https://maps.yandex.com/?ll={lon},{lat}&spn=0.01,0.01&l=sat,skl&pt={lon},{lat}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Google Maps", url=google_maps_url))
        markup.add(InlineKeyboardButton("Bing Maps", url=bing_maps_url))
        markup.add(InlineKeyboardButton("Apple Maps", url=apple_maps_url))
        markup.add(InlineKeyboardButton("Yandex Maps", url=yandex_maps_url))
        
        bot.send_message(message.chat.id, "Дополнительные карты:", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при получении информации о местоположении: {str(e)}")
    finally:
        driver.quit()

    # Send image and additional buttons
    # Дополнительные ресурсы
    image_url = "https://i.postimg.cc/t4LXnfqX/1000474879.png"
    caption = "Дополнительные ресурсы:"
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Arcgis", url=f"https://livingatlas.arcgis.com/wayback/#localChangesOnly=true&ext={lon},{lat},{lon},{lat}"),
        InlineKeyboardButton("EarthEngine", url=f"https://earthengine.google.com/timelapse/#v={lat},{lon},15,latLng&t=3.04"),
        InlineKeyboardButton("Sentinel", url=f"https://apps.sentinel-hub.com/sentinel-playground/?source=S2L2A&lat={lat}&lng={lon}")
    )
    bot.send_photo(message.chat.id, image_url, caption=caption, reply_markup=markup)
    
    # Continue with sending additional resources
    send_photos_with_buttons(message.chat.id, lat, lon)

def send_photos_with_buttons(chat_id, lat, lon):
    # Первое сообщение с дополнительными ресурсами
    toolforge_url = f"https://osm-gadget-leaflet.toolforge.org/#/?lat={lat}&lon={lon}&zoom=15&lang=commons"
    yandex_url = f"https://yandex.com/maps/?l=sat%2Cpht&ll={lon}%2C{lat}&pt={lon},{lat}&z=15"
    flickr_url = f"https://www.flickr.com/map?&fLat={lat}&fLon={lon}&zl=17"
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Toolforge", url=toolforge_url),
        InlineKeyboardButton("Yandex", url=yandex_url),
        InlineKeyboardButton("Flickr", url=flickr_url)
    )
    
    bot.send_photo(chat_id, 'https://i.postimg.cc/dQhTtC42/1000474891.png', 
                   caption="Результаты по введенным координатам:", 
                   reply_markup=markup)

    # Второе сообщение
    pastvu_url = f"https://pastvu.com/?g={lat},{lon}&z=16&s=osm&t=mapnik&type=1"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Pastvu", url=pastvu_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/63Mp9ByB/1000474905.png', reply_markup=markup)
    
    # Третье сообщение
    zoom_earth_url = f"https://zoom.earth/#view={lat},{lon},8z/date=,+0/layers=wind,fires"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Zoom Earth", url=zoom_earth_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/GpqCDqrQ/1000474913.png', reply_markup=markup)
    
    # Четвертое сообщение
    peakfinder_url = f"https://www.peakfinder.org/?lat={lat}&lng={lon}&name=The%20Antipodes%20of%20"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("PeakFinder", url=peakfinder_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/TPwRCZtS/1000474918.png', reply_markup=markup)

    # Пятое сообщение
    wikimapia_url = f"http://wikimapia.org/m/#lang=en&lat={lat}&lon={lon}&z=15&m=b"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Wikimapia", url=wikimapia_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/QMH3pctZ/1000474926.png', reply_markup=markup)

    # Шестое сообщение
    copernix_url = f"https://copernix.io/#?where={lon},{lat},15&query=&pagename=?language=en"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Copernix", url=copernix_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/rygfL3jg/1000474936.png', reply_markup=markup)

    # Седьмое сообщение
    strava_url = f"https://labs.strava.com/heatmap/#15.11/{lon}/{lat}/hot/all"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Strava", url=strava_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/Hs0m9p93/1000474945.png', reply_markup=markup)

    # Восьмое сообщение
    openstreet_url = f"https://openstreetbrowser.org/#map=15/{lat}/{lon}"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("OpenStreetBrowser", url=openstreet_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/mk2YpZFM/1000474954.png', reply_markup=markup)

    # Девятое сообщение
    cities_url = f"https://www.360cities.net/map?lat={lat}&lng={lon}&zoom=15"
    kartaview_url = f"https://kartaview.org/map/@{lat},{lon},17z"
    mapillary_url = f"https://www.mapillary.com/app/?menu=false&lat={lat}&lng={lon}&z=17&mapStyle=Mapillary+satellite"
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("360 Cities", url=cities_url),
        InlineKeyboardButton("KartaView", url=kartaview_url),
        InlineKeyboardButton("Mapillary", url=mapillary_url)
    )
    bot.send_photo(chat_id, 'https://i.postimg.cc/RFqCgjZh/1000474962.png', reply_markup=markup)

    # Десятое сообщение
    kadastr_url = f"https://kadastr.live/#16.30/{lat}/{lon}"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Kadastr", url=kadastr_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/Wz8kqWTb/1000475071.png', reply_markup=markup)

    # 11 Сообщение
    rosreestr_url = f"https://росреестра-выписка.рус/кадастровая_карта#ct={lat}&cg={lon}&zoom=18"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Росреестр", url=rosreestr_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/L63PBmjz/1000475079.png', reply_markup=markup)

    # 11 Сообщение
    deepstate_url = f"https://deepstatemap.live/#18/{lat}/{lon}"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("DeepState", url=deepstate_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/1zhr6J7x/1000476132.png', reply_markup=markup)

# Обработчик ввода кадастрового номера
@bot.message_handler(func=lambda message: is_cadastral_number(message.text))
def handle_cadastral_number(message):
    cadastral_number = message.text.strip()
    url = f'https://opendatabot.ua/l/{cadastral_number}?from=search'
    bot.send_message(message.chat.id, f"Обрабатываю данные по кадастровому номеру: {cadastral_number}")
    
    screenshot_path, description = parse_opendatabot_page(url)
    
    if screenshot_path:
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file, caption=description)
        os.remove(screenshot_path)
    else:
        bot.send_message(message.chat.id, "Не удалось получить информацию по указанному кадастровому номеру.")

# Функция для закрытия драйвера при завершении работы
def shutdown():
    close_driver()
# Конец команды /geoint


# Запуск бота
while True:
    try:
        logging.info("Бот запущен...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        sleep(5)  # Пауза перед повторной попыткой
    finally:
        try:
            from ip import driver
            driver.quit()  # Закрываем браузер при завершении работы программы
        except Exception as e:
            logging.error(f"Ошибка при закрытии браузера: {e}")
