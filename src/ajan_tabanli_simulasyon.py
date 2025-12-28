"""
TR-ZERO:  Ajan Tabanlı Karbon Piyasası Simülasyonu (v2.1 - Düzeltilmiş)
=======================================================================

Bu modül, Türkiye Emisyon Ticaret Sistemi'ni (ETS) simüle etmek için
geliştirilmiş Ajan Tabanlı Model (ABM) içermektedir.

Düzeltmeler (v2.1):
-------------------
✅ PiyasaOperatoru ve MRV agents listesine eklendi
✅ Tahsisat (allowance) mekanizması eklendi
✅ Bankalama (banking) sistemi eklendi
✅ Ceza geri bildirimi tesislere aktarılıyor
✅ NPV hesabı MAC önemleriyle entegre edildi
✅ Kaynak atıfları düzeltildi
✅ Tüm parametrelere birim eklendi

Metodoloji:
-----------
1. Ajan Heterojenliği:  Yu et al. (2020)
2. Cap & Trade Mekanizması: Zhou et al. (2016)
3. MAC Analizi: McKinsey (2009) - Türkiye'ye uyarlanmış
4. Tahsisat ve Ticaret: EU ETS Directive 2003/87/EC

Kaynaklar:
----------
[1] Yu, S., et al. (2020). Modeling the emission trading scheme from 
    an agent-based perspective. European Journal of Operational Research.
    https://doi.org/10.1016/j.ejor.2020.03.080

[2] Zhou, P., et al. (2016). Multi-agent-based Simulation for Policy 
    Evaluation of Carbon Emissions.  Springer.
    https://doi.org/10.1007/978-981-10-2669-0_29

[3] McKinsey & Company (2009). Pathways to a Low-Carbon Economy: 
    Version 2 of the Global Greenhouse Gas Abatement Cost Curve.
    [NOT: MAC değerleri Türkiye sektörlerine uyarlanmıştır]

[4] T. C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı (2025). 
    Türkiye ETS Yönetmelik Taslağı.
    https://iklim.gov.tr/taslaklar-i-2124

[5] European Commission (2003). EU ETS Directive 2003/87/EC
    https://eur-lex.europa.eu/legal-content/EN/TXT/? uri=CELEX:32003L0087

[6] EBRD & PwC (2024). A Low Carbon Pathway for the Cement Sector 
    in the Republic of Türkiye. 

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih:  Aralık 2025
Versiyon: 2.1 (Düzeltilmiş)
"""

from mesa import Agent, Model
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import random
import os
import sqlite3
from datetime import datetime

# Latin Hypercube Sampling için scipy (McKay et al. 1979)
try:
    from scipy.stats import qmc
    LHS_AVAILABLE = True
except ImportError:
    LHS_AVAILABLE = False
    print("⚠️ scipy.stats.qmc yüklenemedi. Rastgele örnekleme kullanılacak.")
    print("   Kurulum: pip install scipy")

# --- YENİ MODÜL ENTEGRASYONU (v4.5) ---
try:
    from src.enerji_dispatch import EnerjiDispatchModulu
    from src.ekonomik_etki_io import InputOutputModel
    MODULES_AVAILABLE = True
except ImportError:
    # Geliştirme/Test aşamasında yerel importlar için
    try:
        from enerji_dispatch import EnerjiDispatchModulu
        from ekonomik_etki_io import InputOutputModel
        MODULES_AVAILABLE = True
    except ImportError:
        MODULES_AVAILABLE = False
        print("⚠️ Enerji/Ekonomi modülleri yüklenemedi. Eskisi kullanılacak.")

# =============================================================================
# REVENUE RECYCLING SENARYOLARI (GELİR GERİ DÖNÜŞÜ)
# =============================================================================
REVENUE_SCENARIOS = {
    "BAU": {"recycling": "hazine", "transfer_ratio": 0.0},
    "Yumusak_ETS": {"recycling": "yesil_yatirim", "transfer_ratio": 0.5},
    "Siki_ETS": {"recycling": "hanehalki_transfer", "transfer_ratio": 0.8},
    "ETS_Tesvik": {"recycling": "firma_destegi", "transfer_ratio": 1.0}
}


# =============================================================================
# PROJE DİZİNİ AYARLARI
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(PROJECT_ROOT, "iklim_veritabani.sqlite")

# Çıktı klasörünü oluştur
try:
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
except OSError as e:
    print(f"⚠️ Klasör oluşturulamadı: {e}")
    OUTPUT_DIR = SCRIPT_DIR


# =============================================================================
# AI BASELINE ENTEGRASYONU (YENİ - v2.2)
# =============================================================================
"""
AI Tahmin Modülü Entegrasyonu
=============================

Bu bölüm, ai_tahmin_v2.py modülünden üretilen baseline verilerini
simülasyonun başlangıç değerleri olarak yükler.

Dosya: output/ai_baseline.json

Entegrasyon Akışı:
------------------
1. ai_tahmin_v2.py çalıştırılır → ai_baseline.json oluşur
2. Bu modül JSON'u okur → başlangıç değerleri belirlenir
3. Simülasyon AI tahminleriyle kalibre edilmiş olarak çalışır

Referanslar:
------------
Bu yaklaşım "model chaining" olarak bilinir ve iklim modellerinde 
yaygın olarak kullanılır [IPCC AR6, WG1, Chapter 1].
"""


def load_ai_baseline():
    """
    AI tahmin modülünden baseline verilerini yükler.
    
    Bu fonksiyon, ai_tahmin_v2.py tarafından üretilen ai_baseline.json
    dosyasını okuyarak simülasyon için başlangıç parametrelerini döndürür.
    
    Returns:
    --------
    dict : AI baseline verileri veya None (dosya yoksa)
    
    Kullanım:
    ---------
    >>> baseline = load_ai_baseline()
    >>> if baseline:
    >>>     initial_cap = baseline['simulation_params']['suggested_ets_cap_2026']
    
    Örnek Çıktı:
    ------------
    {
        'years': [2026, 2027, ..., 2035],
        'emissions': [560.5, 565.2, ...],
        'simulation_params': {
            'initial_emission_2025': 559.0,
            'suggested_ets_cap_2026': 447.2
        }
    }
    """
    import json
    
    ai_baseline_path = os.path.join(OUTPUT_DIR, "ai_baseline.json")
    
    if os.path.exists(ai_baseline_path):
        try:
            with open(ai_baseline_path, 'r', encoding='utf-8') as f:
                baseline = json.load(f)
            
            print("✅ AI Baseline yüklendi:")
            print(f"   ├── Kaynak: {ai_baseline_path}")
            print(f"   ├── Model R²: {baseline.get('model_r2', 'N/A'):.4f}")
            print(f"   ├── 2025 Emisyon: {baseline['simulation_params']['initial_emission_2025']:.1f} Mt")
            print(f"   └── Önerilen Cap: {baseline['simulation_params']['suggested_ets_cap_2026']:.1f} Mt")
            
            return baseline
            
        except Exception as e:
            print(f"⚠️ AI Baseline yüklenemedi: {e}")
            return None
    else:
        print("ℹ️ AI Baseline bulunamadı (output/ai_baseline.json)")
        print("   Oluşturmak için: python src/ai_tahmin_v2.py")
        return None


def load_facility_data():
    """
    Veritabanından tesis listesini yükler.
    
    Bu fonksiyon, database_setup_v2.py tarafından oluşturulan tesisler
    tablosunu okuyarak ETS kapsamındaki tesisleri döndürür.
    
    Returns:
    --------
    pd.DataFrame : Tesis verileri veya boş DataFrame (veri yoksa)
    
    Tablo Sütunları:
    ----------------
    - Tesis_ID: Benzersiz tesis kodu
    - Tesis_Adi: Santral adı
    - Il: Bulunduğu il
    - Yakit_Tipi: Linyit, Dogalgaz, Ithal_Komur, vb.
    - Kapasite_MW: Kurulu güç
    - Yillik_Emisyon_tCO2: Tahmini yıllık emisyon
    - ETS_Kapsami: 'Evet' veya 'Hayir'
    
    Kaynak:
    -------
    - TEİAŞ (2024). 10 Yıllık Kapasite Projeksiyonu
    - EPDK (2024). Elektrik Piyasası Sektör Raporu
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Tesisler tablosunu kontrol et
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tesisler'")
        
        if cursor.fetchone():
            df_tesisler = pd.read_sql("SELECT * FROM tesisler", conn)
            
            # ETS kapsamındaki tesisleri filtrele
            ets_tesisler = df_tesisler[df_tesisler['ETS_Kapsami'] == 'Evet']
            
            print(f"✅ Tesis listesi yüklendi:")
            print(f"   ├── Toplam tesis: {len(df_tesisler)}")
            print(f"   ├── ETS kapsamında: {len(ets_tesisler)}")
            print(f"   ├── Toplam kapasite: {df_tesisler['Kapasite_MW'].sum():,.0f} MW")
            print(f"   └── Toplam emisyon: {df_tesisler['Yillik_Emisyon_tCO2'].sum()/1e6:.1f} Mt CO₂/yıl")
            
            conn.close()
            return df_tesisler
        else:
            print("ℹ️ Tesisler tablosu bulunamadı")
            print("   Oluşturmak için: python src/database_setup_v2.py")
            conn.close()
            return pd.DataFrame()
            
    except Exception as e:
        print(f"⚠️ Tesis verisi yüklenemedi: {e}")
        return pd.DataFrame()


def load_province_data():
    """
    Veritabanından 81 il emissions dağılım katsayılarını yükler.
    
    Bu fonksiyon, TÜİK 2023 verilerine dayanan il bazlı emisyon
    dağılım katsayılarını döndürür.
    
    Returns:
    --------
    pd.DataFrame : İl katsayıları veya boş DataFrame
    
    Sütunlar:
    ---------
    - Il_Kodu: 1-81 arası plaka kodu
    - Il_Adi: İl adı
    - Bolge: Coğrafi bölge (Marmara, Ege, vb.)
    - Sanayi_Payi: İlin sanayi sektörü payı (0-1)
    - Nufus_Payi: İlin nüfus payı (0-1)
    - Enerji_Payi: İlin enerji tüketim payı (0-1)
    - GSYH_Payi: İlin GSYH payı (0-1)
    
    Kaynak:
    -------
    - TÜİK (2024). İl Bazında GSYH İstatistikleri, 2023
    - TÜİK (2024). ADNKS Sonuçları, 2023
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df_iller = pd.read_sql("SELECT * FROM il_katsayilari", conn)
        conn.close()
        
        print(f"✅ İl katsayıları yüklendi: {len(df_iller)} il/bölge")
        
        return df_iller
        
    except Exception as e:
        print(f"⚠️ İl verisi yüklenemedi: {e}")
        return pd.DataFrame()

# =============================================================================
# SABİT DEĞERLER VE PARAMETRELER
# =============================================================================

# Türkiye ETS Parametreleri
# [Kaynak: Kesin değerler - TR-ETS Taslak 2025; Tahmini - AB ETS'den uyarlanmış]
ETS_PARAMS = {
    "PILOT_BASLANGIC": 2026,     # [TR-ETS Taslak, Madde 5]
    "TAM_UYGULAMA": 2028,         # [TR-ETS Taslak, Madde 5]
    "TABAN_FIYAT": 20,            # [TAHMİNİ - $/ton CO₂, modelleme için]
    "TAVAN_FIYAT": 150,           # [TAHMİNİ - $/ton CO₂, AB ETS 2027 ~€111]
    "CEZA_MIKTARI": 100           # [TAHMİNİ - $/ton CO₂, AB ETS €100/ton]
}

# Sektör Profilleri
# [Kaynak: (1) NIR 2024 - sektör emisyonları
#         (2) TÜİK sanayi istatistikleri
#         (3) IPCC EF veritabanı
#         NOT: Değerler Türkiye sektörlerine uyarlanmış tahminlerdir]
SEKTOR_PROFILLERI = {
    "Enerji": {
        "baz_emisyon":  1.0,           # Mt CO₂/yıl (temsilci tesis ortalaması)
        "ihracat_orani": 0.05,        # 0. 05 = %5 (sektör üretiminin ihraç payı)
        "skdm_kapsam": False,         # boolean (AB SKDM/CBAM kapsamında mı?)
        "maliyet_limit": 90,          # Milyon $/yıl (işletme kapanma eşiği)
        "yatirim_bedeli": 200,        # Milyon $ (temizlik teknolojisi CAPEX)
        "duyarlilik":  "Vergi",        # string (politika duyarlılığı)
        "mac_onlemler": {
            "enerji_verimliligi": {"mac": -15, "potansiyel": 0.08, "sure": 2},  # $/ton, oran, yıl
            "yakit_degisimi": {"mac": 35, "potansiyel": 0.20, "sure": 3},
            "yenilenebilir":  {"mac": 50, "potansiyel": 0.35, "sure": 5}
        }
    },
    "Sanayi": {
        "baz_emisyon": 0.75,          # Mt CO₂/yıl
        "ihracat_orani": 0.40,        # 0.40 = %40
        "skdm_kapsam": True,          # AB SKDM kapsamında
        "maliyet_limit": 110,         # Milyon $/yıl
        "yatirim_bedeli": 250,        # Milyon $
        "duyarlilik": "Vergi",
        "mac_onlemler": {
            "enerji_verimliligi": {"mac":  -5, "potansiyel": 0.10, "sure": 2},
            "proses_iyilestirme": {"mac": 25, "potansiyel": 0.15, "sure": 3},
            "teknoloji_degisimi": {"mac": 60, "potansiyel": 0.30, "sure": 6}
        }
    },
    "Tarim": {
        "baz_emisyon": 0.3,           # Mt CO₂/yıl
        "ihracat_orani": 0.20,        # 0.20 = %20
        "skdm_kapsam": False,
        "maliyet_limit":  999,         # Milyon $/yıl (tarım hassas sektör)
        "yatirim_bedeli": 300,        # Milyon $
        "duyarlilik":  "Tesvik",       # Teşvik odaklı sektör
        "mac_onlemler": {
            "gubre_optimizasyonu": {"mac": 10, "potansiyel": 0.15, "sure": 1},
            "metan_yakalama": {"mac": 40, "potansiyel": 0.25, "sure": 5}
        }
    }
}

# =============================================================================
# AJAN SINIFLARI
# =============================================================================

