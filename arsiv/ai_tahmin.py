import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

def gelecek_tahmini_yap():
    print("--- 🔮 YAPAY ZEKA TAHMİN MODÜLÜ BAŞLATILIYOR ---")

    # 1. SQL Veritabanından Geçmiş Veriyi Çek
    conn = sqlite3.connect("iklim_veritabani.sqlite")
    
    # Hangi sektör için tahmin yapacağız? Örn: "Toplam" veya "Enerji"
    hedef_sutun = "Toplam" 
    
    query = f"SELECT Year, {hedef_sutun} FROM ulusal_envanter"
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print("❌ HATA: Veritabanı bulunamadı! Önce 'database_setup.py' çalıştırılmalı.")
        return
    finally:
        conn.close()

    print(f"✅ {len(df)} yıllık geçmiş veri yüklendi.")

    # 2. Veriyi Hazırla (X = Yıllar, y = Emisyon)
    X = df["Year"].values.reshape(-1, 1)
    y = df[hedef_sutun].values

    # 3. Model Eğitimi (Polinom Regresyon - Derece 2)
    # Derece 2: Eğrisel artışı yakalar (Daha gerçekçi)
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)

    # Model Başarısını Ölç (R^2 Skoru)
    y_pred_gecmis = model.predict(X_poly)
    basari_skoru = r2_score(y, y_pred_gecmis)
    print(f"🧠 Model Eğitildi. Başarı Skoru (R²): {basari_skoru:.4f}")

    # 4. Geleceği Tahmin Et (2024 - 2050)
    gelecek_yillar = np.arange(2024, 2051).reshape(-1, 1)
    gelecek_poly = poly.transform(gelecek_yillar)
    gelecek_tahminler = model.predict(gelecek_poly)

    # 2035 Hedef Yıl Tahminini Bul
    tahmin_2035 = model.predict(poly.transform([[2035]]))[0]
    print(f"🚀 2035 Yılı Tahmini ({hedef_sutun}): {tahmin_2035:.2f} Mt CO2")

    # 5. Görselleştirme (Profesyonel Grafik)
    plt.figure(figsize=(12, 6))
    
    # Geçmiş Veriler (Siyah Noktalar)
    plt.scatter(X, y, color='black', label='Gerçek Veriler (1990-2023)', s=70, zorder=3)
    
    # Modelin Geçmiş Üzerindeki Trendi (Mavi Çizgi)
    plt.plot(X, y_pred_gecmis, color='blue', linewidth=2, label='AI Trend Analizi')
    
    # Gelecek Tahmini (Kırmızı Kesik Çizgi)
    plt.plot(gelecek_yillar, gelecek_tahminler, color='red', linestyle='--', linewidth=2, label='2050 Projeksiyonu (BAU)')
    
    # 2035 Noktasını İşaretle
    plt.scatter([2035], [tahmin_2035], color='green', s=150, zorder=5, label=f'2035 Tahmini: {tahmin_2035:.0f} Mt')
    
    # Grafik Süslemeleri
    plt.title(f"Türkiye Ulusal Emisyon Projeksiyonu: {hedef_sutun} (Business As Usual)", fontsize=14)
    plt.xlabel("Yıl", fontsize=12)
    plt.ylabel("Emisyon (Mt CO2 eq.)", fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Grafiği Göster
    print("📊 Grafik çiziliyor...")
    plt.show()

if __name__ == "__main__":
    gelecek_tahmini_yap()