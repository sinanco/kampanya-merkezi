import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Bankaların Ana ve Alt Kategori Sayfaları (Derin Tarama Listesi)
BANKS = [
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "color": "#EC4899",
        "baseUrl": "https://www.bankkart.com.tr",
        "urls": [
            ("Genel", "https://www.bankkart.com.tr/kampanyalar"),
            ("Akaryakıt", "https://www.bankkart.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.bankkart.com.tr/kampanyalar/market"),
            ("E-Ticaret", "https://www.bankkart.com.tr/kampanyalar/e-ticaret"),
            ("Giyim", "https://www.bankkart.com.tr/kampanyalar/giyim-ve-aksesuar"),
            ("Elektronik", "https://www.bankkart.com.tr/kampanyalar/beyaz-esya-ve-elektronik"),
            ("Seyahat", "https://www.bankkart.com.tr/kampanyalar/seyahat"),
            ("Restoran", "https://www.bankkart.com.tr/kampanyalar/kafe-ve-restoran")
        ],
        "howToJoin": "Bankkart Mobil uygulamasından, bankkart.com.tr'den veya SMS ile katılım sağlayabilirsiniz."
    },
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "color": "#10B981",
        "baseUrl": "https://www.bonus.com.tr",
        "urls": [
            ("Genel", "https://www.bonus.com.tr/kampanyalar"),
            ("Akaryakıt", "https://www.bonus.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.bonus.com.tr/kampanyalar/market"),
            ("E-Ticaret", "https://www.bonus.com.tr/kampanyalar/e-ticaret"),
            ("Giyim", "https://www.bonus.com.tr/kampanyalar/giyim-aksesuar"),
            ("Elektronik", "https://www.bonus.com.tr/kampanyalar/elektronik"),
            ("Seyahat", "https://www.bonus.com.tr/kampanyalar/seyahat"),
            ("Restoran", "https://www.bonus.com.tr/kampanyalar/restoran")
        ],
        "howToJoin": "Harcama öncesi BonusFlaş uygulamasından 'Hemen Katıl' butonuna tıklayın."
    },
    {
        "bank": "Maximum",
        "bankFullName": "Maximum (İş Bankası)",
        "color": "#EF4444",
        "baseUrl": "https://www.maximum.com.tr",
        "urls": [
            ("Genel", "https://www.maximum.com.tr/kampanyalar"),
            ("Akaryakıt", "https://www.maximum.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.maximum.com.tr/kampanyalar/market"),
            ("E-Ticaret", "https://www.maximum.com.tr/kampanyalar/e-ticaret"),
            ("Giyim", "https://www.maximum.com.tr/kampanyalar/giyim-ve-aksesuar"),
            ("Elektronik", "https://www.maximum.com.tr/kampanyalar/elektronik"),
            ("Seyahat", "https://www.maximum.com.tr/kampanyalar/seyahat-ve-konaklama")
        ],
        "howToJoin": "Maximum Mobil veya İşCep uygulamasında 'Kampanyalar' bölümünden katılabilirsiniz."
    },
    {
        "bank": "World",
        "bankFullName": "World (Yapı Kredi)",
        "color": "#6366F1",
        "baseUrl": "https://www.worldcard.com.tr",
        "urls": [
            ("Genel", "https://www.worldcard.com.tr/kampanyalar"),
            ("Akaryakıt", "https://www.worldcard.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.worldcard.com.tr/kampanyalar/gida-market"),
            ("E-Ticaret", "https://www.worldcard.com.tr/kampanyalar/internet-alisverisleri"),
            ("Giyim", "https://www.worldcard.com.tr/kampanyalar/giyim-aksesuar"),
            ("Elektronik", "https://www.worldcard.com.tr/kampanyalar/elektronik"),
            ("Seyahat", "https://www.worldcard.com.tr/kampanyalar/seyahat-konaklama")
        ],
        "howToJoin": "World Mobil uygulaması üzerinden 'Hemen Katıl' butonuna basarak aktif edebilirsiniz."
    },
    {
        "bank": "Axess",
        "bankFullName": "Axess (Akbank)",
        "color": "#F59E0B",
        "baseUrl": "https://www.axess.com.tr",
        "urls": [
            ("Genel", "https://www.axess.com.tr/axess/kampanya/83/391/kampanyalar")
        ],
        "howToJoin": "Juzdan uygulamasından kampanya sayfasına gidip 'Hemen Katıl'a dokunun."
    },
    {
        "bank": "Paraf",
        "bankFullName": "Paraf (Halkbank)",
        "color": "#0EA5E9",
        "baseUrl": "https://www.paraf.com.tr",
        "urls": [
            ("Genel", "https://www.paraf.com.tr/tr/kampanyalar.html")
        ],
        "howToJoin": "Paraf Mobil uygulamasından veya SMS ile kampanya katılımınızı onaylayın."
    },
    {
        "bank": "CardFinans",
        "bankFullName": "CardFinans (QNB)",
        "color": "#3B82F6",
        "baseUrl": "https://www.cardfinans.com",
        "urls": [
            ("Genel", "https://www.cardfinans.com/kampanyalar")
        ],
        "howToJoin": "QNB Mobil üzerinden veya POS cihazından taksit/puan seçimiyle katılabilirsiniz."
    }
]

