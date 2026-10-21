import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Banka Kaynakları ve Renk Kodları
BANKS = [
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "color": "#10B981",
        "url": "https://www.bonus.com.tr/kampanyalar",
        "howToJoin": "Harcama öncesi BonusFlaş uygulamasından 'Hemen Katıl' butonuna tıklayın."
    },
    {
        "bank": "Maximum",
        "bankFullName": "Maximum (İş Bankası)",
        "color": "#EF4444",
        "url": "https://www.maximum.com.tr/kampanyalar",
        "howToJoin": "Maximum Mobil veya İşCep uygulamasında 'Kampanyalar' bölümünden katılabilirsiniz."
    },
    {
        "bank": "World",
        "bankFullName": "World (Yapı Kredi)",
        "color": "#6366F1",
        "url": "https://www.worldcard.com.tr/kampanyalar",
        "howToJoin": "World Mobil uygulaması üzerinden 'Hemen Katıl' butonuna basarak aktif edebilirsiniz."
    },
    {
        "bank": "Axess",
        "bankFullName": "Axess (Akbank)",
        "color": "#F59E0B",
        "url": "https://www.axess.com.tr/kampanyalar",
        "howToJoin": "Juzdan uygulamasından kampanya sayfasına gidip 'Hemen Katıl'a dokunun."
    },
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "color": "#EC4899",
        "url": "https://www.bankkart.com.tr/kampanyalar",
        "howToJoin": "Bankkart Mobil uygulamasından veya SMS ile katılım sağlayabilirsiniz."
    },
    {
        "bank": "Paraf",
        "bankFullName": "Paraf (Halkbank)",
        "color": "#0EA5E9",
        "url": "https://www.paraf.com.tr/tr/kampanyalar.html",
        "howToJoin": "Paraf Mobil uygulamasından kampanya katılımınızı onaylayın."
    },
    {
        "bank": "CardFinans",
        "bankFullName": "CardFinans (QNB)",
        "color": "#3B82F6",
        "url": "https://www.cardfinans.com/kampanyalar",
        "howToJoin": "QNB Mobil üzerinden veya POS cihazından taksit/puan seçimiyle katılabilirsiniz."
    }
]

# Metinden Otomatik Kategori Tahmin Etme
def detect_category(text):
    t = text.lower()
    if any(k in t for k in ["akaryakıt", "opet", "shell", "petrol", "otogaz", "bp", "aytemiz", "şarj", "zes", "eşarj"]):
        return "Akaryakıt"
    if any(k in t for k in ["market", "migros", "carrefour", "gıda", "a101", "şok", "bim", "süpermarket"]):
        return "Market"
    if any(k in t for k in ["trendyol", "hepsiburada", "amazon", "n11", "pazarama", "e-ticaret", "online", "internet"]):
        return "E-Ticaret"
    if any(k in t for k in ["giyim", "zara", "boyner", "mavi", "lcw", "ayakkabı", "kozmetik", "moda", "beymen"]):
        return "Giyim"
    if any(k in t for k in ["elektronik", "mediamarkt", "teknosa", "vatan", "apple", "telefon", "bilgisayar", "teknoloji"]):
        return "Elektronik"
    if any(k in t for k in ["uçak", "bilet", "otel", "seyahat", "tatil", "thy", "pegasus", "ets", "jolly", "konaklama"]):
        return "Seyahat"
    if any(k in t for k in ["restoran", "kafe", "kahve", "yemek", "starbucks", "yemeksepeti"]):
        return "Restoran"
    return "E-Ticaret"

# Metinden Otomatik Marka Çıkarımı
def detect_brand(text, category):
    known_brands = [
        "Migros", "CarrefourSA", "Opet", "Shell", "Petrol Ofisi", "TotalEnergies",
        "Trendyol", "Hepsiburada", "Amazon", "Pazarama", "N11", "Zara", "Boyner",
        "Mavi", "LCW", "MediaMarkt", "Teknosa", "Vatan", "THY", "Pegasus", "Obilet",
        "Starbucks", "Yemeksepeti", "A101", "ŞOK", "BİM", "ZES", "Eşarj"
    ]
    found = [b for b in known_brands if b.lower() in text.lower()]
    if found:
        return " & ".join(found[:2])
    return f"Seçili {category} İşyerleri"

