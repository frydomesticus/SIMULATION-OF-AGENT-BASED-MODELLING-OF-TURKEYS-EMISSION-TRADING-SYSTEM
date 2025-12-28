# -*- coding: utf-8 -*-
"""
TR-ZERO: Ekonomik Etki Modülü v1.0
===================================

TÜİK Girdi-Çıktı tablosu tabanlı ekonomik etki analizi.
Karbon politikalarının GDP, istihdam ve sektörler arası 
yayılma etkilerini modeller.

Referanslar:
-----------
- Miller, R.E. & Blair, P.D. (2009). Input-Output Analysis: 
  Foundations and Extensions. Cambridge University Press.
- TÜİK (2022). Girdi-Çıktı Tabloları.
- Leontief, W. (1986). Input-Output Economics. Oxford University Press.

Yazar: TR-ZERO Team
Tarih: 2024-12
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import os

# =============================================================================
# TÜİK GİRDİ-ÇIKTI MATRİSİ (2022 VERİLERİNDEN UYARLANMIŞ)
# =============================================================================

# Sektör kodları ve isimleri (agregat - 15 sektör)
SEKTORLER = {
    0: "Tarım ve Ormancılık",
    1: "Madencilik",
    2: "Gıda ve İçecek",
    3: "Tekstil ve Giyim",
    4: "Ahşap ve Mobilya",
    5: "Kağıt ve Basım",
    6: "Petrol ve Kimya",
    7: "Plastik ve Kauçuk",
    8: "Cam ve Seramik",
    9: "Demir-Çelik ve Metal",
    10: "Makine ve Ekipman",
    11: "Elektrik ve Enerji",
    12: "İnşaat",
    13: "Ulaştırma",
    14: "Hizmetler",
}

# TÜİK 2022 G-Ç tablosundan türetilmiş teknik katsayılar matrisi (A matrisi)
# Not: Bu değerler TÜİK verilerinden basitleştirilmiş biçimde türetilmiştir
# Gerçek projede tam TÜİK verisi kullanılmalıdır

TEKNIK_KATSAYILAR = np.array([
    # Tarım  Madnc  Gıda   Tkstl  Ahşp   Kağıt  Petrl  Plstk  Cam    Metal  Makn   Enrj   İnşt   Ulaş   Hizm
    [0.08,  0.01,  0.25,  0.02,  0.05,  0.01,  0.01,  0.01,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.02],  # Tarım
    [0.00,  0.05,  0.00,  0.00,  0.01,  0.00,  0.10,  0.02,  0.05,  0.15,  0.02,  0.25,  0.10,  0.01,  0.00],  # Madencilik
    [0.02,  0.00,  0.15,  0.00,  0.00,  0.00,  0.01,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.05],  # Gıda
    [0.00,  0.00,  0.00,  0.20,  0.02,  0.00,  0.02,  0.02,  0.00,  0.00,  0.01,  0.00,  0.01,  0.01,  0.02],  # Tekstil
    [0.02,  0.00,  0.01,  0.00,  0.10,  0.05,  0.00,  0.01,  0.01,  0.00,  0.02,  0.00,  0.05,  0.00,  0.01],  # Ahşap
    [0.00,  0.00,  0.02,  0.01,  0.03,  0.12,  0.01,  0.02,  0.01,  0.00,  0.01,  0.00,  0.01,  0.01,  0.03],  # Kağıt
    [0.05,  0.03,  0.02,  0.05,  0.02,  0.03,  0.18,  0.15,  0.05,  0.03,  0.03,  0.15,  0.05,  0.20,  0.03],  # Petrol/Kimya
    [0.01,  0.01,  0.02,  0.02,  0.02,  0.02,  0.05,  0.15,  0.02,  0.02,  0.05,  0.01,  0.03,  0.02,  0.02],  # Plastik
    [0.00,  0.02,  0.01,  0.00,  0.01,  0.00,  0.02,  0.01,  0.12,  0.02,  0.01,  0.01,  0.08,  0.00,  0.01],  # Cam
    [0.01,  0.05,  0.02,  0.01,  0.03,  0.01,  0.03,  0.03,  0.03,  0.25,  0.20,  0.02,  0.15,  0.05,  0.02],  # Metal
    [0.02,  0.03,  0.02,  0.02,  0.03,  0.02,  0.02,  0.03,  0.02,  0.05,  0.15,  0.05,  0.08,  0.05,  0.03],  # Makine
    [0.02,  0.05,  0.03,  0.03,  0.02,  0.03,  0.05,  0.03,  0.05,  0.08,  0.05,  0.10,  0.03,  0.05,  0.05],  # Enerji
    [0.00,  0.02,  0.00,  0.00,  0.02,  0.00,  0.01,  0.01,  0.02,  0.05,  0.02,  0.01,  0.08,  0.02,  0.02],  # İnşaat
    [0.03,  0.03,  0.05,  0.03,  0.03,  0.03,  0.05,  0.03,  0.03,  0.03,  0.03,  0.03,  0.05,  0.15,  0.05],  # Ulaştırma
    [0.05,  0.05,  0.05,  0.05,  0.05,  0.08,  0.05,  0.05,  0.05,  0.05,  0.08,  0.05,  0.10,  0.08,  0.20],  # Hizmetler
])

# İstihdam katsayıları (kişi/milyon TL üretim) - TÜİK 2022
ISTIHDAM_KATSAYILARI = {
    0: 25.0,   # Tarım - yüksek emek yoğun
    1: 5.0,    # Madencilik
    2: 8.0,    # Gıda
    3: 15.0,   # Tekstil
    4: 10.0,   # Ahşap
    5: 6.0,    # Kağıt
    6: 3.0,    # Petrol/Kimya - sermaye yoğun
    7: 7.0,    # Plastik
    8: 6.0,    # Cam
    9: 5.0,    # Metal
    10: 8.0,   # Makine
    11: 2.5,   # Enerji - çok sermaye yoğun
    12: 12.0,  # İnşaat
    13: 10.0,  # Ulaştırma
    14: 18.0,  # Hizmetler
}

# Karbon yoğunluğu (tCO2/milyon TL) - hesaplanmış değerler
KARBON_YOGUNLUGU = {
    0: 50,     # Tarım
    1: 200,    # Madencilik
    2: 40,     # Gıda
    3: 30,     # Tekstil
    4: 25,     # Ahşap
    5: 35,     # Kağıt
    6: 350,    # Petrol/Kimya - yüksek
    7: 45,     # Plastik
    8: 180,    # Cam/Seramik
    9: 400,    # Metal - çok yüksek
    10: 50,    # Makine
    11: 800,   # Enerji - en yüksek
    12: 120,   # İnşaat
    13: 150,   # Ulaştırma
    14: 15,    # Hizmetler - düşük
}


# =============================================================================
# INPUT-OUTPUT MODEL SINIFI
# =============================================================================

class InputOutputModel:
    """
    Leontief Girdi-Çıktı modeli ile ekonomik etki analizi.
    
    Bu model, bir sektördeki talep değişikliğinin diğer sektörlere
    ve toplam ekonomiye etkisini hesaplar.
    
    Matematiksel Temel:
    ------------------
    x = (I - A)^(-1) * f
    
    Burada:
    - x: Toplam üretim vektörü
    - A: Teknik katsayılar matrisi
    - f: Nihai talep vektörü
    - (I-A)^(-1): Leontief ters matrisi
    
    Attributes
    ----------
    A : np.ndarray
        Teknik katsayılar matrisi (n x n)
    L : np.ndarray
        Leontief ters matrisi
    n_sektor : int
        Sektör sayısı
    """
    
    def __init__(self, teknik_katsayilar: np.ndarray = None):
        """
        Parameters
        ----------
        teknik_katsayilar : np.ndarray, optional
            Teknik katsayılar matrisi. None ise varsayılan kullanılır.
        """
        if teknik_katsayilar is None:
            self.A = TEKNIK_KATSAYILAR.copy()
        else:
            self.A = teknik_katsayilar.copy()
        
        self.n_sektor = len(self.A)
        self.sektor_isimleri = SEKTORLER
        
        # Leontief ters matrisini hesapla
        self.L = self._hesapla_leontief()
        
        # Çarpanları hesapla
        self._hesapla_carpanlar()
    
    def _hesapla_leontief(self) -> np.ndarray:
        """
        Leontief ters matrisini hesapla: L = (I - A)^(-1)
        
        Returns
        -------
        np.ndarray
            Leontief ters matrisi
        """
        I = np.eye(self.n_sektor)
        try:
            L = np.linalg.inv(I - self.A)
            return L
        except np.linalg.LinAlgError:
            print("⚠️ Matris tekil! Pseudo-inverse kullanılıyor.")
            return np.linalg.pinv(I - self.A)
    
    def _hesapla_carpanlar(self):
        """Sektörel çarpanları hesapla."""
        # Üretim çarpanları (sütun toplamları)
        self.uretim_carpanlari = self.L.sum(axis=0)
        
        # Gelir çarpanları (işçi ücretleri dahil - basitleştirilmiş)
        self.gelir_carpanlari = self.uretim_carpanlari * 0.45  # Ortalama ücret payı
        
        # İstihdam çarpanları
        istihdam_katsayilari = np.array([ISTIHDAM_KATSAYILARI[i] for i in range(self.n_sektor)])
        self.istihdam_carpanlari = self.L.T @ istihdam_katsayilari
    
    def hesapla_uretim_etkisi(self, nihai_talep: np.ndarray) -> Dict:
        """
        Nihai talep değişikliğinin toplam üretime etkisini hesapla.
        
        Parameters
        ----------
        nihai_talep : np.ndarray
            Nihai talep vektörü (milyon TL)
        
        Returns
        -------
        dict
            Toplam üretim, sektörel dağılım, çarpan etkileri
        """
        # Toplam üretim: x = L * f
        toplam_uretim = self.L @ nihai_talep
        
        # Doğrudan etki (sadece ilgili sektör)
        dogrudan_etki = nihai_talep.sum()
        
        # Dolaylı etki (diğer sektörlere yayılma)
        dolayli_etki = toplam_uretim.sum() - dogrudan_etki
        
        # Çarpan (multiplier)
        carpan = toplam_uretim.sum() / dogrudan_etki if dogrudan_etki > 0 else 0
        
        return {
            'toplam_uretim_milyon_tl': toplam_uretim.sum(),
            'dogrudan_etki': dogrudan_etki,
            'dolayli_etki': dolayli_etki,
            'carpan': carpan,
            'sektorel_dagilim': dict(zip(
                [SEKTORLER[i] for i in range(self.n_sektor)],
                toplam_uretim.tolist()
            ))
        }
    
    def hesapla_istihdam_etkisi(self, nihai_talep: np.ndarray) -> Dict:
        """
        Talep değişikliğinin istihdama etkisini hesapla.
        
        Parameters
        ----------
        nihai_talep : np.ndarray
            Nihai talep vektörü (milyon TL)
        
        Returns
        -------
        dict
            Toplam istihdam etkisi, sektörel dağılım
        """
        # Üretim etkisini hesapla
        toplam_uretim = self.L @ nihai_talep
        
        # İstihdam etkisi
        istihdam_katsayilari = np.array([ISTIHDAM_KATSAYILARI[i] for i in range(self.n_sektor)])
        istihdam_etkisi = toplam_uretim * istihdam_katsayilari
        
        return {
            'toplam_istihdam': istihdam_etkisi.sum(),
            'dogrudan_istihdam': (nihai_talep * istihdam_katsayilari).sum(),
            'dolayli_istihdam': istihdam_etkisi.sum() - (nihai_talep * istihdam_katsayilari).sum(),
            'sektorel_istihdam': dict(zip(
                [SEKTORLER[i] for i in range(self.n_sektor)],
                istihdam_etkisi.tolist()
            ))
        }
    
    def hesapla_emisyon_etkisi(self, nihai_talep: np.ndarray) -> Dict:
        """
        Talep değişikliğinin emisyona etkisini hesapla.
        
        Parameters
        ----------
        nihai_talep : np.ndarray
            Nihai talep vektörü (milyon TL)
        
        Returns
        -------
        dict
            Toplam emisyon etkisi, sektörel dağılım
        """
        # Üretim etkisini hesapla
        toplam_uretim = self.L @ nihai_talep
        
        # Emisyon etkisi
        karbon_yogunlugu = np.array([KARBON_YOGUNLUGU[i] for i in range(self.n_sektor)])
        emisyon_etkisi = toplam_uretim * karbon_yogunlugu / 1e6  # Mt CO2
        
        return {
            'toplam_emisyon_mt': emisyon_etkisi.sum(),
            'dogrudan_emisyon_mt': (nihai_talep * karbon_yogunlugu / 1e6).sum(),
            'dolayli_emisyon_mt': emisyon_etkisi.sum() - (nihai_talep * karbon_yogunlugu / 1e6).sum(),
            'sektorel_emisyon': dict(zip(
                [SEKTORLER[i] for i in range(self.n_sektor)],
                emisyon_etkisi.tolist()
            ))
        }
    
    def karbon_vergisi_etkisi(self, karbon_fiyati: float, 
                               toplam_emisyon_mt: float = 500) -> Dict:
        """
        Karbon vergisinin ekonomiye etkisini analiz et.
        
        Parameters
        ----------
        karbon_fiyati : float
            Karbon fiyatı ($/tCO2)
        toplam_emisyon_mt : float
            Toplam emisyon (Mt CO2)
        
        Returns
        -------
        dict
            Sektörel maliyet etkileri, GDP etkisi, istihdam etkisi
        """
        # Sektörel emisyon payları (yaklaşık)
        sektor_emisyon_paylari = np.array([
            0.05,  # Tarım
            0.03,  # Madencilik
            0.02,  # Gıda
            0.02,  # Tekstil
            0.01,  # Ahşap
            0.01,  # Kağıt
            0.15,  # Petrol/Kimya
            0.02,  # Plastik
            0.03,  # Cam
            0.15,  # Metal
            0.03,  # Makine
            0.35,  # Enerji
            0.05,  # İnşaat
            0.06,  # Ulaştırma
            0.02,  # Hizmetler
        ])
        
        # Sektörel karbon maliyeti (milyon $)
        sektorel_maliyet = sektor_emisyon_paylari * toplam_emisyon_mt * karbon_fiyati
        
        # TL'ye çevir (1$ = 30 TL varsayımı)
        sektorel_maliyet_tl = sektorel_maliyet * 30  # Milyon TL
        
        # Bu maliyetin üretim kaybına dönüşümü (negatif talep şoku)
        negatif_talep = -sektorel_maliyet_tl * 0.3  # %30 üretim azalması varsayımı
        
        # Ekonomik etki
        uretim_etkisi = self.hesapla_uretim_etkisi(negatif_talep)
        istihdam_etkisi = self.hesapla_istihdam_etkisi(negatif_talep)
        
        return {
            'karbon_fiyati_usd': karbon_fiyati,
            'toplam_karbon_maliyeti_musd': sektorel_maliyet.sum(),
            'gdp_etkisi_milyon_tl': uretim_etkisi['toplam_uretim_milyon_tl'],
            'gdp_etkisi_yuzde': (uretim_etkisi['toplam_uretim_milyon_tl'] / 25e6) * 100,  # ~25 trilyon TL GDP
            'istihdam_kaybi': istihdam_etkisi['toplam_istihdam'],
            'sektorel_maliyet_musd': dict(zip(
                [SEKTORLER[i] for i in range(self.n_sektor)],
                sektorel_maliyet.tolist()
            )),
            'en_cok_etkilenen_sektorler': self._en_cok_etkilenen(sektorel_maliyet)
        }
    
    def _en_cok_etkilenen(self, sektorel_maliyet: np.ndarray, n: int = 5) -> List[str]:
        """En çok etkilenen sektörleri bul."""
        sirali = np.argsort(sektorel_maliyet)[::-1]
        return [SEKTORLER[i] for i in sirali[:n]]
    
    def yesil_yatirim_etkisi(self, yatirim_milyon_tl: float, 
                             sektor: str = "Elektrik ve Enerji") -> Dict:
        """
        Yeşil yatırımın (yenilenebilir enerji) ekonomiye etkisini hesapla.
        
        Parameters
        ----------
        yatirim_milyon_tl : float
            Yatırım miktarı (milyon TL)
        sektor : str
            Hedef sektör
        
        Returns
        -------
        dict
            Üretim, istihdam, emisyon etkileri
        """
        # Sektör indeksini bul
        sektor_idx = None
        for idx, isim in SEKTORLER.items():
            if isim == sektor:
                sektor_idx = idx
                break
        
        if sektor_idx is None:
            sektor_idx = 11  # Varsayılan: Enerji
        
        # Nihai talep vektörü oluştur
        nihai_talep = np.zeros(self.n_sektor)
        nihai_talep[sektor_idx] = yatirim_milyon_tl
        
        # Yenilenebilir yatırımı için ek sektörel etkiler
        # (Makine, metal, inşaat sektörlerine yayılma)
        nihai_talep[10] += yatirim_milyon_tl * 0.20  # Makine
        nihai_talep[9] += yatirim_milyon_tl * 0.15   # Metal
        nihai_talep[12] += yatirim_milyon_tl * 0.25  # İnşaat
        
        uretim = self.hesapla_uretim_etkisi(nihai_talep)
        istihdam = self.hesapla_istihdam_etkisi(nihai_talep)
        emisyon = self.hesapla_emisyon_etkisi(nihai_talep)
        
        # Önlenen emisyon (kömür yerine yenilenebilir)
        # Varsayım: 1 MW kurulum = 2000 tCO2/yıl önleme
        mw_kurulum = yatirim_milyon_tl / 50  # 50 milyon TL/MW varsayımı
        onlenen_emisyon = mw_kurulum * 2000 / 1e6  # Mt
        
        return {
            'yatirim_milyon_tl': yatirim_milyon_tl,
            'toplam_uretim_etkisi': uretim['toplam_uretim_milyon_tl'],
            'uretim_carpani': uretim['carpan'],
            'toplam_istihdam_yaratilan': istihdam['toplam_istihdam'],
            'yapim_emisyonu_mt': emisyon['toplam_emisyon_mt'],
            'yillik_onlenen_emisyon_mt': onlenen_emisyon,
            'net_emisyon_etkisi_mt': emisyon['toplam_emisyon_mt'] - onlenen_emisyon * 20,  # 20 yıl ömür
            'mw_kurulum': mw_kurulum
        }
    
    def sektor_baglanti_analizi(self) -> pd.DataFrame:
        """
        Sektörler arası bağlantı (linkage) analizi.
        
        Backward linkage: Sektörün girdi talebi (A sütun toplamı)
        Forward linkage: Sektörün çıktı arzı (A satır toplamı)
        
        Returns
        -------
        pd.DataFrame
            Her sektör için backward/forward linkage değerleri
        """
        backward = self.A.sum(axis=0)  # Sütun toplamları
        forward = self.A.sum(axis=1)   # Satır toplamları
        
        # Normalleştir
        backward_norm = backward / backward.mean()
        forward_norm = forward / forward.mean()
        
        # Sektör tipi belirleme
        sektor_tipleri = []
        for i in range(self.n_sektor):
            if backward_norm[i] > 1 and forward_norm[i] > 1:
                sektor_tipleri.append("Anahtar Sektör")
            elif backward_norm[i] > 1:
                sektor_tipleri.append("Güçlü Geriye Bağ")
            elif forward_norm[i] > 1:
                sektor_tipleri.append("Güçlü İleriye Bağ")
            else:
                sektor_tipleri.append("Zayıf Bağlantılı")
        
        return pd.DataFrame({
            'Sektör': [SEKTORLER[i] for i in range(self.n_sektor)],
            'Geriye_Baglanti': backward_norm,
            'Ileriye_Baglanti': forward_norm,
            'Tip': sektor_tipleri,
            'Istihdam_Carpani': self.istihdam_carpanlari
        })
    
    def hesapla_toplam_etki(self, karbon_fiyati: float, toplam_emisyon_mt: float,
                            gelir_donus_senaryosu: str = "yesil_yatirim",
                            gelir_donus_orani: float = 0.8) -> Dict:
        """
        Karbon politikasının toplam ekonomik etkisini hesapla.
        
        Bu fonksiyon, karbon vergisinin negatif etkilerini ve
        gelir geri dönüşümünün pozitif etkilerini birleştirerek
        net ekonomik etkiyi hesaplar.
        
        Parameters
        ----------
        karbon_fiyati : float
            Karbon fiyatı ($/tCO2)
        toplam_emisyon_mt : float
            Toplam emisyon (Mt CO2)
        gelir_donus_senaryosu : str
            Gelir geri dönüşüm senaryosu:
            - "hazine": Gelirler hazineye (etkisiz)
            - "yesil_yatirim": Yeşil yatırıma yönlendir
            - "hanehalki_transfer": Hanehalklarına dağıt
            - "firma_destegi": Firmalara geri ver
        gelir_donus_orani : float
            Geri dönüştürülen oran (0-1 arası)
        
        Returns
        -------
        dict
            Net ekonomik etki (GDP, istihdam, sektörel)
        
        References
        ----------
        - Carbone & Rivers (2017). Revenue recycling mechanisms.
        - Goulder (1995). Double dividend hypothesis.
        """
        # 1. Karbon vergisi brüt etkisi
        karbon_etkisi = self.karbon_vergisi_etkisi(karbon_fiyati, toplam_emisyon_mt)
        brut_maliyet_musd = karbon_etkisi['toplam_karbon_maliyeti_musd']
        brut_gdp_etkisi = karbon_etkisi['gdp_etkisi_milyon_tl']
        brut_istihdam = karbon_etkisi['istihdam_kaybi']
        
        # 2. Geri dönüştürülen gelir (milyon $)
        geri_donusen_gelir = brut_maliyet_musd * gelir_donus_orani
        geri_donusen_tl = geri_donusen_gelir * 30  # Milyon TL
        
        # 3. Geri dönüşüm senaryosuna göre etki hesapla
        donus_etkisi = self._gelir_donus_etkisi(
            geri_donusen_tl, 
            gelir_donus_senaryosu
        )
        
        # 4. Net etki hesapla
        net_gdp = brut_gdp_etkisi + donus_etkisi['gdp_etkisi_milyon_tl']
        net_istihdam = brut_istihdam + donus_etkisi['istihdam_etkisi']
        
        return {
            'karbon_fiyati_usd': karbon_fiyati,
            'brut_maliyet_musd': brut_maliyet_musd,
            'geri_donusen_musd': geri_donusen_gelir,
            'gelir_donus_senaryosu': gelir_donus_senaryosu,
            'brut_gdp_etkisi_milyon_tl': brut_gdp_etkisi,
            'donus_gdp_etkisi_milyon_tl': donus_etkisi['gdp_etkisi_milyon_tl'],
            'net_gdp_etkisi_milyon_tl': net_gdp,
            'net_gdp_yuzde': (net_gdp / 25e6) * 100,  # 25 trilyon TL GDP
            'brut_istihdam_kaybi': brut_istihdam,
            'donus_istihdam_kazanci': donus_etkisi['istihdam_etkisi'],
            'net_istihdam_etkisi': net_istihdam,
            'cifte_temettü': net_gdp > 0,  # Double dividend
            'sektorel_net_etki': donus_etkisi.get('sektorel_etki', {})
        }
    
    def _gelir_donus_etkisi(self, gelir_milyon_tl: float, 
                            senaryo: str) -> Dict:
        """
        Gelir geri dönüşümünün ekonomik etkisini hesapla.
        
        Parameters
        ----------
        gelir_milyon_tl : float
            Geri dönüştürülecek gelir (milyon TL)
        senaryo : str
            Geri dönüşüm senaryosu
        
        Returns
        -------
        dict
            GDP ve istihdam etkileri
        """
        if senaryo == "hazine":
            # Gelirler hazineye - düşük çarpan etkisi
            carpan = 0.2
            nihai_talep = np.zeros(self.n_sektor)
            nihai_talep[14] = gelir_milyon_tl * carpan  # Hizmetler
            
        elif senaryo == "yesil_yatirim":
            # Yeşil yatırım - yüksek çarpan etkisi
            carpan = 1.5
            nihai_talep = np.zeros(self.n_sektor)
            nihai_talep[11] = gelir_milyon_tl * 0.40  # Enerji
            nihai_talep[10] = gelir_milyon_tl * 0.25  # Makine
            nihai_talep[9] = gelir_milyon_tl * 0.20   # Metal
            nihai_talep[12] = gelir_milyon_tl * 0.15  # İnşaat
            
        elif senaryo == "hanehalki_transfer":
            # Hanehalkı transferi - tüketim etkisi
            carpan = 1.0
            nihai_talep = np.zeros(self.n_sektor)
            # Tüketim dağılımı (TÜİK 2022)
            nihai_talep[2] = gelir_milyon_tl * 0.25   # Gıda
            nihai_talep[3] = gelir_milyon_tl * 0.10   # Tekstil
            nihai_talep[11] = gelir_milyon_tl * 0.15  # Enerji
            nihai_talep[14] = gelir_milyon_tl * 0.35  # Hizmetler
            nihai_talep[13] = gelir_milyon_tl * 0.15  # Ulaştırma
            
        elif senaryo == "firma_destegi":
            # Firma desteği - sanayi üretimine destek
            carpan = 1.2
            nihai_talep = np.zeros(self.n_sektor)
            nihai_talep[6] = gelir_milyon_tl * 0.30   # Petrol/Kimya
            nihai_talep[9] = gelir_milyon_tl * 0.30   # Metal
            nihai_talep[8] = gelir_milyon_tl * 0.15   # Cam
            nihai_talep[10] = gelir_milyon_tl * 0.25  # Makine
            
        else:
            # Varsayılan: hazine
            carpan = 0.2
            nihai_talep = np.zeros(self.n_sektor)
            nihai_talep[14] = gelir_milyon_tl * carpan
        
        # Leontief çarpan etkisi
        uretim = self.hesapla_uretim_etkisi(nihai_talep)
        istihdam = self.hesapla_istihdam_etkisi(nihai_talep)
        
        return {
            'gdp_etkisi_milyon_tl': uretim['toplam_uretim_milyon_tl'],
            'istihdam_etkisi': istihdam['toplam_istihdam'],
            'carpan': uretim['carpan'],
            'sektorel_etki': uretim['sektorel_dagilim']
        }


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def karbon_politikasi_karsilastirma(fiyatlar: List[float] = [20, 40, 60, 80, 100]) -> pd.DataFrame:
    """
    Farklı karbon fiyatlarının ekonomik etkilerini karşılaştır.
    
    Parameters
    ----------
    fiyatlar : list
        Test edilecek karbon fiyatları ($/tCO2)
    
    Returns
    -------
    pd.DataFrame
        Her fiyat için ekonomik etkiler
    """
    model = InputOutputModel()
    sonuclar = []
    
    for fiyat in fiyatlar:
        etki = model.karbon_vergisi_etkisi(fiyat)
        sonuclar.append({
            'Karbon_Fiyati': fiyat,
            'Toplam_Maliyet_MUSD': etki['toplam_karbon_maliyeti_musd'],
            'GDP_Etkisi_Pct': etki['gdp_etkisi_yuzde'],
            'Istihdam_Kaybi': etki['istihdam_kaybi']
        })
    
    return pd.DataFrame(sonuclar)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TR-ZERO Ekonomik Etki Modülü (Input-Output) - Test")
    print("=" * 60)
    
    # Model oluştur
    model = InputOutputModel()
    print(f"\n✅ Model yüklendi: {model.n_sektor} sektör")
    
    # Leontief matrisi kontrolü
    print(f"\nLeontief matrisi boyutu: {model.L.shape}")
    print(f"Ortalama üretim çarpanı: {model.uretim_carpanlari.mean():.2f}")
    
    # Sektör bağlantı analizi
    print("\n📊 Sektör Bağlantı Analizi:")
    baglanti = model.sektor_baglanti_analizi()
    anahtar_sektorler = baglanti[baglanti['Tip'] == 'Anahtar Sektör']['Sektör'].tolist()
    print(f"   Anahtar Sektörler: {anahtar_sektorler}")
    
    # Karbon vergisi etkisi
    print("\n💰 Karbon Vergisi Etki Analizi:")
    for fiyat in [20, 50, 100]:
        etki = model.karbon_vergisi_etkisi(fiyat)
        print(f"\n   ${fiyat}/tCO2:")
        print(f"   Toplam Maliyet: ${etki['toplam_karbon_maliyeti_musd']:.0f}M")
        print(f"   GDP Etkisi: %{etki['gdp_etkisi_yuzde']:.2f}")
        print(f"   İstihdam Kaybı: {etki['istihdam_kaybi']:.0f} kişi")
    
    # Yeşil yatırım etkisi
    print("\n🌱 Yeşil Yatırım Etkisi (10 Milyar TL):")
    yesil = model.yesil_yatirim_etkisi(10000)  # 10 milyar TL
    print(f"   Üretim Çarpanı: {yesil['uretim_carpani']:.2f}")
    print(f"   Yaratılan İstihdam: {yesil['toplam_istihdam_yaratilan']:.0f} kişi")
    print(f"   Kurulum: {yesil['mw_kurulum']:.0f} MW")
    print(f"   Yıllık Önlenen Emisyon: {yesil['yillik_onlenen_emisyon_mt']:.3f} Mt")
    
    print("\n✅ Test tamamlandı!")
