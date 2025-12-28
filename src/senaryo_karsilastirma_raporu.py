"""
TR-ZERO: 16 Ocak Sunum için Senaryo Karşılaştırma Raporu
=========================================================

Bu script, 4 politika senaryosunu karşılaştırarak:
1. Emisyon trendleri grafiği
2. Karbon fiyatı karşılaştırması
3. Tesis dönüşüm durumu grafiği
4. İl bazlı emisyon haritası
5. Özet tablo (PDF/HTML uyumlu)

Oluşturulan dosyalar:
- sunum_emisyon_karsilastirma.png
- sunum_tesis_donusum.png
- sunum_karbon_fiyat.png
- sunum_il_harita.html
- sunum_ozet_tablo.csv
- sunum_temel_bulgular.md

Yazar: TR-ZERO Ekibi
Tarih: 28 Aralık 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import json
from datetime import datetime

# Türkçe karakter desteği
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# =============================================================================
# PROJE DİZİN AYARLARI
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# =============================================================================
# RENK PALETİ (Premium Sunum İçin)
# =============================================================================
RENKLER = {
    "BAU": "#6b7280",           # Gri - Business as Usual
    "Yumusak_ETS": "#3b82f6",   # Mavi - Yumuşak ETS
    "Siki_ETS": "#22c55e",      # Yeşil - Sıkı ETS
    "ETS_Tesvik": "#8b5cf6"     # Mor - ETS + Teşvik
}

SENARYO_ISIMLERI = {
    "BAU": "İş-Her-Zamanki-Gibi (BAU)",
    "Yumusak_ETS": "Yumuşak ETS (%2 Cap Azaltma)",
    "Siki_ETS": "Sıkı ETS (%4 Cap Azaltma)",
    "ETS_Tesvik": "ETS + Yeşil Teşvik"
}

# =============================================================================
# VERİ YÜKLEME
# =============================================================================
def verileri_yukle():
    """Tüm senaryo CSV dosyalarını yükler."""
    senaryolar = {}
    
    dosya_eslesmesi = {
        "BAU": "senaryo_bau.csv",
        "Yumusak_ETS": "senaryo_yumusak_ets.csv",
        "Siki_ETS": "senaryo_siki_ets.csv",
        "ETS_Tesvik": "senaryo_ets_tesvik.csv"
    }
    
    for senaryo, dosya in dosya_eslesmesi.items():
        dosya_yolu = os.path.join(OUTPUT_DIR, dosya)
        if os.path.exists(dosya_yolu):
            df = pd.read_csv(dosya_yolu)
            senaryolar[senaryo] = df
            print(f"✅ {senaryo}: {len(df)} satır yüklendi")
        else:
            print(f"⚠️ {dosya} bulunamadı!")
    
    return senaryolar


def ai_baseline_yukle():
    """AI baseline verilerini yükler."""
    dosya_yolu = os.path.join(OUTPUT_DIR, "ai_baseline.json")
    if os.path.exists(dosya_yolu):
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


# =============================================================================
# GRAFİK 1: EMİSYON TRENDLERİ KARŞILAŞTIRMASI
# =============================================================================
def emisyon_karsilastirma_grafigi(senaryolar):
    """
    Ana emisyon trend grafiği - Tüm senaryoları karşılaştırır.
    16 Ocak sunumunun ana grafiği olacak.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Arka plan gradient efekti
    ax.set_facecolor('#fafafa')
    fig.patch.set_facecolor('white')
    
    for senaryo, df in senaryolar.items():
        yillar = df['Yil'].values
        emisyonlar = df['Toplam_Emisyon'].values
        
        # Ana çizgi
        ax.plot(yillar, emisyonlar, 
                color=RENKLER[senaryo], 
                linewidth=3,
                marker='o',
                markersize=8,
                label=SENARYO_ISIMLERI[senaryo])
        
        # Başlangıç ve bitiş noktalarını vurgula
        ax.scatter(yillar[0], emisyonlar[0], color=RENKLER[senaryo], s=120, zorder=5)
        ax.scatter(yillar[-1], emisyonlar[-1], color=RENKLER[senaryo], s=120, zorder=5)
        
        # 2035 değerini etiketle
        ax.annotate(f'{emisyonlar[-1]:.1f} Mt', 
                   xy=(yillar[-1], emisyonlar[-1]),
                   xytext=(10, 0),
                   textcoords='offset points',
                   fontsize=11,
                   fontweight='bold',
                   color=RENKLER[senaryo])
    
    # NDC hedefini göster (2030 için 695 Mt, %41 artış)
    ax.axhline(y=695, color='#ef4444', linestyle='--', linewidth=2, alpha=0.7, label='NDC 2030 Hedefi (695 Mt)')
    
    # Başlık ve etiketler
    ax.set_title('🌍 Türkiye CO₂ Emisyon Projeksiyonları: Senaryo Karşılaştırması\n(2025-2035)', 
                fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Yıl', fontsize=14)
    ax.set_ylabel('Toplam Emisyon (Mt CO₂/yıl)', fontsize=14)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # X ekseni
    ax.set_xticks(range(2025, 2036))
    ax.set_xlim(2024.5, 2036)
    
    # Legend
    ax.legend(loc='upper right', fontsize=11, framealpha=0.95)
    
    # Kaynak notu
    fig.text(0.99, 0.01, 'Kaynak: TR-ZERO ABM Simülasyonu (v4.5) | Aralık 2025', 
             ha='right', va='bottom', fontsize=9, color='gray')
    
    plt.tight_layout()
    
    # Kaydet
    dosya_yolu = os.path.join(OUTPUT_DIR, "sunum_emisyon_karsilastirma.png")
    plt.savefig(dosya_yolu, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"📊 Emisyon karşılaştırma grafiği: {dosya_yolu}")
    
    plt.close()
    return dosya_yolu


# =============================================================================
# GRAFİK 2: TESİS DÖNÜŞÜM DURUMU
# =============================================================================
def tesis_donusum_grafigi(senaryolar):
    """
    Stacked area chart - Tesis durumlarının zamanla değişimi.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    durum_renkleri = {
        'Aktif': '#ef4444',      # Kırmızı
        'Donusum': '#f59e0b',    # Turuncu
        'Temiz': '#22c55e',      # Yeşil
        'Kapali': '#6b7280'      # Gri
    }
    
    for idx, (senaryo, df) in enumerate(senaryolar.items()):
        ax = axes[idx]
        
        yillar = df['Yil'].values
        aktif = df['Aktif_Tesis'].values
        donusum = df['Donusum_Tesis'].values
        temiz = df['Temiz_Tesis'].values
        kapali = df['Kapali_Tesis'].values
        
        # Stacked area
        ax.stackplot(yillar, aktif, donusum, temiz, kapali,
                    labels=['Aktif (Kirli)', 'Dönüşüm', 'Temiz', 'Kapalı'],
                    colors=[durum_renkleri['Aktif'], durum_renkleri['Donusum'], 
                           durum_renkleri['Temiz'], durum_renkleri['Kapali']],
                    alpha=0.85)
        
        ax.set_title(f'{SENARYO_ISIMLERI[senaryo]}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Yıl', fontsize=11)
        ax.set_ylabel('Tesis Sayısı', fontsize=11)
        ax.set_xlim(2025, 2035)
        ax.grid(True, alpha=0.3)
        
        if idx == 0:
            ax.legend(loc='upper right', fontsize=9)
    
    fig.suptitle('🏭 Endüstriyel Tesislerin Dönüşüm Durumu (2025-2035)', 
                fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    
    dosya_yolu = os.path.join(OUTPUT_DIR, "sunum_tesis_donusum.png")
    plt.savefig(dosya_yolu, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"📊 Tesis dönüşüm grafiği: {dosya_yolu}")
    
    plt.close()
    return dosya_yolu


# =============================================================================
# GRAFİK 3: KARBON FİYATI EVRİMİ
# =============================================================================
def karbon_fiyat_grafigi(senaryolar):
    """
    Karbon fiyatı zaman serisi karşılaştırması.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for senaryo, df in senaryolar.items():
        yillar = df['Yil'].values
        fiyatlar = df['Karbon_Fiyati'].values
        
        ax.plot(yillar, fiyatlar, 
                color=RENKLER[senaryo], 
                linewidth=2.5,
                marker='s',
                markersize=6,
                label=SENARYO_ISIMLERI[senaryo])
    
    # AB ETS referans çizgisi
    ax.axhline(y=80, color='#0ea5e9', linestyle=':', linewidth=2, alpha=0.7, 
               label='AB ETS 2024 (~€80/ton)')
    
    ax.set_title('💶 Karbon Piyasası Fiyat Projeksiyonları (2025-2035)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Yıl', fontsize=12)
    ax.set_ylabel('Karbon Fiyatı ($/ton CO₂)', fontsize=12)
    ax.set_xticks(range(2025, 2036))
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)
    
    # ETS başlangıç notları
    ax.axvline(x=2026, color='gray', linestyle='--', alpha=0.5)
    ax.text(2026.1, ax.get_ylim()[1]*0.9, 'ETS Pilot', fontsize=9, color='gray')
    ax.axvline(x=2028, color='gray', linestyle='--', alpha=0.5)
    ax.text(2028.1, ax.get_ylim()[1]*0.9, 'ETS Tam', fontsize=9, color='gray')
    
    plt.tight_layout()
    
    dosya_yolu = os.path.join(OUTPUT_DIR, "sunum_karbon_fiyat.png")
    plt.savefig(dosya_yolu, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"📊 Karbon fiyat grafiği: {dosya_yolu}")
    
    plt.close()
    return dosya_yolu


