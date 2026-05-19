import os
import json
import time
import traceback
import requests
from playwright.sync_api import sync_playwright

KULLANICI = os.environ["HOROZ_KULLANICI"]
SIFRE = os.environ["HOROZ_SIFRE"]

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(str(msg))

def get_all_stok():
    stok = {}

    # 1. requests ile login — cookie al
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    })

    # Login sayfasını çek — viewstate al
    r = session.get("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx", timeout=30)
    log(f"Login sayfası status: {r.status_code}")

    from html.parser import HTMLParser
    class VSParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.viewstate = ""
            self.eventvalidation = ""
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if attrs.get("id") == "__VIEWSTATE":
                self.viewstate = attrs.get("value", "")
            if attrs.get("id") == "__EVENTVALIDATION":
                self.eventvalidation = attrs.get("value", "")

    parser = VSParser()
    parser.feed(r.text)
    log(f"ViewState uzunluğu: {len(parser.viewstate)}")

    # Login POST
    data = {
        "__VIEWSTATE": parser.viewstate,
        "__EVENTVALIDATION": parser.eventvalidation,
        "txtKullaniciAdi": KULLANICI,
        "txtSifre": SIFRE,
        "bntLogin": "Giriş yap",
    }
    r2 = session.post("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx", data=data, timeout=30, allow_redirects=True)
    log(f"Login POST status: {r2.status_code}, URL: {r2.url}")

    if "frmGiris" in r2.url:
        log("Giriş başarısız!")
        return stok
    log("Giriş başarılı!")

    # 2. Playwright'a cookie'leri aktar
    cookies = [{"name": c.name, "value": c.value, "domain": c.domain or ".horoz.com.tr", "path": "/"} for c in session.cookies]
    log(f"Cookie sayısı: {len(cookies)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()

        # 3. app4'e git
        page.goto("https://app4.horoz.com.tr/wsEvTeslim/frmDefault.aspx", wait_until="load", timeout=30000)
        time.sleep(3)
        log(f"app4 URL: {page.url}")

        # 4. Ev Teslim Sorgular
        page.locator("span.x-panel-header-text", has_text="Ev Teslim Sorgular").click(timeout=15000)
        log("Ev Teslim Sorgular tıklandı")
        time.sleep(8)

        # 5. Stok Sorgulama
        stok_menu = page.locator("span.x-menu-item-text", has_text="Stok Sorgulama")
        stok_menu.wait_for(state="visible", timeout=15000)
        stok_menu.click(timeout=15000, force=True)
        log("Stok Sorgulama tıklandı")
        time.sleep(10)
        log(f"Frame'ler: {[f.url for f in page.frames]}")

        # 6. frmStokSorgulama frame'i bekle
        stok_frame = None
        for _ in range(30):
            time.sleep(1)
            for frame in page.frames:
                if "frmStokSorgulama" in frame.url:
                    stok_frame = frame
                    break
            if stok_frame:
                break

        if stok_frame is None:
            log("HATA: Stok frame bulunamadı!")
            browser.close()
            return stok
        log(f"Stok frame: {stok_frame.url}")

        # 7. Listele
        stok_frame.locator("span.dx-vam", has_text="Listele").click(timeout=15000)
        log("Listele tıklandı")
        time.sleep(8)

        # 8. Kayıt sayısı 500
        try:
            stok_frame.locator(".dxp-dropDownButton").click(timeout=10000)
            time.sleep(1)
            stok_frame.locator("span.dx-vam", has_text="500").click(timeout=10000)
            log("Kayıt sayısı 500 tıklandı")
            time.sleep(8)
        except Exception as e:
            log(f"Kayıt sayısı ayarlanamadı: {e}")

        # 9. JS ile satırları oku
        log("Satırlar okunuyor...")
        result = stok_frame.evaluate("""
            () => {
                const rows = document.querySelectorAll('tr.dxgvDataRow_Office2010Blue');
                const data = [];
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td.dxgv');
                    if (cells.length > 5) {
                        const kod = cells[2].textContent.trim();
                        const stok = cells[5].textContent.trim();
                        if (kod) data.push([kod, stok]);
                    }
                });
                return data;
            }
        """)
        log(f"Toplam satır: {len(result)}")

        for kod, miktar_str in result:
            try:
                stok[kod] = int(float(miktar_str.replace(',', '.'))) if miktar_str else 0
            except:
                stok[kod] = 0

        browser.close()
    return stok

if __name__ == "__main__":
    try:
        log("Horoz stok sorgulanıyor...")
        stok = get_all_stok()
        log(f"{len(stok)} ürün bulundu.")
        with open("stok.json", "w", encoding="utf-8") as f:
            json.dump(stok, f, ensure_ascii=False, indent=2)
        log("stok.json yazıldı.")
    except Exception as e:
        log(f"HATA: {e}")
        log(traceback.format_exc())
    finally:
        print("\n".join(log_lines))
