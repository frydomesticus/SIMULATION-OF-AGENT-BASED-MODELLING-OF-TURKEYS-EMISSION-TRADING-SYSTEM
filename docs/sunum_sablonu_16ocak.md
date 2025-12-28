# 🎤 TR-ZERO: 16 Ocak 2026 Sunum Şablonu

**Tez Rapor Sunumu için PowerPoint İskeleti**

---

## 📋 Sunum Bilgileri

| Bilgi | Değer |
|-------|-------|
| **Tarih** | 16 Ocak 2026 |
| **Süre** | 15-20 dakika sunum + 5-10 dakika soru-cevap |
| **Format** | PowerPoint / Google Slides |
| **Hedef Kitle** | Tez jürisi (akademisyenler) |

---

## 📑 SLAYT YAPISI

---

### SLAYT 1: BAŞLIK

```
TR-ZERO: Ulusal İklim Karar Destek Sistemi
Türkiye Emisyon Ticaret Sistemi için Ajan Tabanlı Simülasyon

───────────────────────────────────────

İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Danışman: Deniz Efendioğlu

Endüstri Mühendisliği Bölümü
16 Ocak 2026
```

**Görsel:** Proje logosu, üniversite logosu

---

### SLAYT 2: GÜNDEM (1 dk)

```
📋 GÜNDEM

1. Problem Tanımı ve Motivasyon
2. Literatür Özeti
3. Önerilen Yaklaşım: Ajan Tabanlı Modelleme
4. Model Mimarisi ve Tasarım
5. Prototip Demo
6. Ön Sonuçlar
7. Kısıtlamalar ve Gelecek Çalışmalar
8. Sonuç
```

---

### SLAYT 3: PROBLEM TANIMI (2 dk)

```
🌍 PROBLEM TANIMI

Türkiye İklim Değişikliği Mücadelesi:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 2022 Emisyonları: 515.5 Mt CO₂e (1990'a göre +135%)
• Paris Anlaşması: 2015'te imza, 2021'de onay
• 2053 Net Sıfır Hedefi: Ulusal taahhüt
• 2026 ETS Başlangıcı: Türkiye Emisyon Ticaret Sistemi

❓ ARAŞTIRMA SORULARI:
1. ETS fiyatlarının emisyon azaltımına etkisi nedir?
2. Hangi politika senaryosu en etkili?
3. İl bazında etkilerin dağılımı nasıl olacak?
```

**Görsel:** Türkiye emisyon trendi grafiği (1990-2022)

---

### SLAYT 4: MOTİVASYON (1 dk)

```
💡 MOTİVASYON

Neden Bu Çalışma?
━━━━━━━━━━━━━━━━━

✗ Türkiye için ETS simülasyon modeli YOK
✗ İl bazlı dağılım analizi MEVCUT DEĞİL
✗ Tesis düzeyi modelleme YAPILMAMIŞ
✗ Politika karşılaştırması SİSTEMATİK DEĞİL

✓ TR-ZERO bu boşlukları dolduruyor
✓ Karar vericiler için kanıt tabanlı araç
✓ Açık kaynak, tekrarlanabilir metodoloji
```

---

### SLAYT 5: LİTERATÜR ÖZETİ - 1 (2 dk)

```
📚 LİTERATÜR: ETS SİSTEMLERİ

Küresel ETS Durumu (ICAP 2024):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 36 aktif ETS sistemi
• Global emisyonların %17'si kapsama dahil
• AB ETS: En olgun piyasa (2005'ten beri)

| Sistem | Başlangıç | Fiyat (2024) |
|--------|-----------|--------------|
| AB ETS | 2005 | ~€80/ton |
| Çin ETS | 2021 | ~$12/ton |
| TR-ETS | 2026 (taslak) | $20-50/ton (tahmin) |

Önemli Referanslar:
• Yu et al. (2020) - ABM ETS simülasyonu
• Zhang & Wei (2010) - EU ETS analizi
```

---

### SLAYT 6: LİTERATÜR ÖZETİ - 2 (1 dk)

```
📚 LİTERATÜR: AJAN TABANLI MODELLEME

ABM Özellikleri:
━━━━━━━━━━━━━━━━

• Heterojen ajanlar
• Aşağıdan yukarıya (bottom-up) yaklaşım
• Kompleks davranış simülasyonu
• Politika deneyimi için ideal

Metodoloji Temelleri:
• Bonabeau (2002) - ABM temelleri
• Zhou et al. (2016) - Karbon piyasası ABM
• Tang et al. (2017) - Açık artırma tasarımı

LİTERATÜR BOŞLUĞU:
❌ Türkiye için ETS ABM çalışması bulunmamaktadır
```

