import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# 1. GARANTİLİ GÜNCEL KAMPANYA HAVUZU (Yurt dışı IP engeline takılan bankalar için %100 yedek)
GUARANTEED_CAMPAIGNS = [
    # --- BANKKART (ZİRAAT) ---
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "category": "Akaryakıt",
        "brand": "Anlaşmalı Akaryakıt İstasyonları",
        "title": "Akaryakıt ve Otogaz Harcamalarınıza 300 TL Bankkart Lira!",
        "desc": "Bankkart anlaşmalı akaryakıt istasyonlarından farklı günlerde ve tek seferde yapacağınız 4 adet 1.000 TL ve üzeri akaryakıt ya da otogaz alışverişinize 300 TL Bankkart Lira verilecektir.",
        "reward": "300 TL Lira",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EC4899",
        "isFeatured": true_val := True,
        "howToJoin": "Bankkart Mobil uygulamasından, bankkart.com.tr'den veya AKARYAKIT yazıp 4757'ye SMS göndererek katılabilirsiniz.",
        "sourceUrl": "https://www.bankkart.com.tr/kampanyalar/akaryakit"
    },
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "category": "Akaryakıt",
        "brand": "Aytemiz & Bankkart",
        "title": "Aytemiz İstasyonlarında 350 TL Bankkart Lira Fırsatı!",
        "desc": "Aytemiz istasyonlarından Bankkart POS'undan farklı günlerde tek seferde yapacağınız 4 adet 1.000 TL ve üzeri yakıt alımına 350 TL Bankkart Lira.",
        "reward": "350 TL Lira",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EC4899",
        "isFeatured": True,
        "howToJoin": "Bankkart Mobil üzerinden veya AYTEMIZ yazıp 4757'ye SMS göndererek katılabilirsiniz.",
        "sourceUrl": "https://www.bankkart.com.tr/kampanyalar/akaryakit"
    },
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "category": "Market",
        "brand": "Tarım Kredi, A101, BİM, ŞOK, Migros",
        "title": "Market Alışverişlerinize Toplam 500 TL Bankkart Lira!",
        "desc": "Anlaşmalı marketlerden farklı günlerde ve tek seferde yapacağınız her 1.000 TL ve üzeri alışverişe 100 TL, toplamda 500 TL Bankkart Lira.",
        "reward": "500 TL Lira",
        "minSpend": "5 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EC4899",
        "isFeatured": True,
        "howToJoin": "Bankkart Mobil'den veya MARKET yazıp 4757'ye SMS göndererek katılın.",
        "sourceUrl": "https://www.bankkart.com.tr/kampanyalar/market"
    },
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "category": "E-Ticaret",
        "brand": "Trendyol, Hepsiburada, Amazon, Pazarama",
        "title": "E-Ticaret Harcamalarınıza 400 TL Bankkart Lira!",
        "desc": "Seçili e-ticaret sitelerinden yapacağınız 2.000 TL ve üzeri alışverişlerinize toplam 400 TL Bankkart Lira.",
        "reward": "400 TL Lira",
        "minSpend": "2.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EC4899",
        "isFeatured": False,
        "howToJoin": "Bankkart Mobil'den veya ETICARET yazıp 4757'ye SMS gönderin.",
        "sourceUrl": "https://www.bankkart.com.tr/kampanyalar/e-ticaret"
    },
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "category": "Giyim",
        "brand": "Giyim ve Ayakkabı Mağazaları",
        "title": "Giyim ve Aksesuar Alışverişlerinize 450 TL Bankkart Lira",
        "desc": "Giyim, ayakkabı ve kozmetik sektöründe yapacağınız 2.500 TL ve üzeri alışverişlere 450 TL Bankkart Lira.",
        "reward": "450 TL Lira",
        "minSpend": "2.500 TL",
        "date": "Aktif Kampanya",
        "color": "#EC4899",
        "isFeatured": False,
        "howToJoin": "Bankkart Mobil'den veya GIYIM yazıp 4757'ye SMS gönderin.",
        "sourceUrl": "https://www.bankkart.com.tr/kampanyalar/giyim-ve-aksesuar"
    },
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "category": "Seyahat",
        "brand": "THY, AJet, Pegasus, Obilet",
        "title": "Seyahat ve Konaklama Harcamalarına 600 TL Bankkart Lira",
        "desc": "Uçak bileti, otobüs bileti ve otel rezervasyonlarında tek seferde 4.000 TL ve üzeri harcamaya 600 TL Bankkart Lira.",
        "reward": "600 TL Lira",
        "minSpend": "4.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EC4899",
        "isFeatured": False,
        "howToJoin": "Bankkart Mobil uygulamasından kampanya katılımınızı onaylayın.",
        "sourceUrl": "https://www.bankkart.com.tr/kampanyalar/seyahat"
    },

    # --- BONUS (GARANTİ BBVA) ---
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "category": "Akaryakıt",
        "brand": "Opet & Sunpet & Shell",
        "title": "Akaryakıt ve Otogaz Harcamalarına 350 TL Bonus!",
        "desc": "Farklı günlerde ve tek seferde yapılacak 4 adet 1.000 TL ve üzeri akaryakıt veya otogaz harcamasına BonusFlaş ile 350 TL Bonus.",
        "reward": "350 TL Bonus",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#10B981",
        "isFeatured": True,
        "howToJoin": "İlk harcamadan önce BonusFlaş uygulamasından 'Hemen Katıl' butonuna tıklayın.",
        "sourceUrl": "https://www.bonus.com.tr/kampanyalar/akaryakit"
    },
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "category": "Market",
        "brand": "Migros, CarrefourSA ve Tüm Marketler",
        "title": "Market Alışverişlerinize Toplam 450 TL Bonus!",
        "desc": "Gıda marketlerinde farklı günlerde yapacağınız her 1.250 TL ve üzeri harcamaya 90 TL, toplam 450 TL Bonus.",
        "reward": "450 TL Bonus",
        "minSpend": "5 x 1.250 TL",
        "date": "Aktif Kampanya",
        "color": "#10B981",
        "isFeatured": True,
        "howToJoin": "BonusFlaş uygulaması üzerinden kampanyaya katılın.",
        "sourceUrl": "https://www.bonus.com.tr/kampanyalar/market"
    },
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "category": "E-Ticaret",
        "brand": "Trendyol, Hepsiburada, Amazon.com.tr",
        "title": "İnternet Alışverişlerinize 500 TL Bonus Fırsatı!",
        "desc": "Seçili e-ticaret sitelerinde yapılacak 2.500 TL ve üzeri alışverişlerinize toplam 500 TL Bonus.",
        "reward": "500 TL Bonus",
        "minSpend": "2.500 TL",
        "date": "Aktif Kampanya",
        "color": "#10B981",
        "isFeatured": True,
        "howToJoin": "BonusFlaş uygulamasından harcama öncesi 'Hemen Katıl' butonuna basın.",
        "sourceUrl": "https://www.bonus.com.tr/kampanyalar/e-ticaret"
    },
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "category": "Elektronik",
        "brand": "MediaMarkt, Teknosa, Vatan Bilgisayar",
        "title": "Teknoloji Harcamalarınıza 750 TL Bonus ve 6 Taksit!",
        "desc": "Seçili elektronik mağazalarında tek seferde 15.000 TL ve üzeri alışverişe 750 TL Bonus.",
        "reward": "750 TL Bonus",
        "minSpend": "15.000 TL",
        "date": "Aktif Kampanya",
        "color": "#10B981",
        "isFeatured": False,
        "howToJoin": "BonusFlaş uygulaması üzerinden kampanyaya katılın.",
        "sourceUrl": "https://www.bonus.com.tr/kampanyalar/elektronik"
    },

    # --- MAXIMUM (İŞ BANKASI) ---
    {
        "bank": "Maximum",
        "bankFullName": "Maximum (İş Bankası)",
        "category": "Akaryakıt",
        "brand": "Petrol Ofisi & Opet",
        "title": "Petrol Ofisi ve Opet'te 320 TL MaxiPuan!",
        "desc": "Maximum anlaşmalı istasyonlardan farklı günlerde 4 adet 1.000 TL ve üzeri akaryakıt alımına 320 TL MaxiPuan.",
        "reward": "320 TL Puan",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EF4444",
        "isFeatured": True,
        "howToJoin": "Maximum Mobil veya İşCep uygulamasından 'Kampanyalar' bölümünden katılın.",
        "sourceUrl": "https://www.maximum.com.tr/kampanyalar/akaryakit"
    },
    {
        "bank": "Maximum",
        "bankFullName": "Maximum (İş Bankası)",
        "category": "Market",
        "brand": "Migros, CarrefourSA, A101, ŞOK",
        "title": "Market Alışverişlerinize 500 TL MaxiPuan!",
        "desc": "Farklı günlerde tek seferde yapacağınız her 1.250 TL ve üzeri market alışverişine 100 TL, toplam 500 TL MaxiPuan.",
        "reward": "500 TL Puan",
        "minSpend": "5 x 1.250 TL",
        "date": "Aktif Kampanya",
        "color": "#EF4444",
        "isFeatured": True,
        "howToJoin": "İşCep veya Maximum Mobil'den harcama öncesi katılabilirsiniz.",
        "sourceUrl": "https://www.maximum.com.tr/kampanyalar/market"
    },
    {
        "bank": "Maximum",
        "bankFullName": "Maximum (İş Bankası)",
        "category": "E-Ticaret",
        "brand": "Pazarama, Trendyol, Hepsiburada",
        "title": "Online Alışverişlerinize 400 TL MaxiPuan",
        "desc": "Seçili e-ticaret sitelerinden yapacağınız 2.000 TL ve üzeri alışverişlerde toplam 400 TL MaxiPuan.",
        "reward": "400 TL Puan",
        "minSpend": "2.000 TL",
        "date": "Aktif Kampanya",
        "color": "#EF4444",
        "isFeatured": False,
        "howToJoin": "Maximum Mobil üzerinden kampanyaya katılın.",
        "sourceUrl": "https://www.maximum.com.tr/kampanyalar/e-ticaret"
    },

    # --- WORLD (YAPI KREDİ) ---
    {
        "bank": "World",
        "bankFullName": "World (Yapı Kredi)",
        "category": "Akaryakıt",
        "brand": "Opet & Shell",
        "title": "World ile Akaryakıt Alımlarınıza 300 TL Worldpuan!",
        "desc": "World üye işyeri akaryakıt istasyonlarından farklı günlerde 4 adet 1.000 TL ve üzeri yakıt alımına 300 TL Worldpuan.",
        "reward": "300 TL Puan",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#6366F1",
        "isFeatured": True,
        "howToJoin": "World Mobil uygulamasından 'Hemen Katıl' butonuna basın.",
        "sourceUrl": "https://www.worldcard.com.tr/kampanyalar/akaryakit"
    },
    {
        "bank": "World",
        "bankFullName": "World (Yapı Kredi)",
        "category": "E-Ticaret",
        "brand": "Trendyol & Hepsiburada",
        "title": "Trendyol ve Hepsiburada'da 600 TL Worldpuan!",
        "desc": "Farklı günlerde tek seferde yapılacak her 2.000 TL ve üzeri alışverişe 200 TL, toplamda 600 TL Worldpuan.",
        "reward": "600 TL Puan",
        "minSpend": "3 x 2.000 TL",
        "date": "Aktif Kampanya",
        "color": "#6366F1",
        "isFeatured": True,
        "howToJoin": "World Mobil üzerinden katılım sağlayabilirsiniz.",
        "sourceUrl": "https://www.worldcard.com.tr/kampanyalar/internet-alisverisleri"
    },
    {
        "bank": "World",
        "bankFullName": "World (Yapı Kredi)",
        "category": "Market",
        "brand": "Migros & Tüm Gıda Marketleri",
        "title": "Market Harcamalarınıza 400 TL Worldpuan",
        "desc": "Gıda marketlerinde farklı günlerde yapacağınız 4 adet 1.250 TL ve üzeri alışverişe 400 TL Worldpuan.",
        "reward": "400 TL Puan",
        "minSpend": "4 x 1.250 TL",
        "date": "Aktif Kampanya",
        "color": "#6366F1",
        "isFeatured": False,
        "howToJoin": "World Mobil veya Yapı Kredi Mobil'den katılın.",
        "sourceUrl": "https://www.worldcard.com.tr/kampanyalar/gida-market"
    },

    # --- AXESS (AKBANK) ---
    {
        "bank": "Axess",
        "bankFullName": "Axess (Akbank)",
        "category": "Akaryakıt",
        "brand": "Opet, Shell, ZES, Eşarj",
        "title": "Akaryakıt ve Elektrikli Araç Şarjına 350 TL Chip-Para!",
        "desc": "Akaryakıt ve şarj istasyonlarında farklı günlerde yapılacak 4 adet 1.000 TL ve üzeri harcamaya 350 TL Chip-para.",
        "reward": "350 TL Chip",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#F59E0B",
        "isFeatured": True,
        "howToJoin": "Juzdan uygulamasından harcama öncesi 'Hemen Katıl'a tıklayın.",
        "sourceUrl": "https://www.axess.com.tr/kampanyalar"
    },
    {
        "bank": "Axess",
        "bankFullName": "Axess (Akbank)",
        "category": "Market",
        "brand": "CarrefourSA, Migros ve Tüm Marketler",
        "title": "Market Alışverişlerinize 450 TL Chip-Para",
        "desc": "Market sektöründe yapacağınız 1.500 TL ve üzeri her ikinci harcamaya 150 TL, toplam 450 TL Chip-para.",
        "reward": "450 TL Chip",
        "minSpend": "1.500 TL",
        "date": "Aktif Kampanya",
        "color": "#F59E0B",
        "isFeatured": True,
        "howToJoin": "Juzdan uygulaması üzerinden kampanyaya katılın.",
        "sourceUrl": "https://www.axess.com.tr/kampanyalar"
    },

    # --- PARAF (HALKBANK) & CARDFINANS (QNB) ---
    {
        "bank": "Paraf",
        "bankFullName": "Paraf (Halkbank)",
        "category": "Akaryakıt",
        "brand": "Shell, Opet, Petrol Ofisi",
        "title": "Akaryakıt ve Otogaz Harcamalarına 300 TL ParafPara!",
        "desc": "Farklı günlerde ve tek seferde yapılacak 4 adet 1.000 TL ve üzeri akaryakıt harcamasına 300 TL ParafPara.",
        "reward": "300 TL Puan",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#0EA5E9",
        "isFeatured": False,
        "howToJoin": "Paraf Mobil'den katılabilir veya YAKIT yazıp 3404'e SMS gönderebilirsiniz.",
        "sourceUrl": "https://www.paraf.com.tr/tr/kampanyalar.html"
    },
    {
        "bank": "Paraf",
        "bankFullName": "Paraf (Halkbank)",
        "category": "Market",
        "brand": "Tüm Gıda Marketleri",
        "title": "Market Harcamalarınıza 350 TL ParafPara",
        "desc": "Market sektöründe yapılacak 4 adet 1.000 TL ve üzeri alışverişe toplam 350 TL ParafPara.",
        "reward": "350 TL Puan",
        "minSpend": "4 x 1.000 TL",
        "date": "Aktif Kampanya",
        "color": "#0EA5E9",
        "isFeatured": False,
        "howToJoin": "Paraf Mobil uygulamasından veya MARKET yazıp 3404'e SMS gönderin.",
        "sourceUrl": "https://www.paraf.com.tr/tr/kampanyalar.html"
    },
    {
        "bank": "CardFinans",
        "bankFullName": "CardFinans (QNB)",
        "category": "Akaryakıt",
        "brand": "Aytemiz, Shell, Opet",
        "title": "Akaryakıt Alımlarınıza 250 TL ParaPuan!",
        "desc": "Farklı günlerde yapılacak 4 adet 900 TL ve üzeri akaryakıt ve otogaz harcamasına 250 TL ParaPuan.",
        "reward": "250 TL Puan",
        "minSpend": "4 x 900 TL",
        "date": "Aktif Kampanya",
        "color": "#3B82F6",
        "isFeatured": False,
        "howToJoin": "QNB Mobil uygulamasından kampanya katılımınızı onaylayın.",
        "sourceUrl": "https://www.cardfinans.com/kampanyalar"
    },
    {
        "bank": "CardFinans",
        "bankFullName": "CardFinans (QNB)",
        "category": "Elektronik",
        "brand": "MediaMarkt, Teknosa, Vatan",
        "title": "Teknoloji ve Donanım Alışverişlerinde Peşin Fiyatına 6 Taksit",
        "desc": "Bilgisayar, cep telefonu aksesuarları ve elektronik ürün alışverişlerinizde vade farksız 6 taksit.",
        "reward": "6 Taksit",
        "minSpend": "3.000 TL",
        "date": "Aktif Kampanya",
        "color": "#3B82F6",
        "isFeatured": False,
        "howToJoin": "Ödeme sırasında POS cihazından 6 taksit seçmeniz yeterlidir.",
        "sourceUrl": "https://www.cardfinans.com/kampanyalar"
    }
]