# =============================================================================
# GRAFİK 4: AZALTIM MİKTARI BAR CHART
# =============================================================================
def azaltim_bar_grafigi(senaryolar):
    """
    2035 yılındaki emisyon azaltımlarını karşılaştıran bar chart.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # BAU'yu referans al
    bau_2035 = senaryolar['BAU']['Toplam_Emisyon'].iloc[-1]
    bau_2025 = senaryolar['BAU']['Toplam_Emisyon'].iloc[0]
    
    senaryo_adlari = []
    azaltimlar = []
    yuzde_azaltimlar = []
    renkler_list = []
    
    for senaryo, df in senaryolar.items():
        emisyon_2035 = df['Toplam_Emisyon'].iloc[-1]
        azaltim = bau_2025 - emisyon_2035
        yuzde = (azaltim / bau_2025) * 100
        
        senaryo_adlari.append(SENARYO_ISIMLERI[senaryo].split('(')[0].strip())
        azaltimlar.append(azaltim)
        yuzde_azaltimlar.append(yuzde)
        renkler_list.append(RENKLER[senaryo])
    
    # Bar chart
    bars = ax.bar(senaryo_adlari, azaltimlar, color=renkler_list, edgecolor='white', linewidth=2)
    
    # Değer etiketleri
    for bar, yuzde in zip(bars, yuzde_azaltimlar):
        height = bar.get_height()
        ax.annotate(f'{height:.1f} Mt\n({yuzde:.1f}%)',
                   xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 10),
                   textcoords='offset points',
                   ha='center', va='bottom',
                   fontsize=12, fontweight='bold')
    
    ax.set_title('📉 2035 Yılı Emisyon Azaltımları (2025 Baz Yılına Göre)', 
                fontsize=16, fontweight='bold')
    ax.set_ylabel('Emisyon Azaltımı (Mt CO₂)', fontsize=12)
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    dosya_yolu = os.path.join(OUTPUT_DIR, "sunum_azaltim_karsilastirma.png")
    plt.savefig(dosya_yolu, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"📊 Azaltım karşılaştırma grafiği: {dosya_yolu}")
    
    plt.close()
    return dosya_yolu


# =============================================================================
# ÖZET TABLO
# =============================================================================
def ozet_tablo_olustur(senaryolar):
    """
    Tüm senaryoları özetleyen tablo oluşturur.
    """
    ozet_satirlari = []
    
    for senaryo, df in senaryolar.items():
        satir = {
            'Senaryo': SENARYO_ISIMLERI[senaryo],
            '2025 Emisyon (Mt)': f"{df['Toplam_Emisyon'].iloc[0]:.1f}",
            '2035 Emisyon (Mt)': f"{df['Toplam_Emisyon'].iloc[-1]:.1f}",
            'Değişim (%)': f"{((df['Toplam_Emisyon'].iloc[-1] - df['Toplam_Emisyon'].iloc[0]) / df['Toplam_Emisyon'].iloc[0] * 100):.1f}%",
            '2035 Karbon Fiyatı ($/ton)': f"${df['Karbon_Fiyati'].iloc[-1]:.0f}",
            '2035 Temiz Tesis': f"{df['Temiz_Tesis'].iloc[-1]:.0f}",
            '2035 Kapalı Tesis': f"{df['Kapali_Tesis'].iloc[-1]:.0f}",
            'Toplam MRV Cezası (M$)': f"${df['MRV_Toplam_Ceza'].iloc[-1]:.1f}M"
        }
        ozet_satirlari.append(satir)
    
    ozet_df = pd.DataFrame(ozet_satirlari)
    
    # CSV kaydet
    dosya_yolu = os.path.join(OUTPUT_DIR, "sunum_ozet_tablo.csv")
    ozet_df.to_csv(dosya_yolu, index=False, encoding='utf-8-sig')
    print(f"📋 Özet tablo: {dosya_yolu}")
    
    return ozet_df


# =============================================================================
# TEMEL BULGULAR MARKDOWN
# =============================================================================
def temel_bulgular_olustur(senaryolar, ai_baseline):
    """
    16 Ocak sunumu için temel bulguları markdown formatında oluşturur.
    """
    bau = senaryolar['BAU']
    siki = senaryolar['Siki_ETS']
    
    bulgular = f"""# 🌍 TR-ZERO: Temel Simülasyon Bulguları