---

### SLAYT 7: ÖNERİLEN YAKLAŞIM (2 dk)

```
🎯 ÖNERİLEN YAKLAŞIM: TR-ZERO

Hibrit Ajan Tabanlı Model:
━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────┐
│           TR-ZERO MİMARİSİ              │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ ABM Core │──│  System  │──│Dispatch│ │
│  │ (Mesa)   │  │ Dynamics │  │ Modülü │ │
│  └──────────┘  └──────────┘  └────────┘ │
├─────────────────────────────────────────┤
│  Veri Katmanı: SQLite + CSV + GeoJSON   │
└─────────────────────────────────────────┘

Teknoloji Yığını:
• Python 3.11 + Mesa Framework
• Streamlit Dashboard
• Matplotlib + Plotly görselleştirme
```

---

### SLAYT 8: MODEL MİMARİSİ - AJAN TİPLERİ (2 dk)

```
🏭 AJAN TİPLERİ (v2.1)

┌─────────────────────────────────────────────────────────────┐
│  AJAN               │ SAYI  │ KARAR MEKANİZMASI             │
├─────────────────────────────────────────────────────────────┤
│  🏭 Endüstriyel Tesis │  110  │ MAC analizi, NPV hesabı       │
│  🏢 İhracatçı Tesis   │   10  │ CBAM maliyet optimizasyonu    │
│  📊 Piyasa Operatörü  │    1  │ Cap ayarlama, fiyat belirleme │
│  🔍 MRV Ajanı         │    1  │ Denetim, ceza mekanizması     │
│  🏠 Hanehalkı         │   50  │ Fiyat elastikiyeti            │
│  🚗 Ulaşım            │   ~   │ EV penetrasyonu               │
└─────────────────────────────────────────────────────────────┘

Toplam: 170+ ajan
```

---

### SLAYT 9: KARAR MEKANİZMASI (1 dk)

```
🧠 TESİS KARAR MEKANİZMASI

Üç Aşamalı Karar:
━━━━━━━━━━━━━━━━━

1. MAC ANALİZİ
   • Karbon fiyatı vs Marjinal Azaltım Maliyeti
   • McKinsey (2009) eğrileri adapte edildi

2. NPV HESABI
   • r = %8 (Türkiye risk primi dahil)
   • 10 yıl ekonomik ömür
   • NPV > 0 → Yatırım kararı

3. KAPANMA EŞİĞİ
   • Net emisyon × Karbon fiyatı > Maliyet limiti
   • Tesis kapanır veya dönüşür
```

---

### SLAYT 10: SENARYOLAR (1 dk)

```
📊 POLİTİKA SENARYOLARI

┌────────────────────────────────────────────────────────────┐
│ SENARYO        │ CAP AZALTMA │ TEŞVİK   │ SKDM FİYAT      │
├────────────────────────────────────────────────────────────┤
│ 🔴 BAU         │     %0      │   $0     │   $80/ton       │
│ 🟡 Yumuşak ETS │    %2/yıl   │  $50M    │   $80/ton       │
│ 🟢 Sıkı ETS    │    %4/yıl   │  $50M    │   $80/ton       │
│ 🟣 ETS+Teşvik  │    %4/yıl   │ $100M    │   $80/ton       │
└────────────────────────────────────────────────────────────┘

• Simülasyon dönemi: 2025-2035 (11 yıl)
• Zaman adımı: Yıllık
• Monte Carlo: 100-500 iterasyon (belirsizlik analizi)
```

---

### SLAYT 11: PROTOTİP DEMO (3 dk)

```
🖥️ PROTOTİP DEMO

[CANLI DEMO veya VİDEO]

Dashboard Özellikleri:
━━━━━━━━━━━━━━━━━━━━

• Gerçek zamanlı simülasyon
• 4 senaryo karşılaştırması
• İl bazlı emisyon haritası
• Tesis dönüşüm görselleştirme
• Karbon piyasası dinamikleri

Komut: streamlit run src/dashboard_v4.py
```

**Görsel:** Dashboard ekran görüntüsü veya canlı demo

---

### SLAYT 12: SONUÇLAR - EMİSYON TRENDLERİ (2 dk)

