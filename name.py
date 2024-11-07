import os

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
    print("set_location_and_dates ---  çalıstı")
    url = f"https://www.agoda.com/?checkIn={check_in_date}&checkOut={check_out_date}&textToSearch={location}"
    driver.get(url)
    try:
        # Konum kutusunu bekleyip ayarlama
        location_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "textInput"))
        )
        location_box.click()
        location_box.clear()
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
    print("set_location_and_dates ---  sona erdi")


# Otel bilgilerini toplama fonksiyonu
def collect_hotel_data(driver, checkin_date, checkout_date):
    print("collect_hotel_data ---  çalıstı")
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
    print("collect_hotel_data ---  sona erdi")
    return hotel_data


# Sayfayı kaydırarak verileri toplama fonksiyonu
def scroll_and_collect_data(driver, checkin_date, checkout_date):
    print("scroll_and_collect_data ---  çalıstı")
    all_hotel_data = []
    scroll_pause_time = 3
    scroll_increment = 250
    last_height = driver.execute_script("return document.body.scrollHeight")
    no_more_data_count = 0
    last_collected_count = 0  # Son topladığımız otel sayısını takip edeceğiz

    while len(all_hotel_data) < 10:
        # Sayfayı aşağı kaydırma
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(scroll_pause_time)  # Kaydırma sonrası yüklenmesi için bekle

        # Yeni otel verilerini toplama
        new_data = collect_hotel_data(driver, checkin_date, checkout_date)

        # Yeni otelleri ana listeye ekleme ve tekrarları önleme
        for hotel in new_data:
            if hotel not in all_hotel_data:
                all_hotel_data.append(hotel)

        # Eğer topladığımız veri sayısı son kaydırmada değişmediyse, sayfa sonunda olabiliriz
        if len(all_hotel_data) == last_collected_count:
            no_more_data_count += 1
            if no_more_data_count >= 5:  # 5 defa üst üste veri artmazsa çık
                print("Sayfa sonuna ulaşıldı veya daha fazla veri yok.")
                break
        else:
            no_more_data_count = 0  # Yeni veri gelirse sıfırla
            last_collected_count = len(all_hotel_data)  # Güncel sayıya göre ayarla

        # Sayfa sonunda olup olmadığını yükseklikle de kontrol etme
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_more_data_count += 1
            if no_more_data_count >= 5:
                print("Sayfa sonuna ulaşıldı veya daha fazla veri yok.")
                break
        else:
            no_more_data_count = 0
        last_height = new_height
    print("scroll_and_collect_data ---  sona erdi")
    return all_hotel_data[:10]  # İlk 10 otel ile sınırlıyoruz


def dongulu_web_scraping(location, baslangic_tarihi, bitis_tarihi, gun_araligi, tekrar_sayisi):
    driver = initialize_browser()

    # Tarih çiftlerini oluşturuyoruz
    tarih_ciftleri = tarih_ciftleri_olustur(baslangic_tarihi, bitis_tarihi, gun_araligi, tekrar_sayisi)

    # Her tarih çifti için scraping işlemleri
    for idx, (check_in_date, check_out_date) in enumerate(tarih_ciftleri, start=1):
        print(f"\n{idx}. Çift: Giriş: {check_in_date}, Çıkış: {check_out_date} arası veri toplanıyor...")
        web_scraping_islemleri(driver, location, check_in_date, check_out_date)

    print("dongulu_web_scraping--------> sona erdi")


def save_data_to_json(data, filename):
    # Dosya zaten varsa önceki veriyi okuruz, yoksa boş bir liste başlatırız
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as json_file:
            existing_data = json.load(json_file)
    else:
        existing_data = []

    # Mevcut veriye yeni veriyi ekleyerek güncel listeyi oluştururuz
    existing_data.extend(data)

    # Güncellenmiş veri listesini dosyaya yazarız
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)


def web_scraping_islemleri(driver, location, check_in_date, check_out_date):
    # 1. Tarih ve konum ayarlama
    set_location_and_dates(driver, location, check_in_date, check_out_date)

    # 2. Sayfa kaydırma ve veri toplama
    hotel_data = scroll_and_collect_data(driver, check_in_date, check_out_date)

    # 3. Veriyi kaydetme
    filename = "hotels_data.json"  # Tek bir dosya adı belirledik
    save_data_to_json(hotel_data, filename)
    print(f"{filename} dosyasına veri eklendi.")


def tarih_ciftleri_olustur(baslangic_tarihi, bitis_tarihi, gun_araligi, tekrar_sayisi):
    tarih_ciftleri = []

    # İlk başlangıç ve bitiş tarihlerini datetime formatına çeviriyoruz
    baslangic = datetime.strptime(baslangic_tarihi, "%Y-%m-%d")
    bitis = datetime.strptime(bitis_tarihi, "%Y-%m-%d")

    # Kullanıcının belirlediği ilk tarih çifti listeye eklenir
    tarih_ciftleri.append((baslangic.strftime("%Y-%m-%d"), bitis.strftime("%Y-%m-%d")))

    # Belirtilen tekrar sayısı kadar yeni tarih çifti oluşturuyoruz
    for _ in range(tekrar_sayisi - 1):
        # Yeni başlangıç tarihi bir önceki bitiş tarihinden başlar
        baslangic = bitis
        # Yeni bitiş tarihi başlangıç tarihinden itibaren gun_araligi gün kadar ileri taşınır
        bitis = baslangic + timedelta(days=gun_araligi)

        # Yeni tarih çifti listeye eklenir
        tarih_ciftleri.append((baslangic.strftime("%Y-%m-%d"), bitis.strftime("%Y-%m-%d")))

    return tarih_ciftleri


# Main işlemi
if __name__ == "__main__":
    driver = initialize_browser()

    location = "Erzurum"
    start_date = "2024-11-13"
    end_date = "2024-11-14"
    gun_araliği = 1
    tekrar_sayisi = 3 # kaç gün için data kazısın sorusunun cevabı

    dongulu_web_scraping(location, start_date, end_date, gun_araliği, tekrar_sayisi)
    driver.quit()
