import os
import json
import time
from playwright.sync_api import sync_playwright

KULLANICI = os.environ["HOROZ_KULLANICI"]
SIFRE = os.environ["HOROZ_SIFRE"]

def get_all_stok():
    stok = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Giriş
        page.goto("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx", wait_until="networkidle", timeout=30000)
        print(f"Login sayfası başlığı: {page.title()}")
        page.fill("input[type='text']", KULLANICI)
        page.fill("input[type='password']", SIFRE)
        page.click("input[name='bntLogin']")
        page.wait_for_load_state("networkidle", timeout=30000)
        print(f"Giriş sonrası URL: {page.url}")
        print(f"Giriş sonrası başlık: {page.title()}")

        # 2. app4'e geç — aynı context, cookie'ler taşınır
        page.goto("https://app4.horoz.com.tr/wsEvTeslim/frmDefault.aspx", wait_until="networkidle", timeout=30000)
        time.sleep(3)
        print(f"app4 URL: {page.url}")
        print(f"app4 başlık: {page.title()}")
        
        # Sayfadaki tüm span.x-panel-header-text elementlerini listele
        spans = page.locator("span.x-panel-header-text").all_text_contents()
        print(f"Menü başlıkları: {spans}")

        # 3. "Ev Teslim Sorgular" accordion'unu aç
        page.locator("span.x-panel-header-text", has_text="Ev Teslim Sorgular").click(timeout=15000)
        time.sleep(1)

        # 4. "Stok Sorgulama" menü öğesine tıkla
        page.locator("span.x-menu-item-text", has_text="Stok Sorgulama").click(timeout=15000)
        time.sleep(2)

        # 5. Listele'ye bas
        page.locator("span.dx-vam", has_text="Listele").click(timeout=15000)
        time.sleep(5)

        # 6. Kayıt sayısını 500 yap
        try:
            page.locator(".dx-page-sizes .dx-selectbox").click()
            time.sleep(1)
            page.locator(".dx-list-item").filter(has_text="500").click()
            time.sleep(4)
        except Exception as e:
            print(f"Kayıt sayısı ayarlanamadı: {e}")

        # 7. Header sırasını bul
        header_cells = page.locator(".dx-datagrid-headers .dx-header-row td").all_text_contents()
        header_cells = [h.strip() for h in header_cells]
        print(f"Headers: {header_cells}")

        urun_kodu_idx = None
        satilabilir_idx = None
        for idx, h in enumerate(header_cells):
            hu = h.upper().replace(" ", "")
            if "URUNKODU" in hu or "ÜRÜNKODU" in hu:
                urun_kodu_idx = idx
            if "SATILABILIRMIKTAR" in hu:
                satilabilir_idx = idx

        print(f"Ürün kodu idx: {urun_kodu_idx}, Satılabilir idx: {satilabilir_idx}")

        if urun_kodu_idx is None or satilabilir_idx is None:
            print("HATA: Kolon bulunamadı!")
            browser.close()
            return stok

        # 8. Tüm satırları oku
        rows = page.locator(".dx-datagrid-rowsview .dx-data-row").all()
        print(f"Toplam satır: {len(rows)}")

        for row in rows:
            cells = row.locator("td").all_text_contents()
            if len(cells) > max(urun_kodu_idx, satilabilir_idx):
                kod = cells[urun_kodu_idx].strip()
                miktar_str = cells[satilabilir_idx].strip()
                if kod:
                    try:
                        stok[kod] = int(float(miktar_str)) if miktar_str else 0
                    except:
                        stok[kod] = 0

        browser.close()
    return stok

if __name__ == "__main__":
    print("Horoz stok sorgulanıyor...")
    stok = get_all_stok()
    print(f"{len(stok)} ürün bulundu.")

    with open("stok.json", "w", encoding="utf-8") as f:
        json.dump(stok, f, ensure_ascii=False, indent=2)

    print("stok.json yazıldı.")
    print(json.dumps(stok, ensure_ascii=False, indent=2)[:500])