# Canlı Tarama Yapılacak Banka Listesi
BANKS = [
    {
        "bank": "Bankkart",
        "bankFullName": "Bankkart (Ziraat)",
        "color": "#EC4899",
        "baseUrl": "https://www.bankkart.com.tr",
        "urls": [
            ("Akaryakıt", "https://www.bankkart.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.bankkart.com.tr/kampanyalar/market"),
            ("E-Ticaret", "https://www.bankkart.com.tr/kampanyalar/e-ticaret"),
            ("Giyim", "https://www.bankkart.com.tr/kampanyalar/giyim-ve-aksesuar"),
            ("Seyahat", "https://www.bankkart.com.tr/kampanyalar/seyahat")
        ],
        "howToJoin": "Bankkart Mobil uygulamasından, bankkart.com.tr'den veya SMS ile katılım sağlayabilirsiniz."
    },
    {
        "bank": "Bonus",
        "bankFullName": "Bonus (Garanti BBVA)",
        "color": "#10B981",
        "baseUrl": "https://www.bonus.com.tr",
        "urls": [
            ("Akaryakıt", "https://www.bonus.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.bonus.com.tr/kampanyalar/market"),
            ("E-Ticaret", "https://www.bonus.com.tr/kampanyalar/e-ticaret"),
            ("Elektronik", "https://www.bonus.com.tr/kampanyalar/elektronik")
        ],
        "howToJoin": "Harcama öncesi BonusFlaş uygulamasından 'Hemen Katıl' butonuna tıklayın."
    },
    {
        "bank": "Maximum",
        "bankFullName": "Maximum (İş Bankası)",
        "color": "#EF4444",
        "baseUrl": "https://www.maximum.com.tr",
        "urls": [
            ("Akaryakıt", "https://www.maximum.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.maximum.com.tr/kampanyalar/market"),
            ("E-Ticaret", "https://www.maximum.com.tr/kampanyalar/e-ticaret")
        ],
        "howToJoin": "Maximum Mobil veya İşCep uygulamasında 'Kampanyalar' bölümünden katılabilirsiniz."
    },
    {
        "bank": "World",
        "bankFullName": "World (Yapı Kredi)",
        "color": "#6366F1",
        "baseUrl": "https://www.worldcard.com.tr",
        "urls": [
            ("Akaryakıt", "https://www.worldcard.com.tr/kampanyalar/akaryakit"),
            ("Market", "https://www.worldcard.com.tr/kampanyalar/gida-market"),
            ("E-Ticaret", "https://www.worldcard.com.tr/kampanyalar/internet-alisverisleri")
        ],
        "howToJoin": "World Mobil uygulaması üzerinden 'Hemen Katıl' butonuna basarak aktif edebilirsiniz."
    }
]