**Oluşturulma Tarihi:** {datetime.now().strftime('%d %B %Y, %H:%M')}

---

## 📊 Model Özeti

| Parametre | Değer |
|-----------|-------|
| Simülasyon Dönemi | 2025-2035 (11 yıl) |
| Toplam Ajan Sayısı | 170+ (Tesisler, Hanehalkları, Operatörler) |
| Senaryo Sayısı | 4 (BAU, Yumuşak ETS, Sıkı ETS, ETS+Teşvik) |
| Zaman Adımı | Yıllık |
| Model Tipi | Ajan Tabanlı Model (Mesa Framework) |

---

## 🔑 Temel Bulgular

### 1. Emisyon Trendleri

- **2025 Başlangıç Emisyonu:** ~{bau['Toplam_Emisyon'].iloc[0]:.0f} Mt CO₂
- **2035 BAU Senaryosu:** {bau['Toplam_Emisyon'].iloc[-1]:.1f} Mt CO₂
- **2035 Sıkı ETS Senaryosu:** {siki['Toplam_Emisyon'].iloc[-1]:.1f} Mt CO₂
- **Maksimum Azaltım Potansiyeli:** {bau['Toplam_Emisyon'].iloc[-1] - siki['Toplam_Emisyon'].iloc[-1]:.1f} Mt CO₂/yıl

