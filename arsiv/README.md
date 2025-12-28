#  TR-ZERO: Ulusal İklim Karar Destek Sistemi

Bu proje, Türkiye'nin 2053 Net Sıfır Emisyon hedeflerine ulaşması için geliştirilmiş **Hibrit Simülasyon ve Optimizasyon** yazılımıdır. TÜBİTAK 2209-A kapsamında geliştirilmiştir.

## 🚀 Özellikler
1.  **Veri Ambarı:** 1990-2025 arası envanter verileri (SQLite).
2.  **Yapay Zeka (AI):** Polinom Regresyon ile 2050 projeksiyonu.
3.  **Optimizasyon:** SciPy (Linear Programming) ile en ucuz enerji karması hesabı.
4.  **Simülasyon (ABM):** Mesa kütüphanesi ile SKDM, Karbon Vergisi ve Teşvik senaryolarının analizi.

## 🛠️ Kurulum
Gerekli kütüphaneleri yükleyin:
```bash
pip install pandas numpy scipy scikit-learn mesa streamlit pydeck matplotlib