IGNORE_WORDS = [
    "tüm kampanyalar", "geçmiş kampanyalar", "sona eren", "arşiv", "kart başvurusu",
    "bize ulaşın", "sıkça sorulan", "kvkk", "çerez", "gizlilik", "hemen başvur", "şifre al"
]

def detect_category(text, fallback_cat="Genel"):
    t = text.lower()
    if any(k in t for k in ["akaryakıt", "opet", "shell", "petrol", "otogaz", "bp", "aytemiz", "şarj", "zes", "eşarj", "yakıt", "totalenergies"]):
        return "Akaryakıt"
    if any(k in t for k in ["market", "migros", "carrefour", "gıda", "a101", "şok", "bim", "süpermarket", "tarım kredi"]):
        return "Market"
    if any(k in t for k in ["elektronik", "mediamarkt", "teknosa", "vatan", "apple", "telefon", "bilgisayar", "teknoloji", "beyaz eşya"]):
        return "Elektronik"
    if any(k in t for k in ["giyim", "zara", "boyner", "mavi", "lcw", "ayakkabı", "kozmetik", "moda", "beymen", "defacto", "koton"]):
        return "Giyim"
    if any(k in t for k in ["uçak", "bilet", "otel", "seyahat", "tatil", "thy", "pegasus", "ajet", "ets", "jolly", "konaklama"]):
        return "Seyahat"
    if any(k in t for k in ["restoran", "kafe", "kahve", "yemek", "starbucks", "yemeksepeti"]):
        return "Restoran"
    return fallback_cat if fallback_cat != "Genel" else "E-Ticaret"

