# -*- coding: utf-8 -*-
"""
TR-ZERO: Enerji Dispatch Modülü v1.0
=====================================

PyPSA tabanlı elektrik üretim optimizasyonu modülü.
Merit-order dispatch ve yenilenebilir entegrasyonunu modeller.

Referanslar:
-----------
- Brown et al. (2018). PyPSA: Python for Power System Analysis. 
  Journal of Open Research Software, 6(1), p.4.
- TEİAŞ (2024). Türkiye Elektrik Üretim-Tüketim İstatistikleri.
- EPDK (2024). Elektrik Piyasası Sektör Raporu.

Yazar: TR-ZERO Team
Tarih: 2024-12
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import os
import sys

# PyPSA opsiyonel - yoksa basit dispatch kullan
try:
    import pypsa
    PYPSA_AVAILABLE = True
except ImportError:
    PYPSA_AVAILABLE = False
    print("⚠️ PyPSA yüklü değil. Basitleştirilmiş dispatch kullanılacak.")
    print("   Kurulum: pip install pypsa")

# =============================================================================
# SABİTLER VE PARAMETRELER
# =============================================================================

# Türkiye elektrik sistemi parametreleri (TEİAŞ 2024)
TURKIYE_ELEKTRIK = {
    "peak_demand_mw": 57000,          # MW (2024 pik)
    "total_capacity_mw": 105000,       # MW (toplam kurulu güç)
    "annual_consumption_twh": 340,     # TWh (2024 tahmini)
    "reserve_margin": 0.15,            # %15 yedek
    "transmission_losses": 0.08,       # %8 iletim kaybı
}

# Yakıt fiyatları ($/birim) - 2024 ortalamaları
YAKIT_FIYATLARI = {
    "Kömür": 120,          # $/ton (ithal)
    "Linyit": 45,          # $/ton (yerli)
    "Doğalgaz": 10.5,      # $/MMBtu
    "Fuel Oil": 650,       # $/ton
    "Jeotermal": 0,        # Yakıt maliyeti yok
    "Hidrolik": 0,         # Yakıt maliyeti yok
    "Rüzgar": 0,           # Yakıt maliyeti yok
    "Güneş": 0,            # Yakıt maliyeti yok
    "Biyokütle": 30,       # $/ton
}

# Termal verimlilikler (%)
VERIMLILIK = {
    "Kömür": 0.38,
    "Linyit": 0.35,
    "Doğalgaz_CCGT": 0.55,
    "Doğalgaz_OCGT": 0.35,
    "Fuel Oil": 0.32,
    "Biyokütle": 0.28,
}

# Emisyon faktörleri (tCO2/MWh) - IPCC 2006
EMISYON_FAKTORLERI_MWH = {
    "Kömür": 0.95,
    "Linyit": 1.10,
    "Doğalgaz": 0.40,
    "Fuel Oil": 0.75,
    "Biyokütle": 0.0,      # Karbon nötr kabul
    "Jeotermal": 0.05,     # Düşük
    "Hidrolik": 0.0,
    "Rüzgar": 0.0,
    "Güneş": 0.0,
    "Nükleer": 0.0,
}

# Kapasite faktörleri (yıllık ortalama)
KAPASITE_FAKTORLERI = {
    "Kömür": 0.70,
    "Linyit": 0.65,
    "Doğalgaz": 0.45,
    "Fuel Oil": 0.10,
    "Jeotermal": 0.85,
    "Hidrolik": 0.35,      # Mevsimsel değişken
    "Rüzgar": 0.30,
    "Güneş": 0.18,
    "Biyokütle": 0.60,
    "Nükleer": 0.90,
}


# =============================================================================
# SINIFLAR
# =============================================================================

class EnerjiDispatchModulu:
    """
    Merit-order tabanlı elektrik dispatch optimizasyonu.
    
    Bu modül, karbon fiyatını içeren marjinal maliyet sıralamasına göre
    santralleri devreye alır ve toplam emisyonu hesaplar.
    
    Attributes
    ----------
    santraller : pd.DataFrame
        Tesis bilgileri (kapasite, yakıt, maliyet, emisyon)
    karbon_fiyati : float
        $/tCO2 karbon fiyatı
    yillik_talep_twh : float
        Yıllık elektrik talebi (TWh)
    
    Methods
    -------
    optimize_dispatch(talep_mwh)
        Verilen talep için optimal üretim karışımını belirler
    hesapla_emisyon()
        Toplam yıllık emisyonu hesaplar
    """
    
    def __init__(self, santraller: pd.DataFrame, karbon_fiyati: float = 0):
        """
        Parameters
        ----------
        santraller : pd.DataFrame
            Santral verileri (columns: Tesis_Adi, Kapasite_MW, Yakit_Tipi, ...)
        karbon_fiyati : float
            Karbon fiyatı ($/tCO2)
        """
        self.santraller = santraller.copy()
        self.karbon_fiyati = karbon_fiyati
        self.yillik_talep_twh = TURKIYE_ELEKTRIK["annual_consumption_twh"]
        
        # Marjinal maliyetleri hesapla
        self._hesapla_marjinal_maliyetler()
        
        # Merit-order sıralaması
        self._sirala_merit_order()
    
    def _hesapla_marjinal_maliyetler(self):
        """
        Her santral için marjinal maliyet hesapla.
        
        Marjinal Maliyet = Yakıt Maliyeti + Karbon Maliyeti + O&M
        
        Referans: IEA (2023). Projected Costs of Generating Electricity.
        """
        # Yakıt maliyeti ($/MWh)
        self.santraller['Yakit_Maliyet'] = self.santraller['Yakit_Tipi'].apply(
            lambda x: self._yakit_maliyet_mwh(x)
        )
        
        # Emisyon faktörü (tCO2/MWh)
        self.santraller['Emisyon_Faktor'] = self.santraller['Yakit_Tipi'].apply(
            lambda x: EMISYON_FAKTORLERI_MWH.get(x, 0)
        )
        
        # Karbon maliyeti ($/MWh)
        self.santraller['Karbon_Maliyet'] = (
            self.santraller['Emisyon_Faktor'] * self.karbon_fiyati
        )
        
        # O&M maliyeti ($/MWh) - yaklaşık değerler
        om_maliyetleri = {
            "Kömür": 4, "Linyit": 5, "Doğalgaz": 3, "Fuel Oil": 6,
            "Jeotermal": 8, "Hidrolik": 2, "Rüzgar": 5, "Güneş": 3,
            "Biyokütle": 10, "Nükleer": 12
        }
        self.santraller['OM_Maliyet'] = self.santraller['Yakit_Tipi'].apply(
            lambda x: om_maliyetleri.get(x, 5)
        )
        
        # Toplam marjinal maliyet
        self.santraller['Marjinal_Maliyet'] = (
            self.santraller['Yakit_Maliyet'] + 
            self.santraller['Karbon_Maliyet'] + 
            self.santraller['OM_Maliyet']
        )
    
    def _yakit_maliyet_mwh(self, yakit_tipi: str) -> float:
        """Yakıt tipine göre $/MWh maliyet hesapla."""
        
        if yakit_tipi in ["Hidrolik", "Rüzgar", "Güneş", "Jeotermal"]:
            return 0.0
        
        verimlilik = VERIMLILIK.get(yakit_tipi, 0.35)
        yakit_fiyat = YAKIT_FIYATLARI.get(yakit_tipi, 0)
        
        # Dönüşüm faktörleri
        if yakit_tipi in ["Kömür", "Linyit"]:
            # ton kömür → MWh (yaklaşık 8 MWh/ton * verimlilik)
            mwh_per_ton = 8.0 * verimlilik
            return yakit_fiyat / mwh_per_ton
        
        elif yakit_tipi == "Doğalgaz":
            # MMBtu → MWh (1 MMBtu ≈ 0.293 MWh)
            mwh_per_mmbtu = 0.293 * verimlilik
            return yakit_fiyat / mwh_per_mmbtu
        
        elif yakit_tipi == "Fuel Oil":
            # ton fuel oil → MWh
            mwh_per_ton = 11.6 * verimlilik
            return yakit_fiyat / mwh_per_ton
        
        return 0.0
    
    def _sirala_merit_order(self):
        """Santralleri marjinal maliyete göre sırala (merit-order)."""
        self.santraller = self.santraller.sort_values(
            'Marjinal_Maliyet', ascending=True
        ).reset_index(drop=True)
    
    def optimize_dispatch(self, talep_mwh: float) -> Dict:
        """
        Verilen talep için optimal üretim karışımını belirle.
        
        Merit-order dispatch: En düşük marjinal maliyetli santralden
        başlayarak talep karşılanana kadar devreye al.
        
        Parameters
        ----------
        talep_mwh : float
            Karşılanacak talep (MWh)
        
        Returns
        -------
        dict
            Üretim karışımı, toplam maliyet, toplam emisyon
        """
        kalan_talep = talep_mwh
        toplam_maliyet = 0
        toplam_emisyon = 0
        uretim_karisimi = {}
        
        for _, santral in self.santraller.iterrows():
            if kalan_talep <= 0:
                break
            
            # Santral kapasitesi (yıllık MWh)
            kapasite_faktor = KAPASITE_FAKTORLERI.get(
                santral['Yakit_Tipi'], 0.5
            )
            max_uretim = santral['Kapasite_MW'] * 8760 * kapasite_faktor
            
            # Gerçek üretim
            uretim = min(kalan_talep, max_uretim)
            
            if uretim > 0:
                uretim_karisimi[santral['Tesis_Adi']] = {
                    'Uretim_MWh': uretim,
                    'Yakit_Tipi': santral['Yakit_Tipi'],
                    'Marjinal_Maliyet': santral['Marjinal_Maliyet'],
                    'Emisyon_tCO2': uretim * santral['Emisyon_Faktor']
                }
                
                toplam_maliyet += uretim * santral['Marjinal_Maliyet']
                toplam_emisyon += uretim * santral['Emisyon_Faktor']
                kalan_talep -= uretim
        
        return {
            'uretim_karisimi': uretim_karisimi,
            'toplam_maliyet_usd': toplam_maliyet,
            'toplam_emisyon_tco2': toplam_emisyon,
            'ortalama_maliyet_mwh': toplam_maliyet / talep_mwh if talep_mwh > 0 else 0,
            'karsilanmayan_talep_mwh': max(0, kalan_talep)
        }
    
    def hesapla_yillik_emisyon(self) -> Dict:
        """
        Yıllık elektrik üretiminden kaynaklanan emisyonu hesapla.
        
        Returns
        -------
        dict
            Toplam emisyon, sektörel dağılım, karbon maliyeti
        """
        yillik_talep_mwh = self.yillik_talep_twh * 1e6  # TWh → MWh
        
        dispatch = self.optimize_dispatch(yillik_talep_mwh)
        
        # Yakıt tipine göre gruplama
        yakit_emisyonlari = {}
        for santral, veri in dispatch['uretim_karisimi'].items():
            yakit = veri['Yakit_Tipi']
            if yakit not in yakit_emisyonlari:
                yakit_emisyonlari[yakit] = 0
            yakit_emisyonlari[yakit] += veri['Emisyon_tCO2']
        
        return {
            'toplam_emisyon_mt': dispatch['toplam_emisyon_tco2'] / 1e6,
            'yakit_emisyonlari_mt': {k: v/1e6 for k, v in yakit_emisyonlari.items()},
            'karbon_maliyeti_musd': (dispatch['toplam_emisyon_tco2'] * self.karbon_fiyati) / 1e6,
            'ortalama_emisyon_faktor': dispatch['toplam_emisyon_tco2'] / yillik_talep_mwh,
            'talep_karsilama_orani': 1 - (dispatch['karsilanmayan_talep_mwh'] / yillik_talep_mwh)
        }
    
    def karbon_fiyati_etkisi(self, fiyat_aralik: List[float]) -> pd.DataFrame:
        """
        Farklı karbon fiyatlarının dispatch'e etkisini analiz et.
        
        Parameters
        ----------
        fiyat_aralik : list
            Test edilecek karbon fiyatları ($/tCO2)
        
        Returns
        -------
        pd.DataFrame
            Her fiyat için emisyon, maliyet, üretim karışımı
        """
        sonuclar = []
        
        for fiyat in fiyat_aralik:
            self.karbon_fiyati = fiyat
            self._hesapla_marjinal_maliyetler()
            self._sirala_merit_order()
            
            emisyon = self.hesapla_yillik_emisyon()
            
            sonuclar.append({
                'Karbon_Fiyati': fiyat,
                'Toplam_Emisyon_Mt': emisyon['toplam_emisyon_mt'],
                'Karbon_Maliyeti_MUSD': emisyon['karbon_maliyeti_musd'],
                'Ortalama_EF': emisyon['ortalama_emisyon_faktor'],
                'Yakit_Dagilim': emisyon['yakit_emisyonlari_mt']
            })
        
        return pd.DataFrame(sonuclar)


class PyPSADispatch:
    """
    PyPSA tabanlı gelişmiş dispatch optimizasyonu.
    
    Bu sınıf saatlik talep profili ve yenilenebilir kapasite kısıtlarını
    dikkate alarak optimal üretim planlaması yapar.
    
    Not: PyPSA kütüphanesi gerektirir (pip install pypsa)
    """
    
    def __init__(self, santraller: pd.DataFrame, karbon_fiyati: float = 0):
        if not PYPSA_AVAILABLE:
            raise ImportError("PyPSA kütüphanesi yüklü değil. pip install pypsa")
        
        self.santraller = santraller
        self.karbon_fiyati = karbon_fiyati
        self.network = pypsa.Network()
        
        self._setup_network()
    
    def _setup_network(self):
        """PyPSA ağ yapısını kur."""
        # Türkiye tek bus olarak modelleniyor
        self.network.add("Bus", "TR", carrier="AC")
        
        # Santralleri ekle
        for _, santral in self.santraller.iterrows():
            yakit = santral['Yakit_Tipi']
            kapasite = santral['Kapasite_MW']
            
            # Marjinal maliyet hesapla
            mc = self._hesapla_marjinal_maliyet(yakit)
            
            self.network.add(
                "Generator",
                santral['Tesis_Adi'],
                bus="TR",
                p_nom=kapasite,
                marginal_cost=mc,
                carrier=yakit,
                efficiency=VERIMLILIK.get(yakit, 1.0)
            )
        
        # Talep ekle
        self.network.add(
            "Load",
            "TR_Talep",
            bus="TR",
            p_set=TURKIYE_ELEKTRIK["peak_demand_mw"] * 0.6  # Ortalama
        )
    
    def _hesapla_marjinal_maliyet(self, yakit: str) -> float:
        """Karbon dahil marjinal maliyet."""
        yakit_maliyet = YAKIT_FIYATLARI.get(yakit, 0)
        emisyon_faktor = EMISYON_FAKTORLERI_MWH.get(yakit, 0)
        karbon_maliyet = emisyon_faktor * self.karbon_fiyati
        
        return yakit_maliyet + karbon_maliyet
    
    def _talep_profili_olustur(self, snapshots: int) -> np.ndarray:
        """
        Türkiye için tipik saatlik talep profili oluştur.
        
        TEİAŞ verilerine dayalı mevsimsel ve günlük paternler içerir.
        
        Parameters
        ----------
        snapshots : int
            Saat sayısı (8760 = 1 yıl)
        
        Returns
        -------
        np.ndarray
            Saatlik talep değerleri (MW)
        """
        # Baz talep (ortalama)
        baz_talep = TURKIYE_ELEKTRIK["peak_demand_mw"] * 0.6
        
        talep = np.zeros(snapshots)
        for t in range(snapshots):
            saat = t % 24
            gun = (t // 24) % 365
            
            # Günlük profil (gece düşük, gündüz yüksek)
            if 6 <= saat < 22:
                gunluk_faktor = 1.1 + 0.2 * np.sin((saat - 6) * np.pi / 16)
            else:
                gunluk_faktor = 0.7
            
            # Mevsimsel profil (kış ve yaz yüksek)
            mevsim_faktor = 1.0 + 0.15 * np.cos(2 * np.pi * (gun - 15) / 365)
            
            talep[t] = baz_talep * gunluk_faktor * mevsim_faktor
        
        return talep
    
    def _yenilenebilir_profili_olustur(self, snapshots: int, yakit: str) -> np.ndarray:
        """
        Yenilenebilir kaynaklar için kapasite faktörü profili.
        
        Parameters
        ----------
        snapshots : int
            Saat sayısı
        yakit : str
            Yakıt tipi (Güneş, Rüzgar, vb.)
        
        Returns
        -------
        np.ndarray
            Saatlik kapasite faktörleri [0-1]
        """
        profil = np.ones(snapshots)
        
        if yakit == "Güneş":
            for t in range(snapshots):
                saat = t % 24
                gun = (t // 24) % 365
                
                # Gündüz üretim (06:00-18:00)
                if 6 <= saat <= 18:
                    # Öğlen maksimum
                    saat_faktor = np.sin((saat - 6) * np.pi / 12)
                    # Yaz ayları daha yüksek
                    mevsim_faktor = 0.7 + 0.3 * np.sin(2 * np.pi * (gun - 80) / 365)
                    profil[t] = saat_faktor * mevsim_faktor
                else:
                    profil[t] = 0.0
                    
        elif yakit == "Rüzgar":
            # Rüzgar daha stokastik - basitleştirilmiş model
            np.random.seed(42)
            for t in range(snapshots):
                gun = (t // 24) % 365
                # Kış aylarında daha yüksek
                mevsim_faktor = 0.25 + 0.15 * np.cos(2 * np.pi * (gun - 15) / 365)
                # Rastgele dalgalanma
                rastgele = 0.8 + 0.4 * np.random.random()
                profil[t] = min(1.0, mevsim_faktor * rastgele)
                
        elif yakit == "Hidrolik":
            # Bahar aylarında kar erimesi ile yüksek
            for t in range(snapshots):
                gun = (t // 24) % 365
                # Nisan-Haziran yüksek
                if 90 <= gun <= 180:
                    profil[t] = 0.5 + 0.3 * np.sin((gun - 90) * np.pi / 90)
                else:
                    profil[t] = 0.25 + 0.1 * np.random.random()
        
        return profil
    
    def optimize(self, snapshots: int = 8760, solver_name: str = "glpk") -> Dict:
        """
        Yıllık optimizasyon çalıştır (lopf - Linear Optimal Power Flow).
        
        PyPSA'nın lopf() fonksiyonunu kullanarak doğrusal optimal güç akışı
        hesaplaması yapar. Bu, karbon maliyeti dahil edilmiş marjinal 
        maliyetlere göre üretimi optimize eder.
        
        Parameters
        ----------
        snapshots : int
            Simülasyon adım sayısı (8760 = saatlik, 24 = günlük test)
        solver_name : str
            Kullanılacak çözücü: "glpk" (ücretsiz), "gurobi", "cplex"
        
        Returns
        -------
        dict
            Optimizasyon sonuçları (toplam üretim, emisyon, maliyet)
        
        Notes
        -----
        Referans: Brown, T., et al. (2018). PyPSA: Python for Power System 
        Analysis. Journal of Open Research Software, 6(1), p.4.
        """
        # Snapshot'ları ayarla
        self.network.set_snapshots(range(snapshots))
        
        # Saatlik talep profili ekle
        talep_profili = self._talep_profili_olustur(snapshots)
        self.network.loads_t.p_set = pd.DataFrame(
            {'TR_Talep': talep_profili}, 
            index=range(snapshots)
        )
        
        # Yenilenebilir kaynaklar için kapasite faktörü profili
        for gen_name in self.network.generators.index:
            yakit = self.network.generators.loc[gen_name, 'carrier']
            if yakit in ["Güneş", "Rüzgar", "Hidrolik"]:
                profil = self._yenilenebilir_profili_olustur(snapshots, yakit)
                p_nom = self.network.generators.loc[gen_name, 'p_nom']
                
                if gen_name not in self.network.generators_t.p_max_pu.columns:
                    self.network.generators_t.p_max_pu[gen_name] = profil
                else:
                    self.network.generators_t.p_max_pu.loc[:, gen_name] = profil
        
        # =================================================================
        # LOPF - Linear Optimal Power Flow
        # =================================================================
        # Brown et al. (2018): lopf() minimizes total system cost subject
        # to network constraints using linear programming.
        #
        # min Σ_t Σ_g (marginal_cost_g × p_g,t)
        # s.t. Σ_g p_g,t = demand_t  (power balance)
        #      0 ≤ p_g,t ≤ p_nom_g × p_max_pu_g,t  (capacity limits)
        # =================================================================
        
        try:
            # lopf = Linear Optimal Power Flow
            status = self.network.lopf(solver_name=solver_name, pyomo=False)
            
            if status[0] != 'ok':
                print(f"⚠️ Optimizasyon tamamlanmadı: {status}")
                return self._fallback_sonuclari(snapshots)
                
        except Exception as e:
            print(f"⚠️ lopf hatası: {e}")
            print("   Basit optimize() deneniyor...")
            try:
                self.network.optimize(solver_name=solver_name)
            except:
                return self._fallback_sonuclari(snapshots)
        
        # Sonuçları çıkar
        uretim = self.network.generators_t.p
        toplam_uretim = uretim.sum().sum()  # MWh
        
        # Emisyon hesabı
        toplam_emisyon = 0
        for gen in self.network.generators.index:
            yakit = self.network.generators.loc[gen, 'carrier']
            ef = EMISYON_FAKTORLERI_MWH.get(yakit, 0)
            gen_uretim = uretim[gen].sum()
            toplam_emisyon += gen_uretim * ef
        
        return {
            'toplam_uretim_twh': toplam_uretim / 1e6,
            'toplam_emisyon_mt': toplam_emisyon / 1e6,
            'uretim_detay': uretim.sum().to_dict(),
            'ortalama_fiyat': self.network.buses_t.marginal_price.mean().mean()
        }
    
    def _fallback_sonuclari(self, snapshots: int) -> Dict:
        """
        Optimizasyon başarısız olursa varsayılan sonuçlar döndür.
        
        Parameters
        ----------
        snapshots : int
            Simülasyon adım sayısı
        
        Returns
        -------
        dict
            Yaklaşık sonuçlar
        """
        # Basit merit-order dispatch ile tahmini sonuç
        yillik_talep_mwh = TURKIYE_ELEKTRIK["annual_consumption_twh"] * 1e6
        
        # Ortalama emisyon faktörü (Türkiye grid ortalaması ~0.5 tCO2/MWh)
        ortalama_ef = 0.48
        
        return {
            'toplam_uretim_twh': TURKIYE_ELEKTRIK["annual_consumption_twh"],
            'toplam_emisyon_mt': yillik_talep_mwh * ortalama_ef / 1e6,
            'uretim_detay': {},
            'ortalama_fiyat': 50.0,  # $/MWh varsayılan
            'not': 'Fallback sonuç - optimizasyon başarısız'
        }
    
    def karbon_fiyati_etkisi_pypsa(self, fiyat_aralik: List[float], snapshots: int = 24) -> pd.DataFrame:
        """
        Farklı karbon fiyatlarının PyPSA dispatch'e etkisini analiz et.
        
        Parameters
        ----------
        fiyat_aralik : list
            Test edilecek karbon fiyatları ($/tCO2)
        snapshots : int
            Her senaryo için simülasyon saati (24 = 1 gün, hız için)
        
        Returns
        -------
        pd.DataFrame
            Her fiyat için emisyon, maliyet, üretim karışımı
        """
        sonuclar = []
        
        for fiyat in fiyat_aralik:
            # Karbon fiyatını güncelle
            self.karbon_fiyati = fiyat
            
            # Generator marjinal maliyetlerini güncelle
            for gen_name in self.network.generators.index:
                yakit = self.network.generators.loc[gen_name, 'carrier']
                mc = self._hesapla_marjinal_maliyet(yakit)
                self.network.generators.loc[gen_name, 'marginal_cost'] = mc
            
            # Optimizasyonu çalıştır
            sonuc = self.optimize(snapshots=snapshots)
            
            sonuclar.append({
                'Karbon_Fiyati': fiyat,
                'Toplam_Emisyon_Mt': sonuc['toplam_emisyon_mt'] * (8760 / snapshots),  # Yıllık tahmin
                'Toplam_Uretim_TWh': sonuc['toplam_uretim_twh'] * (8760 / snapshots),
                'Ortalama_Fiyat': sonuc['ortalama_fiyat']
            })
        
        return pd.DataFrame(sonuclar)


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def yukle_santral_verileri(db_path: str = None) -> pd.DataFrame:
    """
    Veritabanından santral verilerini yükle.
    
    Parameters
    ----------
    db_path : str, optional
        SQLite veritabanı yolu
    
    Returns
    -------
    pd.DataFrame
        Santral verileri
    """
    if db_path is None:
        # Varsayılan yol
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        db_path = os.path.join(project_root, "iklim_veritabani.sqlite")
    
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT * FROM tesisler", conn)
        conn.close()
        return df
    else:
        print(f"⚠️ Veritabanı bulunamadı: {db_path}")
        return _ornek_santral_verisi()


def _ornek_santral_verisi() -> pd.DataFrame:
    """Örnek santral verisi oluştur (test için)."""
    return pd.DataFrame([
        {"Tesis_Adi": "Afsin-Elbistan A", "Kapasite_MW": 1355, "Yakit_Tipi": "Linyit"},
        {"Tesis_Adi": "Afsin-Elbistan B", "Kapasite_MW": 1440, "Yakit_Tipi": "Linyit"},
        {"Tesis_Adi": "Isken Sugözü", "Kapasite_MW": 1320, "Yakit_Tipi": "Kömür"},
        {"Tesis_Adi": "Gebze CCGT", "Kapasite_MW": 1540, "Yakit_Tipi": "Doğalgaz"},
        {"Tesis_Adi": "Atatürk HES", "Kapasite_MW": 2400, "Yakit_Tipi": "Hidrolik"},
        {"Tesis_Adi": "Karapınar GES", "Kapasite_MW": 1350, "Yakit_Tipi": "Güneş"},
        {"Tesis_Adi": "Balıkesir RES", "Kapasite_MW": 850, "Yakit_Tipi": "Rüzgar"},
    ])


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TR-ZERO Enerji Dispatch Modülü - Test")
    print("=" * 60)
    
    # Santral verilerini yükle
    santraller = yukle_santral_verileri()
    print(f"\n✅ {len(santraller)} santral yüklendi")
    
    # Karbon fiyatsız dispatch
    dispatch_0 = EnerjiDispatchModulu(santraller, karbon_fiyati=0)
    sonuc_0 = dispatch_0.hesapla_yillik_emisyon()
    print(f"\n📊 Karbon Fiyatı: $0/tCO2")
    print(f"   Toplam Emisyon: {sonuc_0['toplam_emisyon_mt']:.1f} Mt")
    
    # Karbon fiyatlı dispatch
    dispatch_50 = EnerjiDispatchModulu(santraller, karbon_fiyati=50)
    sonuc_50 = dispatch_50.hesapla_yillik_emisyon()
    print(f"\n📊 Karbon Fiyatı: $50/tCO2")
    print(f"   Toplam Emisyon: {sonuc_50['toplam_emisyon_mt']:.1f} Mt")
    print(f"   Karbon Maliyeti: ${sonuc_50['karbon_maliyeti_musd']:.0f}M")
    
    # Fiyat analizi
    print("\n📈 Karbon Fiyatı Duyarlılık Analizi:")
    fiyatlar = [0, 20, 40, 60, 80, 100]
    analiz = dispatch_50.karbon_fiyati_etkisi(fiyatlar)
    print(analiz[['Karbon_Fiyati', 'Toplam_Emisyon_Mt', 'Karbon_Maliyeti_MUSD']].to_string(index=False))
    
    print("\n✅ Test tamamlandı!")
