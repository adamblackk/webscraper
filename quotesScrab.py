from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json

# Tarayıcıyı headless modda başlatmak için seçenekleri ayarlıyoruz
options = Options()
options.add_argument("--headless")  # Arka planda çalışması için

# ChromeDriver başlatma
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Web sitesine gidiyoruz
url = "http://quotes.toscrape.com//"
driver.get(url)

# Tüm veriyi saklayacak bir liste
all_quotes_data = []

# Ana sayfada bulunan "Top Ten Tags" başlığının altındaki etiketleri buluyoruz
soup = BeautifulSoup(driver.page_source, 'html.parser')
top_ten_tags_section = soup.find("div", class_="tags-box")  # Top Ten Tags bölümü
tags = top_ten_tags_section.find_all("a") if top_ten_tags_section else []  # Tüm etiketleri bul

# Her etiketi ziyaret etmek için döngüye alıyoruz
for tag in tags:
    tag_name = tag.text.strip()  # Etiketin ismini alıyoruz
    tag_link = url + tag['href']  # Etiketin bağlantısını alıyoruz

    # Etiketin ilk sayfasına gidiyoruz
    driver.get(tag_link)

    while True:  # Sayfalar arası gezinmek için döngü
        time.sleep(2)  # Sayfanın yüklenmesi için kısa bir süre bekliyoruz

        # Sayfa kaynağını BeautifulSoup ile analiz ediyoruz
        tag_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Sözleri ve yazarları çekiyoruz
        quotes = tag_soup.find_all("span", class_="text")
        authors = tag_soup.find_all("small", class_="author")

        # Etiket altında bulunan her sözü ve yazarı listeye ekliyoruz
        for quote, author in zip(quotes, authors):
            quote_text = quote.text.strip()
            author_text = author.text.strip()
            print(f"Etiket: {tag_name}, Söz: {quote_text}, Yazar: {author_text}")

            # JSON verisi için hazırlıyoruz
            all_quotes_data.append({
                "tag": tag_name,
                "quote":quote_text,
                "auther":author_text
            })

        # "Next" düğmesi var mı kontrol ediyoruz
        next_button = tag_soup.find("li", class_="next")
        if next_button:
            # "Next" düğmesine tıklayarak bir sonraki sayfaya geçiyoruz
            next_link = next_button.find("a")["href"]
            driver.get(url + next_link)
        else:
            # Eğer "Next" düğmesi yoksa döngüden çıkıyoruz
            break

# Tarayıcıyı kapatıyoruz
driver.quit()

# JSON dosyasına yazıyoruz
with open("quotes_by_top_ten_tags_all_pages.json", "w", encoding="utf-8") as json_file:
    json.dump(all_quotes_data, json_file, ensure_ascii=False, indent=4)
