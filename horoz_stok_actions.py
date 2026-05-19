import os
import json
import time
import traceback
import requests
from html.parser import HTMLParser

KULLANICI = os.environ["HOROZ_KULLANICI"]
SIFRE = os.environ["HOROZ_SIFRE"]

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(str(msg))

class VSParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get("name", "")
        value = attrs.get("value", "")
        if name and tag in ("input",):
            self.fields[name] = value

def get_all_stok():
    stok = {}
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9",
    })

    # 1. Login
    r = session.get("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx", timeout=30)
    parser = VSParser()
    parser.feed(r.text)

    login_data = dict(parser.fields)
    login_data["txtUserName"] = KULLANICI
    login_data["txtPassword"] = SIFRE
    login_data["bntLogin"] = "Giriş yap"

    r2 = session.post("https://app3.horoz.com.tr/wsKurumsal/frmGiris.aspx",
                      data=login_data, timeout=30, allow_redirects=True)
    log(f"Login URL: {r2.url}")

    if "frmGiris" in r2.url:
        log("Giriş başarısız!")
        return stok
    log("Giriş başarılı!")

    # 2. Stok sorgulama sayfasını aç — viewstate al
    r3 = session.get("https://app4.horoz.com.tr/wsEvTeslim/_sorgu/EvTeslim/Depo/frmStokSorgulama.aspx", timeout=30)
    log(f"Stok sayfa status: {r3.status_code}")

    parser2 = VSParser()
    parser2.feed(r3.text)
    vs = parser2.fields.get("__VIEWSTATE", "")
    ev = parser2.fields.get("__EVENTVALIDATION", "")
    vsg = parser2.fields.get("__VIEWSTATEGENERATOR", "")
    log(f"ViewState uzunluğu: {len(vs)}")

    # 3. Listele POST — payload'dan aldığımız değerler
    stok_data = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": vsg,
        "__EVENTVALIDATION": ev,
        "ASPxRoundPanel1_lstMusteri_ComboBox_VI": "7160",
        "ASPxRoundPanel1$lstMusteri$pnlComboState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1_lstSube_ComboBox_VI": "406",
        "ASPxRoundPanel1$lstSube$pnlComboState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lstBayi$ComboBox$State": '{"validationState":""}',
        "ASPxRoundPanel1_lstBayi_ComboBox_VI": "2103",
        "ASPxRoundPanel1$lstBayi$ComboBox": "GOKMEN TEKNOLOJI URUNLERI PAZARLAMASANAYI VE TICAR",
        "ASPxRoundPanel1$lstBayi$ComboBox$DDDState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lstBayi$ComboBox$DDD$L$State": '{"CustomCallback":""}',
        "ASPxRoundPanel1$lstBayi$ComboBox$DDD$L": "2103",
        "ASPxRoundPanel1$lstBayi$pnlComboState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1_lstSatisOrgList_ComboBox_VI": "",
        "ASPxRoundPanel1$lstSatisOrgList$ComboBox": "Lütfen bir seçim yapınız..",
        "ASPxRoundPanel1$lstSatisOrgList$ComboBox$DDDState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lstSatisOrgList$ComboBox$DDD$L$State": '{"CustomCallback":""}',
        "ASPxRoundPanel1$lstSatisOrgList$ComboBox$DDD$L": "",
        "ASPxRoundPanel1$lstSatisOrgList$pnlComboState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$chkBakiye": "on",
        "ASPxRoundPanel1_lstUrunGrupList_ComboBox_VI": "",
        "ASPxRoundPanel1$lstUrunGrupList$ComboBox": "Lütfen bir seçim yapınız..",
        "ASPxRoundPanel1$lstUrunGrupList$ComboBox$DDDState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lstUrunGrupList$ComboBox$DDD$L$State": '{"CustomCallback":""}',
        "ASPxRoundPanel1$lstUrunGrupList$ComboBox$DDD$L": "",
        "ASPxRoundPanel1$lstUrunGrupList$pnlComboState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$txtUrunKodu$ASPxTextBox1": "",
        "ASPxRoundPanel1$txtUrunKodu$pnlTextState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$txtUrunAdi$ASPxTextBox1": "",
        "ASPxRoundPanel1$txtUrunAdi$pnlTextState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1_lstUrunTipiList_ComboBox_VI": "",
        "ASPxRoundPanel1$lstUrunTipiList$ComboBox": "Lütfen bir seçim yapınız..",
        "ASPxRoundPanel1$lstUrunTipiList$ComboBox$DDDState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lstUrunTipiList$ComboBox$DDD$L$State": '{"CustomCallback":""}',
        "ASPxRoundPanel1$lstUrunTipiList$ComboBox$DDD$L": "",
        "ASPxRoundPanel1$lstUrunTipiList$pnlComboState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$tarih$dx_txt_Tarih$State": '{"useMinDateInsteadOfNull":false,"rawValue":"N"}',
        "ASPxRoundPanel1$tarih$dx_txt_Tarih": "",
        "ASPxRoundPanel1$tarih$dx_txt_Tarih$DDDState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$tarih$dx_txt_Tarih$DDD$C": '{"visibleDate":"05/19/2026","initialVisibleDate":"05/19/2026","selectedDates":[]}',
        "ASPxRoundPanel1$tarih$pnlTarihState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$btnListele$ASPxButton1": "Listele",
        "ASPxRoundPanel1$btnListele$popupControlState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lnkYardim$pnlYardimLinkState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "ASPxRoundPanel1$lnkYardim$pnlEkranState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "DXScript": "1_11,1_12,1_255,1_23,1_64,1_14,1_15,1_183,1_189,1_17,1_41,1_184,1_21,1_22,1_190,1_186,1_193,1_192,1_194,1_8,1_182,1_49,1_42",

        "DXCss": "1_74,1_68,1_73,1_210,1_207,1_209,1_206",
    }

    r4 = session.post(
        "https://app4.horoz.com.tr/wsEvTeslim/_sorgu/EvTeslim/Depo/frmStokSorgulama.aspx",
        data=stok_data, timeout=60
    )
    log(f"Stok POST status: {r4.status_code}, boyut: {len(r4.text)}")

    # callbackState'i r4'ten al
    import re as _re
    cs_match = _re.search(r'"callbackState"\s*:\s*"([^"]+)"', r4.text)
    callback_state = cs_match.group(1) if cs_match else ""
    log(f"callbackState uzunluğu: {len(callback_state)}")

    # Sayfa boyutunu 500'e çıkar — callback isteği
    vs2_match = _re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', r4.text)
    ev2_match = _re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', r4.text)
    vs2 = vs2_match.group(1) if vs2_match else vs
    ev2 = ev2_match.group(1) if ev2_match else ev

    callback_data = dict(stok_data)
    callback_data["__VIEWSTATE"] = vs2
    callback_data["__EVENTVALIDATION"] = ev2
    callback_data["__CALLBACKID"] = "grid$dgGrid"
    callback_data["__CALLBACKPARAM"] = "c0:KV|2;[];CT|2;{};CR|2;{};GB|23;12|PAGERONCLICK6|PSP500;"
    callback_data["grid$dgGrid"] = '{"groupLevelState":{},"selection":"","callbackState":"' + callback_state + '","resizingState":"{}","keys":[],"toolbar":"{}"}'
    callback_data["grid$dgGrid$DXPagerBottom$PSP"] = '{"selectedItemIndexPath":"5","checkedState":""}'
    callback_data["grid$dgGrid$custwindowState"] = '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}'

    r5 = session.post(
        "https://app4.horoz.com.tr/wsEvTeslim/_sorgu/EvTeslim/Depo/frmStokSorgulama.aspx",
        data=callback_data, timeout=60
    )
    log(f"Callback POST status: {r5.status_code}, boyut: {len(r5.text)}")
    r4 = r5  # parse için r4'ü güncelle

    # 4. HTML'den veriyi parse et
    from html.parser import HTMLParser as HP

    class TableParser(HP):
        def __init__(self):
            super().__init__()
            self.in_row = False
            self.in_cell = False
            self.current_row = []
            self.current_cell = ""
            self.rows = []
            self.row_class = ""

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "tr":
                self.row_class = attrs.get("class", "")
                if "dxgvDataRow" in self.row_class:
                    self.in_row = True
                    self.current_row = []
            if tag == "td" and self.in_row:
                self.in_cell = True
                self.current_cell = ""

        def handle_endtag(self, tag):
            if tag == "td" and self.in_cell:
                self.current_row.append(self.current_cell.strip())
                self.in_cell = False
            if tag == "tr" and self.in_row:
                self.rows.append(self.current_row)
                self.in_row = False

        def handle_data(self, data):
            if self.in_cell:
                self.current_cell += data

    tp = TableParser()
    tp.feed(r4.text)
    log(f"Bulunan satır sayısı: {len(tp.rows)}")

    if tp.rows:
        log(f"Örnek satır: {tp.rows[0]}")

    for row in tp.rows:
        if len(row) > 5:
            kod = row[2].strip()
            miktar_str = row[5].strip()
            if kod and kod != "":
                try:
                    stok[kod] = int(float(miktar_str.replace(",", "."))) if miktar_str else 0
                except:
                    stok[kod] = 0

    return stok

if __name__ == "__main__":
    try:
        log("Horoz stok sorgulanıyor...")
        stok = get_all_stok()
        log(f"{len(stok)} ürün bulundu.")
        with open("stok.json", "w", encoding="utf-8") as f:
            json.dump(stok, f, ensure_ascii=False, indent=2)
        log("stok.json yazıldı.")
        if stok:
            log(json.dumps(dict(list(stok.items())[:5]), ensure_ascii=False))
    except Exception as e:
        log(f"HATA: {e}")
        log(traceback.format_exc())
    finally:
        output = "\n".join(log_lines)
        print(output)
        with open("horoz_log.txt", "w", encoding="utf-8") as f:
            f.write(output)