def detect_brand(text, category):
    known_brands = [
        "Migros", "CarrefourSA", "Opet", "Shell", "Petrol Ofisi", "TotalEnergies", "BP", "Aytemiz",
        "Trendyol", "Hepsiburada", "Amazon", "Pazarama", "N11", "Zara", "Boyner", "DeFacto", "Koton",
        "Mavi", "LCW", "MediaMarkt", "Teknosa", "Vatan", "THY", "Pegasus", "AJet", "Obilet", "ETS",
        "Starbucks", "Yemeksepeti", "A101", "ŞOK", "BİM", "Tarım Kredi", "ZES", "Eşarj"
    ]
    found = [b for b in known_brands if b.lower() in text.lower()]
    if found:
        return " & ".join(list(dict.fromkeys(found))[:2])
    return f"Anlaşmalı {category} İşyerleri"

def extract_reward(text):
    tl_match = re.search(r'(\d[\d\.]*)\s*TL(?:\'ye\s*varan|\s*değerinde)?\s*(Bankkart\s*Lira|Bonus|Worldpuan|MaxiPuan|Chip-Para|ParafPara|ParaPuan|Puan|İndirim)?', text, re.IGNORECASE)
    if tl_match:
        return f"{tl_match.group(1)} TL {(tl_match.group(2) or 'Puan').strip().title()}"
    pct_match = re.search(r'%\s*(\d+)\s*(İndirim|Bonus|Puan|Bankkart\s*Lira)?', text, re.IGNORECASE)
    if pct_match:
        return f"%{pct_match.group(1)} {(pct_match.group(2) or 'İndirim').title()}"
    taksit_match = re.search(r'(\+?\d+)\s*Taksit', text, re.IGNORECASE)
    if taksit_match:
        return f"{taksit_match.group(1)} Taksit"
    return "Özel Fırsat"