# İstenmeyen menü/footer linklerini elemek için kara liste
IGNORE_WORDS = [
    "tüm kampanyalar", "geçmiş kampanyalar", "sona eren", "arşiv", "kart başvurusu",
    "bize ulaşın", "sıkça sorulan", "kvkk", "çerez", "gizlilik", "detaylı bilgi",
    "hemen başvur", "şifre al", "kredi kartları", "özellikler", "üye işyeri"
]

def detect_category(text, fallback_cat="Genel"):
    t = text.lower()
    if any(k in t for k in ["akaryakıt", "opet", "shell", "petrol", "otogaz", "bp", "aytemiz", "şarj", "zes", "eşarj", "trugo", "yakıt", "lukoil", "totalenergies", "kadoil", "alpet"]):
        return "Akaryakıt"
    if any(k in t for k in ["market", "migros", "carrefour", "gıda", "a101", "şok", "bim", "süpermarket", "file", "macrocenter", "tarım kredi", "kasap", "manav"]):
        return "Market"
    if any(k in t for k in ["elektronik", "mediamarkt", "teknosa", "vatan", "apple", "telefon", "bilgisayar", "teknoloji", "beyaz eşya", "vestel", "arçelik", "beko", "samsung", "monster", "itopya"]):
        return "Elektronik"
    if any(k in t for k in ["giyim", "zara", "boyner", "mavi", "lcw", "lc waikiki", "ayakkabı", "kozmetik", "moda", "beymen", "defacto", "koton", "flo", "network", "altınyıldız"]):
        return "Giyim"
    if any(k in t for k in ["uçak", "bilet", "otel", "seyahat", "tatil", "thy", "pegasus", "ajet", "ets", "jolly", "setur", "obilet", "konaklama", "araç kiralama", "duty free", "yurt dışı"]):
        return "Seyahat"
    if any(k in t for k in ["restoran", "kafe", "kahve", "yemek", "starbucks", "yemeksepeti", "getiryemek", "burger", "espressolab"]):
        return "Restoran"
    if any(k in t for k in ["trendyol", "hepsiburada", "amazon", "n11", "pazarama", "e-ticaret", "online", "internet", "çiçeksepeti", "idefix"]):
        return "E-Ticaret"
    return fallback_cat if fallback_cat != "Genel" else "E-Ticaret"

def detect_brand(text, category):
    known_brands = [
        "Migros", "CarrefourSA", "Opet", "Shell", "Petrol Ofisi", "TotalEnergies", "BP", "Aytemiz", "Lukoil",
        "Trendyol", "Hepsiburada", "Amazon", "Pazarama", "N11", "Zara", "Boyner", "Beymen", "DeFacto", "Koton",
        "Mavi", "LCW", "FLO", "MediaMarkt", "Teknosa", "Vatan", "Arçelik", "Beko", "Vestel", "Samsung", "Apple",
        "THY", "Pegasus", "AJet", "Obilet", "ETS", "Jolly", "Setur", "Starbucks", "Yemeksepeti",
        "A101", "ŞOK", "BİM", "Tarım Kredi", "ZES", "Eşarj", "Trugo", "İdefix"
    ]
    found = [b for b in known_brands if re.search(r'\b' + re.escape(b.lower()) + r'\b', text.lower()) or b.lower() in text.lower()]
    if found:
        # Tekrarları kaldırıp ilk 2 markayı birleştir
        unique_brands = list(dict.fromkeys(found))
        return " & ".join(unique_brands[:2])
    return f"Anlaşmalı {category} İşyerleri"

