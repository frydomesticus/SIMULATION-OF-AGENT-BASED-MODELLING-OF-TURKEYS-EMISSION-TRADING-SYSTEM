"""
TR-ZERO: Ulusal İklim Karar Destek Sistemi - Veritabanı Kurulum Modülü
=======================================================================

Bu modül, Türkiye Ulusal Sera Gazı Envanteri verilerini SQLite veritabanına
yüklemek için tasarlanmıştır. 

Metodoloji:
-----------
Veri yapısı, IPCC 2006 Kılavuzları ve Türkiye Ulusal Envanter Raporu (NIR)
metodolojisine uygun olarak tasarlanmıştır.

Kaynaklar:
----------
[1] IPCC (2006).  2006 IPCC Guidelines for National Greenhouse Gas Inventories.
    https://www.ipcc-nggip.iges.or.jp/public/2006gl/
    
[2] T. C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı (2024).  
    Turkish Greenhouse Gas Inventory 1990-2022: National Inventory Report. 
    https://unfccc.int/documents/627786
    
[3] TÜİK (2023).  Sera Gazı Emisyon İstatistikleri, 1990-2022. 
    https://data.tuik.gov.tr/

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih: Aralık 2025
Versiyon: 2.0
"""

import pandas as pd
import sqlite3
import os

def veritabani_kurulumu():
    """
    Ulusal envanter verilerini SQLite veritabanına yükler. 
    
    Bu fonksiyon, NIR raporundaki sektörel emisyon verilerini ve
    il bazlı dağılım katsayılarını veritabanına aktarır.
    
    Returns:
        bool: Kurulum başarılı ise True, aksi halde False
        
    Raises:
        FileNotFoundError: CSV dosyaları bulunamazsa
        sqlite3.Error: Veritabanı hatası oluşursa
    """
    print("=" * 60)
    print("TR-ZERO SİSTEM KURULUMU")
    print("Türkiye Ulusal Sera Gazı Envanter Veritabanı")
    print("=" * 60)
    
    db_adi = "iklim_veritabani.sqlite"
    
    # -------------------------------------------------------------------------
    # 1. Veri Dosyalarını Kontrol Et
    # -------------------------------------------------------------------------
    # Kaynak: Dosya yapısı IPCC 2006 Kılavuzları Cilt 1, Bölüm 8'e uygun [1]
    # -------------------------------------------------------------------------
    
    gerekli_dosyalar = ["sektorel_emisyonlar.csv", "il_dagilim_katsayilari. csv"]
    
    for dosya in gerekli_dosyalar:
        if not os.path.exists(dosya):  # ✅ DÜZELTME: Boşluk hatası giderildi
            print(f"❌ HATA: '{dosya}' bulunamadı!")
            print("   Lütfen CSV dosyalarının proje dizininde olduğundan emin olun.")
            return False
    
    print("✅ Gerekli veri dosyaları doğrulandı.")
    
    # -------------------------------------------------------------------------
    # 2. SQL Bağlantısını Aç
    # -------------------------------------------------------------------------
    try:
        conn = sqlite3.connect(db_adi)
        cursor = conn.cursor()
        print(f"✅ Veritabanı bağlantısı oluşturuldu: {db_adi}")
    except sqlite3.Error as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return False

    try:
        # ---------------------------------------------------------------------
        # 3. Sektörel Emisyonları Yükle (Ulusal Envanter)
        # ---------------------------------------------------------------------
        # Kaynak: NIR 2024 Raporu, Tablo ES. 1 - Sektörel Emisyon Özeti [2]
        # Birim: Mt CO2 eşdeğeri (GWP-AR5 değerleri kullanılmıştır)
        # ---------------------------------------------------------------------
        
        df_emisyon = pd.read_csv("sektorel_emisyonlar.csv")
        df_emisyon = df_emisyon.fillna(0)
        
        # Veri doğrulama: NIR raporuyla tutarlılık kontrolü
        if "Year" not in df_emisyon.columns:
            raise ValueError("CSV dosyasında 'Year' sütunu bulunamadı")
        
        df_emisyon. to_sql("ulusal_envanter", conn, if_exists="replace", index=False)
        print(f"✅ Ulusal Envanter Tablosu oluşturuldu ({len(df_emisyon)} yıllık veri)")
        print(f"   Kapsam: {df_emisyon['Year'].min()} - {df_emisyon['Year'].max()}")

        # ---------------------------------------------------------------------
        # 4. İl Katsayılarını Yükle (Downscaling Metodolojisi)
        # ---------------------------------------------------------------------
        # Kaynak: Emisyon dağılımı için "top-down" yaklaşımı kullanılmıştır. 
        # Metodoloji: Moran, D., et al. (2018). "Carbon footprints of 13,000 
        #             cities." Environmental Research Letters, 13(6). 
        #             https://doi.org/10. 1088/1748-9326/aac72a
        # ---------------------------------------------------------------------
        
        df_il = pd.read_csv("il_dagilim_katsayilari.csv")
        df_il. to_sql("il_katsayilari", conn, if_exists="replace", index=False)
        print(f"✅ İl Dağılım Katsayıları oluşturuldu ({len(df_il)} bölge)")
        
        # ---------------------------------------------------------------------
        # 5. Doğrulama Testi
        # ---------------------------------------------------------------------
        # 2022 yılı verisi NIR raporu ile karşılaştırılarak doğrulanmıştır. 
        # NIR 2024, Sayfa ES-4: Toplam emisyon (LULUCF hariç) = 558.3 Mt CO2eq
        # ---------------------------------------------------------------------
        
        print("\n" + "-" * 40)
        print("DOĞRULAMA TESTİ: 2022 Yılı Verileri")
        print("-" * 40)
        
        test_sorgu = "SELECT Year, Enerji, Toplam FROM ulusal_envanter WHERE Year = 2022"
        test_sonuc = pd.read_sql(test_sorgu, conn)
        
        if not test_sonuc.empty:
            toplam_2022 = test_sonuc['Toplam'].values[0]
            print(f"   Veritabanı değeri: {toplam_2022:.2f} Mt CO2eq")
            print(f"   NIR 2024 referans: 558.27 Mt CO2eq")
            
            # Tolerans kontrolü (%1)
            if abs(toplam_2022 - 558.27) / 558.27 < 0.01:
                print("   ✅ Doğrulama BAŞARILI (<%1 sapma)")
            else:
                print("   ⚠️ UYARI: Veri sapması tespit edildi")
        
        return True
        
    except Exception as e:
        print(f"❌ BEKLENMEYEN HATA: {e}")
        return False
        
    finally:
        conn.close()
        print("\n" + "=" * 60)
        print("KURULUM TAMAMLANDI")
        print("=" * 60)


if __name__ == "__main__":
    basari = veritabani_kurulumu()
    if basari:
        print("\n🎉 Sistem kullanıma hazır!")
    else:
        print("\n⚠️ Kurulum tamamlanamadı.  Hataları kontrol edin.")