# Metinden Otomatik Ödül / Kazanım Çıkarımı (Regex)
def extract_reward(text):
    # Örn: "500 TL Bonus", "1.000 TL MaxiPuan", "350 TL İndirim"
    tl_match = re.search(r'(\d[\d\.]*)\s*TL\s*(Bonus|Puan|Worldpuan|MaxiPuan|Chip-Para|Chip|ParafPara|Bankkart Lira|İndirim)?', text, re.IGNORECASE)
    if tl_match:
        amount = tl_match.group(1)
        rtype = tl_match.group(2) or "Puan"
        return f"{amount} TL {rtype.capitalize()}"

    # Örn: "%20 İndirim", "%15 Bonus"
    pct_match = re.search(r'%\s*(\d+)\s*(İndirim|Bonus|Puan)?', text, re.IGNORECASE)
    if pct_match:
        return f"%{pct_match.group(1)} {pct_match.group(2) or 'Avantaj'}"

    # Örn: "6 Taksit"
    taksit_match = re.search(r'(\d+)\s*Taksit', text, re.IGNORECASE)
    if taksit_match:
        return f"{taksit_match.group(1)} Taksit"

    return "Özel Fırsat"

async def scrape_bank(page, bank_info, start_id):
    results = []
    try:
        print(f"Taranıyor: {bank_info['bankFullName']} -> {bank_info['url']}")
        await page.goto(bank_info["url"], wait_until="domcontentloaded", timeout=35000)
        await page.wait_for_timeout(4000)  # JS kartlarının yüklenmesi için bekle

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Kampanya başlıklarını ve kartlarını yakalayan genel seçiciler
        candidates = soup.find_all(["h2", "h3", "h4", "a", "div"], class_=re.compile(r"(camp|card|item|title|box|list)", re.I))
        seen_titles = set()

        for el in candidates:
            text = " ".join(el.get_text(" ", strip=True).split())
            # Çok kısa veya çok uzun alakasız menü yazılarını ele
            if len(text) < 25 or len(text) > 160:
                continue
            # İçinde kampanya sinyali (TL, Taksit, %, Puan, İndirim) geçen gerçek kampanya cümlelerini al
            if not re.search(r'(\d+\s*TL|%\s*\d+|\d+\s*Taksit|Puan|Bonus|Chip|İndirim)', text, re.IGNORECASE):
                continue

            title_key = text[:45].lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            category = detect_category(text)
            brand = detect_brand(text, category)
            reward = extract_reward(text)
            is_featured = any(x in reward for x in ["500", "600", "750", "1.000", "1000", "%20"])

            results.append({
                "id": start_id + len(results),
                "bank": bank_info["bank"],
                "bankFullName": bank_info["bankFullName"],
                "category": category,
                "brand": brand,
                "title": text[:110] + ("..." if len(text) > 110 else ""),
                "desc": f"{bank_info['bankFullName']} tarafından sunulan {text} kampanyası. Detaylar ve katılım koşulları için resmi banka sayfasını ziyaret edebilirsiniz.",
                "reward": reward,
                "minSpend": "Kampanya Koşullarında",
                "date": f"Güncel ({datetime.now().strftime('%B %Y')})",
                "color": bank_info["color"],
                "isFeatured": is_featured,
                "howToJoin": bank_info["howToJoin"],
                "sourceUrl": bank_info["url"]
            })

            if len(results) >= 12:  # Her bankadan en güncel 12 kampanyayı al
                break

    except Exception as e:
        print(f"Hata ({bank_info['bank']}): {e}")

    return results

async def main():
    all_campaigns = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="tr-TR"
        )
        page = await context.new_page()

        current_id = 1
        for bank in BANKS:
            bank_camps = await scrape_bank(page, bank, current_id)
            all_campaigns.extend(bank_camps)
            current_id += len(bank_camps)

        await browser.close()

    # Eğer sitelerin güvenlik duvarı (Cloudflare vb.) nedeniyle hiç veri çekilemezse mevcut dosyayı koru
    if len(all_campaigns) > 5:
        with open("campaigns.json", "w", encoding="utf-8") as f:
            json.dump(all_campaigns, f, ensure_ascii=False, indent=2)
        print(f"Başarılı! Toplam {len(all_campaigns)} güncel kampanya 'campaigns.json' dosyasına yazıldı.")
    else:
        print("Yeterli kampanya çekilemedi, mevcut 'campaigns.json' korunuyor.")

if __name__ == "__main__":
    asyncio.run(main())