def extract_reward(text):
    # 1. TL / Puan / Lira yakalama (Örn: "300 TL Bankkart Lira", "1.500 TL'ye varan Bonus")
    tl_match = re.search(r'(\d[\d\.]*)\s*TL(?:\'ye\s*varan|\s*değerinde)?\s*(Bankkart\s*Lira|Bonus|Worldpuan|MaxiPuan|Chip-Para|Chip\s*Para|ParafPara|ParaPuan|Puan|İndirim|Hediye)?', text, re.IGNORECASE)
    if tl_match:
        amount = tl_match.group(1)
        rtype = (tl_match.group(2) or "Puan").strip()
        return f"{amount} TL {rtype.title()}"

    # 2. Yüzde indirim/kazanım yakalama (Örn: "%20 İndirim", "%10 Bonus")
    pct_match = re.search(r'%\s*(\d+)\s*(İndirim|Bonus|Puan|Bankkart\s*Lira|Chip-Para|Avantaj)?', text, re.IGNORECASE)
    if pct_match:
        return f"%{pct_match.group(1)} {(pct_match.group(2) or 'İndirim').title()}"

    # 3. Taksit yakalama (Örn: "6 Taksit", "+3 Taksit")
    taksit_match = re.search(r'(\+?\d+)\s*Taksit', text, re.IGNORECASE)
    if taksit_match:
        return f"{taksit_match.group(1)} Taksit"

    return "Özel Kampanya"

def extract_min_spend(text):
    # Harcama şartı yakalama (Örn: "1.000 TL ve üzeri", "4 kez 750 TL")
    multi_match = re.search(r'(\d+)\s*(?:kez|adet|defa)\s*(\d[\d\.]*)\s*TL', text, re.IGNORECASE)
    if multi_match:
        return f"{multi_match.group(1)} x {multi_match.group(2)} TL"
    
    spend_match = re.search(r'(\d[\d\.]*)\s*TL\s*(?:ve\s*üzeri|harcamaya|alışverişe)', text, re.IGNORECASE)
    if spend_match:
        return f"{spend_match.group(1)} TL ve üzeri"
    
    return "Detaylar Resmi Sayfada"

async def auto_scroll_and_load_more(page):
    """Sayfayı aşağı kaydırarak Lazy-Load (sonradan yüklenen) kampanya kartlarını açar."""
    try:
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, 1200)")
            await page.wait_for_timeout(800)
            
            # Eğer "Daha Fazla Göster" butonu varsa tıkla
            for btn_text in ["Daha Fazla", "Tümünü Gör", "Daha Fazla Göster"]:
                btn = page.locator(f"button:has-text('{btn_text}'), a:has-text('{btn_text}')").first
                if await btn.is_visible(timeout=500):
                    await btn.click()
                    await page.wait_for_timeout(1200)
    except Exception:
        pass

