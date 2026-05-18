import os
import json
import time
import traceback
from playwright.sync_api import sync_playwright

KULLANICI = os.environ["HOROZ_KULLANICI"]
SIFRE = os.environ["HOROZ_SIFRE"]

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(str(msg))

def get_all_stok():
    stok = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)
        context = browser.new_context()
        page = context.new_page()

        # 1. Giriş
        page.goto("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx", wait_until="load", timeout=30000)
        kullanici_input = page.locator("input[type='text']").first
        kullanici_input.click()
        time.sleep(0.3)
        kullanici_input.fill(KULLANICI)
        time.sleep(0.5)
        page.keyboard.press("Tab")
        time.sleep(0.5)
        sifre_input = page.locator("input[type='password']").first
        sifre_input.fill(SIFRE)
        time.sleep(2)
        sifre_input.fill(SIFRE)
        time.sleep(1)
        page.keyboard.press("Tab")
        time.sleep(0.5)
        page.keyboard.press("Enter")
        page.wait_for_load_state("load", timeout=30000)
        time.sleep(4)
        log(f"Giriş sonrası URL: {page.url}")

        # Giriş kontrolü — sadece URL'e bak
        if "frmChange" in page.url:
            log("Şifre değiştirme sayfası!")
            browser.close()
            return stok
        if "frmGiris" in page.url:
            log("Giriş başarısız!")
            browser.close()
            return stok
        log("Giriş başarılı!")

        # 2. app4
        page.goto("https://app4.horoz.com.tr/wsEvTeslim/frmDefault.aspx", wait_until="load", timeout=30000)
        time.sleep(3)

        # 3. Ev Teslim Sorgular
        page.locator("span.x-panel-header-text", has_text="Ev Teslim Sorgular").click(timeout=15000)
        log("Ev Teslim Sorgular tıklandı")
        time.sleep(8)

        # 4. Stok Sorgulama
        stok_menu = page.locator("span.x-menu-item-text", has_text="Stok Sorgulama")
        stok_menu.wait_for(state="visible", timeout=15000)
        log("Stok Sorgulama menüsü görünür")
        stok_menu.click(timeout=15000, force=True)
        log("Stok Sorgulama tıklandı")
        time.sleep(10)
        log(f"Frame'ler: {[f.url for f in page.frames]}")

        # 5. frmStokSorgulama frame'i yüklenene kadar bekle
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

        # 6. Listele
        stok_frame.locator("span.dx-vam", has_text="Listele").click(timeout=15000)
        log("Listele tıklandı")
        time.sleep(8)

        # 7. Kayıt sayısı 500
        try:
            stok_frame.locator(".dxp-dropDownButton").click(timeout=10000)
            time.sleep(1)
            stok_frame.locator("span.dx-vam", has_text="500").click(timeout=10000)
            log("Kayıt sayısı 500 tıklandı")
            time.sleep(8)
        except Exception as e:
            log(f"Kayıt sayısı ayarlanamadı: {e}")

        # 8. JS ile tüm satırları oku
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
