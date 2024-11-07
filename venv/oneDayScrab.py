from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import json


# Tarayıcıyı başlatma ve ayarlama fonksiyonu
def initialize_browser():
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# Konum ve tarihleri ayarlayan fonksiyon
def set_location_and_dates(driver, location, check_in_date, check_out_date):
    driver.get("https://www.agoda.com/")
    try:
        location_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "textInput"))
        )
        location_box.click()
        location_box.send_keys(location)
        time.sleep(2)
        location_box.send_keys(Keys.DOWN)
        location_box.send_keys(Keys.RETURN)

        check_in_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "check-in-box"))
        )
        driver.execute_script("arguments[0].click();", check_in_box)
        time.sleep(1)
        check_in_element = driver.find_element(By.CSS_SELECTOR, f"div[data-date='{check_in_date}']")
        check_in_element.click()

        check_out_box = driver.find_element(By.ID, "check-out-box")
        driver.execute_script("arguments[0].click();", check_out_box)
        time.sleep(1)
        check_out_element = driver.find_element(By.CSS_SELECTOR, f"div[data-date='{check_out_date}']")
        check_out_element.click()

        search_button = driver.find_element(By.CSS_SELECTOR, "button[data-element-name='search-button']")
        driver.execute_script("arguments[0].click();", search_button)
    except Exception as e:
        print("Bir hata oluştu:", e)
        driver.quit()
        exit()


# Otel bilgilerini toplama fonksiyonu
def collect_hotel_data(driver):
    hotel_data = []
    hotels = driver.find_elements(By.XPATH, "//li[@data-hotelid]")
    for hotel in hotels:
        if len(hotel_data) >= 10:
            break

        try:
            hotel_name = hotel.find_element(By.XPATH, ".//h3[@data-selenium='hotel-name']").text
        except:
            hotel_name = "N/A"

        try:
            discount_text = hotel.find_element(By.XPATH, ".//div[@data-element-name='discount-percent']//span").text
        except:
            discount_text = "N/A"

        try:
            hotel_location = hotel.find_element(By.XPATH,
                                                ".//div[@data-element-name='searchweb-propertycard-arealink']//span").text
        except:
            hotel_location = "N/A"

        try:
            old_price = hotel.find_element(By.XPATH, ".//div[@data-element-name='first-cor']").text
        except:
            old_price = "N/A"

        try:
            final_price = hotel.find_element(By.XPATH, ".//span[@data-selenium='display-price']").text
            currency = hotel.find_element(By.XPATH, ".//span[@data-selenium='hotel-currency']").text
        except:
            final_price, currency = "N/A", "N/A"

        hotel_data.append({
            "hotel_name": hotel_name,
            "location": hotel_location,
            "discount_state": discount_text,
            "old_price": old_price,
            "final_price": f"{final_price} {currency}"
        })
    return hotel_data


# Sayfayı kaydırarak verileri toplama fonksiyonu
def scroll_and_collect_data(driver):
    all_hotel_data = []
    scroll_pause_time = 2
    scroll_increment = 300
    last_height = driver.execute_script("return document.body.scrollHeight")
    no_more_data_count = 0

    while len(all_hotel_data) < 10:
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(scroll_pause_time)

        new_data = collect_hotel_data(driver)
        all_hotel_data.extend(new_data)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_more_data_count += 1
            if no_more_data_count >= 5:
                break
        else:
            no_more_data_count = 0
        last_height = new_height

    return all_hotel_data[:10]  # İlk 10 otel ile sınırlıyoruz


# JSON dosyasına kaydetme fonksiyonu
def save_data_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


# Main işlemi
if __name__ == "__main__":
    driver = initialize_browser()
    set_location_and_dates(driver, "Erzurum", "2024-11-14", "2024-11-15")
    hotel_data = scroll_and_collect_data(driver)
    save_data_to_json(hotel_data, "erzurum_top_10_hotels.json")
    driver.quit()