async def scrape_bank(page, bank_info, start_id, global_seen_titles):
    results = []
    
    for default_cat, url in bank_info["urls"]:
        try:
            print(f"[{bank_info['bank']}] Taranıyor ({default_cat}): {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=35000)
            await page.wait_for_timeout(2500)
            await auto_scroll_and_load_more(page)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Kampanya kartlarını ve linklerini geniş kapsamlı yakala
            elements = soup.select("a[href*='kampanya'], div[class*='camp'], div[class*='card'], div[class*='item'], li[class*='camp'], h3, h4")

            for el in elements:
                # Elementin kendisinden veya üst/alt linkinden URL'yi bul
                link_href = el.get("href")
                if not link_href:
                    a_tag = el.find("a", href=True) or el.find_parent("a", href=True)
                    if a_tag:
                        link_href = a_tag.get("href")

                full_url = urljoin(bank_info["baseUrl"], link_href) if link_href else url

                # Başlık ve açıklama metnini temizle
                raw_text = " ".join(el.get_text(" ", strip=True).split())
                raw_text = re.sub(r'\s*(Detaylı Bilgi|Hemen Katıl|İncele|Detaylar|Kampanya Detayı)\s*$', '', raw_text, flags=re.IGNORECASE)

                if len(raw_text) < 20 or len(raw_text) > 220:
                    continue

                lower_text = raw_text.lower()
                if any(bad in lower_text for bad in IGNORE_WORDS):
                    continue

                # Gerçek bir kampanya mı kontrol et (Ödül kelimesi, rakam veya kampanya detay linki içermeli)
                has_campaign_signal = bool(re.search(r'(\d+\s*TL|%\s*\d+|Taksit|Puan|Bonus|Lira|Chip|Paraf|İndirim|Fırsat|Hediye|Kampanya|üzeri|alışveriş)', raw_text, re.IGNORECASE))
                is_deep_campaign_url = link_href and ("/kampanyalar/" in link_href or "/kampanya/" in link_href) and len(link_href) > 22

                if not (has_campaign_signal or is_deep_campaign_url):
                    continue

                # Aynı kampanyayı iki kez eklemeyi önle
                norm_key = f"{bank_info['bank']}_{re.sub(r'[^a-z0-9ğüşıöç]', '', lower_text)[:40]}"
                if norm_key in global_seen_titles:
                    continue
                global_seen_titles.add(norm_key)

                category = detect_category(raw_text, default_cat)
                brand = detect_brand(raw_text, category)
                reward = extract_reward(raw_text)
                min_spend = extract_min_spend(raw_text)

                # Yüksek ödüllü kampanyaları vitrine (Öne Çıkanlar) çıkar
                is_featured = any(x in reward for x in ["300", "350", "400", "500", "600", "750", "1.000", "1000", "1.500", "%20", "%25"])

                results.append({
                    "id": start_id + len(results),
                    "bank": bank_info["bank"],
                    "bankFullName": bank_info["bankFullName"],
                    "category": category,
                    "brand": brand,
                    "title": raw_text[:115] + ("..." if len(raw_text) > 115 else ""),
                    "desc": f"{raw_text}. Kampanya katılım koşulları ve geçerli üye işyerleri için resmi banka sayfasını inceleyebilirsiniz.",
                    "reward": reward,
                    "minSpend": min_spend,
                    "date": f"Aktif ({datetime.now().strftime('%d.%m.%Y')})",
                    "color": bank_info["color"],
                    "isFeatured": is_featured,
                    "howToJoin": bank_info["howToJoin"],
                    "sourceUrl": full_url
                })

                if len(results) >= 60:  # Banka başına 60 kampanyaya kadar izin ver
                    break

        except Exception as e:
            print(f"Uyarı ({bank_info['bank']} - {url}): {e}")

    print(f"--> {bank_info['bankFullName']}: Toplam {len(results)} kampanya çekildi.")
    return results

async def main():
    all_campaigns = []
    global_seen_titles = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="tr-TR",
            viewport={"width": 1366, "height": 900}
        )
        page = await context.new_page()

        current_id = 1
        for bank in BANKS:
            bank_camps = await scrape_bank(page, bank, current_id, global_seen_titles)
            all_campaigns.extend(bank_camps)
            current_id += len(bank_camps)

        await browser.close()

    if len(all_campaigns) > 10:
        with open("campaigns.json", "w", encoding="utf-8") as f:
            json.dump(all_campaigns, f, ensure_ascii=False, indent=2)
        print(f"BAŞARILI! Toplam {len(all_campaigns)} kampanya 'campaigns.json' dosyasına kaydedildi.")
    else:
        print("Yeterli kampanya çekilemedi, mevcut 'campaigns.json' korundu.")

if __name__ == "__main__":
    asyncio.run(main())
