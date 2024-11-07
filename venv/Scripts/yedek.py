from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
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
        # Konum kutusunu bekleyip ayarlama
        location_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "textInput"))
        )
        location_box.click()
        location_box.send_keys(location)
        time.sleep(2)
        location_box.send_keys(Keys.DOWN)
        location_box.send_keys(Keys.RETURN)

        # Check-in kutusunu tıklayıp takvimi açma
        check_in_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "check-in-box"))
        )
        print("Check-in kutusuna tıklanıyor")
        driver.execute_script("arguments[0].click();", check_in_box)
        time.sleep(2)

        # Check-in tarihini seçme
        try:
            check_in_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"span[data-selenium-date='{check_in_date}']"))
            )
            check_in_element.click()
        except TimeoutException:
            print("Check-in tarih elementi bulunamadı, alternatif yöntemle ayarlanıyor.")
            driver.execute_script(
                f"document.querySelector('input[data-element-name=\"check-in-box\"]').value = '{check_in_date}';")

        # Check-out tarihini seçme
        print("Check-out tarihi seçiliyor")
        try:
            check_out_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"span[data-selenium-date='{check_out_date}']"))
            )
            check_out_element.click()
        except TimeoutException:
            print("Check-out tarih elementi bulunamadı, alternatif yöntemle ayarlanıyor.")
            driver.execute_script(
                f"document.querySelector('input[data-element-name=\"check-out-box\"]').value = '{check_out_date}';")

        # Ara butonuna tıklama
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-element-name='search-button']"))
        )
        search_button.click()

    except Exception as e:
        print("Bir hata oluştu:", e)
        driver.quit()


# Otel bilgilerini toplama fonksiyonu
def collect_hotel_data(driver, checkin_date, checkout_date):
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
            "start_date": checkin_date,
            "end_date": checkout_date,
            "hotel_name": hotel_name,
            "location": hotel_location,
            "discount_state": discount_text,
            "old_price": old_price,
            "final_price": f"{final_price} {currency}"
        })
    return hotel_data


# Sayfayı kaydırarak verileri toplama fonksiyonu
def scroll_and_collect_data(driver, checkin_date, checkout_date):
    all_hotel_data = []
    scroll_pause_time = 3
    scroll_increment = 250
    last_height = driver.execute_script("return document.body.scrollHeight")
    no_more_data_count = 0

    while len(all_hotel_data) < 10:
        # Sayfayı aşağı kaydırma
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(scroll_pause_time)

        # Yeni otel verilerini toplama
        new_data = collect_hotel_data(driver, checkin_date, checkout_date)

        """
                for hotel in new_data:
            if hotel not in all_hotel_data:
                all_hotel_data.append(hotel)
        """

        all_hotel_data.append(new_data)
        # Yeterli veri toplandıysa döngüden çıkma
        if len(all_hotel_data) >= 10:
            break

        # Sayfa sonunda olup olmadığını kontrol etme
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_more_data_count += 1
            if no_more_data_count >= 5:  # Aynı yüksekliğe 5 kez ulaşırsa çık
                print("Sayfa sonuna ulaşıldı veya daha fazla veri yok.")
                break
        else:
            no_more_data_count = 0
        last_height = new_height

    return all_hotel_data[:10]  # İlk 10 otel ile sınırlıyoruz


def load_data_by_date(driver, location, start_date, end_date, num_days):
    # Başlangıç tarihini datetime formatına çeviriyoruz
    current_date = datetime.strptime(start_date, "%Y-%m-%d")

    all_collected_data = []

    while current_date < datetime.strptime(end_date, "%Y-%m-%d"):
        # Check-in ve check-out tarihlerini ayarla
        check_in_date = current_date.strftime("%Y-%m-%d")
        check_out_date = (current_date + timedelta(days=num_days)).strftime("%Y-%m-%d")

        # URL'de tarihleri güncelleme
        url = f"https://www.agoda.com/?checkIn={check_in_date}&checkOut={check_out_date}&location={location}"
        driver.get(url)

        # Ara butonuna tıklama
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-element-name='search-button']"))
        )
        search_button.click()

        # Otel verilerini kaydırarak toplama
        hotel_data = scroll_and_collect_data(driver, start_date, end_date)
        all_collected_data.extend(hotel_data)

        # Tarih aralığını güncelle (örneğin 7 gün ileriye git)
        current_date += timedelta(days=num_days)

        # Her aramadan sonra biraz bekleyin (isteğe bağlı)
        time.sleep(3)

    # Tüm verileri JSON olarak kaydetme
    save_data_to_json(all_collected_data, "all_dates_hotels.json")
    print("Tüm tarihler için veriler kaydedildi.")


# JSON dosyasına kaydetme fonksiyonu
def save_data_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


# Main işlemi
if __name__ == "__main__":
    driver = initialize_browser()
    set_location_and_dates(driver, "Erzurum", "2024-11-13", "2024-11-14")
    hotel_data = scroll_and_collect_data(driver, "2024-11-14", "2024-11-15")
    load_data_by_date(driver, "Erzurum", "2024-11-15", "2024-11-16", 2)
    driver.quit()