```
📈 ÖN SONUÇLAR: EMİSYON PROJEKSİYONLARI

[EMİSYON KARŞILAŞTIRMA GRAFİĞİ]
sunum_emisyon_karsilastirma.png

Temel Bulgular:
• BAU 2035: 135.1 Mt → %7.3 azalma
• Sıkı ETS 2035: 137.1 Mt → %8.3 azalma
• Maksimum azaltım potansiyeli: ~10 Mt/yıl
```

---

### SLAYT 13: SONUÇLAR - TESİS DÖNÜŞÜMÜ (1 dk)

```
🏭 ÖN SONUÇLAR: TESİS DÖNÜŞÜMÜ

[TESİS DÖNÜŞÜM GRAFİĞİ]
sunum_tesis_donusum.png

• 2025: 110 aktif (kirli) tesis
• 2035: 80 temiz tesis, 0 kapalı
• Dönüşüm süresi: 3-5 yıl (yatırım bağımlı)
```

---

### SLAYT 14: SONUÇLAR - İL BAZLI ETKİ (1 dk)

```
🗺️ ÖN SONUÇLAR: İL BAZLI ETKİ

[TÜRKİYE HARİTASI - İL EMİSYONLARI]

En Yüksek Emisyonlu İller (2035):
1. Hatay: 15.8 Mt (termik santraller)
2. İstanbul: 8.9 Mt (sanayi + konut)
3. Ankara: 10.0 Mt (enerji + ulaşım)
4. İzmir: 7.2 Mt (liman + sanayi)

81 il için dağılım katsayıları hesaplandı
```

---

### SLAYT 15: KISITLAMALAR (1 dk)

```
⚠️ KISITLAMALAR VE SINIRLILIKLAR

Veri Kısıtlamaları:
• Tesis düzeyi gerçek emisyon verileri kamuya açık değil
• İl bazlı dağılım katsayıları tahmine dayalı
• MAC eğrileri uluslararası kaynaklardan adapte edildi

Model Basitleştirmeleri:
• Yıllık zaman adımı (saatlik dispatch yok)
• Lineer cap azaltma varsayımı
• Eksik ajan tipleri (finans, belediye, vb.)

Doğrulama Eksiklikleri:
• Hindcast validasyonu henüz tamamlanmadı
• Duyarlılık analizi devam ediyor
```

---

### SLAYT 16: HAZİRAN'A ROADMAP - 1 (1 dk)

```
🛣️ HAZİRAN 2026 YOL HARİTASI (1/2)

OCAK-ŞUBAT:
━━━━━━━━━━━
□ İl bazlı detaylı emisyon veritabanı (81 il)
□ 50-100 tesis detaylı modelleme
□ MAC eğrileri yerelleştirme
□ 11 ajan tipinin tamamlanması

MART-NİSAN:
━━━━━━━━━━━
□ System Dynamics entegrasyonu (PySD)
□ Enerji dispatch modülü (PyPSA)
□ Monte Carlo analizi (500 koşu)
□ Sensitivite analizi (SALib)
```

---

### SLAYT 17: HAZİRAN'A ROADMAP - 2 (1 dk)

```
🛣️ HAZİRAN 2026 YOL HARİTASI (2/2)

MAYIS:
━━━━━
□ Hindcast doğrulama (2020-2023)
□ İnteraktif dashboard (Folium haritalar)
□ Maliyet-etkinlik analizi
□ Politika önerileri raporu

HAZİRAN:
━━━━━━━
□ Tam proje raporu (50-80 sayfa)
□ Açık kaynak GitHub deposu
□ Dokümantasyon (Sphinx)
□ Makale taslağı (Energy Policy / MDPI Sustainability)
```

---

### SLAYT 18: BEKLENEN KATKILAR (1 dk)

```
🎯 BEKLENEN KATKILAR

Akademik Katkı:
• Türkiye için ilk ETS ABM simülasyonu
• Hibrit model yaklaşımı (ABM + SD + Dispatch)
• İl bazlı emisyon dağılım metodolojisi

Pratik Katkı:
• Karar vericiler için politika karşılaştırma aracı
• Açık kaynak, tekrarlanabilir model
• İnteraktif görselleştirme platformu

Potansiyel Yayın:
• Energy Policy (Q1 dergi)
• MDPI Sustainability (açık erişim)
• Ulusal iklim konferansı bildirisi
```

---

### SLAYT 19: SONUÇ (1 dk)