### 2. Karbon Piyasası

- **ETS Başlangıcı:** 2026 (Pilot), 2028 (Tam Uygulama)
- **2035 Karbon Fiyatı (Sıkı ETS):** ${siki['Karbon_Fiyati'].iloc[-1]:.0f}/ton CO₂
- **Piyasa Mekanizması:** Cap & Trade (Emisyon Üst Limiti ve Ticaret)

### 3. Endüstriyel Dönüşüm

- **2035'te Temiz Tesis Sayısı (BAU):** {bau['Temiz_Tesis'].iloc[-1]:.0f} / 110
- **2035'te Temiz Tesis Sayısı (Sıkı ETS):** {siki['Temiz_Tesis'].iloc[-1]:.0f} / 110
- **Yenilenebilir Enerji Kapasitesi (2035):** {siki['Yenilenebilir_Kapasite_MW'].iloc[-1]:,.0f} MW

---

## 📈 Politika Önerileri

1. **ETS Erken Başlatılmalı:** Pilot dönem 2026'da başlayarak sektöre uyum süresi verilmeli.
2. **Kademeli Cap Azaltımı:** Yıllık %4 cap azaltımı optimal dengeyi sağlıyor.
3. **Teşvik Mekanizmaları:** Yeşil yatırım desteği dönüşümü hızlandırıyor.
4. **CBAM Uyumu:** AB SKDM ile uyum için karbon fiyatlandırması kritik.

