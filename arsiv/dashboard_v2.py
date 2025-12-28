"""
TR-ZERO: Entegre Karar Destek Sistemi Dashboard (v2.0)
======================================================

Bu modül, Türkiye'nin sera gazı emisyonlarını analiz etmek ve
politika senaryolarını değerlendirmek için interaktif bir
Streamlit dashboard sağlar. 

Entegre Modüller:
-----------------
1.  Veritabanı Modülü (database_setup_v2.py)
2. AI Tahmin Modülü (ai_tahmin_v2.py)
3. ABM Simülasyon Modülü (piyasa_simulasyonu_v2.py)

Kaynaklar:
----------
[1] Tüm kaynak referansları ilgili modüllerde belirtilmiştir. 

[2] Streamlit Documentation (2024). 
    https://docs.streamlit.io/

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih: Aralık 2025
Versiyon: 2.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# Proje modüllerini import et
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# Veritabanı yolu
DB_PATH = os.path.join(PROJECT_ROOT, "iklim_veritabani.sqlite")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# =============================================================================
# SAYFA AYARLARI
# =============================================================================

st.set_page_config(
    page_title="TR-ZERO | Ulusal İklim Karar Destek Sistemi",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS STİLLERİ
# =============================================================================

st.markdown("""
<style>
    /* Ana Tema */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a5f;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Metrik Kartları */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Butonlar */
    .stButton>button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30,58,95,0.4);
    }
    
    /* Tab Stilleri */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3a5f;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# VERİ FONKSİYONLARI
# =============================================================================

@st.cache_data
def veri_yukle():
    """Veritabanından verileri yükler."""
    if not os.path.exists(DB_PATH):
        return None, None
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df_envanter = pd.read_sql("SELECT * FROM ulusal_envanter", conn)
        df_il = pd.read_sql("SELECT * FROM il_katsayilari", conn)
        return df_envanter, df_il
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        return None, None
    finally:
        conn.close()

@st.cache_data
def senaryo_sonuclari_yukle():
    """Önceden hesaplanmış senaryo sonuçlarını yükler."""
    sonuclar = {}
    senaryo_dosyalari = ["bau", "yumusak_ets", "siki_ets", "ets_tesvik"]
    
    for senaryo in senaryo_dosyalari:
        dosya_yolu = os.path.join(OUTPUT_DIR, f"senaryo_{senaryo}.csv")
        if os.path.exists(dosya_yolu):
            sonuclar[senaryo] = pd.read_csv(dosya_yolu)
    
    return sonuclar if sonuclar else None

# =============================================================================
# BAŞLIK VE GİRİŞ
# =============================================================================

st.markdown('<h1 class="main-header">🌍 TR-ZERO</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Türkiye Ulusal İklim Karar Destek Sistemi | Emisyon Azaltım ve Politika Analiz Platformu</p>', unsafe_allow_html=True)

# Veri kontrolü
df_envanter, df_il = veri_yukle()

if df_envanter is None:
    st.error("⚠️ Veritabanı bulunamadı!  Lütfen önce `database_setup_v2.py` dosyasını çalıştırın.")
    st.code("python src/database_setup_v2.py", language="bash")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/globe.png", width=80)
    st.markdown("### ⚙️ Kontrol Paneli")
    st.markdown("---")
    
    # Yıl seçimi
    yil_aralik = st.slider(
        "📅 Analiz Dönemi",
        min_value=int(df_envanter['Year'].min()),
        max_value=2035,
        value=(2020, 2035)
    )
    
    st.markdown("---")
    
    # Senaryo seçimi
    st.markdown("### 📊 Senaryo Seçimi")
    secili_senaryolar = st.multiselect(
        "Karşılaştırılacak Senaryolar",
        ["BAU", "Yumuşak ETS", "Sıkı ETS", "ETS + Teşvik"],
        default=["BAU", "Sıkı ETS"]
    )
    
    st.markdown("---")
    
    # Parametre ayarları
    st.markdown("### 🎛️ ETS Parametreleri")
    
    karbon_fiyat_baslangic = st.number_input(
        "Başlangıç Karbon Fiyatı ($/ton)",
        min_value=10, max_value=100, value=20
    )
    
    cap_azalma = st.slider(
        "Yıllık Cap Azalma Oranı (%)",
        min_value=1.0, max_value=5.0, value=2.1, step=0.1
    )
    
    tesvik = st.number_input(
        "Yenilenebilir Teşviği ($/MW)",
        min_value=0, max_value=200000, value=50000, step=10000
    )
    
    st.markdown("---")
    
    # Simülasyon butonu
    run_simulation = st.button("🚀 Simülasyonu Çalıştır", use_container_width=True)
    
    st.markdown("---")
    st.markdown("##### 📚 Kaynaklar")
    st.markdown("""
    - [NIR 2024 Raporu](https://unfccc.int)
    - [Türkiye ETS Taslağı](https://iklim.gov.tr)
    - [IPCC AR6](https://www.ipcc.ch)
    """)