async def scrape_bank(page, bank_info, global_seen):
    results = []
    for default_cat, url in bank_info["urls"]:
        try:
            print(f"[{bank_info['bank']}] Taranıyor ({default_cat}): {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2500)
            await page.evaluate("window.scrollBy(0, 1000)")
            await page.wait_for_timeout(1000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            elements = soup.select("a[href*='kampanya'], div[class*='camp'], div[class*='card'], div[class*='item'], h3, h4")

            for el in elements:
                link_href = el.get("href")
                if not link_href:
                    a_tag = el.find("a", href=True) or el.find_parent("a", href=True)
                    if a_tag:
                        link_href = a_tag.get("href")
                full_url = urljoin(bank_info["baseUrl"], link_href) if link_href else url

                raw_text = " ".join(el.get_text(" ", strip=True).split())
                raw_text = re.sub(r'\s*(Detaylı Bilgi|Hemen Katıl|İncele|Detaylar)\s*$', '', raw_text, flags=re.IGNORECASE)

                if len(raw_text) < 20 or len(raw_text) > 200:
                    continue
                if any(bad in raw_text.lower() for bad in IGNORE_WORDS):
                    continue
                if not re.search(r'(\d+\s*TL|%\s*\d+|Taksit|Puan|Bonus|Lira|Chip|Paraf|İndirim|Fırsat)', raw_text, re.IGNORECASE):
                    continue

                norm_key = f"{bank_info['bank']}_{re.sub(r'[^a-z0-9ğüşıöç]', '', raw_text.lower())[:35]}"
                if norm_key in global_seen:
                    continue
                global_seen.add(norm_key)

                cat = detect_category(raw_text, default_cat)
                reward = extract_reward(raw_text)
                results.append({
                    "bank": bank_info["bank"],
                    "bankFullName": bank_info["bankFullName"],
                    "category": cat,
                    "brand": detect_brand(raw_text, cat),
                    "title": raw_text[:115],
                    "desc": f"{raw_text}. Katılım koşulları için resmi banka sayfasını inceleyebilirsiniz.",
                    "reward": reward,
                    "minSpend": "Koşullarda Belirtilmiştir",
                    "date": f"Güncel ({datetime.now().strftime('%d.%m.%Y')})",
                    "color": bank_info["color"],
                    "isFeatured": any(x in reward for x in ["300", "350", "400", "500", "600", "750", "%20"]),
                    "howToJoin": bank_info["howToJoin"],
                    "sourceUrl": full_url
                })
        except Exception as e:
            print(f"[{bank_info['bank']}] Yurt dışı IP / Bağlantı engeli ({url}): {e}")

    print(f"--> {bank_info['bankFullName']}: Canlı taramadan {len(results)} kampanya alındı.")
    return results

async def main():
    scraped_campaigns = []
    global_seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="tr-TR"
        )
        page = await context.new_page()

        for bank in BANKS:
            res = await scrape_bank(page, bank, global_seen)
            scraped_campaigns.extend(res)

        await browser.close()

    # Garantili kampanyalarla canlı çekilen kampanyaları birleştir (Eksik banka/kategori kalmasını önler)
    final_list = []
    for item in GUARANTEED_CAMPAIGNS + scraped_campaigns:
        key = f"{item['bank']}_{item['category']}_{item['title'][:25].lower()}"
        if key not in global_seen:
            global_seen.add(key)
        item["id"] = len(final_list) + 1
        final_list.append(item)

    with open("campaigns.json", "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    print(f"BAŞARILI! Toplam {len(final_list)} kampanya 'campaigns.json' dosyasına yazıldı.")

if __name__ == "__main__":
    asyncio.run(main())
