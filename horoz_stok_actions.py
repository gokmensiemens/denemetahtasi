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
        page = browser.new_page()

        # 1. Giriş
        page.goto("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx", wait_until="networkidle", timeout=30000)
        page.fill("input[type='text']", KULLANICI)
        page.fill("input[type='password']", SIFRE)
        page.click("input[type='submit'], button:has-text('Giriş yap')")
        page.wait_for_load_state("networkidle", timeout=30000)

        # 2. Stok Sorgulama sayfasına geç
        page.goto("https://app4.horoz.com.tr/wsEvTeslim/frmDefault.aspx", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 3. "Ev Teslim Sorgular" accordion'unu aç
        page.click("#ext-gen103")
        time.sleep(1)

        # 4. "Stok Sorgulama" menü öğesine tıkla
        page.click("span.x-menu-item-text:has-text('Stok Sorgulama')")
        time.sleep(2)

        # 5. Kayıt sayısını 500 yap
        try:
            sayfa_basi = page.locator("input.dx-texteditor-input[aria-label], .dx-page-sizes input").last
            sayfa_basi.triple_click()
            sayfa_basi.type("500")
            time.sleep(500)
        except:
            pass

        # 6. Listele'ye bas
        page.click("span.dx-vam:has-text('Listele')")
        time.sleep(5)

        # 7. Sayfa başına 500 seç (dropdown)
        try:
            page.select_option(".dx-page-sizes select", "500")
            time.sleep(3)
        except:
            pass

        # 8. Header sırasını bul
        header_cells = page.locator(".dx-datagrid-headers .dx-header-row td").all_text_contents()
        header_cells = [h.strip() for h in header_cells]
        
        urun_kodu_idx = None
        satilabilir_idx = None
        for idx, h in enumerate(header_cells):
            hu = h.upper().replace(" ", "")
            if "URUNKODU" in hu or "ÜRÜNKODU" in hu:
                urun_kodu_idx = idx
            if "SATILABILIRMIKTAR" in hu:
                satilabilir_idx = idx

        print(f"Headers: {header_cells}")
        print(f"Ürün kodu idx: {urun_kodu_idx}, Satılabilir idx: {satilabilir_idx}")

        if urun_kodu_idx is None or satilabilir_idx is None:
            print("HATA: Kolon bulunamadı!")
            browser.close()
            return stok

        # 9. Tüm satırları oku
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
