import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import pydeck as pdk
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from scipy.optimize import linprog
from mesa import Agent, Model
from mesa.datacollection import DataCollector
import os
import random

# --- 1. SAYFA VE TASARIM AYARLARI ---
st.set_page_config(
    page_title="TR-ZERO | Entegre Karar Destek Sistemi",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌍"
)

# Profesyonel CSS Tasarımı
st.markdown("""
    <style>
    html, body, [class*="css"] { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1 { color: #0f172a; font-weight: 700; }
    h3 { color: #334155; }
    .stMetric { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .stButton>button { background-color: #0f172a; color: white; border-radius: 6px; width: 100%; height: 50px; font-weight: bold; }
    .stButton>button:hover { background-color: #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ ALTYAPISI ---
def get_data(query):
    db_file = "iklim_veritabani.sqlite"
    if not os.path.exists(db_file): return pd.DataFrame()
    conn = sqlite3.connect(db_file)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- BAŞLIK ---
st.title("TR-ZERO")
st.markdown("### Ulusal Emisyon Azaltım ve Karar Destek Sistemi")
st.markdown("TÜBİTAK 2209-A Projesi | **Kapsam:** Enerji • Sanayi • Tarım • Atık Yönetimi")
st.divider()

tabs = st.tabs(["MEVCUT DURUM & AI", "ENERJİ OPTİMİZASYONU", "ÇOKLU SEKTÖR SİMÜLASYONU", "COĞRAFİ ANALİZ"])

# ==============================================================================
# TAB 1: YAPAY ZEKA TAHMİNİ
# ==============================================================================
with tabs[0]:
    col_main, col_kpi = st.columns([3, 1])
    with col_kpi:
        st.markdown("#### ⚙️ Parametreler")
        df = get_data("SELECT * FROM ulusal_envanter")
        if not df.empty:
            sektorler = [c for c in df.columns if c!='Year']
            secilen = st.selectbox("Sektör Seçimi", sektorler, index=4)
            yil_hedef = st.slider("Projeksiyon Yılı", 2024, 2050, 2035)
            derece = st.radio("Model Hassasiyeti", [1, 2], index=1)
            
            val_2023 = df.iloc[-1][secilen]
            st.metric(f"2023 {secilen}", f"{val_2023:.1f} Mt", "TÜİK Verisi")
            
    with col_main:
        if not df.empty:
            st.markdown(f"#### 📈 {secilen} Emisyon Projeksiyonu")
            X = df["Year"].values.reshape(-1, 1)
            y = df[secilen].values
            poly = PolynomialFeatures(degree=derece)
            model = LinearRegression().fit(poly.fit_transform(X), y)
            
            gelecek = np.arange(1990, 2051).reshape(-1, 1)
            tahmin = model.predict(poly.transform(gelecek))
            hedef_deger = model.predict(poly.transform([[yil_hedef]]))[0]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
            ax.scatter(X, y, color='#1e293b', label='Gerçekleşen')
            ax.plot(gelecek, tahmin, color='#ef4444', linestyle='-', linewidth=2, label='AI Trendi')
            ax.scatter([yil_hedef], [hedef_deger], color='#22c55e', s=100, zorder=5)
            ax.set_ylabel("Mt CO2 eq."); ax.legend(frameon=False)
            st.pyplot(fig)
            st.info(f"Yapay Zeka, mevcut politikalarla {yil_hedef} yılında **{hedef_deger:.1f} Mt** emisyon öngörmektedir.")

# ==============================================================================
# TAB 2: OPTİMİZASYON
# ==============================================================================
with tabs[1]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 🎯 2035 Hedefleri")
        talep = st.number_input("Elektrik Talebi (GWh)", value=510000000)
        max_em = st.slider("Emisyon Kotası (Mt CO2)", 50, 250, 150)
        calc_btn = st.button("Optimal Çözümü Hesapla")
    with c2:
        if calc_btn:
            # Kaynaklar: Kömür, Gaz, Rüzgar, Güneş, Nükleer
            c = [60, 80, 40, 35, 110] 
            # Kısıtlar
            res = linprog(c, A_ub=[[0.9, 0.4, 0, 0, 0]], b_ub=[max_em*1e6], 
                          A_eq=[[1,1,1,1,1]], b_eq=[talep], 
                          bounds=[(0, 1.5e8), (0, 1.5e8), (5e7, 1.5e8), (6e7, 2e8), (0, 6e7)], method='highs')
            if res.success:
                st.success(f"✅ Minimum Maliyet: ${res.fun/1e9:.2f} Milyar")
                fig, ax = plt.subplots()
                ax.pie(res.x, labels=['Kömür','Gaz','Rüzgar','Güneş','Nükleer'], autopct='%1.1f%%', 
                       colors=['#475569','#f97316','#06b6d4','#eab308','#22c55e'], startangle=90)
                plt.Circle((0,0),0.70,fc='white'); fig.gca().add_artist(plt.Circle((0,0),0.70,fc='white'))
                st.pyplot(fig)
            else: st.error("Çözüm bulunamadı.")

# ==============================================================================
# TAB 3: ÇOKLU SEKTÖR SİMÜLASYONU (EVRENSEL MODEL)
# ==============================================================================
with tabs[2]:
    st.markdown("#### 🏭 Sektörel Etki Analizi (Simülasyon)")
    st.markdown("Bu modül, farklı sektörlerin **Karbon Vergisi (Sopa)** ve **Devlet Teşviki (Havuç)** politikalarına verdiği tepkileri simüle eder.")
    
    col_kapsam, col_param, col_sim = st.columns([1, 1, 3])
    
    with col_kapsam:
        st.info("📂 **Analiz Kapsamı**")
        secilen_kapsam = st.selectbox("Simüle Edilecek Sektör:", 
                                      ["Tüm Ekonomi", "Enerji", "Sanayi (Çimento/Çelik)", "Tarım", "Atık Yönetimi"])
    
    with col_param:
        st.warning("⚙️ **Politika Araçları**")
        vergi_artis = st.slider("Karbon Vergisi Artışı ($/yıl)", 1, 15, 5)
        ab_vergisi = st.number_input("AB SKDM Sınırı ($)", 50, 150, 90)
        tesvik_miktari = st.slider("Yeşil Dönüşüm Teşviği ($)", 0, 500, 200)
        run_sim = st.button("SİMÜLASYONU BAŞLAT ▶️")

    # --- EVRENSEL AJAN MODELİ ---
    class UniversalAgent(Agent):
        def __init__(self, uid, model, sektor):
            super().__init__(model)
            self.sektor = sektor
            self.durum = "Kirleten"
            # İhracatçı olma durumu (SKDM için)
            self.ihracatci = True if random.random() < 0.4 and sektor in ["Enerji", "Sanayi"] else False
            
            # SEKTÖREL PROFİLLER
            if sektor == "Enerji":
                self.limit, self.yatirim_bedeli, self.duyarli_oldugu = 90, 200, "Vergi"
            elif sektor == "Sanayi":
                self.limit, self.yatirim_bedeli, self.duyarli_oldugu = 110, 250, "Vergi"
            elif sektor == "Tarım":
                self.limit, self.yatirim_bedeli, self.duyarli_oldugu = 999, 300, "Teşvik"
            elif sektor == "Atık":
                self.limit, self.yatirim_bedeli, self.duyarli_oldugu = 999, 150, "Teşvik"
            
            self.yatirim_taksiti = self.yatirim_bedeli / 10

        def step(self):
            # VERGİ YÜKÜ (SKDM DAHİL)
            vergi_yuku = max(self.model.tax, self.model.ab_tax) if self.ihracatci else self.model.tax
            devlet_destegi = self.model.tesvik
            
            # KARAR ALGORİTMASI (MAC)
            if self.duyarli_oldugu == "Vergi":
                maliyet_eski = 40 + (0.9 * vergi_yuku)
                maliyet_yeni = 40 + (0.2 * vergi_yuku) + (self.yatirim_taksiti - (devlet_destegi/10))
                
                if self.durum == "Kirleten":
                    if maliyet_yeni < maliyet_eski and maliyet_yeni < self.limit: self.durum = "Temiz"
                    elif maliyet_eski >= self.limit: self.durum = "Kapalı"
                    
            elif self.duyarli_oldugu == "Teşvik":
                # Tarım sadece hibe yeterliyse dönüşür
                if devlet_destegi >= (self.yatirim_bedeli * 0.6): self.durum = "Temiz"

    class EkonomiModeli(Model):
        def __init__(self, rate, ab_tax, tesvik, kapsam):
            super().__init__()
            self.tax, self.rate = 0, rate
            self.ab_tax, self.tesvik = ab_tax, tesvik
            
            # Ajan Dağılımı
            if kapsam == "Tüm Ekonomi": adetler = {"Enerji": 30, "Sanayi": 30, "Tarım": 20, "Atık": 20}
            elif kapsam == "Enerji": adetler = {"Enerji": 100}
            elif kapsam == "Sanayi (Çimento/Çelik)": adetler = {"Sanayi": 100}
            elif kapsam == "Tarım": adetler = {"Tarım": 100}
            elif kapsam == "Atık Yönetimi": adetler = {"Atık": 100}
            
            for sekt, sayi in adetler.items():
                for _ in range(sayi): UniversalAgent(random.randint(0,10000), self, sekt)
            
            self.dc = DataCollector(model_reporters={
                "Vergi": lambda m: m.tax,
                "Statüko (Kirleten)": lambda m: sum([1 for a in m.agents if a.durum=="Kirleten"]),
                "Dönüşen (Yeşil)": lambda m: sum([1 for a in m.agents if a.durum=="Temiz"]),
                "Batan": lambda m: sum([1 for a in m.agents if a.durum=="Kapalı"])
            })
            
        def step(self):
            self.dc.collect(self)
            self.tax += self.rate
            self.agents.shuffle().do("step")

    with col_sim:
        if run_sim:
            model = EkonomiModeli(vergi_artis, ab_vergisi, tesvik_miktari, secilen_kapsam)
            for _ in range(25): model.step()
            df_res = model.dc.get_model_vars_dataframe()
            
            fig, ax1 = plt.subplots(figsize=(10, 5))
            ax1.stackplot(df_res.index, df_res["Statüko (Kirleten)"], df_res["Dönüşen (Yeşil)"], df_res["Batan"],
                          labels=['Kirleten', 'Yeşil Dönüşüm', 'Batan/Kayıp'], 
                          colors=['#94a3b8', '#22c55e', '#ef4444'], alpha=0.8)
            ax1.legend(loc='upper left', ncol=3, frameon=False)
            ax1.set_ylabel("Firma Sayısı"); ax1.set_xlabel("Yıl")
            st.pyplot(fig)
            
            # CSV İndir
            st.download_button("📥 Analiz Sonuçlarını İndir", df_res.to_csv(), "simulasyon_sonuc.csv")
            st.success(f"Analiz Tamamlandı: {secilen_kapsam}")

# ==============================================================================
# TAB 4: COĞRAFİ ANALİZ (HEATMAP)
# ==============================================================================
with tabs[3]:
    st.markdown("#### 🗺️ İl Bazlı Emisyon Yoğunluk Haritası")
    df_il = get_data("SELECT * FROM il_katsayilari")
    df_ulusal = get_data("SELECT * FROM ulusal_envanter")
    
    if not df_il.empty:
        total = df_ulusal.iloc[-1]["Toplam"]
        df_il["Emisyon"] = df_il["Sanayi_Payi"] * total
        
        # Koordinatlar
        coords = {'Istanbul': [41.0082, 28.9784], 'Kocaeli': [40.8533, 29.8815], 'Ankara': [39.9334, 32.8597], 
                  'Izmir': [38.4192, 27.1287], 'Bursa': [40.1885, 29.0610], 'Tekirdag': [40.9833, 27.5167],
                  'Adana': [37.0000, 35.3213], 'Gaziantep': [37.0662, 37.3833], 'Zonguldak': [41.4564, 31.7987], 
                  'Kahramanmaras': [37.5858, 36.9371], 'Hatay': [36.4018, 36.3498], 'Manisa': [38.6191, 27.4289]}
        
        df_il['lat'] = df_il['Il_Adi'].map(lambda x: coords.get(x, [0,0])[0])
        df_il['lon'] = df_il['Il_Adi'].map(lambda x: coords.get(x, [0,0])[1])
        map_df = df_il[df_il['lat']!=0].copy()
        
        layer = pdk.Layer("ColumnLayer", data=map_df, get_position=["lon", "lat"], get_elevation="Emisyon", 
                          elevation_scale=1000, radius=20000, get_fill_color=[255, 0, 0, 140], pickable=True, auto_highlight=True)
        view = pdk.ViewState(latitude=39.0, longitude=35.0, zoom=5, pitch=50)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip={"text": "{Il_Adi}: {Emisyon} Mt"}))