class PiyasaOperatoru(Agent):
    """
    ETS Piyasa Operatörü - Cap & Trade mekanizmasını yönetir. 
    
    Referanslar:
    - [cite:  Yu et al. 2020] Piyasa-clearing mekanizması
    - [cite: EU ETS Directive] Cap azaltma kuralları
    """
    
    def __init__(self, model, baslangic_cap, azalma_orani):
        super().__init__(model)
        self.ajan_tipi = "PiyasaOperatoru"
        self.cap = baslangic_cap  # Mt CO₂
        self.azalma_orani = azalma_orani  # yıllık oran (0-1 arası)
        self.piyasa_fiyati = ETS_PARAMS["TABAN_FIYAT"]  # $/ton
        self.fiyat_gecmisi = []
        self.toplam_gelir = 0  # Milyon $
        
    def step(self):
        """Her yıl için piyasa operatörü adımı."""
        # Cap azaltma sadece ETS aktif olduğunda
        if self. model.yil >= ETS_PARAMS["PILOT_BASLANGIC"]: 
            self.cap *= (1 - self.azalma_orani)
        
        # Toplam Emisyon Hesaplama
        toplam_emisyon = self._toplam_emisyon_hesapla()
        
        # Fiyat Belirleme (Arz-Talep Modeli) - Sadece ETS aktifse
        if self.model.yil >= ETS_PARAMS["PILOT_BASLANGIC"] and self.cap > 0 and toplam_emisyon > 0:
            # Emisyon/Cap oranına göre fiyat belirleme
            arz_talep_orani = toplam_emisyon / self.cap
            
            # Fiyat formülü: Oran > 1 ise fiyat hızla artar
            if arz_talep_orani > 1:
                self.piyasa_fiyati = ETS_PARAMS["TABAN_FIYAT"] * (arz_talep_orani ** 2)
            else:
                self.piyasa_fiyati = ETS_PARAMS["TABAN_FIYAT"] * (arz_talep_orani ** 0.5)
            
            # Taban ve tavan sınırları
            self.piyasa_fiyati = max(ETS_PARAMS["TABAN_FIYAT"], 
                                    min(ETS_PARAMS["TAVAN_FIYAT"], self.piyasa_fiyati))
        else:
            # ETS öncesi dönem - fiyat sıfır
            self.piyasa_fiyati = 0
        
        # Model fiyatını güncelle
        self.model.karbon_fiyati = self.piyasa_fiyati
        self.fiyat_gecmisi.append(self.piyasa_fiyati)
        
        # Açık artırma geliri hesapla (Tam uygulama döneminde)
        if self.model.yil >= ETS_PARAMS["TAM_UYGULAMA"] and self.piyasa_fiyati > 0:
            acik_artirma_orani = 0.3  # %30 açık artırma
            acik_artirma_miktari = self.cap * acik_artirma_orani
            yil_geliri = acik_artirma_miktari * self.piyasa_fiyati
            self.toplam_gelir += yil_geliri
            
            # --- GELİR GERİ DÖNÜŞÜ (REVENUE RECYCLING) ---
            recycling_config = self.model.rev_recycling
            transfer_miktari = yil_geliri * recycling_config["transfer_ratio"]
            
            if recycling_config["recycling"] == "hanehalki_transfer":
                # Hanehalkına eşit dağıtım
                haneler = [a for a in self.model.agents if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Hanehalki"]
                if haneler:
                    pay_basina = transfer_miktari / len(haneler)
                    for h in haneler:
                        # Basitçe hane bütçesine veya 'gelir' değişkenine ekle (varsa)
                        if hasattr(h, 'gelir'): h.gelir += pay_basina
            
            elif recycling_config["recycling"] == "yesil_yatirim":
                # Proje geliştiricilere yatırım desteği olarak aktar
                self.model.tesvik_miktari += (transfer_miktari / 100) # Teşvik havuzunu büyüt
                
            elif recycling_config["recycling"] == "firma_destegi":
                # Endüstriyel tesislere teknoloji desteği
                tesisler = [a for a in self.model.agents if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "EndustriyelTesis"]
                if tesisler:
                    pay_basina = transfer_miktari / len(tesisler)
                    for t in tesisler:
                        if hasattr(t, 'butce'): t.butce += pay_basina

    
    def _toplam_emisyon_hesapla(self):
        """Aktif tesislerin toplam emisyonunu hesaplar."""
        return sum(
            agent.emisyon for agent in self.model.agents
            if hasattr(agent, 'ajan_tipi') and agent.ajan_tipi in ["Tesis", "IhracatciTesis"] 
            and agent.durum != "Kapali"
        )


class EndustriyelTesis(Agent):
    """
    Endüstriyel Tesis Ajanı - Geliştirilmiş karar mekanizması. 
    
    Özellikler:
    1. MAC Analizi (McKinsey 2009)
    2. NPV Hesabı (standart finans modeli)
    3. Tahsisat ve Bankalama (EU ETS)
    4. Kapanma Eşiği
    
    Referanslar:
    - [cite: McKinsey 2009] MAC eğrileri
    - [cite: Tang et al. 2022] Firma karar mekanizması
    - [cite: EU ETS Directive] Tahsisat kuralları
    """
    
    def __init__(self, model, sektor, city="Istanbul"):
        super().__init__(model)
        self.ajan_tipi = "Tesis"
        self.sektor = sektor
        self.city = city
        self.profil = SEKTOR_PROFILLERI. get(sektor, SEKTOR_PROFILLERI["Sanayi"])
        
        # Emisyon (heterojen) - il katsayısı ile çarpılır
        il_katsayi = model.il_katsayilari. get(city, {}).get(sektor. lower(), 1.0) if hasattr(model, 'il_katsayilari') else 1.0
        self.emisyon = self.profil["baz_emisyon"] * np.random.uniform(0.7, 1.3) * il_katsayi  # Mt CO₂/yıl
        self.baslangic_emisyon = self.emisyon
        
        # SKDM:  İhracatçı mı? 
        self.ihracatci = random.random() < self.profil["ihracat_orani"]
        
        # Durum
        self.durum = "Aktif"  # Aktif, Donusum, Temiz, Kapali
        self.yatirim_durumu = None
        self.kalan_yatirim_suresi = 0
        self.emisyon_azalma_potansiyeli = 0
        
        # Maliyet parametreleri
        self.maliyet_limit = self.profil["maliyet_limit"]  # Milyon $/yıl
        self. yatirim_bedeli = self. profil["yatirim_bedeli"]  # Milyon $
        self. duyarlilik = self.profil["duyarlilik"]
        
        # ETS mekanizmaları (YENİ)
        self.ucretsiz_tahsisat = 0  # tCO₂/yıl
        self.izin_bankasi = 0  # tCO₂ (birikmiş izinler)
        self.net_emisyon = 0  # tCO₂ (tahsisat sonrası)
        
        # Ceza takibi (YENİ)
        self.ceza_durumu = False
        self.ceza_miktari = 0.0  # Milyon $
        
    def step(self):
        """Her yıl için tesis karar adımı."""
        if self.durum == "Kapali":
            return
        
        # 1. Efektif Karbon Fiyatı (SKDM dahil)
        if self.ihracatci and self.profil["skdm_kapsam"]:
            efektif_fiyat = max(self.model.karbon_fiyati, self.model.ab_skdm_fiyat)
        else:
            efektif_fiyat = self.model.karbon_fiyati
        
        # 2. ÜCRETSİZ TAHSİSAT HESAPLA (YENİ)
        if self.model.yil >= ETS_PARAMS["PILOT_BASLANGIC"]:
            if self.model.yil < ETS_PARAMS["TAM_UYGULAMA"]: 
                ucretsiz_oran = 1.0  # Pilot dönem %100
            else:
                ucretsiz_oran = 0.7  # Tam uygulama %70
            
            self.ucretsiz_tahsisat = self.baslangic_emisyon * ucretsiz_oran
            
            # BANKALAMA MEKANİZMASI (YENİ)
            fazla_tahsisat = self.ucretsiz_tahsisat - self.emisyon
            
            if fazla_tahsisat > 0:
                # Fazla izni bankala
                self.izin_bankasi += fazla_tahsisat
                self.net_emisyon = 0
            else:
                # Önce bankadan kullan
                eksik = abs(fazla_tahsisat)
                bankadan_kullan = min(eksik, self.izin_bankasi)
                self.izin_bankasi -= bankadan_kullan
                self.net_emisyon = eksik - bankadan_kullan
        else:
            # ETS öncesi dönem
            self.net_emisyon = 0
        
        # 3. Yatırım süreci devam ediyor mu?
        if self. kalan_yatirim_suresi > 0:
            self. kalan_yatirim_suresi -= 1
            if self.kalan_yatirim_suresi == 0:
                self.emisyon *= (1 - self.emisyon_azalma_potansiyeli)
                self.durum = "Temiz"
                self.ceza_durumu = False  # Yatırım tamamlandı, ceza sıfırlandı
            return
        
        # 4. Karar Mekanizması
        if self.durum == "Aktif":
            karar = self._karar_ver(efektif_fiyat)
            
            if karar == "yatirim":
                self._yatirim_baslat(efektif_fiyat)
            elif karar == "kapat":
                self. durum = "Kapali"
                self.emisyon = 0
    
    def _karar_ver(self, efektif_fiyat):
        """
        Geliştirilmiş karar algoritması - Hibrit ve Dinamik Yapı. 
        
        Üç aşamalı karar mekanizması:
        1. MAC Analizi:  Karbon fiyatı vs marjinal azaltım maliyeti
        2. NPV Hesabı: Yatırımın net bugünkü değeri (her MAC önlemi için)
        3. Kapanma Eşiği:  Karbon maliyeti faaliyet limitini geçerse
        
        Referanslar:
        - MAC Analizi: [cite: McKinsey 2009]
        - NPV Formülü: [cite: Brealey et al. 2020, Corporate Finance]
        - Kapanma Eşiği: [cite:  Tang et al. 2022]
        """
        # Teşvik duyarlı sektörler (Tarım)
        if self. duyarlilik == "Tesvik":
            if self.model.tesvik_miktari >= (self.yatirim_bedeli * 0.6 * 1000):
                return "yatirim"
            return "bekle"
        
        # Ceza aldıysa zorla yatırım yap
        if self.ceza_durumu:
            return "yatirim"
        
        # --- GELİŞTİRİLMİŞ KARAR MEKANİZMASI ---
        
        # NPV Parametreleri
        r = 0.08  # İskonto oranı (Türkiye risk primi dahil)
        ekonomik_omur = 10  # Yatırım ekonomik ömrü (yıl)
        
        # Her MAC önlemi için NPV hesapla
        mac_onlemler = self. profil. get("mac_onlemler", {})
        en_iyi_npv = -9999
        en_iyi_onlem = None
        
        for onlem_adi, onlem in mac_onlemler.items():
            # 1. MAC Kontrolü
            if onlem["mac"] >= efektif_fiyat: 
                continue  # Bu önlem karbon fiyatından pahalı, atla
            
            # 2. NPV Hesabı (her önlem için özel)
            yillik_azaltim = self.emisyon * onlem["potansiyel"]  # tCO₂/yıl
            yillik_tasarruf = yillik_azaltim * efektif_fiyat * 1e6  # $/yıl (Mt -> ton)
            
            # Yatırım maliyeti
            if onlem["mac"] > 0:
                yatirim_maliyeti = yillik_azaltim * onlem["mac"] * 1e6  # $
            else:
                yatirim_maliyeti = 0  # Negatif MAC = kar ediyor
            
            # NPV Formülü: -Yatırım + Σ(Tasarruf / (1+r)^t)
            npv = -yatirim_maliyeti
            for t in range(1, ekonomik_omur + 1):
                npv += yillik_tasarruf / ((1 + r) ** t)
            
            # En iyi NPV'yi kaydet
            if npv > en_iyi_npv: 
                en_iyi_npv = npv
                en_iyi_onlem = (onlem_adi, onlem)
        
        # Yatırım kararı:  En iyi NPV pozitifse
        if en_iyi_npv > 0:
            self._yatirim_onlemi_kaydet = en_iyi_onlem  # Sonraki adımda kullanmak için
            return "yatirim"
        
        # 3. Kapanma Eşiği:  Net emisyon maliyeti limitini geçerse
        if self.net_emisyon > 0:
            karbon_maliyeti = self. net_emisyon * efektif_fiyat  # Mt × $/ton = Milyon $
            if karbon_maliyeti > self.maliyet_limit:
                return "kapat"
        
        return "bekle"
    
    def _yatirim_baslat(self, karbon_fiyati):
        """En uygun yatırımı başlatır."""
        # Önceki adımda kaydedilen en iyi önlemi kullan
        if hasattr(self, '_yatirim_onlemi_kaydet') and self._yatirim_onlemi_kaydet:
            onlem_adi, onlem = self._yatirim_onlemi_kaydet
        else:
            # Fallback: İlk uygun önlemi seç
            mac_onlemler = self.profil.get("mac_onlemler", {})
            onlem_adi, onlem = None, None
            for adi, o in mac_onlemler.items():
                if o["mac"] < karbon_fiyati: 
                    onlem_adi, onlem = adi, o
                    break
        
        if onlem: 
            self. yatirim_durumu = onlem_adi
            self. kalan_yatirim_suresi = onlem["sure"]
            self.emisyon_azalma_potansiyeli = onlem["potansiyel"]
            self.durum = "Donusum"
        else:
            # MAC'tan uygun önlem yoksa basit dönüşüm
            self.yatirim_durumu = "genel_iyilestirme"
            self.kalan_yatirim_suresi = 3
            self.emisyon_azalma_potansiyeli = 0.20
            self.durum = "Donusum"


class IhracatciAjani(EndustriyelTesis):
    """
    İhracatçı Ajan - CBAM (SKDM) etkisini ve dış ticaret tepkisini modeller.
    
    Bu ajan, AB Sınırda Karbon Düzenleme Mekanizması'nın (CBAM/SKDM)
    Türk ihracatçılarına etkisini simüle eder.
    
    Referanslar:
    - [cite: EU Regulation 2023/956] CBAM kuralları
    - [cite:  OECD 2024] Sınır karbon ayarlaması etkileri
    """
    
    def __init__(self, model, sektor, city="Istanbul"):
        super().__init__(model, sektor, city=city)
        self.ajan_tipi = "IhracatciTesis"
        self.ihracat_payi = self.profil["ihracat_orani"]
        self.cbam_maliyeti = 0.0  # Milyon $/yıl
        self. rekabet_gucu_indeksi = 1.0  # 0-1 arası
        
    def step(self):
        """İhracatçı ajan adımı - CBAM maliyeti hesaplar."""
        if self.durum == "Kapali":
            return
        
        # CBAM Maliyeti Hesaplama
        if self.ihracatci and self.profil["skdm_kapsam"]:
            # CBAM maliyeti = Emisyon × AB SKDM fiyatı
            self.cbam_maliyeti = self.emisyon * self.model.ab_skdm_fiyat  # Milyon $
            
            # Türkiye'deki karbon fiyatı CBAM'dan düşülebilir
            if self.model.karbon_fiyati > 0:
                dusilebilir_miktar = min(self.cbam_maliyeti, 
                                          self.emisyon * self.model.karbon_fiyati)
                self.cbam_maliyeti -= dusilebilir_miktar
            
            # Rekabet gücü indeksini güncelle
            self._rekabet_gucu_hesapla()
        else:
            self.cbam_maliyeti = 0.0
        
        # Üst sınıfın step metodunu çağır
        super().step()
    
    def _rekabet_gucu_hesapla(self):
        """CBAM maliyetine göre rekabet gücü indeksini hesaplar."""
        maliyet_esik = 50  # Milyon $
        if self.cbam_maliyeti > 0:
            self.rekabet_gucu_indeksi = max(0.3, 1.0 - (self.cbam_maliyeti / maliyet_esik) * 0.1)
        else:
            self.rekabet_gucu_indeksi = 1.0


class MRVAjani(Agent):
    """
    MRV (İzleme, Raporlama, Doğrulama) Ajanı - Denetim ve ceza mekanizmasını yönetir.
    
    Bu ajan, ETS sisteminin uyum mekanizmasını simüle eder: 
    - Tesislerin rastgele denetimi
    - Raporlama uyumsuzluğu tespiti
    - Ceza uygulama ve tesislere geri bildirim
    
    Referanslar:
    - [cite: EU ETS Directive] MRV gereksinimleri
    - [cite: Zhou et al. 2016] Uyum mekanizması modellemesi
    """
    
    def __init__(self, model):
        super().__init__(model)
        self.ajan_tipi = "MRV"
        self. denetim_olasiligi = 0.2  # %20 rastgele denetim
        self.ceza_miktari = ETS_PARAMS["CEZA_MIKTARI"]  # $/ton CO₂
        self.toplam_denetim = 0
        self.toplam_ceza = 0.0  # Milyon $
        self. uyumsuz_tesis_sayisi = 0
        
    def step(self):
        """MRV denetim adımı - Tesisleri rastgele denetle ve gerekirse ceza kes."""
        self. uyumsuz_tesis_sayisi = 0
        
        for agent in self.model.agents:
            # Sadece tesis ajanlarını denetle
            if hasattr(agent, 'ajan_tipi') and agent.ajan_tipi in ["Tesis", "IhracatciTesis"]:
                if agent.durum != "Kapali":
                    # Rastgele denetim kontrolü
                    if random.random() < self.denetim_olasiligi: 
                        self.toplam_denetim += 1
                        
                        # Raporlanan vs Gerçek emisyon kontrolü simülasyonu
                        # %5 uyumsuzluk olasılığı (eksik raporlama)
                        if random.random() < 0.05:
                            self.uyumsuz_tesis_sayisi += 1
                            
                            # Ceza hesapla:  Eksik raporlanan emisyon × ceza birim fiyatı
                            eksik_emisyon = agent.emisyon * np.random.uniform(0.05, 0.15)  # Mt
                            ceza = eksik_emisyon * self. ceza_miktari  # Milyon $
                            self.toplam_ceza += ceza
                            
                            # EKLEME: Tesise ceza durumunu bildir
                            agent.ceza_durumu = True
                            agent.ceza_miktari = ceza


class Hanehalki(Agent):
    """
    Hanehalkı Ajanı - Konut enerji tüketimi ve fiyat duyarlılığını modeller.
    
    Referanslar:
    - Labandeira et al. (2017). A meta-analysis on the price elasticity of energy demand
    - [cite: TÜİK 2024] Hanehalkı enerji tüketimi istatistikleri
    """
    
    def __init__(self, model, city="Istanbul"):
        super().__init__(model)
        self.ajan_tipi = "Hanehalki"
        self.city = city
        
        # Gelir grubu ve tüketim parametreleri
        self.gelir_grubu = random.choice(["dusuk", "orta", "yuksek"])
        
        # Gelir grubuna göre elektrik tüketimi (kWh/yıl)
        tuketim_aralik = {
            "dusuk": (1500, 2500),
            "orta": (2500, 4000),
            "yuksek": (4000, 6000)
        }
        min_t, max_t = tuketim_aralik[self.gelir_grubu]
        self. tuketim = np.random.uniform(min_t, max_t)  # kWh/yıl
        
        # Emisyon hesabı:  kWh -> MWh -> ton CO₂
        self.emisyon = (self.tuketim / 1000) * model. EMISYON_FAKTORU_TR  # ton CO₂/yıl
        self.baslangic_emisyon = self.emisyon
        self.durum = "Aktif"
        
        # Fiyat elastikiyesi (Labandeira et al. 2017)
        self.elastikiyet = {
            "dusuk": -0.6,
            "orta": -0.4,
            "yuksek": -0.25
        }[self.gelir_grubu]
    
    def step(self):
        """Hanehalkı tüketim ve emisyon güncelleme adımı."""
        if self. durum != "Aktif":
            return
        
        # Karbon fiyatı etkisi - elastikiyet modeli
        if self.model.karbon_fiyati > 0:
            fiyat_orani = self.model.karbon_fiyati / 100  # 100 $/ton referans
            fiyat_etkisi = max(0.5, 1 + (self.elastikiyet * fiyat_orani))
            
            # Tüketim ve emisyonu güncelle
            self. emisyon = (self.tuketim / 1000) * self.model. EMISYON_FAKTORU_TR * fiyat_etkisi
        else:
            self.emisyon = (self.tuketim / 1000) * self.model.EMISYON_FAKTORU_TR

# =============================================================================
# ULAŞIM SEKTÖRÜ AJANI 
# =============================================================================
"""
Ulaşım Sektörü Emisyon Modeli
=============================

Metodoloji:
-----------
Bu ajan, Türkiye ulaşım sektörünün karbon emisyonlarını ve elektrikli 
araç (EV) geçiş kararlarını simüle eder.

Referanslar:
------------
[1] IEA (2024). Turkey Transport Sector Statistics.
    - Türkiye ulaşım sektörü toplam emisyonların ~%17'sini oluşturur
    - Modal dağılım:  Karayolu %90, Havayolu %7, Denizyolu %3
    https://www.iea.org/countries/turkey/transport

[2] IPCC (2006). 2006 IPCC Guidelines, Volume 2, Chapter 3:  
    Mobile Combustion - Emission Factors.
    - Karayolu (Dizel): 74. 1 tCO₂/TJ
    - Havayolu (Jet Fuel): 71.5 tCO₂/TJ  
    - Denizyolu (Heavy Fuel Oil): 77.4 tCO₂/TJ
    https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_3_Ch3_Mobile_Combustion. pdf

[3] IEA (2023). Global EV Outlook - Policy Trigger Analysis.
    - Karbon fiyatı $50/ton üzerinde → EV yatırım hızlanması
    - EV penetrasyon hızı:  Yüksek fiyat senaryosunda yıllık +%2
    https://www.iea.org/reports/global-ev-outlook-2023

Temel Formül:
-------------
Emisyon = Yakıt_Tüketimi (TJ) × Emisyon_Faktörü (tCO₂/TJ) × (1 - EV_Payı)

Varsayımlar:
-----------
- EV'ler sıfır emisyon (şebeke şarjı varsayımı)
- Karbon fiyatı $50/ton üzerinde → EV penetrasyon hızı %2/yıl
- Maksimum EV penetrasyonu: %50 (2035'e kadar ulaşılabilir)

NOT:  Başlangıç değerleri placeholder (yer tutucu). Gerçek veri 
     TÜİK Ulaştırma İstatistikleri'nden alınacak.
"""


class UlasimAgent(Agent):
    """
    Ulaşım Sektörü Ajanı - Karayolu, Havayolu, Denizyolu
    
    Bu ajan, ulaşım modlarının emisyonlarını ve elektrikli araç (EV) 
    geçiş dinamiklerini simüle eder. 
    
    Parametreler:
    -------------
    model :  TurkiyeETSModel
        Ana model nesnesi
    ulasim_tipi : str
        'karayolu', 'havayolu', veya 'denizyolu'
    city : str, optional
        Bölge/şehir (varsayılan: 'Ulusal')
    
    Önemli Notlar:
    --------------
    1. Yakıt tüketimi TJ (TeraJoule) cinsinden - IPCC standart birim
    2. Emisyon faktörleri IPCC 2006 Tier 1 metodolojisi
    3. EV payı sadece karayolu için geçerli (havayolu/deniz için biofuel)
    
    Örnek Kullanım:
    ---------------
    >>> model = TurkiyeETSModel()
    >>> karayolu = UlasimAgent(model, 'karayolu')
    >>> karayolu.step()  # Bir yıllık adım
    >>> print(karayolu.emisyon_miktari)  # Mt CO₂
    """
    
    def __init__(self, model, ulasim_tipi, city="Ulusal"):
        """
        Ulaşım ajanı başlatıcı. 
        
        Parametre Notları:
        ------------------
        - ulasim_tipi kontrolü yapılır (geçersiz tip hata verir)
        - Başlangıç değerleri literatür ortalamalarıdır
        - İl bazlı katsayı uygulanır (varsa)
        """
        super().__init__(model)
        self.ajan_tipi = "Ulasim"
        self.ulasim_tipi = ulasim_tipi
        self.city = city
        
        # Geçerli ulaşım tipi kontrolü
        gecerli_tipler = ['karayolu', 'havayolu', 'denizyolu']
        if ulasim_tipi not in gecerli_tipler:
            raise ValueError(
                f"❌ Geçersiz ulaşım tipi: '{ulasim_tipi}'.  "
                f"Geçerli seçenekler: {gecerli_tipler}"
            )
        
        # ===================================================================
        # BAŞLANGIÇ PARAMETRELERİ (Düzeltilmiş - Gerçekçi Değerler)
        # ===================================================================
        # 
        # Kaynaklar:
        # ----------
        # [1] IEA (2024). Turkey - Countries & Regions - Transport Statistics.
        #     https://www.iea.org/countries/turkey/transport
        #     Erişim: Aralık 2024
        #     Veriler:
        #       - Toplam ulaşım emisyonu: ~90 Mt CO₂ (2022)
        #       - Modal pay: Karayolu %89.8, Havayolu %7.1, Denizyolu %3.1
        #
        # [2] TÜİK (2023). Ulaştırma İstatistikleri, 2022.
        #     https://data.tuik.gov.tr/Kategori/GetKategori?p=ulastirma-ve-haberlesme-113
        #     Tablo 21.1: Ulaştırma sektörü enerji tüketimi
        #
        # [3] IPCC (2006). 2006 IPCC Guidelines, Volume 2, Chapter 3.
        #     Emisyon faktörleri:
        #       - Road: 74.1 tCO₂/TJ (Tablo 3.2.1)
        #       - Aviation: 71.5 tCO₂/TJ (Tablo 3.2.2) 
        #       - Maritime: 77.4 tCO₂/TJ (Tablo 3.2.3)
        #
        # NOT: Türkiye toplam ulaşım sektörü ~90 Mt CO₂/yıl
        #      Bu ajanlar sektör toplamını temsil eder
        #
        # Hesaplama: Emisyon (Mt) = Yakıt × Emisyon_Faktörü
        # Geriye dönük: Yakıt = Hedef_Emisyon / EF
        
        if ulasim_tipi == 'karayolu':
            # Karayolu Ulaşım (Türkiye'nin %90'ı)
            # Hedef emisyon: ~81 Mt CO₂/yıl (türkiye ulaşım ~90 Mt × 0.90)
            # Yakıt = 81 / 74.1 ≈ 1.093
            self.yakit_tuketimi = 1.093       # Mt CO₂ equivalent (basitleştirilmiş)
            self.emisyon_faktoru = 74.1       # tCO₂/TJ [IPCC 2006, Tablo 3.2.1]
            self.modal_share = 0.90           # Toplam ulaşım içinde %90
            self.ev_yatirim_esik = 50         # Karbon fiyatı eşiği ($/ton)
            self.aciklama = "Yolcu + yük taşımacılığı (otomobil, kamyon, otobüs)"
            
        elif ulasim_tipi == 'havayolu': 
            # Havayolu Ulaşım (Türkiye'nin %7'si)
            # Hedef emisyon: ~6.3 Mt CO₂/yıl (90 × 0.07)
            # Yakıt = 6.3 / 71.5 ≈ 0.088
            self.yakit_tuketimi = 0.088       # Mt CO₂ equivalent
            self.emisyon_faktoru = 71.5       # tCO₂/TJ [IPCC 2006, Tablo 3.2.2]
            self.modal_share = 0.07           # Toplam ulaşım içinde %7
            self.ev_yatirim_esik = 999        # Elektrikli uçak henüz yok
            self.aciklama = "İç + dış hat uçuşlar (kerosen yakıt)"
            
        elif ulasim_tipi == 'denizyolu':
            # Denizyolu Ulaşım (Türkiye'nin %3'ü)
            # Hedef emisyon: ~2.7 Mt CO₂/yıl (90 × 0.03)
            # Yakıt = 2.7 / 77.4 ≈ 0.035
            self.yakit_tuketimi = 0.035       # Mt CO₂ equivalent
            self.emisyon_faktoru = 77.4       # tCO₂/TJ [IPCC 2006, Tablo 3.2.3]
            self.modal_share = 0.03           # Toplam ulaşım içinde %3
            self.ev_yatirim_esik = 999        # Elektrikli gemi sınırlı
            self.aciklama = "Yük + yolcu gemileri (fuel oil)"
        
        # ===================================================================
        # TÜRETİLMİŞ DEĞİŞKENLER 
        # ===================================================================
        
        # İl bazlı katsayı uygula (varsa)
        il_katsayi = self._il_katsayisi_al()
        self.yakit_tuketimi *= il_katsayi
        
        # Başlangıç emisyonu hesapla
        # Formül: E = Yakıt × EF
        self.emisyon_miktari = self.yakit_tuketimi * self.emisyon_faktoru
        self.baslangic_emisyon = self.emisyon_miktari  # Karşılaştırma için
        
        # EV/Temiz teknoloji payı
        self.ev_pay = 0.0                   # Başlangıçta %0 EV payı
        self.max_ev_pay = 0.50              # Maksimum %50 penetrasyon
        self.ev_buyume_hizi = 0.02          # Yıllık %2 artış
        
        # Durum takibi
        self.durum = "Aktif"
        self.yatirim_sayisi = 0
    
    def _il_katsayisi_al(self):
        """
        İl bazlı yakıt tüketimi katsayısını alır.
        
        Açıklama:
        ---------
        - Büyük şehirler (İstanbul, Ankara) daha yüksek katsayı
        - Küçük iller daha düşük katsayı
        - Veri yoksa 1.0 (ortalama) kullanılır
        
        Returns:
        --------
        float :  İl katsayısı (0.5 - 2.0 arası)
        """
        if hasattr(self.model, 'il_katsayilari'):
            katsayilar = self.model.il_katsayilari.get(self.city, {})
            # Ulaşım için özel katsayı varsa kullan, yoksa 1.0
            return katsayilar.get('ulasim', 1.0)
        else:
            return 1.0  # Varsayılan: ortalama
    
    def step(self):
        """
        Ulaşım ajanı yıllık adım fonksiyonu.
        
        Adım Sırası:
        ------------
        1. Model karbon fiyatını kontrol et
        2. EV yatırım kararı ver (karayolu için)
        3. Emisyonu güncelle
        4. Durum bilgilerini kaydet
        
        Karar Mantığı:
        --------------
        - Karbon fiyatı > eşik → EV payını artır
        - EV payı maksimuma ulaştıysa durdur
        - Havayolu/denizyolu için biofuel (gelecek özellik)
        """
        if self.durum != "Aktif":
            return
        
        # ===============================================================
        # ADIM 1: Model Parametrelerini Al
        # ===============================================================
        karbon_fiyati = getattr(self.model, 'karbon_fiyati', 0)
        mevcut_yil = getattr(self.model, 'yil', 2025)
        
        # ===============================================================
        # ADIM 2: EV Yatırım Kararı (Sadece Karayolu)
        # ===============================================================
        """
        EV Yatırım Mantığı:
        -------------------
        Referans: IEA Global EV Outlook (2023)
        
        Tetikleyici Koşullar:
        1. Karbon fiyatı > eşik değer ($50/ton)
        2. EV payı henüz maksimuma ulaşmadı
        3. Ulaşım tipi karayolu (havayolu/deniz için N/A)
        
        Penetrasyon Hızı: 
        - Yüksek karbon fiyatı:  Yıllık %2 artış
        - Gerçek dünya örneği:  Norveç 2020-2023 döneminde %15 → %80
        """
        if (karbon_fiyati > self.ev_yatirim_esik and 
            self.ulasim_tipi == 'karayolu' and 
            self.ev_pay < self.max_ev_pay):
            
            # EV payını artır
            eski_pay = self.ev_pay
            self.ev_pay = min(self.max_ev_pay, 
                             self.ev_pay + self.ev_buyume_hizi)
            
            # Yatırım kaydı (raporlama için)
            if self.ev_pay > eski_pay: 
                self.yatirim_sayisi += 1
        
        # ===============================================================
        # ADIM 3: Emisyon Güncellemesi
        # ===============================================================
        """
        Emisyon Hesaplama Formülü:
        --------------------------
        E = Yakıt × EF × (1 - EV_payı)
        
        Açıklama:
        - Yakıt:  TJ cinsinden yıllık tüketim
        - EF:  IPCC emisyon faktörü (tCO₂/TJ)
        - EV_payı: Elektrikli araç penetrasyonu (0-1)
        
        Varsayım:
        - EV'ler sıfır emisyon (şebeke yeşil enerji varsayımı)
        - Gerçek modellemede şebeke emisyon faktörü eklenebilir
        
        Örnek: 
        ------
        Yakıt = 1000 TJ
        EF = 74.1 tCO₂/TJ
        EV_payı = 0.20 (yani %20 EV)
        
        E = 1000 × 74.1 × (1 - 0.20)
          = 1000 × 74.1 × 0.80
          = 59,280 ton CO₂
          = 0.059 Mt CO₂
        """
        self.emisyon_miktari = (
            self.yakit_tuketimi * 
            self.emisyon_faktoru * 
            (1.0 - self.ev_pay)
        )
        
        # Negatif emisyon kontrolü (güvenlik)
        self.emisyon_miktari = max(0.0, self.emisyon_miktari)
    
    def get_emisyon(self):
        """
        Güncel emisyon miktarını döndürür.
        
        Returns:
        --------
        float : Emisyon miktarı (Mt CO₂/yıl)
        
        Kullanım: 
        ---------
        >>> ajan = UlasimAgent(model, 'karayolu')
        >>> ajan.step()
        >>> print(f"Emisyon: {ajan.get_emisyon():.2f} Mt")
        """
        return self.emisyon_miktari
    
    def get_azaltim_orani(self):
        """
        Başlangıca göre emisyon azaltım oranını hesaplar.
        
        Returns:
        --------
        float : Azaltım oranı (0-1 arası)
        
        Örnek:
        ------
        Başlangıç: 100 Mt → Şimdi: 80 Mt → Azaltım: 0.20 (yani %20)
        """
        if self.baslangic_emisyon > 0:
            azalim = self.baslangic_emisyon - self.emisyon_miktari
            return azalim / self.baslangic_emisyon
        return 0.0
    
    def __repr__(self):
        """
        Ajan bilgilerini okunabilir formatta gösterir.
        
        Örnek Çıktı:
        ------------
        <UlasimAgent:  karayolu | Emisyon: 74.10 Mt | EV: %15>
        """
        return (
            f"<UlasimAgent: {self.ulasim_tipi} | "
            f"Emisyon: {self.emisyon_miktari:.2f} Mt | "
            f"EV: %{self.ev_pay*100:.0f}>"
        )

class ProjeGelistirici(Agent):
    """
    Yenilenebilir Enerji Proje Geliştirici - NPV analizi ile karar verir.
    
    Referanslar:
    - Brealey et al. (2020). Principles of Corporate Finance
    - [cite:  IRENA 2024] Yenilenebilir enerji maliyetleri
    """
    
    def __init__(self, model):
        super().__init__(model)
        self.ajan_tipi = "ProjeGelistirici"
        self.sermaye = np.random.uniform(10e6, 100e6)  # Milyon $
        self.risk_primi = np.random.uniform(0.08, 0.15)
        self.projeler = []
        self.toplam_kapasite = 0  # MW
        
    def step(self):
        """Her yıl için yatırım kararı."""
        karbon_fiyati = self.model.karbon_fiyati
        tesvik = self.model.tesvik_miktari
        
        proje_tipleri = {
            "GES": {"kapasite": 10, "yatirim": 7e5, "kf": 0.18, "omur": 25},  # MW, $/MW, kapasite faktörü, yıl
            "RES": {"kapasite": 20, "yatirim": 1.2e6, "kf": 0.35, "omur": 25}
        }
        
        for proje_tipi, params in proje_tipleri. items():
            toplam_yatirim = params["kapasite"] * params["yatirim"]  # $
            
            if self.sermaye >= toplam_yatirim:
                npv = self._npv_hesapla(params, karbon_fiyati, tesvik)
                
                if npv > 0:
                    self.sermaye -= toplam_yatirim
                    self.toplam_kapasite += params["kapasite"]
                    self.model.yenilenebilir_kapasite += params["kapasite"]
                    self.projeler.append({
                        "tip": proje_tipi,
                        "kapasite": params["kapasite"],
                        "yil": self.model.yil
                    })
    
    def _npv_hesapla(self, params, karbon_fiyati, tesvik):
        """Net Bugünkü Değer hesaplar."""
        kapasite = params["kapasite"]
        yatirim = kapasite * params["yatirim"]
        kf = params["kf"]
        omur = params["omur"]
        
        yillik_uretim = kapasite * kf * 8760  # MWh/yıl
        enerji_fiyati = 80  # $/MWh
        enerji_geliri = yillik_uretim * enerji_fiyati
        karbon_geliri = yillik_uretim * 0.5 * karbon_fiyati  # 0.5 ton CO₂/MWh kaçınılmış
        tesvik_geliri = tesvik * kapasite
        
        yillik_gelir = enerji_geliri + karbon_geliri + tesvik_geliri
        
        npv = -yatirim
        for t in range(1, omur + 1):
            npv += yillik_gelir / ((1 + self.risk_primi) ** t)
        
        return npv


# =============================================================================
# EKSİK AJANLAR - YENİ EKLENENLER (v2.2)
# =============================================================================
"""
Hocanın İstediği Eksik Ajanlar
==============================

Bu bölüm, değerlendirme raporunda eksik olarak belirtilen kritik ajan 
tiplerini içerir.

Referanslar:
------------
[7] Moran, D., et al. (2018). Carbon footprints of 13,000 cities. 
    Environmental Research Letters, 13(6), 064041.
    https://doi.org/10.1088/1748-9326/aac72a

[8] Labandeira, X., et al. (2017). A meta-analysis on the price 
    elasticity of energy demand. Energy Economics, 52, 408-425.
    https://doi.org/10.1016/j.eneco.2016.05.009

[9] IEA (2023). Global EV Outlook - Policy Trigger Analysis.
    https://www.iea.org/reports/global-ev-outlook-2023

[10] TEİAŞ (2024). Türkiye Elektrik İletim Sistemi 10 Yıllık Yatırım Planı.
     https://www.teias.gov.tr

[11] BDDK (2024). Türk Bankacılık Sektörü Temel Göstergeleri.
     https://www.bddk.org.tr
"""


class SebekeOperatoru(Agent):
    """
    Şebeke Operatörü (TSO/DSO) - Elektrik Dispatch ve Kapasite Yönetimi
    
    Bu ajan, elektrik şebekesinin işletilmesini, yenilenebilir enerji 
    entegrasyonunu ve bölgesel enerji akışlarını modeller.
    
    Temel Görevleri:
    ----------------
    1. Merit-order dispatch (düşük maliyetliden başlayarak santral sıralama)
    2. Yenilenebilir enerji entegrasyonu ve curtailment (kesinti) hesabı
    3. Bölgesel iletim kapasitesi kısıtları
    4. Peak load yönetimi
    
    Referanslar:
    ------------
    - [cite: TEİAŞ 2024] Türkiye elektrik iletim kapasitesi verileri
    - [cite: EPDK 2024] Elektrik piyasası düzenlemeleri
    
    Formüller:
    ----------
    1. Merit-Order Dispatch:
       dispatch_order = sorted(generators, key=lambda x: x.marginal_cost)
       
    2. Yenilenebilir Curtailment:
       curtailment = max(0, renewable_gen - (demand - must_run_gen))
       
    3. Emisyon Faktörü (Grid):
       grid_ef = Σ(gen_i × ef_i) / Σ(gen_i)
    
    Parametreler:
    -------------
    model : TurkiyeETSModel
        Ana model nesnesi
    bolge : str, optional
        Bölge adı (varsayılan: "Ulusal")
    """
    
    def __init__(self, model, bolge="Ulusal"):
        """
        Şebeke operatörü başlatıcı.
        
        Kaynak: TEİAŞ 10 Yıllık Yatırım Planı (2024)
        """
        super().__init__(model)
        self.ajan_tipi = "SebekeOperatoru"
        self.bolge = bolge
        
        # ===================================================================
        # KAPASİTE PARAMETRELERİ (TEİAŞ 2024 verileri)
        # ===================================================================
        # Kaynak: TEİAŞ Türkiye Elektrik Enerjisi 10 Yıllık Üretim Kapasite
        # Projeksiyonu (2024-2033)
        
        self.iletim_kapasitesi = 60000  # MW (Türkiye toplam kurulu güç ~105 GW)
        self.peak_talep = 55000         # MW (2024 peak: ~54.8 GW)
        self.yenilenebilir_kapasite = 0  # MW (model tarafından güncellenecek)
        
        # Bölgesel kapasite dağılımı (tahmini)
        self.bolgesel_kapasite = {
            "Marmara": 0.35,      # Türkiye'nin %35'i
            "İç Anadolu": 0.15,
            "Ege": 0.15,
            "Akdeniz": 0.12,
            "Karadeniz": 0.08,
            "Doğu Anadolu": 0.08,
            "Güneydoğu": 0.07
        }
        
        # ===================================================================
        # SANTRAL TİPLERİ VE MARJİNAL MALİYETLER
        # ===================================================================
        # Kaynak: EPDK Elektrik Piyasası Sektör Raporu (2024)
        # NOT: Marjinal maliyetler yakıt fiyatlarına göre değişir
        
        self.santral_tipleri = {
            "nukleer": {"kapasite_mw": 0, "marginal_cost": 15, "ef": 0},
            "hidroelektrik": {"kapasite_mw": 32000, "marginal_cost": 0, "ef": 0},
            "ruzgar": {"kapasite_mw": 12000, "marginal_cost": 0, "ef": 0},
            "gunes": {"kapasite_mw": 11000, "marginal_cost": 0, "ef": 0},
            "dogalgaz": {"kapasite_mw": 26000, "marginal_cost": 65, "ef": 0.40},  # tCO₂/MWh
            "linyit": {"kapasite_mw": 10000, "marginal_cost": 35, "ef": 1.10},
            "ithal_komur": {"kapasite_mw": 8000, "marginal_cost": 45, "ef": 0.85}
        }
        
        # Çıktı değişkenleri
        self.grid_emisyon_faktoru = 0.442  # tCO₂/MWh (Türkiye ortalaması)
        self.curtailment = 0               # MW (kesilen yenilenebilir)
        self.toplam_uretim = 0             # MWh/yıl
        self.durum = "Aktif"
    
    def step(self):
        """
        Şebeke operatörü yıllık adım fonksiyonu.
        
        Adımlar:
        --------
        1. Yenilenebilir kapasite güncelleme (modelden)
        2. Merit-order dispatch hesaplama
        3. Grid emisyon faktörü güncelleme
        4. Curtailment hesaplama
        """
        if self.durum != "Aktif":
            return
        
        # 1. Yenilenebilir kapasite güncelleme
        self.santral_tipleri["ruzgar"]["kapasite_mw"] = 12000 + self.model.yenilenebilir_kapasite * 0.6
        self.santral_tipleri["gunes"]["kapasite_mw"] = 11000 + self.model.yenilenebilir_kapasite * 0.4
        
        # 2. Merit-order dispatch (basitleştirilmiş)
        # Önce yenilenebilirler, sonra düşük maliyetliler
        dispatch = self._merit_order_dispatch()
        
        # 3. Grid emisyon faktörü güncelleme
        self.grid_emisyon_faktoru = self._calculate_grid_ef(dispatch)
        
        # 4. Model emisyon faktörünü güncelle
        self.model.EMISYON_FAKTORU_TR = self.grid_emisyon_faktoru
    
    def _merit_order_dispatch(self):
        """
        Merit-order sıralamasına göre santral dispatch.
        
        Açıklama:
        ---------
        Elektrik piyasasında santraller marjinal maliyetlerine göre
        sıralanır ve talep karşılanana kadar devreye alınır.
        
        Sıralama:
        1. Yenilenebilir (maliyet = 0)
        2. Nükleer (maliyet ≈ 15 $/MWh)
        3. Linyit (maliyet ≈ 35 $/MWh)
        4. İthal kömür (maliyet ≈ 45 $/MWh)
        5. Doğalgaz (maliyet ≈ 65 $/MWh)
        
        Returns:
        --------
        dict : Her santral tipinin üretim miktarı (MWh)
        """
        talep = self.peak_talep * 8760 * 0.6  # Yıllık enerji (kapasite faktörü ~60%)
        dispatch = {}
        kalan_talep = talep
        
        # Maliyet sırasına göre sırala
        sirali_santraller = sorted(
            self.santral_tipleri.items(),
            key=lambda x: x[1]["marginal_cost"]
        )
        
        for santral_adi, params in sirali_santraller:
            if kalan_talep <= 0:
                dispatch[santral_adi] = 0
                continue
            
            # Kapasite faktörü (yenilenebilirler için düşük)
            if santral_adi in ["ruzgar", "gunes"]:
                cf = 0.25  # Yenilenebilir kapasite faktörü
            elif santral_adi == "hidroelektrik":
                cf = 0.35
            else:
                cf = 0.80  # Termik kapasite faktörü
            
            maks_uretim = params["kapasite_mw"] * 8760 * cf
            uretim = min(maks_uretim, kalan_talep)
            
            dispatch[santral_adi] = uretim
            kalan_talep -= uretim
        
        self.toplam_uretim = sum(dispatch.values())
        return dispatch
    
    def _calculate_grid_ef(self, dispatch):
        """
        Şebeke ortalama emisyon faktörünü hesaplar.
        
        Formül:
        -------
        Grid EF = Σ(üretim_i × ef_i) / Σ(üretim_i)
        
        Returns:
        --------
        float : Grid emisyon faktörü (tCO₂/MWh)
        """
        toplam_emisyon = 0
        toplam_uretim = 0
        
        for santral_adi, uretim in dispatch.items():
            ef = self.santral_tipleri[santral_adi]["ef"]
            toplam_emisyon += uretim * ef
            toplam_uretim += uretim
        
        if toplam_uretim > 0:
            return toplam_emisyon / toplam_uretim
        return 0.442  # Varsayılan


class FinansKurumu(Agent):
    """
    Finans Kurumu / Banka - Proje Finansmanı ve Kredi Yönetimi
    
    Bu ajan, yeşil yatırımların finansmanını, kredi onaylarını ve
    risk değerlendirmesini modeller. Proje Geliştiriciler bu ajandan
    kredi alarak yatırım yapar.
    
    Temel Görevleri:
    ----------------
    1. Proje kredi başvurularını değerlendirme
    2. Risk bazlı faiz oranı belirleme
    3. Yeşil tahvil ihraç etme (green bonds)
    4. Likidite yönetimi
    
    Referanslar:
    ------------
    - [cite: BDDK 2024] Türk bankacılık sektörü göstergeleri
    - [cite: TBB 2024] Sürdürülebilir bankacılık kriterleri
    
    Formüller:
    ----------
    1. Kredi Onay Skoru:
       score = (project_npv / loan_amount) * credit_rating * collateral_ratio
       
    2. Faiz Oranı (Risk Bazlı):
       rate = base_rate + risk_premium + green_discount
       
    3. Varsayılan Kayıp (Expected Loss):
       EL = PD × LGD × EAD
    
    Parametreler:
    -------------
    model : TurkiyeETSModel
        Ana model nesnesi
    banka_tipi : str, optional
        "kamu", "ozel", "kalkinma" (varsayılan: "ozel")
    """
    
    def __init__(self, model, banka_tipi="ozel"):
        """
        Finans kurumu başlatıcı.
        
        Kaynak: BDDK Türk Bankacılık Sektörü Temel Göstergeleri (2024)
        """
        super().__init__(model)
        self.ajan_tipi = "FinansKurumu"
        self.banka_tipi = banka_tipi
        
        # ===================================================================
        # FİNANSAL PARAMETRELER (BDDK 2024 verileri)
        # ===================================================================
        
        # Banka tiplerine göre özellikler
        banka_profilleri = {
            "kamu": {
                "likidite": 50e9,        # 50 Milyar TL
                "risk_istahi": 0.6,      # Orta risk
                "baz_faiz": 0.35,        # %35 (yüksek enflasyon ortamı)
                "yesil_indirim": 0.05,   # Yeşil projeler için %5 indirim
                "kredi_limiti": 10e9     # Proje başına maks 10 Milyar TL
            },
            "ozel": {
                "likidite": 30e9,
                "risk_istahi": 0.4,
                "baz_faiz": 0.40,
                "yesil_indirim": 0.03,
                "kredi_limiti": 5e9
            },
            "kalkinma": {
                "likidite": 100e9,       # Kalkınma bankaları daha büyük
                "risk_istahi": 0.7,      # Daha yüksek risk toleransı
                "baz_faiz": 0.25,        # Daha düşük faiz
                "yesil_indirim": 0.10,   # Yeşil projeler için %10 indirim
                "kredi_limiti": 20e9
            }
        }
        
        profil = banka_profilleri.get(banka_tipi, banka_profilleri["ozel"])
        
        self.likidite = profil["likidite"]           # TL
        self.risk_istahi = profil["risk_istahi"]     # 0-1 arası
        self.baz_faiz = profil["baz_faiz"]           # Yıllık oran
        self.yesil_indirim = profil["yesil_indirim"]
        self.kredi_limiti = profil["kredi_limiti"]
        
        # Kredi portföyü takibi
        self.aktif_krediler = []                     # Onaylanan krediler listesi
        self.toplam_kredi_hacmi = 0                  # TL
        self.npl_orani = 0.02                        # Takipteki kredi oranı (%2)
        
        self.durum = "Aktif"
    
    def step(self):
        """
        Finans kurumu yıllık adım fonksiyonu.
        
        Adımlar:
        --------
        1. Mevcut kredilerin takibi (geri ödeme, temerrüt)
        2. Likidite güncelleme
        3. Risk parametreleri güncelleme
        """
        if self.durum != "Aktif":
            return
        
        # Yıllık kredi geri ödemeleri (basitleştirilmiş)
        for kredi in self.aktif_krediler:
            if kredi["kalan_vade"] > 0:
                yillik_odeme = kredi["tutar"] / kredi["vade"]
                self.likidite += yillik_odeme * (1 + kredi["faiz"])
                kredi["kalan_vade"] -= 1
        
        # Kapanan kredileri listeden çıkar
        self.aktif_krediler = [k for k in self.aktif_krediler if k["kalan_vade"] > 0]
        
        # NPL oranı güncelleme (karbon fiyatı arttıkça riskli sektörlerde artabilir)
        if self.model.karbon_fiyati > 50:
            self.npl_orani = min(0.10, self.npl_orani + 0.005)
    
    def kredi_basvurusu_degerlendir(self, proje_tipi, tutar, proje_npv, vade=10):
        """
        Kredi başvurusunu değerlendirir ve onaylar/reddeder.
        
        Parametreler:
        -------------
        proje_tipi : str
            "yenilenebilir", "enerji_verimliligi", "temiz_teknoloji" vb.
        tutar : float
            İstenen kredi tutarı (TL)
        proje_npv : float
            Projenin Net Bugünkü Değeri (TL)
        vade : int
            Kredi vadesi (yıl)
        
        Returns:
        --------
        dict : {"onay": bool, "faiz": float, "tutar": float}
        """
        # Kredi skoru hesaplama
        if tutar > 0:
            npv_orani = proje_npv / tutar
        else:
            npv_orani = 0
        
        kredi_skoru = npv_orani * self.risk_istahi * 100
        
        # Yeşil proje kontrolü
        yesil_projeler = ["yenilenebilir", "enerji_verimliligi", "temiz_teknoloji", "ev_sarj"]
        yesil_mi = proje_tipi.lower() in yesil_projeler
        
        # Faiz hesaplama
        if yesil_mi:
            faiz = self.baz_faiz - self.yesil_indirim
        else:
            faiz = self.baz_faiz
        
        # Risk primi ekleme
        if kredi_skoru < 50:
            faiz += 0.05  # Düşük skorlu projeler için +%5
        
        # Onay koşulları
        onay = (
            kredi_skoru >= 30 and
            tutar <= self.kredi_limiti and
            tutar <= self.likidite * 0.1 and  # Tek kredi likiditenin %10'unu geçemez
            proje_npv > 0
        )
        
        if onay:
            # Krediyi portföye ekle
            self.aktif_krediler.append({
                "proje_tipi": proje_tipi,
                "tutar": tutar,
                "faiz": faiz,
                "vade": vade,
                "kalan_vade": vade
            })
            self.likidite -= tutar
            self.toplam_kredi_hacmi += tutar
        
        return {
            "onay": onay,
            "faiz": faiz if onay else None,
            "tutar": tutar if onay else 0,
            "kredi_skoru": kredi_skoru
        }


class Belediye(Agent):
    """
    Belediye / Yerel Yönetim - Bölgesel İklim Politikaları
    
    Bu ajan, il/belediye düzeyinde iklim politikalarını, toplu taşıma
    yatırımlarını ve yerel teşvikleri modeller.
    
    Temel Görevleri:
    ----------------
    1. Toplu taşıma kapasitesi yatırımları (metro, otobüs, tramvay)
    2. Yerel karbon vergisi / teşvik uygulamaları
    3. Bina enerji verimliliği programları
    4. Yeşil alan ve orman projeleri (karbon yutak)
    
    Referanslar:
    ------------
    - [cite: Moran et al. 2018] Şehir bazlı karbon ayak izi
    - [cite: ICLEI 2024] Yerel yönetimler iklim eylem rehberi
    
    Formüller:
    ----------
    1. Toplu Taşıma Modal Shift:
       modal_shift = transit_capacity / (transit_capacity + car_capacity)
       
    2. Bina Enerji Tasarrufu:
       savings = retrofit_rate × building_stock × avg_savings_per_building
       
    3. Yerel Karbon Yutak:
       sink = forest_area × carbon_sink_rate
    
    Parametreler:
    -------------
    model : TurkiyeETSModel
        Ana model nesnesi
    city : str
        Şehir adı
    """
    
    def __init__(self, model, city):
        """
        Belediye başlatıcı.
        
        Kaynak: TÜİK Belediye İstatistikleri, İBB/ABB Faaliyet Raporları
        """
        super().__init__(model)
        self.ajan_tipi = "Belediye"
        self.city = city
        
        # ===================================================================
        # BELEDİYE PROFİLLERİ (Büyükşehir vs Diğer)
        # ===================================================================
        # Kaynak: TÜİK Belediye Bütçe İstatistikleri (2024)
        
        buyuksehirler = [
            "Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana",
            "Konya", "Gaziantep", "Kocaeli", "Mersin", "Kayseri", "Eskisehir"
        ]
        
        if city in buyuksehirler:
            self.belediye_tipi = "buyuksehir"
            self.butce = np.random.uniform(20e9, 100e9)  # 20-100 Milyar TL
            self.transit_capacity = np.random.uniform(0.2, 0.4)  # %20-40 modal share
            self.yesil_alan_orani = np.random.uniform(0.05, 0.15)  # %5-15
        else:
            self.belediye_tipi = "standart"
            self.butce = np.random.uniform(1e9, 10e9)   # 1-10 Milyar TL
            self.transit_capacity = np.random.uniform(0.05, 0.15)
            self.yesil_alan_orani = np.random.uniform(0.02, 0.08)
        
        # ===================================================================
        # İKLİM POLİTİKALARI
        # ===================================================================
        
        self.iklim_butcesi = self.butce * 0.03  # Bütçenin %3'ü iklim için
        self.yerel_tesvik = 0                    # TL/ton CO₂ (yerel teşvik)
        self.bina_retrofit_orani = 0.01          # Yıllık %1 bina yenileme
        
        # Politika çıktıları
        self.yillik_emisyon_azaltimi = 0         # tCO₂/yıl
        self.transit_yatirim_toplam = 0          # TL
        
        self.durum = "Aktif"
    
    def step(self):
        """
        Belediye yıllık adım fonksiyonu.
        
        Adımlar:
        --------
        1. Toplu taşıma yatırım kararı
        2. Bina enerji verimliliği programı
        3. Karbon fiyatına göre yerel politika güncelleme
        """
        if self.durum != "Aktif":
            return
        
        karbon_fiyati = self.model.karbon_fiyati
        
        # 1. Toplu taşıma yatırımı (karbon fiyatı arttıkça daha fazla)
        if karbon_fiyati > 30:
            yatirim_orani = min(0.5, 0.1 + (karbon_fiyati - 30) * 0.01)
            yatirim = self.iklim_butcesi * yatirim_orani
            
            # Her 1 Milyar TL yatırım → %0.5 transit kapasite artışı
            kapasite_artisi = (yatirim / 1e9) * 0.005
            self.transit_capacity = min(0.6, self.transit_capacity + kapasite_artisi)
            self.transit_yatirim_toplam += yatirim
        
        # 2. Bina retrofit programı
        # Her %1 retrofit → ~0.5% şehir emisyon azalımı
        self.yillik_emisyon_azaltimi = self.bina_retrofit_orani * 0.005  # Oran olarak
        
        # 3. Yerel teşvik güncelleme (merkezi karbon fiyatını desteklemek için)
        if karbon_fiyati > 50:
            self.yerel_tesvik = 5  # 5 TL/ton yerel teşvik
        elif karbon_fiyati > 30:
            self.yerel_tesvik = 2
        else:
            self.yerel_tesvik = 0
    
    def get_modal_shift_impact(self):
        """
        Toplu taşıma yatırımlarının otomobil kullanımına etkisini hesaplar.
        
        Returns:
        --------
        float : Otomobil kullanımındaki azalma oranı (0-1)
        """
        # Her %10 transit kapasite → %2 otomobil azalımı
        return self.transit_capacity * 0.2


# =============================================================================
# EKONOMİK ETKİ MODÜLÜ (YENİ)
# =============================================================================
"""
Ekonomik Etki Modülü
====================

Hocanın istediği: "Ekonomik etki / makro modül — basit input-output veya 
CGE benzeri etki modellemesi (GDP ve istihdam etkileri için)"

Bu modül, karbon fiyatlandırmasının makroekonomik etkilerini hesaplar.

Metodoloji:
-----------
Basitleştirilmiş Input-Output (I/O) modeli kullanılmaktadır. 

Referanslar:
------------
[12] Leontief, W. (1986). Input-Output Economics. Oxford University Press.
[13] Miller, R.E., & Blair, P.D. (2009). Input-Output Analysis. Cambridge.
[14] TÜİK (2022). Türkiye Girdi-Çıktı Tabloları.
"""


class EkonomikEtkiModulu:
    """
    Input-Output Ekonomik Etki Modeli (v4.5)
    
    Bu modül, ETS politikalarının GDP ve istihdam üzerindeki 
    etkilerini hesaplar.
    
    Metodoloji:
    -----------
    Basitleştirilmiş Input-Output (I/O) modeli kullanılmaktadır.
    
    Referanslar:
    ------------
    [12] Leontief, W. (1986). Input-Output Economics. Oxford University Press.
    [13] Miller, R.E., & Blair, P.D. (2009). Input-Output Analysis. Cambridge.
    [14] TÜİK (2022). Türkiye Girdi-Çıktı Tabloları.
    """
    
    def __init__(self, model):
        """
        Ekonomik etki modülü başlatıcı.
        """
        self.model = model
        self.gdp_etkisi = 0
        self.istihdam_etkisi = 0
        self.karbon_maliyeti = 0
        self.net_refah_etkisi = 0
        
        # Türkiye bazı ekonomik parametreler [Kaynak: TÜİK 2024]
        self.baz_gdp = 1.1e12  # Trilyon USD (~1.1 trilyon)
        
        # Sektörel çarpanlar (TÜİK I-O tablosundan türetilmiş)
        self.sektor_carpanlari = {
            "Enerji": {"output_multiplier": 1.8, "employment_ratio": 0.08, "carbon_intensity": 800},
            "Sanayi": {"output_multiplier": 2.1, "employment_ratio": 0.12, "carbon_intensity": 400},
            "Tarim": {"output_multiplier": 1.5, "employment_ratio": 0.25, "carbon_intensity": 50},
            "Ulasim": {"output_multiplier": 1.7, "employment_ratio": 0.10, "carbon_intensity": 150},
            "Hizmetler": {"output_multiplier": 1.4, "employment_ratio": 0.18, "carbon_intensity": 15}
        }
        
        # Yeni I-O Modeli Entegrasyonu
        if MODULES_AVAILABLE:
            self.io_model = InputOutputModel()
        else:
            self.io_model = None
    
    def hesapla_yillik_etki(self):
        """
        Yıllık ekonomik etkileri hesaplar.
        
        Bu fonksiyon, modeldeki yatırımları ve karbon maliyetlerini
        analiz ederek GDP ve istihdam etkilerini hesaplar.
        
        Returns:
        --------
        dict: GDP etkisi, istihdam etkisi, karbon maliyeti
        """
        # I-O modeli varsa onu kullan
        if self.io_model is not None:
            return self._hesapla_io_model_ile()
        
        # Yoksa basit hesaplama yap
        return self._hesapla_basit()
    
    def _hesapla_io_model_ile(self):
        """
        I-O modeli kullanarak ekonomik etkileri hesaplar.
        """
        # 1. Yatırım toplamlarını hesapla
        toplam_yatirim = sum([
            getattr(a, 'yatirim_bedeli', 0) for a in self.model.agents
            if hasattr(a, 'durum') and a.durum == "Donusum"
        ])
        
        # 2. Sektörel yatırım dağılımı
        sektor_yatirim = {
            "Enerji": toplam_yatirim * 0.5,
            "Sanayi": toplam_yatirim * 0.3,
            "Hizmetler": toplam_yatirim * 0.2
        }
        
        # 3. I-O modeli ile yeşil yatırım etkisi hesapla
        yesil_etki = self.io_model.yesil_yatirim_etkisi(
            yatirim_milyon_tl=toplam_yatirim * 30  # USD → TL (kur: 30)
        )
        
        # 4. GDP etkisi (TL → USD)
        gdp_etkisi = yesil_etki['toplam_uretim_etkisi'] / 30
        istihdam_etkisi = yesil_etki['toplam_istihdam_yaratilan']
        
        # 5. Karbon maliyeti (negatif etki)
        toplam_emisyon = sum([
            a.emisyon for a in self.model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi in ["Tesis", "IhracatciTesis"]
            and getattr(a, 'durum', 'Aktif') != "Kapali"
        ])
        karbon_maliyeti = toplam_emisyon * self.model.karbon_fiyati * 1e6  # Mt × $/ton → USD
        
        # 6. Net refah etkisi
        net_etki = gdp_etkisi - karbon_maliyeti
        
        # Sonuçları kaydet
        self.gdp_etkisi = gdp_etkisi
        self.istihdam_etkisi = istihdam_etkisi
        self.karbon_maliyeti = karbon_maliyeti
        self.net_refah_etkisi = net_etki
        
        return {
            "gdp_etkisi_usd": gdp_etkisi,
            "gdp_etkisi_oran": (gdp_etkisi / self.baz_gdp) * 100,
            "istihdam_etkisi_kisi": istihdam_etkisi,
            "karbon_maliyeti_usd": karbon_maliyeti,
            "net_refah_etkisi_usd": net_etki
        }
    
    def _hesapla_basit(self):
        """
        I-O modeli olmadan basit ekonomik etki hesabı.
        """
        gdp_etkisi = 0
        istihdam_etkisi = 0
        
        # 1. Sektörel yatırımları topla
        for sektor, params in self.sektor_carpanlari.items():
            # Sektördeki yatırımlar
            sektor_yatirim = sum([
                getattr(a, 'yatirim_bedeli', 0) for a in self.model.agents
                if hasattr(a, 'sektor') and a.sektor == sektor
                and hasattr(a, 'durum') and a.durum == "Donusum"
            ])
            
            if sektor_yatirim == 0:
                sektor_yatirim = sum([
                    getattr(a, 'yatirim_bedeli', 0) for a in self.model.agents
                    if hasattr(a, 'durum') and a.durum == "Donusum"
                ]) * 0.05  # Varsayılan pay
            
            # GDP etkisi (çarpan ile)
            sektor_gdp = sektor_yatirim * params["output_multiplier"] * 1e6  # Milyon $ → $
            gdp_etkisi += sektor_gdp
            
            # İstihdam etkisi
            sektor_istihdam = sektor_gdp * params["employment_ratio"] / 1e6  # Kişi
            istihdam_etkisi += sektor_istihdam
        
        # 2. Karbon maliyeti (negatif etki)
        toplam_emisyon = sum([
            a.emisyon for a in self.model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi in ["Tesis", "IhracatciTesis"]
            and getattr(a, 'durum', 'Aktif') != "Kapali"
        ])
        karbon_maliyeti = toplam_emisyon * self.model.karbon_fiyati * 1e6
        
        # 3. Net refah etkisi
        net_etki = gdp_etkisi - karbon_maliyeti
        
        # Sonuçları kaydet
        self.gdp_etkisi = gdp_etkisi
        self.istihdam_etkisi = istihdam_etkisi
        self.karbon_maliyeti = karbon_maliyeti
        self.net_refah_etkisi = net_etki
        
        return {
            "gdp_etkisi_usd": gdp_etkisi,
            "gdp_etkisi_oran": (gdp_etkisi / self.baz_gdp) * 100,
            "istihdam_etkisi_kisi": istihdam_etkisi,
            "karbon_maliyeti_usd": karbon_maliyeti,
            "net_refah_etkisi_usd": net_etki
        }
    
    def hesapla_sektorel_dagilim(self):
        """
        Sektörel etki dağılımını hesaplar.
        
        Returns:
        --------
        pd.DataFrame : Sektör bazlı GDP ve istihdam etkileri
        """
        sonuclar = []
        
        for sektor, params in self.sektor_carpanlari.items():
            sonuclar.append({
                "Sektor": sektor,
                "GDP_Carpani": params["output_multiplier"],
                "Istihdam_Orani": params["employment_ratio"],
                "Karbon_Yogunlugu": params["carbon_intensity"]
            })
        
        return pd.DataFrame(sonuclar)


# =============================================================================
# MONTE CARLO BELİRSİZLİK ANALİZİ (YENİ)
# =============================================================================
"""
Monte Carlo Belirsizlik Analizi
===============================

Hocanın istediği: "Belirsizlik ve risk modülü — Monte Carlo senaryoları, 
parametre belirsizliği"

Bu modül, model parametrelerindeki belirsizliği analiz eder.

Metodoloji:
-----------
Latin Hypercube Sampling (LHS) kullanarak parametre uzayını tarar ve
sonuçların dağılımını analiz eder.

Referanslar:
------------
[15] Saltelli, A., et al. (2008). Global Sensitivity Analysis. Wiley.
[16] McKay, M.D., et al. (1979). A comparison of three methods for 
     selecting values of input variables. Technometrics, 21(2), 239-245.
"""


def monte_carlo_analizi(n_runs=100, seed=42):
    """
    Monte Carlo belirsizlik analizi gerçekleştirir.
    
    Bu fonksiyon, model parametrelerini rastgele değiştirerek
    sonuçların belirsizlik aralığını hesaplar.
    
    Parametreler:
    -------------
    n_runs : int
        Monte Carlo iterasyon sayısı (varsayılan: 100)
    seed : int
        Rastgele sayı üreteci seed'i (tekrarlanabilirlik için)
    
    Değiştirilen Parametreler:
    --------------------------
    1. cap_azalma_orani: U(0.02, 0.05) - Yıllık tavan azalma oranı
    2. ab_skdm_fiyat: U(60, 120) - AB SKDM fiyatı ($/ton)
    3. tesvik_miktari: U(30000, 100000) - Yenilenebilir teşviği ($/MW)
    4. baslangic_cap: U(70, 90) - Başlangıç emisyon tavanı (Mt)
    
    Returns:
    --------
    tuple : (df_results, percentiles, uncertainty_stats)
        - df_results: Tüm iterasyonların sonuçları
        - percentiles: 5., 50., 95. yüzdelikler
        - uncertainty_stats: Ortalama ve standart sapma
    
    Örnek Kullanım:
    ---------------
    >>> results, percentiles, stats = monte_carlo_analizi(n_runs=100)
    >>> print(f"2035 Emisyon: {percentiles.loc[0.5, 'final_emission']:.1f} Mt")
    >>> print(f"Belirsizlik: [{percentiles.loc[0.05, 'final_emission']:.1f}, "
    ...       f"{percentiles.loc[0.95, 'final_emission']:.1f}] Mt")
    """
    np.random.seed(seed)
    random.seed(seed)
    
    results = []
    
    print(f"\n🎲 Monte Carlo Analizi Başlatılıyor ({n_runs} iterasyon)...")
    print("=" * 60)
    
    # =================================================================
    # LATIN HYPERCUBE SAMPLİNG (LHS) - McKay et al. (1979)
    # =================================================================
    # LHS, parametre uzayını daha verimli tarar ve daha az iterasyonla
    # daha iyi kapsama sağlar.
    #
    # Referans: McKay, M.D., Beckman, R.J., & Conover, W.J. (1979).
    # A comparison of three methods for selecting values of input 
    # variables in the analysis of output from a computer code.
    # Technometrics, 21(2), 239-245.
    # =================================================================
    
    # Parametre sınırları (7 boyutlu parametre uzayı)
    param_bounds = {
        'cap_azalma': (0.02, 0.05),      # Yıllık tavan azalma oranı
        'karbon_fiyati': (40, 150),      # $/tCO2
        'tesvik': (20000, 150000),       # $/MW
        'baslangic_cap': (70, 90),       # Mt
        'ekonomik_buyume': (0.02, 0.05), # %
        'teknoloji_maliyeti': (600000, 1200000),  # $/MW
        'yakit_fiyat_soku': (0.8, 1.5)   # Çarpan
    }
    
    n_params = len(param_bounds)
    
    # LHS örnekleme
    if LHS_AVAILABLE:
        print("   ✓ Latin Hypercube Sampling kullanılıyor")
        sampler = qmc.LatinHypercube(d=n_params, seed=seed)
        lhs_samples = sampler.random(n=n_runs)  # [0,1] aralığında
        
        # Parametre sınırlarına ölçekle
        l_bounds = [v[0] for v in param_bounds.values()]
        u_bounds = [v[1] for v in param_bounds.values()]
        scaled_samples = qmc.scale(lhs_samples, l_bounds, u_bounds)
    else:
        print("   ⚠️ LHS yok, rastgele uniform örnekleme kullanılıyor")
        # Fallback: Rastgele uniform örnekleme
        scaled_samples = np.column_stack([
            np.random.uniform(bounds[0], bounds[1], n_runs)
            for bounds in param_bounds.values()
        ])
    
    for run in range(n_runs):
        # LHS örneklerinden parametreleri al
        params = scaled_samples[run]
        cap_azalma = params[0]
        karbon_fiyati = params[1]
        tesvik = params[2]
        baslangic_cap = params[3]
        ekonomik_buyume = params[4]
        teknoloji_maliyeti = params[5]
        yakit_fiyat_soku = params[6]
        
        try:
            # Modeli oluştur ve çalıştır
            model = TurkiyeETSModel(
                n_enerji=20,      # Daha az ajan (hız için)
                n_sanayi=15,
                n_tarim=10,
                n_hanehalki=25,
                baslangic_cap=baslangic_cap,
                cap_azalma_orani=cap_azalma,
                ab_skdm_fiyat=karbon_fiyati,
                tesvik_miktari=tesvik,
                random_seed=run
            )
            
            # Parametre şoklarını uygula
            model.vergi_artis_orani *= (1 + ekonomik_buyume) # Büyüme emisyon artsını tetikler
            
            # 11 yıllık simülasyon (2025-2035)
            for _ in range(11):
                model.step()
            
            # Sonuçları topla
            df = model.datacollector.get_model_vars_dataframe()
            
            results.append({
                'run': run,
                'cap_azalma': cap_azalma,
                'karbon_fiyati': karbon_fiyati,
                'tesvik': tesvik,
                'ekonomik_buyume': ekonomik_buyume,
                'teknoloji_maliyeti': teknoloji_maliyeti,
                'yakit_fiyat_soku': yakit_fiyat_soku,
                'final_emission': df['Toplam_Emisyon'].iloc[-1],
                'final_price': df['Karbon_Fiyati'].iloc[-1],
                'temiz_tesis': df['Temiz_Tesis'].iloc[-1] if 'Temiz_Tesis' in df.columns else 0,
                'gdp_etkisi': df['GDP_Etkisi_USD'].iloc[-1] if 'GDP_Etkisi_USD' in df.columns else 0
            })

            
            # İlerleme göster
            if (run + 1) % 10 == 0:
                print(f"   ✓ {run + 1}/{n_runs} iterasyon tamamlandı")
                
        except Exception as e:
            print(f"   ⚠️ Run {run} hata: {str(e)[:50]}")
            continue
    
    # Sonuçları DataFrame'e dönüştür
    df_results = pd.DataFrame(results)
    
    if len(df_results) == 0:
        print("❌ Hiçbir iterasyon başarılı olmadı!")
        return None, None, None
    
    # Yüzdelikleri hesapla
    percentiles = df_results[['final_emission', 'final_price', 'temiz_tesis']].quantile([0.05, 0.5, 0.95])
    
    # İstatistikler
    uncertainty_stats = {
        'final_emission': {
            'mean': df_results['final_emission'].mean(),
            'std': df_results['final_emission'].std(),
            'min': df_results['final_emission'].min(),
            'max': df_results['final_emission'].max()
        },
        'final_price': {
            'mean': df_results['final_price'].mean(),
            'std': df_results['final_price'].std()
        }
    }
    
    # Sonuç özeti
    print("\n" + "=" * 60)
    print("📊 MONTE CARLO SONUÇ ÖZETİ")
    print("=" * 60)
    print(f"Toplam başarılı iterasyon: {len(df_results)}")
    print(f"\n2035 Emisyon Tahmini:")
    print(f"   Ortalama: {uncertainty_stats['final_emission']['mean']:.1f} Mt")
    print(f"   Std. Sapma: {uncertainty_stats['final_emission']['std']:.1f} Mt")
    print(f"   %90 Güven Aralığı: [{percentiles.loc[0.05, 'final_emission']:.1f}, "
          f"{percentiles.loc[0.95, 'final_emission']:.1f}] Mt")
    print(f"\n2035 Karbon Fiyatı:")
    print(f"   Ortalama: ${uncertainty_stats['final_price']['mean']:.1f}/ton")
    print(f"   %90 Güven Aralığı: [${percentiles.loc[0.05, 'final_price']:.1f}, "
          f"${percentiles.loc[0.95, 'final_price']:.1f}]/ton")
    
    return df_results, percentiles, uncertainty_stats


# =============================================================================
# İL BAZLI EMİSYON HESAPLAMA FONKSİYONU (YENİ)
# =============================================================================
"""
İl Bazlı Emisyon Takibi
=======================

Hocanın istediği: "İl bazlı çıktılar simülasyondan gelmiyor"

Bu fonksiyon, tüm illerin emisyonlarını hesaplayarak DataCollector'a 
aktarılabilir hale getirir.
"""


def il_bazli_emisyon_hesapla(model):
    """
    Tüm iller için emisyon değerlerini hesaplar.
    
    Bu fonksiyon, modeldeki tüm ajanların 'city' özelliğini kullanarak
    il bazlı emisyon toplamlarını hesaplar.
    
    Parametreler:
    -------------
    model : TurkiyeETSModel
        Ana model nesnesi
    
    Returns:
    --------
    dict : {il_adi: emisyon_mt} formatında sözlük
    
    Örnek:
    ------
    >>> il_emisyonlari = il_bazli_emisyon_hesapla(model)
    >>> print(il_emisyonlari["Istanbul"])  # İstanbul'un toplam emisyonu
    45.2
    """
    il_emisyonlari = {}
    
    for il in model.iller:
        il_emisyonlari[il] = sum([
            a.emisyon for a in model.agents
            if hasattr(a, 'city') and a.city == il 
            and hasattr(a, 'emisyon')  # Sadece emisyon özelliği olanlar
            and hasattr(a, 'durum') and a.durum != "Kapali"
        ])
    
    return il_emisyonlari


# =============================================================================
# ANA MODEL
# =============================================================================

class TurkiyeETSModel(Model):
    """
    Türkiye ETS Simülasyon Modeli - Düzeltilmiş ve Geliştirilmiş Versiyon
    
    Özellikler:
    -----------
    ✅ PiyasaOperatoru ve MRV agents listesinde
    ✅ Tahsisat ve bankalama mekanizması
    ✅ Ceza geri bildirimi tesislere aktarılıyor
    ✅ NPV hesabı MAC önemleriyle entegre
    ✅ İl bazlı tesis dağılımı
    ✅ 2025-2035 zaman çizelgesi
    
    Referanslar:
    - [cite: Yu et al. 2020] ABM metodolojisi
    - [cite: EU ETS] Cap & Trade kuralları
    """
    
    # Türkiye ortalama emisyon faktörü [Kaynak: Enerji Bakanlığı 2024]
    EMISYON_FAKTORU_TR = 0.442  # ton CO₂/MWh
    
    def __init__(self,
                 n_enerji=40,
                 n_sanayi=30,
                 n_tarim=30,
                 n_yatirimci=15,
                 n_ihracatci=10,
                 n_hanehalki=50,
                 baslangic_cap=80,  # Mt CO₂
                 cap_azalma_orani=0.03,
                 ab_skdm_fiyat=90,  # $/ton
                 tesvik_miktari=50000,  # $/MW
                 vergi_artis_orani=5,  # %
                 senaryo_tipi="Siki_ETS",
                 veritabani_kullan=False,
                 random_seed=None):
        """Model başlatıcı."""
        
        # Random seed
        if random_seed is None:
            random_seed = int(datetime.now().timestamp() * 1000) % 100000
        super().__init__(seed=random_seed)
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        # --- AI BASELINE KALİBRASYONU (V4.5) ---
        baseline = load_ai_baseline()
        if baseline:
            # AI tahmininden başlangıç değerlerini al
            suggested_cap = baseline['simulation_params']['suggested_ets_cap_2026']
            baslangic_cap = suggested_cap  # AI'nın önerdiği Cap ile başla
            print(f"✅ AI Baseline entegre edildi: Başlangıç Cap = {baslangic_cap:.1f} Mt")

        # --- TEMEL PARAMETRELER ---
        self.yil = 2025
        self.karbon_fiyati = 0  # $/ton
        self.ab_skdm_fiyat = ab_skdm_fiyat
        self.tesvik_miktari = tesvik_miktari
        self.vergi_artis_orani = vergi_artis_orani
        self.yenilenebilir_kapasite = 0  # MW
        
        # --- SENARYO YÖNETİMİ ---
        self.senaryo_tipi = senaryo_tipi
        self.rev_recycling = REVENUE_SCENARIOS.get(senaryo_tipi, REVENUE_SCENARIOS["BAU"])
        self.ets_aktif = False
        self.acik_artirma_aktif = False
        
        # --- VERİTABANI ENTEGRASYİYONU ---
        self.il_katsayilari = {}
        if veritabani_kullan: 
            self._veritabani_yukle()
        
        # --- MODÜL BAŞLATMA (V4.5) ---
        if MODULES_AVAILABLE:
            # Enerji Dispatch Modülü - Santraller veritabanından veya dummy
            import sqlite3
            try:
                conn = sqlite3.connect(DB_PATH)
                df_plants = pd.read_sql("SELECT * FROM tesisler", conn)
                conn.close()
            except:
                df_plants = pd.DataFrame([
                    {"Tesis_Adi": "Ornek_Santral", "Kapasite_MW": 1000, "Yakit_Tipi": "Linyit"}
                ])
            
            self.dispatch_modulu = EnerjiDispatchModulu(df_plants, karbon_fiyati=0)
            self.ekonomi_modulu = InputOutputModel()
            print("🚀 Dispatch ve Ekonomi modülleri başlatıldı.")
        else:
            self.dispatch_modulu = None
            self.ekonomi_modulu = None

        # --- İL LİSTESİ ---
        self.iller = list(self.il_katsayilari.keys()) if self.il_katsayilari else [
            "Istanbul", "Ankara", "Izmir", "Bursa", "Kocaeli", "Adana",
            "Gaziantep", "Konya", "Antalya", "Mersin", "Kayseri", "Eskisehir",
            "Sakarya", "Denizli", "Manisa", "Zonguldak", "Hatay", "Samsun"
        ]
        
        # --- 1. PİYASA OPERATÖRÜ (DÜZELTİLMİŞ) ---
        self.piyasa_operatoru = PiyasaOperatoru(self, baslangic_cap, cap_azalma_orani)
        self.agents.add(self.piyasa_operatoru)  # ✅ AGENTS LİSTESİNE EKLENDİ

        
        # --- 2. MRV MERKEZİ (DÜZELTİLMİŞ) ---
        self.mrv_merkezi = MRVAjani(self)
        self.agents.add(self.mrv_merkezi)  # ✅ AGENTS LİSTESİNE EKLENDİ
        
        # --- 3. TESİSLER (İl bazlı dağıtım) ---
        for _ in range(n_enerji):
            city = random.choice(self. iller)
            EndustriyelTesis(self, "Enerji", city=city)
        
        for _ in range(n_sanayi):
            city = random. choice(self.iller)
            EndustriyelTesis(self, "Sanayi", city=city)
        
        for _ in range(n_tarim):
            city = random.choice(self.iller)
            EndustriyelTesis(self, "Tarim", city=city)
        
        # --- 4. İHRACATÇI AJANLAR ---
        for _ in range(n_ihracatci):
            city = random.choice(self.iller)
            IhracatciAjani(self, "Sanayi", city=city)
        
        # --- 5. HANEHALKİ AJANLARI ---
        for _ in range(n_hanehalki):
            city = random.choice(self.iller)
            Hanehalki(self, city=city)

        # --- 5. 1 ULAŞIM AJANLARI (YENİ EKLENEN - v2.2) ---
        """
        Ulaşım Ajanları Oluşturma
        
        Referans: IEA Turkey Transport Modal Split (2023)
        - Her ulaşım modu için 1 temsili ajan
        - Gerçek dünyada sektör toplamını temsil eder
        
        Not: İleride her mod için çoklu ajan eklenebilir
             (örn.  3 karayolu ajanı:  yolcu/yük/toplu)
        """
        ulasim_tipleri = ['karayolu', 'havayolu', 'denizyolu']
        
        for tip in ulasim_tipleri:
            ulasim_ajani = UlasimAgent(
                self, 
                ulasim_tipi=tip,
                city="Ulusal"  # Başlangıçta ulusal seviye
            )
            self.agents.add(ulasim_ajani)
        
        print(f"✅ Ulaşım ajanları oluşturuldu: {len(ulasim_tipleri)} mod")
        
        # --- 6. YATIRIMCILAR ---
        for _ in range(n_yatirimci):
            ProjeGelistirici(self)
        
        # --- 7. YENİ AJANLAR (v2.2 Eklemeler) ---
        # Şebeke Operatörü (TSO)
        self.sebeke_operatoru = SebekeOperatoru(self, bolge="Ulusal")
        self.agents.add(self.sebeke_operatoru)
        print("✅ Şebeke Operatörü oluşturuldu")
        
        # Finans Kurumları (3 tip banka)
        self.finans_kurumlari = []
        for banka_tipi in ["kamu", "ozel", "kalkinma"]:
            banka = FinansKurumu(self, banka_tipi=banka_tipi)
            self.finans_kurumlari.append(banka)
            self.agents.add(banka)
        print(f"✅ Finans kurumları oluşturuldu: {len(self.finans_kurumlari)} banka")
        
        # Belediyeler (büyükşehirler)
        self.belediyeler = []
        buyuksehirler = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", 
                         "Adana", "Konya", "Gaziantep", "Kocaeli", "Mersin"]
        for city in buyuksehirler:
            belediye = Belediye(self, city=city)
            self.belediyeler.append(belediye)
            self.agents.add(belediye)
        print(f"✅ Belediyeler oluşturuldu: {len(self.belediyeler)} belediye")
        
        # Ekonomik Etki Modülü
        self.ekonomik_etki = EkonomikEtkiModulu(self)
        print("✅ Ekonomik Etki Modülü oluşturuldu")
        
        # --- VERİ TOPLAMA ---
        self.datacollector = DataCollector(
            model_reporters={
                "Yil": lambda m: m.yil,
                "Karbon_Fiyati": lambda m: m. karbon_fiyati,
                "Toplam_Emisyon": lambda m: self._toplam_emisyon(m),
                "Aktif_Tesis": lambda m: self._tesis_sayisi(m, "Aktif"),
                "Donusum_Tesis": lambda m: self._tesis_sayisi(m, "Donusum"),
                "Temiz_Tesis": lambda m:  self._tesis_sayisi(m, "Temiz"),
                "Kapali_Tesis": lambda m: self._tesis_sayisi(m, "Kapali"),
                "Yenilenebilir_Kapasite_MW": lambda m: m.yenilenebilir_kapasite,
                "Cap":  lambda m: m.piyasa_operatoru.cap,
                "Senaryo": lambda m: m. senaryo_tipi,
                "CBAM_Toplam_Maliyet": lambda m: self._cbam_toplam_maliyet(m),
                "MRV_Toplam_Ceza": lambda m: m.mrv_merkezi.toplam_ceza,
                "Ihracatci_Tesis": lambda m: self._ihracatci_sayisi(m),
                "Hanehalki_Sayisi": lambda m: self._hanehalki_sayisi(m),
                "Hanehalki_Emisyon": lambda m: self._hanehalki_emisyon(m),
                # Ulaşım Metrikleri (YENİ EKLENEN - v2.2)
                "Ulasim_Toplam_Emisyon": lambda m: sum([
                    a.get_emisyon() 
                    for a in m.agents 
                    if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Ulasim"
                ]),
                "Karayolu_EV_Penetrasyon": lambda m: (
                    [a.ev_pay for a in m.agents 
                     if hasattr(a, 'ulasim_tipi') and a.ulasim_tipi == 'karayolu'][0] 
                    if any(hasattr(a, 'ulasim_tipi') and a.ulasim_tipi == 'karayolu' 
                           for a in m.agents) 
                    else 0.0
                ),
                "Ulasim_Azaltim_Orani": lambda m: (
                    sum([a.get_azaltim_orani() for a in m.agents 
                         if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Ulasim"]) / 
                    max(1, sum([1 for a in m.agents 
                               if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Ulasim"]))
                ),
                # İl Bazlı Emisyonlar (YENİ - v2.2) - JSON formatında
                "Il_Emisyonlari_JSON": lambda m: __import__('json').dumps(
                    il_bazli_emisyon_hesapla(m)
                ),
                # İl bazlı toplam (hızlı erişim için)
                "Istanbul_Emisyon": lambda m: sum([
                    a.emisyon for a in m.agents
                    if hasattr(a, 'city') and a.city == "Istanbul"
                    and hasattr(a, 'emisyon') and getattr(a, 'durum', 'Aktif') != "Kapali"
                ]),
                "Ankara_Emisyon": lambda m: sum([
                    a.emisyon for a in m.agents
                    if hasattr(a, 'city') and a.city == "Ankara"
                    and hasattr(a, 'emisyon') and getattr(a, 'durum', 'Aktif') != "Kapali"
                ]),
                "Izmir_Emisyon": lambda m: sum([
                    a.emisyon for a in m.agents
                    if hasattr(a, 'city') and a.city == "Izmir"
                    and hasattr(a, 'emisyon') and getattr(a, 'durum', 'Aktif') != "Kapali"
                ]),
                # Grid Emisyon Faktörü (YENİ - v2.2)
                "Grid_Emisyon_Faktoru": lambda m: (
                    m.sebeke_operatoru.grid_emisyon_faktoru 
                    if hasattr(m, 'sebeke_operatoru') else 0.442
                ),
                # Ekonomik Etkiler (YENİ - v2.2)
                "GDP_Etkisi_USD": lambda m: (
                    m.ekonomik_etki.gdp_etkisi 
                    if hasattr(m, 'ekonomik_etki') else 0
                ),
                "Istihdam_Etkisi_Kisi": lambda m: (
                    m.ekonomik_etki.istihdam_etkisi 
                    if hasattr(m, 'ekonomik_etki') else 0
                ),
                # Belediye Toplam Transit Kapasitesi (YENİ - v2.2)
                "Ortalama_Transit_Kapasite": lambda m: (
                    sum([b.transit_capacity for b in m.belediyeler]) / len(m.belediyeler)
                    if hasattr(m, 'belediyeler') and len(m.belediyeler) > 0 else 0
                )
            }
        )
    
    def _veritabani_yukle(self):
        """SQLite veritabanından il katsayılarını yükler."""
        db_path = os.path.join(PROJECT_ROOT, "iklim_veritabani.sqlite")
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                df_il = pd.read_sql("SELECT * FROM il_katsayilari", conn)
                
                if not df_il.empty and 'Bolge' in df_il.columns:
                    for _, row in df_il.iterrows():
                        self.il_katsayilari[row['Bolge']] = {
                            'enerji': row.get('Enerji_Katsayisi', 1.0),
                            'sanayi': row.get('Sanayi_Katsayisi', 1.0),
                            'tarim': row.get('Tarim_Katsayisi', 1.0)
                        }
                
                conn.close()
                print(f"✅ Veritabanı yüklendi: {len(self.il_katsayilari)} bölge")
                
            except Exception as e: 
                print(f"⚠️ Veritabanı yüklenemedi: {e}")
    
    def _toplam_emisyon(self, model):
        """Toplam emisyonu hesaplar."""
        return sum(
            a.emisyon for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi in ["Tesis", "IhracatciTesis", "Hanehalki"] 
            and getattr(a, 'durum', 'Aktif') != "Kapali"
        )
    
    def _tesis_sayisi(self, model, durum):
        """Belirli durumdaki tesis sayısını hesaplar."""
        return sum(
            1 for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi in ["Tesis", "IhracatciTesis"] 
            and a.durum == durum
        )
    
    def _cbam_toplam_maliyet(self, model):
        """Toplam CBAM maliyetini hesaplar."""
        return sum(
            a.cbam_maliyeti for a in model.agents
            if hasattr(a, 'cbam_maliyeti')
        )
    
    def _ihracatci_sayisi(self, model):
        """İhracatçı tesis sayısını hesaplar."""
        return sum(
            1 for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "IhracatciTesis"
        )
    
    def _hanehalki_sayisi(self, model):
        """Hanehalkı ajan sayısını hesaplar."""
        return sum(
            1 for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Hanehalki"
        )
    
    def _hanehalki_emisyon(self, model):
        """Hanehalkı toplam emisyonunu hesaplar."""
        return sum(
            a.emisyon for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Hanehalki"
        )
    
    def step(self):
        """
        Model adımı (bir yıl) - Zaman Çizelgesi Mantığı. 
        
        2025-2035 Türkiye ETS Yol Haritası:
        - 2025: Hazırlık dönemi
        - 2026: Pilot ETS başlangıcı
        - 2028: Tam uygulama ve Açık Artırma
        - 2030: AB CBAM tam uygulama
        - 2035: Hedef yılı
        """
        
        # --- ZAMAN ÇİZELGESİ MANTIĞI ---
        
        # 2026: Pilot ETS Başlangıcı
        if self.yil == 2026:
            if not self.ets_aktif:
                self.ets_aktif = True
                print(f"📢 {self.yil}:  Pilot ETS Başlatıldı - Karbon Fiyatı: ${self.karbon_fiyati}/ton")
        
        # 2028: Tam Uygulama ve Açık Artırma
        elif self.yil == 2028:
            if not self.acik_artirma_aktif:
                self.acik_artirma_aktif = True
                print(f"📢 {self.yil}:  Tam Uygulama ve Açık Artırma (Auction) Devreye Girdi")
        
        # --- ENERJİ DİSPATCH GÜNCELLEME (V4.5) ---
        if self.dispatch_modulu:
            # Karbon fiyatını güncelle ve dispatch hesapla
            self.dispatch_modulu.karbon_fiyati = self.karbon_fiyati
            self.dispatch_modulu._hesapla_marjinal_maliyetler()
            self.dispatch_modulu._sirala_merit_order()
            
            # Yıllık emisyonu hesapla ve model emisyonuna yansıt (örnek entegrasyon)
            dispatch_sonuc = self.dispatch_modulu.hesapla_yillik_etki(self.dispatch_modulu.yillik_talep_twh * 1e6) \
                             if hasattr(self.dispatch_modulu, 'hesapla_yillik_etki') else self.dispatch_modulu.optimize_dispatch(self.dispatch_modulu.yillik_talep_twh * 1e6)
            
        # --- VERİ TOPLAMA ---
        self.datacollector.collect(self)
        
        # --- TÜM AJANLARI ÇALIŞTIR ---
        # Not: PiyasaOperatoru ve MRV artık agents listesinde, otomatik çağrılacak
        self.agents.shuffle_do("step")
        
        # --- EKONOMİK ETKİ HESABI (YENİ - v4.5) ---
        # Her yıl ekonomik etkileri güncelle
        if hasattr(self, 'ekonomik_etki'):
            self.ekonomik_etki.hesapla_yillik_etki()
        
        # --- YILI İLERLET ---
        self.yil += 1
    
    def run_simulation(self, years=11):
        """Simülasyonu çalıştırır."""
        for _ in range(years):
            self.step()
        return self.datacollector.get_model_vars_dataframe()


# =============================================================================
# SENARYO KARŞILAŞTIRMASI
# =============================================================================

def senaryo_karsilastirmasi():
    """Farklı politika senaryolarını karşılaştırır."""
    print("=" * 70)
    print("TR-ZERO:  AJAN TABANLI KARBON PİYASASI SİMÜLASYONU")
    print("v2.1 - Düzeltilmiş Versiyon")
    print("=" * 70)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 70)
    
    # Senaryolar (DÜZELTİLMİŞ CAP DEĞERLERİ)
    senaryolar = {
        "BAU": {
            "baslangic_cap": 9999,
            "cap_azalma_orani": 0,
            "tesvik_miktari": 0,
            "ab_skdm_fiyat": 0,
            "renk": "#94a3b8"
        },
        "Yumusak_ETS": {
            "baslangic_cap": 75,
            "cap_azalma_orani": 0.02,
            "tesvik_miktari": 30000,
            "ab_skdm_fiyat": 60,
            "renk": "#3b82f6"
        },
        "Siki_ETS": {
            "baslangic_cap":  60,
            "cap_azalma_orani": 0.04,
            "tesvik_miktari": 50000,
            "ab_skdm_fiyat": 90,
            "renk":  "#22c55e"
        },
        "ETS_Tesvik": {
            "baslangic_cap": 60,
            "cap_azalma_orani": 0.04,
            "tesvik_miktari": 150000,
            "ab_skdm_fiyat": 90,
            "renk": "#8b5cf6"
        }
    }
    
    sonuclar = {}
    
    for senaryo_adi, params in senaryolar.items():
        print(f"\n🔄 {senaryo_adi} senaryosu çalıştırılıyor...")
        
        model = TurkiyeETSModel(
            baslangic_cap=params["baslangic_cap"],
            cap_azalma_orani=params["cap_azalma_orani"],
            tesvik_miktari=params["tesvik_miktari"],
            ab_skdm_fiyat=params["ab_skdm_fiyat"]
        )
        
        df = model.run_simulation(years=11)
        df["Senaryo"] = senaryo_adi
        sonuclar[senaryo_adi] = df
        
        # Sonuç özeti
        son_emisyon = df['Toplam_Emisyon']. iloc[-1]
        son_fiyat = df['Karbon_Fiyati'].iloc[-1]
        temiz_tesis = df['Temiz_Tesis'].iloc[-1]
        
        print(f"   ✅ Tamamlandı:")
        print(f"      • 2035 Emisyon: {son_emisyon:.2f} Mt")
        print(f"      • Karbon Fiyatı:  ${son_fiyat:.0f}/ton")
        print(f"      • Temiz Tesis:  {temiz_tesis:.0f}")
    
    # Özet tablo
    _ozet_tablo_yazdir(sonuclar)
    
    return sonuclar


def _ozet_tablo_yazdir(sonuclar):
    """Özet tablo yazdırır."""
    print("\n" + "=" * 80)
    print("SENARYO KARŞILAŞTIRMA TABLOSU (2035)")
    print("=" * 80)
    print(f"{'Senaryo':<18} {'Emisyon (Mt)':<14} {'Azaltım (%)':<14} {'Fiyat ($/t)':<14} {'Temiz Tesis':<14}")
    print("-" * 80)
    
    bau_emisyon = sonuclar["BAU"]["Toplam_Emisyon"].iloc[-1]
    
    for senaryo_adi, df in sonuclar.items():
        emisyon = df["Toplam_Emisyon"].iloc[-1]
        azaltim = (bau_emisyon - emisyon) / bau_emisyon * 100 if bau_emisyon > 0 else 0
        fiyat = df["Karbon_Fiyati"].iloc[-1]
        temiz = df["Temiz_Tesis"].iloc[-1]
        
        print(f"{senaryo_adi:<18} {emisyon: <14.2f} {azaltim: <14.1f} {fiyat:<14.0f} {int(temiz):<14}")
    
    print("=" * 80)


# =============================================================================
# CSV KAYDETME
# =============================================================================

def csv_kaydet(sonuclar):
    """Dashboard'un beklediği formatta CSV'leri kaydeder."""
    isim_eslesme = {
        "BAU": "bau",
        "Yumusak_ETS": "yumusak_ets",
        "Siki_ETS":  "siki_ets",
        "ETS_Tesvik": "ets_tesvik"
    }
    
    for senaryo_adi, df in sonuclar.items():
        dosya_adi = isim_eslesme.get(senaryo_adi, senaryo_adi. lower())
        csv_path = os.path.join(OUTPUT_DIR, f"senaryo_{dosya_adi}.csv")
        df.to_csv(csv_path, index=False)
        print(f"   📄 {csv_path}")


# =============================================================================
# SENARYO KONFİGÜRASYONU (MERKEZİ - v4.5)
# =============================================================================
"""
Merkezi Senaryo Konfigürasyonu
==============================

Tüm senaryoların parametrelerini tek bir yerde yönetir.
Dashboard ve simülasyon arasında tutarlılık sağlar.
"""

SENARYO_KONFIG = {
    "BAU": {
        "aciklama": "Mevcut Politikalar (Business as Usual)",
        "baslangic_cap": 9999,      # Mt CO₂ (sınırsız)
        "cap_azalma_orani": 0.0,    # Yıllık azalma yok
        "tesvik_miktari": 0,        # $/MW
        "ab_skdm_fiyat": 0,         # $/ton
        "acik_artirma": False,
        "renk": "#94a3b8"
    },
    "Yumusak_ETS": {
        "aciklama": "Yumuşak ETS Geçişi",
        "baslangic_cap": 75,        # Mt CO₂
        "cap_azalma_orani": 0.021,  # %2.1/yıl (EU ETS Phase 4)
        "tesvik_miktari": 30000,    # $/MW
        "ab_skdm_fiyat": 60,        # $/ton
        "acik_artirma": False,
        "renk": "#3b82f6"
    },
    "Siki_ETS": {
        "aciklama": "Sıkı ETS Uygulaması",
        "baslangic_cap": 60,        # Mt CO₂
        "cap_azalma_orani": 0.04,   # %4/yıl
        "tesvik_miktari": 50000,    # $/MW
        "ab_skdm_fiyat": 90,        # $/ton
        "acik_artirma": True,
        "renk": "#22c55e"
    },
    "ETS_Tesvik": {
        "aciklama": "ETS + Yüksek Teşvik",
        "baslangic_cap": 60,        # Mt CO₂
        "cap_azalma_orani": 0.04,   # %4/yıl
        "tesvik_miktari": 150000,   # $/MW (yüksek)
        "ab_skdm_fiyat": 90,        # $/ton
        "acik_artirma": True,
        "renk": "#8b5cf6"
    }
}


def main_senaryo_calistir(senaryo_tipi, n_yil=11):
    """
    Tek bir senaryoyu çalıştırır ve kaydeder.
    
    Parametreler:
    -------------
    senaryo_tipi : str
        SENARYO_KONFIG içindeki senaryo adı
    n_yil : int
        Simülasyon süresi (varsayılan: 11 yıl, 2025-2035)
    
    Returns:
    --------
    pd.DataFrame : Simülasyon sonuçları
    """
    if senaryo_tipi not in SENARYO_KONFIG:
        print(f"❌ Geçersiz senaryo: {senaryo_tipi}")
        print(f"   Geçerli seçenekler: {list(SENARYO_KONFIG.keys())}")
        return None
    
    params = SENARYO_KONFIG[senaryo_tipi]
    
    print(f"\n🔄 {senaryo_tipi} senaryosu çalıştırılıyor...")
    print(f"   Açıklama: {params['aciklama']}")
    
    model = TurkiyeETSModel(
        baslangic_cap=params["baslangic_cap"],
        cap_azalma_orani=params["cap_azalma_orani"],
        tesvik_miktari=params["tesvik_miktari"],
        ab_skdm_fiyat=params["ab_skdm_fiyat"],
        senaryo_tipi=senaryo_tipi
    )
    
    # Çalıştır
    for _ in range(n_yil):
        model.step()
    
    # Sonuçları al
    df = model.datacollector.get_model_vars_dataframe()
    df["Senaryo"] = senaryo_tipi
    
    # Kaydet
    isim_eslesme = {
        "BAU": "bau",
        "Yumusak_ETS": "yumusak_ets",
        "Siki_ETS": "siki_ets",
        "ETS_Tesvik": "ets_tesvik"
    }
    dosya_adi = isim_eslesme.get(senaryo_tipi, senaryo_tipi.lower())
    csv_path = os.path.join(OUTPUT_DIR, f"senaryo_{dosya_adi}.csv")
    df.to_csv(csv_path, index=False)
    
    print(f"   ✅ Tamamlandı: {csv_path}")
    print(f"      • 2035 Emisyon: {df['Toplam_Emisyon'].iloc[-1]:.2f} Mt")
    print(f"      • Karbon Fiyatı: ${df['Karbon_Fiyati'].iloc[-1]:.0f}/ton")
    
    return df


def monte_carlo_sonuclari_kaydet(df_results, percentiles, stats):
    """
    Monte Carlo sonuçlarını dosyaya kaydeder ve görselleştirir.
    """
    import json
    
    # CSV kaydet
    csv_path = os.path.join(OUTPUT_DIR, "monte_carlo_results.csv")
    df_results.to_csv(csv_path, index=False)
    print(f"📄 Monte Carlo sonuçları: {csv_path}")
    
    # İstatistikleri JSON olarak kaydet
    json_path = os.path.join(OUTPUT_DIR, "monte_carlo_stats.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'n_runs': len(df_results),
            'final_emission': {
                'mean': float(stats['final_emission']['mean']),
                'std': float(stats['final_emission']['std']),
                'min': float(stats['final_emission']['min']),
                'max': float(stats['final_emission']['max']),
                'p05': float(percentiles.loc[0.05, 'final_emission']),
                'p50': float(percentiles.loc[0.50, 'final_emission']),
                'p95': float(percentiles.loc[0.95, 'final_emission'])
            },
            'final_price': {
                'mean': float(stats['final_price']['mean']),
                'std': float(stats['final_price']['std'])
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"📄 Monte Carlo istatistikleri: {json_path}")
    
    # Görselleştirme (matplotlib varsa)
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Emisyon histogram
        ax1 = axes[0]
        ax1.hist(df_results['final_emission'], bins=30, edgecolor='black', alpha=0.7, color='#3b82f6')
        ax1.axvline(percentiles.loc[0.5, 'final_emission'], color='red', linestyle='--', 
                   linewidth=2, label=f"Medyan: {percentiles.loc[0.5, 'final_emission']:.1f} Mt")
        ax1.axvline(percentiles.loc[0.05, 'final_emission'], color='orange', linestyle=':', 
                   linewidth=2, label=f"P5: {percentiles.loc[0.05, 'final_emission']:.1f} Mt")
        ax1.axvline(percentiles.loc[0.95, 'final_emission'], color='orange', linestyle=':', 
                   linewidth=2, label=f"P95: {percentiles.loc[0.95, 'final_emission']:.1f} Mt")
        ax1.set_xlabel('2035 Emisyon (Mt CO₂)', fontsize=12)
        ax1.set_ylabel('Frekans', fontsize=12)
        ax1.set_title('Monte Carlo Sonuçları - Emisyon Dağılımı', fontsize=14)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Karbon fiyatı histogram
        ax2 = axes[1]
        ax2.hist(df_results['final_price'], bins=30, edgecolor='black', alpha=0.7, color='#22c55e')
        ax2.axvline(percentiles.loc[0.5, 'final_price'], color='red', linestyle='--', 
                   linewidth=2, label=f"Medyan: ${percentiles.loc[0.5, 'final_price']:.0f}/ton")
        ax2.set_xlabel('2035 Karbon Fiyatı ($/ton CO₂)', fontsize=12)
        ax2.set_ylabel('Frekans', fontsize=12)
        ax2.set_title('Monte Carlo Sonuçları - Fiyat Dağılımı', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        fig_path = os.path.join(OUTPUT_DIR, "monte_carlo_histogram.png")
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f"📊 Monte Carlo grafiği: {fig_path}")
        plt.close()
        
    except ImportError:
        print("⚠️ matplotlib yüklü değil, grafik oluşturulamadı.")


# =============================================================================
# ANA ÇALIŞTIRMA (v4.5 - ARGPARSE DESTEĞİ)
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TR-ZERO: Ajan Tabanlı Karbon Piyasası Simülasyonu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
---------
  # Tüm senaryoları çalıştır (varsayılan)
  python ajan_tabanli_simulasyon.py
  
  # Tek senaryo çalıştır
  python ajan_tabanli_simulasyon.py --mode single --senaryo Siki_ETS
  
  # Monte Carlo analizi (100 iterasyon)
  python ajan_tabanli_simulasyon.py --mode monte_carlo --n_runs 100
  
  # Monte Carlo analizi (500 iterasyon, farklı seed)
  python ajan_tabanli_simulasyon.py --mode monte_carlo --n_runs 500 --seed 123
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["all", "single", "monte_carlo"], 
        default="all",
        help="Çalışma modu: all=tüm senaryolar, single=tek senaryo, monte_carlo=belirsizlik analizi"
    )
    
    parser.add_argument(
        "--senaryo", 
        choices=list(SENARYO_KONFIG.keys()),
        default="Siki_ETS",
        help="Tek senaryo modunda çalıştırılacak senaryo"
    )
    
    parser.add_argument(
        "--n_runs", 
        type=int, 
        default=100,
        help="Monte Carlo iterasyon sayısı (varsayılan: 100)"
    )
    
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Rastgele sayı seed'i (tekrarlanabilirlik için)"
    )
    
    parser.add_argument(
        "--n_yil", 
        type=int, 
        default=11,
        help="Simülasyon süresi (varsayılan: 11 yıl, 2025-2035)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🌱 TR-ZERO: AJAN TABANLI KARBON PİYASASI SİMÜLASYONU")
    print("   Türkiye Emisyon Ticaret Sistemi (2025-2035)")
    print("   v4.5 - Geliştirilmiş Versiyon")
    print("=" * 70)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mod: {args.mode.upper()}")
    print("-" * 70)
    
    if args.mode == "monte_carlo":
        # ============== MONTE CARLO MODU ==============
        print(f"\n🎲 Monte Carlo Modu Başlatılıyor...")
        print(f"   İterasyon sayısı: {args.n_runs}")
        print(f"   Seed: {args.seed}")
        
        df_results, percentiles, stats = monte_carlo_analizi(
            n_runs=args.n_runs, 
            seed=args.seed
        )
        
        if df_results is not None:
            monte_carlo_sonuclari_kaydet(df_results, percentiles, stats)
            print(f"\n✅ Monte Carlo analizi tamamlandı!")
        else:
            print(f"\n❌ Monte Carlo analizi başarısız!")
    
    elif args.mode == "single":
        # ============== TEK SENARYO MODU ==============
        print(f"\n▶ Tek Senaryo Modu: {args.senaryo}")
        
        df = main_senaryo_calistir(args.senaryo, n_yil=args.n_yil)
        
        if df is not None:
            print(f"\n✅ Senaryo tamamlandı!")
    
    else:
        # ============== TÜM SENARYOLAR MODU (VARSAYILAN) ==============
        print(f"\n📊 Tüm Senaryolar Modu")
        
        sonuclar = senaryo_karsilastirmasi()
        
        # CSV kaydet
        print("\n📁 CSV dosyaları kaydediliyor...")
        csv_kaydet(sonuclar)
    
    print(f"\n✅ Tüm sonuçlar '{OUTPUT_DIR}' klasörüne kaydedildi.")
    print("\n🎉 Simülasyon tamamlandı!")
    print("\n💡 Kullanım İpuçları:")
    print("   - Dashboard'u çalıştırmak için: streamlit run src/dashboard_v4.py")
    print("   - Monte Carlo analizi için: python src/ajan_tabanli_simulasyon.py --mode monte_carlo")
    print("   - Yardım için: python src/ajan_tabanli_simulasyon.py --help")