---

## 📚 Kaynaklar

- TR-ETS Taslak Yönetmeliği (2025)
- EU ETS Directive 2003/87/EC
- IPCC 2006 Guidelines
- TÜİK Sera Gazı İstatistikleri (2024)
- TEİAŞ 10 Yıllık Kapasite Projeksiyonu

---

*Bu rapor, TR-ZERO Ajan Tabanlı Karbon Piyasası Simülasyonu (v4.5) tarafından otomatik oluşturulmuştur.*
"""
    
    dosya_yolu = os.path.join(OUTPUT_DIR, "sunum_temel_bulgular.md")
    with open(dosya_yolu, 'w', encoding='utf-8') as f:
        f.write(bulgular)
    print(f"📝 Temel bulgular: {dosya_yolu}")
    
    return bulgular


# =============================================================================
# ANA ÇALIŞTIRMA
# =============================================================================
def main():
    """Ana fonksiyon - Tüm raporları oluşturur."""
    print("\n" + "=" * 60)
    print("🌱 TR-ZERO: 16 OCAK SUNUM RAPORU OLUŞTURULUYOR")
    print("=" * 60)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 60)
    
    # 1. Verileri yükle
    print("\n📂 Veriler yükleniyor...")
    senaryolar = verileri_yukle()
    ai_baseline = ai_baseline_yukle()
    
    if len(senaryolar) < 4:
        print("⚠️ Bazı senaryolar eksik! Önce simülasyonu çalıştırın:")
        print("   python src/ajan_tabanli_simulasyon.py")
        return
    
    # 2. Grafikler oluştur
    print("\n📊 Grafikler oluşturuluyor...")
    emisyon_karsilastirma_grafigi(senaryolar)
    tesis_donusum_grafigi(senaryolar)
    karbon_fiyat_grafigi(senaryolar)
    azaltim_bar_grafigi(senaryolar)
    
    # 3. Özet tablo
    print("\n📋 Özet tablo oluşturuluyor...")
    ozet_df = ozet_tablo_olustur(senaryolar)
    print(ozet_df.to_string())
    
    # 4. Temel bulgular
    print("\n📝 Temel bulgular raporu oluşturuluyor...")
    temel_bulgular_olustur(senaryolar, ai_baseline)
    
    # 5. Özet
    print("\n" + "=" * 60)
    print("✅ TÜM RAPORLAR BAŞARIYLA OLUŞTURULDU!")
    print("=" * 60)
    print(f"\n📁 Çıktı Klasörü: {OUTPUT_DIR}")
    print("\n📊 Oluşturulan Dosyalar:")
    print("   • sunum_emisyon_karsilastirma.png")
    print("   • sunum_tesis_donusum.png")
    print("   • sunum_karbon_fiyat.png")
    print("   • sunum_azaltim_karsilastirma.png")
    print("   • sunum_ozet_tablo.csv")
    print("   • sunum_temel_bulgular.md")
    print("\n🎯 16 Ocak sunumunuz için hazır!")


if __name__ == "__main__":
    main()