# =============================================================================
# ANA İÇERİK - TABLAR
# =============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Mevcut Durum",
    "🤖 AI Projeksiyon", 
    "🏭 ABM Simülasyon",
    "🗺️ Coğrafi Analiz",
    "📋 Rapor"
])

# =============================================================================
# TAB 1: MEVCUT DURUM ANALİZİ
# =============================================================================

with tab1:
    st.markdown("## 📈 Türkiye Sera Gazı Emisyonları - Mevcut Durum")
    
    # KPI Kartları
    col1, col2, col3, col4 = st.columns(4)
    
    son_yil = df_envanter['Year'].max()
    son_veri = df_envanter[df_envanter['Year'] == son_yil].iloc[0]
    
    # Toplam sütun adını bul
    toplam_sutun = 'Toplam_LULUCF_Haric' if 'Toplam_LULUCF_Haric' in df_envanter.columns else 'Toplam'
    enerji_sutun = 'Enerji_Toplam' if 'Enerji_Toplam' in df_envanter.columns else 'Enerji'
    
    with col1:
        st.metric(
            label=f"📊 Toplam Emisyon ({son_yil})",
            value=f"{son_veri[toplam_sutun]:.1f} Mt",
            delta=f"{son_veri[toplam_sutun] - df_envanter[df_envanter['Year'] == son_yil-1][toplam_sutun].values[0]:.1f} Mt"
        )
    
    with col2:
        st.metric(
            label="⚡ Enerji Sektörü Payı",
            value=f"{(son_veri[enerji_sutun]/son_veri[toplam_sutun]*100):.1f}%",
            delta=None
        )
    
    with col3:
        # 1990'a göre değişim
        ilk_veri = df_envanter[df_envanter['Year'] == 1990][toplam_sutun].values[0]
        degisim = ((son_veri[toplam_sutun] - ilk_veri) / ilk_veri) * 100
        st.metric(
            label="📈 1990'a Göre Değişim",
            value=f"+{degisim:.1f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="🎯 NDC 2030 Hedefi",
            value="695 Mt",
            delta=f"{695 - son_veri[toplam_sutun]:.0f} Mt kalan"
        )
    
    st.markdown("---")
    
    # Grafik: Sektörel Emisyon Trendi
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 📊 Sektörel Emisyon Trendi")
        
        # Sütun isimlerini kontrol et
        if 'Enerji_Toplam' in df_envanter.columns:
            sektor_sutunlar = ['Enerji_Toplam', 'IPPU_Toplam', 'Tarim_Toplam', 'Atik_Toplam']
            sektor_isimler = ['Enerji', 'Endüstri (IPPU)', 'Tarım', 'Atık']
        else:
            sektor_sutunlar = ['Enerji', 'Endustriyel_Islemler', 'Tarim', 'Atik']
            sektor_isimler = ['Enerji', 'Endüstri', 'Tarım', 'Atık']
        
        fig = go.Figure()
        
        colors = ['#3b82f6', '#f59e0b', '#22c55e', '#ef4444']
        
        for i, (sutun, isim) in enumerate(zip(sektor_sutunlar, sektor_isimler)):
            if sutun in df_envanter.columns:
                fig.add_trace(go.Scatter(
                    x=df_envanter['Year'],
                    y=df_envanter[sutun],
                    mode='lines+markers',
                    name=isim,
                    line=dict(color=colors[i], width=2),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            xaxis_title="Yıl",
            yaxis_title="Emisyon (Mt CO₂eq)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            hovermode="x unified",
            template="plotly_white",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 🥧 Sektörel Dağılım")
        
        sektor_veriler = []
        for sutun, isim in zip(sektor_sutunlar, sektor_isimler):
            if sutun in df_envanter.columns:
                sektor_veriler.append({
                    'Sektör': isim,
                    'Emisyon': son_veri[sutun]
                })
        
        df_pie = pd.DataFrame(sektor_veriler)
        
        fig_pie = px.pie(
            df_pie, 
            values='Emisyon', 
            names='Sektör',
            color_discrete_sequence=['#3b82f6', '#f59e0b', '#22c55e', '#ef4444'],
            hole=0.4
        )
        fig_pie.update_layout(height=350)
        
        st.plotly_chart(fig_pie, use_container_width=True)

# =============================================================================
# TAB 2: AI PROJEKSİYON
# =============================================================================

with tab2:
    st.markdown("## 🤖 Yapay Zeka Destekli Emisyon Projeksiyonu")
    
    col_param, col_result = st.columns([1, 3])
    
    with col_param:
        st.markdown("### ⚙️ Model Parametreleri")
        
        hedef_sektor = st.selectbox(
            "Sektör Seçimi",
            [toplam_sutun] + [s for s in sektor_sutunlar if s in df_envanter.columns]
        )
        
        model_derece = st.radio(
            "Polinom Derecesi",
            [1, 2, 3],
            index=1,
            help="Derece 2 (kuadratik) genellikle en iyi sonucu verir"
        )
        
        hedef_yil = st.slider(
            "Projeksiyon Yılı",
            min_value=2025,
            max_value=2050,
            value=2035
        )
        
        projeksiyon_btn = st.button("📊 Projeksiyon Hesapla", use_container_width=True)
    
    with col_result:
        if projeksiyon_btn or 'projeksiyon_yapildi' not in st.session_state:
            from sklearn.preprocessing import PolynomialFeatures
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_absolute_error
            
            # Veri hazırlığı
            X = df_envanter['Year'].values.reshape(-1, 1)
            y = df_envanter[hedef_sektor].values
            
            # Model eğitimi
            poly = PolynomialFeatures(degree=model_derece)
            X_poly = poly.fit_transform(X)
            model = LinearRegression()
            model.fit(X_poly, y)
            
            # Tahmin
            y_pred = model.predict(X_poly)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            # Gelecek projeksiyonu
            gelecek_yillar = np.arange(df_envanter['Year'].max() + 1, hedef_yil + 1).reshape(-1, 1)
            gelecek_poly = poly.transform(gelecek_yillar)
            gelecek_tahmin = model.predict(gelecek_poly)
            
            # NDC senaryosu
            son_emisyon = y[-1]
            ndc_hedef = 695
            ndc_yillar = np.arange(df_envanter['Year'].max() + 1, 2031)
            ndc_tahmin = np.linspace(son_emisyon, ndc_hedef, len(ndc_yillar))
            
            # Grafik
            fig = go.Figure()
            
            # Gerçek veriler
            fig.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=y,
                mode='markers',
                name='Gerçekleşen',
                marker=dict(color='#1e3a5f', size=10)
            ))
            
            # Model trendi
            fig.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=y_pred,
                mode='lines',
                name='AI Trend',
                line=dict(color='#3b82f6', width=2)
            ))
            
            # BAU projeksiyonu
            fig.add_trace(go.Scatter(
                x=gelecek_yillar.flatten(),
                y=gelecek_tahmin,
                mode='lines',
                name='BAU Projeksiyon',
                line=dict(color='#ef4444', width=2, dash='dash')
            ))
            
            # NDC hedefi
            fig.add_trace(go.Scatter(
                x=ndc_yillar,
                y=ndc_tahmin,
                mode='lines',
                name='NDC Hedefi',
                line=dict(color='#22c55e', width=2, dash='dot')
            ))
            
            # 2030 ve 2035 noktaları
            hedef_tahmin = model.predict(poly.transform([[hedef_yil]]))[0]
            fig.add_trace(go.Scatter(
                x=[hedef_yil],
                y=[hedef_tahmin],
                mode='markers+text',
                name=f'{hedef_yil} Tahmini',
                marker=dict(color='#f59e0b', size=15, symbol='star'),
                text=[f'{hedef_tahmin:.0f} Mt'],
                textposition='top center'
            ))
            
            fig.update_layout(
                title=f"📈 {hedef_sektor} Emisyon Projeksiyonu",
                xaxis_title="Yıl",
                yaxis_title="Emisyon (Mt CO₂eq)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                hovermode="x unified",
                template="plotly_white",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Model metrikleri
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("R² Skoru", f"{r2:.4f}")
            with col_m2:
                st.metric("MAE", f"{mae:.2f} Mt")
            with col_m3:
                st.metric(f"{hedef_yil} Tahmini", f"{hedef_tahmin:.1f} Mt")
            
            st.session_state['projeksiyon_yapildi'] = True

# =============================================================================
# TAB 3: ABM SİMÜLASYON
# =============================================================================

with tab3:
    st.markdown("## 🏭 Ajan Tabanlı Model (ABM) Simülasyonu")
    
    # Önceki sonuçları kontrol et
    senaryo_sonuclari = senaryo_sonuclari_yukle()
    
    if senaryo_sonuclari:
        st.success("✅ Önceden hesaplanmış senaryo sonuçları yüklendi!")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("### 📉 Emisyon Karşılaştırması")
            
            fig = go.Figure()
            colors = {'bau': '#94a3b8', 'yumusak_ets': '#3b82f6', 
                     'siki_ets': '#22c55e', 'ets_tesvik': '#8b5cf6'}
            names = {'bau': 'BAU', 'yumusak_ets': 'Yumuşak ETS', 
                    'siki_ets': 'Sıkı ETS', 'ets_tesvik': 'ETS + Teşvik'}
            
            for senaryo, df in senaryo_sonuclari.items():
                fig.add_trace(go.Scatter(
                    x=df['Yil'],
                    y=df['Toplam_Emisyon'],
                    mode='lines+markers',
                    name=names.get(senaryo, senaryo),
                    line=dict(color=colors.get(senaryo, '#666'), width=2)
                ))
            
            fig.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Emisyon (Mt CO₂eq)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                template="plotly_white",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            st.markdown("### 💰 Karbon Fiyatı Gelişimi")
            
            fig2 = go.Figure()
            
            for senaryo, df in senaryo_sonuclari.items():
                fig2.add_trace(go.Scatter(
                    x=df['Yil'],
                    y=df['Karbon_Fiyati'],
                    mode='lines+markers',
                    name=names.get(senaryo, senaryo),
                    line=dict(color=colors.get(senaryo, '#666'), width=2)
                ))
            
            fig2.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Fiyat ($/ton CO₂)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                template="plotly_white",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Özet tablo
        st.markdown("### 📋 Senaryo Özet Tablosu (2035)")
        
        ozet_data = []
        bau_emisyon = senaryo_sonuclari.get('bau', pd.DataFrame({'Toplam_Emisyon': [0]}))['Toplam_Emisyon'].iloc[-1]
        
        for senaryo, df in senaryo_sonuclari.items():
            emisyon = df['Toplam_Emisyon'].iloc[-1]
            azaltim = ((bau_emisyon - emisyon) / bau_emisyon * 100) if bau_emisyon > 0 else 0
            ozet_data.append({
                'Senaryo': names.get(senaryo, senaryo),
                'Emisyon (Mt)': f"{emisyon:.1f}",
                'BAU\'dan Azaltım (%)': f"{azaltim:.1f}%",
                'Karbon Fiyatı ($)': f"{df['Karbon_Fiyati'].iloc[-1]:.0f}",
                'Temiz Tesis': int(df['Temiz_Tesis'].iloc[-1]) if 'Temiz_Tesis' in df.columns else '-'
            })
        
        st.dataframe(pd.DataFrame(ozet_data), use_container_width=True, hide_index=True)
        
    else:
        st.warning("⚠️ Senaryo sonuçları bulunamadı.  Lütfen önce simülasyonu çalıştırın.")
        st.code("python src/piyasa_simulasyonu_v2.py", language="bash")
        
        if run_simulation:
            st.info("🔄 Simülasyon başlatılıyor...  Bu işlem birkaç dakika sürebilir.")
            # Burada simülasyon çalıştırılabilir

# =============================================================================
# TAB 4: COĞRAFİ ANALİZ
# =============================================================================

with tab4:
    st.markdown("## 🗺️ İl Bazlı Emisyon Dağılımı")
    
    if df_il is not None and not df_il.empty:
        # İl koordinatları
        il_koordinatlar = {
            'Istanbul': (41.0082, 28.9784),
            'Ankara': (39.9334, 32.8597),
            'Izmir': (38.4192, 27.1287),
            'Bursa': (40.1885, 29.0610),
            'Kocaeli': (40.8533, 29.8815),
            'Adana': (37.0000, 35.3213),
            'Gaziantep': (37.0662, 37.3833),
            'Zonguldak': (41.4564, 31.7987),
            'Hatay': (36.4018, 36.3498),
            'Manisa': (38.6191, 27.4289),
            'Tekirdag': (40.9833, 27.5167),
            'Kahramanmaras': (37.5858, 36.9371)
        }
        
        # Emisyon hesaplama
        son_toplam = df_envanter[df_envanter['Year'] == son_yil][toplam_sutun].values[0]
        
        df_harita = df_il.copy()
        df_harita['Emisyon'] = df_harita['Sanayi_Payi'] * son_toplam
        df_harita['lat'] = df_harita['Il_Adi'].map(lambda x: il_koordinatlar.get(x, (39.0, 35.0))[0])
        df_harita['lon'] = df_harita['Il_Adi'].map(lambda x: il_koordinatlar.get(x, (39.0, 35.0))[1])
        
        # Harita
        fig_map = px.scatter_mapbox(
            df_harita,
            lat='lat',
            lon='lon',
            size='Emisyon',
            color='Emisyon',
            hover_name='Il_Adi',
            hover_data={'Emisyon': ':.2f', 'lat': False, 'lon': False},
            color_continuous_scale='Reds',
            size_max=50,
            zoom=5,
            center={"lat": 39.0, "lon": 35.0}
        )
        
        fig_map.update_layout(
            mapbox_style="carto-positron",
            height=500,
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
        
        # İl tablosu
        st.markdown("### 📊 İl Bazlı Emisyon Tablosu")
        df_goster = df_harita[['Il_Adi', 'Bolge', 'Sanayi_Payi', 'Emisyon']].copy()
        df_goster['Sanayi_Payi'] = (df_goster['Sanayi_Payi'] * 100).round(1).astype(str) + '%'
        df_goster['Emisyon'] = df_goster['Emisyon'].round(2).astype(str) + ' Mt'
        df_goster.columns = ['İl', 'Bölge', 'Sanayi Payı', 'Emisyon']
        
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
    else:
        st.warning("İl verileri bulunamadı.")

# =============================================================================
# TAB 5: RAPOR
# =============================================================================

with tab5:
    st.markdown("## 📋 Analiz Raporu")
    
    st.markdown("""
    ### 🎯 Yönetici Özeti
    
    Bu rapor, Türkiye'nin sera gazı emisyonlarının mevcut durumunu ve farklı 
    politika senaryoları altında 2035 yılına kadar olan projeksiyonlarını 
    sunmaktadır. 
    
    #### Temel Bulgular:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Mevcut Durum:**
        - 2022 toplam emisyon: **558.3 Mt CO₂eq**
        - Enerji sektörü payı: **%71.8**
        - 1990'a göre artış: **+%145**
        """)
    
    with col2:
        st.markdown("""
        **🎯 Hedefler:**
        - NDC 2030 hedefi: **695 Mt CO₂eq**
        - Net sıfır hedef yılı: **2053**
        - ETS başlangıç: **2026**
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 📚 Metodoloji
    
    Bu çalışmada üç ana metodoloji kullanılmıştır:
    
    1. **Polinom Regresyon (AI Projeksiyon):** Geçmiş verilere dayalı trend analizi
    2. **Ajan Tabanlı Modelleme (ABM):** Firma davranışlarının simülasyonu
    3. **Senaryo Analizi:** Farklı politika seçeneklerinin karşılaştırması
    
    ### 📖 Kaynaklar
    
    - IPCC (2006).  Guidelines for National Greenhouse Gas Inventories
    - T.C. Çevre Bakanlığı (2024). Turkish NIR 1990-2022
    - Yu et al. (2020). Modeling the ETS from an agent-based perspective
    """)
    
    # Rapor indirme
    st.markdown("---")
    st.markdown("### 📥 Rapor İndirme")
    
    if senaryo_sonuclari:
        # Tüm sonuçları birleştir
        tum_sonuclar = pd.concat([
            df.assign(Senaryo=senaryo) 
            for senaryo, df in senaryo_sonuclari.items()
        ])
        
        csv = tum_sonuclar.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📊 Senaryo Sonuçlarını İndir (CSV)",
            data=csv,
            file_name="tr_zero_senaryo_sonuclari.csv",
            mime="text/csv"
        )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem;">
    <p>TR-ZERO v2.0 | Endüstri Mühendisliği Bitirme Tezi | 2024</p>
    <p>Veri Kaynakları: UNFCCC NIR 2024, TÜİK, IEA</p>
</div>
""", unsafe_allow_html=True)