```
✅ SONUÇ

TR-ZERO Projesi:
━━━━━━━━━━━━━━━━

• Türkiye ETS için ajan tabanlı simülasyon modeli
• 170+ ajan, 4 politika senaryosu
• 2025-2035 projeksiyon dönemi
• İl bazlı dağılım analizi

16 Ocak 2026 itibariyle:
• Çalışan prototip ✅
• 4 senaryo sonuçları ✅
• Dashboard ✅

Haziran 2026'ya kadar:
• Tam model tamamlanacak
• Kapsamlı analiz ve doğrulama yapılacak
```

---

### SLAYT 20: TEŞEKKÜRLER

```
🙏 TEŞEKKÜRLER

Sorularınız için teşekkür ederiz.

───────────────────────────────────────

İletişim:
📧 [e-posta adresleri]

GitHub:
🔗 github.com/[kullanıcı]/tr-zero

───────────────────────────────────────

İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Danışman: Deniz Efendioğlu
16 Ocak 2026
```

---

## 📎 YEDEK SLAYTLAR (Soru-Cevap İçin)

### YEDEK 1: DETAYLI MAC EĞRİSİ

```
Marjinal Azaltım Maliyeti Eğrisi:
• Negatif MAC: Enerji verimliliği (-$15/ton)
• Orta MAC: Yakıt değişimi ($35/ton)
• Yüksek MAC: CCS teknolojisi ($80/ton)
[Kaynak: McKinsey 2009, Türkiye'ye uyarlanmış]
```

### YEDEK 2: MONTE CARLO SONUÇLARI

```
100 iterasyon sonuçları:
• Medyan 2035 emisyon: 136.5 Mt
• P5-P95 aralığı: 130-145 Mt
• Karbon fiyatı dağılımı: $18-25/ton
```

### YEDEK 3: CBAM/SKDM ETKİSİ

```
AB Sınırda Karbon Düzenlemesi:
• 2026'da başlıyor
• Türk ihracatçıları için maliyet baskısı
• Model bu etkiyi simüle ediyor
```

### YEDEK 4: VERİ KAYNAKLARI

```
Ana Veri Kaynakları:
• TÜİK: Sera gazı istatistikleri
• TEİAŞ: Santral kapasiteleri
• EPDK: Elektrik piyasası verileri
• NIR 2024: Ulusal envanter
```

---

## 🎨 SUNUM TASARIM ÖNERİLERİ

### Renk Paleti
- **Ana renk:** #22c55e (yeşil - sürdürülebilirlik)
- **Vurgu:** #3b82f6 (mavi - veri/analiz)
- **Uyarı:** #ef4444 (kırmızı - dikkat)
- **Nötr:** #6b7280 (gri - BAU)

### Font
- **Başlık:** Inter Bold, 36pt
- **Alt başlık:** Inter SemiBold, 24pt
- **Metin:** Inter Regular, 18pt
- **Veri:** JetBrains Mono, 16pt

### Görsel İlkeler
- Her slaytta maksimum 6 bullet point
- Grafiklerde net etiketler
- Emoji kullanımı minimal ama etkili
- Yüksek kontrast (erişilebilirlik)

---

## ⏱️ ZAMANLAMA TABLOSU

| Bölüm | Slayt | Süre |
|-------|-------|------|
| Giriş | 1-2 | 1 dk |
| Problem | 3-4 | 3 dk |
| Literatür | 5-6 | 3 dk |
| Metodoloji | 7-10 | 4 dk |
| Demo | 11 | 3 dk |
| Sonuçlar | 12-14 | 4 dk |
| Kısıtlamalar & Roadmap | 15-17 | 3 dk |
| Kapanış | 18-20 | 2 dk |
| **TOPLAM** | **20** | **~20 dk** |

---

## ✅ SUNUM ÖNCESİ KONTROL LİSTESİ

- [ ] Dashboard çalışıyor mu? (`streamlit run src/dashboard_v4.py`)
- [ ] Tüm grafikler güncel mi?
- [ ] Video yedek hazır mı? (canlı demo başarısız olursa)
- [ ] Sunum dosyası USB'de kopyalandı mı?
- [ ] PDF versiyonu çıkarıldı mı?
- [ ] Yedek slaytlar ekli mi?
- [ ] Zamanlama prova edildi mi?
- [ ] Soru-cevap için hazırlık yapıldı mı?

---

*Son güncelleme: 28 Aralık 2025*
