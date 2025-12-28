"""
TR-ZERO: Ulusal İklim Karar Destek Sistemi Dashboard (v3.0)
===========================================================

Profesyonel, tez sunumuna uygun, tamamen Türkçe dashboard. 

Özellikler:
-----------
- Light tema optimizasyonu
- Smooth animasyonlar
- Türkçe karakter desteği
- Responsive tasarım
- Profesyonel renk paleti

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih: Aralık 2025
Versiyon: 3.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# =============================================================================
# PROJE AYARLARI
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

DB_PATH = os.path.join(PROJECT_ROOT, "iklim_veritabani.sqlite")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# =============================================================================
# SAYFA YAPILANDIRMASI
# =============================================================================

st.set_page_config(
    page_title="TR-ZERO | Ulusal İklim Karar Destek Sistemi",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "TR-ZERO: Türkiye Sera Gazı Emisyon Analiz ve Projeksiyon Sistemi"
    }
)

# =============================================================================
# PROFESYONEL CSS TASARIMI
# =============================================================================

st.markdown("""
<style>
    /* ===== GENEL TEMA ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* ===== HEADER ===== */
    .main-header {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 50%, #134e4a 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(15, 118, 110, 0.3);
        text-align: center;
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* ===== METRİK KARTLARI ===== */
    .metric-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        flex: 1;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card.teal {
        border-left: 4px solid #0f766e;
    }
    
    .metric-card.blue {
        border-left: 4px solid #2563eb;
    }
    
    .metric-card.amber {
        border-left: 4px solid #d97706;
    }
    
    .metric-card.emerald {
        border-left: 4px solid #059669;
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0.25rem 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 500;
    }
    
    .metric-delta {
        font-size: 0.8rem;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    .metric-delta.positive {
        background: #dcfce7;
        color: #166534;
    }
    
    .metric-delta.negative {
        background: #fee2e2;
        color: #991b1b;
    }
    
    /* ===== BÖLÜM BAŞLIKLARI ===== */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .section-header h2 {
        color: #1e293b;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    
    .section-header .icon {
        font-size: 1.5rem;
    }
    
    /* ===== KART KONTEYNERLERI ===== */
    .chart-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
    }
    
    .chart-card h3 {
        color: #1e293b;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    .sidebar-header {
        text-align: center;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .sidebar-header h2 {
        color: #0f766e;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 0.5rem 0 0 0;
    }
    
    .sidebar-section {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .sidebar-section h4 {
        color: #475569;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }
    
    /* ===== TAB TASARIMI ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 0.5rem;
        gap: 0.5rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #64748b;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #0f766e;
    }
    
    /* ===== BUTONLAR ===== */
    .stButton > button {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(15, 118, 110, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(15, 118, 110, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* ===== INPUT ALANLARI ===== */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    
    .stSlider > div > div > div {
        background: #0f766e;
    }
    
    /* ===== DATAFRAME ===== */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    }
    
    /* ===== BİLGİ KUTULARI ===== */
    .info-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border-left: 4px solid #059669;
        margin: 1rem 0;
    }
    
    .info-box p {
        color: #065f46;
        margin: 0;
        font-size: 0.95rem;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border-left: 4px solid #d97706;
        margin: 1rem 0;
    }
    
    .warning-box p {
        color: #92400e;
        margin: 0;
        font-size: 0.95rem;
    }
    
    /* ===== FOOTER ===== */
    .footer {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    }
    
    .footer p {
        color: #64748b;
        font-size: 0.85rem;
        margin: 0.25rem 0;
    }
    
    .footer a {
        color: #0f766e;
        text-decoration: none;
        font-weight: 500;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# RENK PALETİ
# =============================================================================

RENKLER = {
    'birincil': '#0f766e',      # Teal
    'ikincil': '#115e59',       # Koyu Teal
    'vurgu': '#059669',         # Emerald
    'uyari': '#d97706',         # Amber
    'tehlike': '#dc2626',       # Kırmızı
    'basari': '#16a34a',        # Yeşil
    'bilgi': '#2563eb',         # Mavi
    'metin': '#1e293b',         # Koyu
    'acik_metin': '#64748b',    # Gri
    'arka_plan': '#f8fafc',     # Açık
    'kart': '#ffffff',          # Beyaz
    
    # Grafik renkleri
    'grafik': ['#0f766e', '#2563eb', '#d97706', '#dc2626', '#8b5cf6', '#059669']
}

SEKTOR_RENKLERI = {
    'Enerji': '#0f766e',
    'Endüstri': '#2563eb',
    'Tarım': '#d97706',
    'Atık': '#dc2626'
}

# =============================================================================
# VERİ FONKSİYONLARI
# =============================================================================

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
def senaryo_sonuclari_yukle():
    """Senaryo sonuçlarını yükler."""
    sonuclar = {}
    senaryo_isimleri = {
        "bau": "Referans Senaryo (BAU)",
        "yumusak_ets": "Yumuşak ETS",
        "siki_ets": "Sıkı ETS",
        "ets_tesvik": "ETS + Teşvik"
    }
    
    for dosya_adi, gorunen_isim in senaryo_isimleri.items():
        dosya_yolu = os.path.join(OUTPUT_DIR, f"senaryo_{dosya_adi}.csv")
        if os.path.exists(dosya_yolu):
            sonuclar[gorunen_isim] = pd.read_csv(dosya_yolu)
    
    return sonuclar if sonuclar else None

def sutun_adini_bul(df, adaylar):
    """DataFrame'de mevcut olan sütun adını bulur."""
    for aday in adaylar:
        if aday in df.columns:
            return aday
    return None

# =============================================================================
# BAŞLIK
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🌱 TR-ZERO</h1>
    <p>Türkiye Ulusal İklim Karar Destek Sistemi</p>
</div>
""", unsafe_allow_html=True)

# Veri kontrolü
df_envanter, df_il = veri_yukle()

if df_envanter is None:
    st.markdown("""
    <div class="warning-box">
        <p>⚠️ Veritabanı bulunamadı.  Lütfen önce kurulum dosyasını çalıştırın.</p>
    </div>
    """, unsafe_allow_html=True)
    st.code("python src/database_setup_v2.py", language="bash")
    st.stop()

# Sütun adlarını belirle
toplam_sutun = sutun_adini_bul(df_envanter, ['Toplam_LULUCF_Haric', 'Toplam'])
enerji_sutun = sutun_adini_bul(df_envanter, ['Enerji_Toplam', 'Enerji'])
ippu_sutun = sutun_adini_bul(df_envanter, ['IPPU_Toplam', 'Endustriyel_Islemler'])
tarim_sutun = sutun_adini_bul(df_envanter, ['Tarim_Toplam', 'Tarim'])
atik_sutun = sutun_adini_bul(df_envanter, ['Atik_Toplam', 'Atik'])

# Son yıl verileri
son_yil = int(df_envanter['Year'].max())
son_veri = df_envanter[df_envanter['Year'] == son_yil].iloc[0]
ilk_veri = df_envanter[df_envanter['Year'] == df_envanter['Year'].min()].iloc[0]

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div style="font-size: 3rem;">🌱</div>
        <h2>TR-ZERO</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Analiz Dönemi
    st.markdown("#### 📅 Analiz Dönemi")
    yil_baslangic, yil_bitis = st.slider(
        "Yıl Aralığı",
        min_value=int(df_envanter['Year'].min()),
        max_value=2035,
        value=(2015, 2035),
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Senaryo Seçimi
    st.markdown("#### 📊 Senaryo Seçimi")
    senaryo_secenekleri = ["Referans Senaryo (BAU)", "Yumuşak ETS", "Sıkı ETS", "ETS + Teşvik"]
    secili_senaryolar = st.multiselect(
        "Karşılaştırılacak Senaryolar",
        senaryo_secenekleri,
        default=["Referans Senaryo (BAU)", "Sıkı ETS"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # ETS Parametreleri
    st.markdown("#### ⚙️ ETS Parametreleri")
    
    karbon_fiyati = st.number_input(
        "Başlangıç Karbon Fiyatı ($/ton)",
        min_value=10,
        max_value=150,
        value=25,
        step=5
    )
    
    cap_azalma = st.slider(
        "Yıllık Tavan Azalma Oranı (%)",
        min_value=1.0,
        max_value=5.0,
        value=2.1,
        step=0.1
    )
    
    tesvik_miktari = st.number_input(
        "Yenilenebilir Teşviği ($/MW)",
        min_value=0,
        max_value=200000,
        value=50000,
        step=10000
    )
    
    st.markdown("---")
    
    # Çalıştır Butonu
    simule_et = st.button("🚀 Simülasyonu Çalıştır", use_container_width=True)
    
    st.markdown("---")
    
    # Kaynaklar
    st.markdown("#### 📚 Veri Kaynakları")
    st.markdown("""
    <small>
    • NIR 2024 Raporu<br>
    • TÜİK Emisyon İstatistikleri<br>
    • IEA Türkiye Profili<br>
    • IPCC AR6 Senaryoları
    </small>
    """, unsafe_allow_html=True)

# =============================================================================
# ANA İÇERİK - KPI KARTLARI
# =============================================================================

st.markdown("""
<div class="section-header">
    <span class="icon">📊</span>
    <h2>Temel Göstergeler</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    toplam_emisyon = son_veri[toplam_sutun]
    onceki_emisyon = df_envanter[df_envanter['Year'] == son_yil - 1][toplam_sutun].values[0]
    degisim = toplam_emisyon - onceki_emisyon
    
    st.markdown(f"""
    <div class="metric-card teal">
        <div class="metric-icon">📈</div>
        <div class="metric-label">Toplam Emisyon ({son_yil})</div>
        <div class="metric-value">{toplam_emisyon:.1f} Mt</div>
        <div class="metric-delta {'negative' if degisim > 0 else 'positive'}">
            {'↑' if degisim > 0 else '↓'} {abs(degisim):.1f} Mt
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    enerji_payi = (son_veri[enerji_sutun] / son_veri[toplam_sutun]) * 100
    
    st.markdown(f"""
    <div class="metric-card blue">
        <div class="metric-icon">⚡</div>
        <div class="metric-label">Enerji Sektörü Payı</div>
        <div class="metric-value">%{enerji_payi:.1f}</div>
        <div class="metric-delta negative">Ana emisyon kaynağı</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    artis_orani = ((son_veri[toplam_sutun] - ilk_veri[toplam_sutun]) / ilk_veri[toplam_sutun]) * 100
    
    st.markdown(f"""
    <div class="metric-card amber">
        <div class="metric-icon">📊</div>
        <div class="metric-label">1990'dan Bu Yana</div>
        <div class="metric-value">+%{artis_orani:.0f}</div>
        <div class="metric-delta negative">Kümülatif artış</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    ndc_hedef = 695
    kalan = ndc_hedef - son_veri[toplam_sutun]
    
    st.markdown(f"""
    <div class="metric-card emerald">
        <div class="metric-icon">🎯</div>
        <div class="metric-label">NDC 2030 Hedefi</div>
        <div class="metric-value">{ndc_hedef} Mt</div>
        <div class="metric-delta {'positive' if kalan > 0 else 'negative'}">
            {abs(kalan):.0f} Mt {'boşluk' if kalan > 0 else 'aşım'}
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# TABLAR
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Mevcut Durum",
    "🤖 Yapay Zeka Projeksiyonu",
    "🏭 Piyasa Simülasyonu",
    "🗺️ Bölgesel Analiz",
    "📋 Rapor ve İndirme"
])

# =============================================================================
# TAB 1: MEVCUT DURUM
# =============================================================================

with tab1:
    st.markdown("""
    <div class="section-header">
        <span class="icon">📈</span>
        <h2>Sektörel Emisyon Analizi</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col_grafik1, col_grafik2 = st.columns([3, 2])
    
    with col_grafik1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("<h3>📊 Sektörel Emisyon Trendi (1990-Günümüz)</h3>", unsafe_allow_html=True)
        
        # Çizgi grafiği
        fig_trend = go.Figure()
        
        sektor_verileri = [
            (enerji_sutun, 'Enerji', RENKLER['grafik'][0]),
            (ippu_sutun, 'Endüstri', RENKLER['grafik'][1]),
            (tarim_sutun, 'Tarım', RENKLER['grafik'][2]),
            (atik_sutun, 'Atık', RENKLER['grafik'][3])
        ]
        
        for sutun, isim, renk in sektor_verileri:
            if sutun and sutun in df_envanter.columns:
                fig_trend.add_trace(go.Scatter(
                    x=df_envanter['Year'],
                    y=df_envanter[sutun],
                    mode='lines+markers',
                    name=isim,
                    line=dict(color=renk, width=3),
                    marker=dict(size=6),
                    hovertemplate=f'<b>{isim}</b><br>Yıl: %{{x}}<br>Emisyon: %{{y:.1f}} Mt<extra></extra>'
                ))
        
        fig_trend.update_layout(
            xaxis_title="Yıl",
            yaxis_title="Emisyon (Mt CO₂ eşdeğeri)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450,
            margin=dict(l=60, r=30, t=30, b=60),
            xaxis=dict(gridcolor='#e2e8f0', zerolinecolor='#e2e8f0'),
            yaxis=dict(gridcolor='#e2e8f0', zerolinecolor='#e2e8f0')
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_grafik2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(f"<h3>🥧 Sektörel Dağılım ({son_yil})</h3>", unsafe_allow_html=True)
        
        # Pasta grafiği verileri
        sektor_degerleri = []
        sektor_isimleri = []
        sektor_renkleri = []
        
        for sutun, isim, renk in sektor_verileri:
            if sutun and sutun in df_envanter.columns:
                deger = son_veri[sutun]
                sektor_degerleri.append(deger)
                sektor_isimleri.append(isim)
                sektor_renkleri.append(renk)
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=sektor_isimleri,
            values=sektor_degerleri,
            hole=0.55,
            marker=dict(colors=sektor_renkleri),
            textinfo='label+percent',
            textfont=dict(size=13, color='#1e293b'),
            hovertemplate='<b>%{label}</b><br>Emisyon: %{value:.1f} Mt<br>Oran: %{percent}<extra></extra>',
            pull=[0.02, 0.02, 0.02, 0.02]
        )])
        
        fig_pie.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(
                text=f'<b>{son_veri[toplam_sutun]:.0f}</b><br>Mt CO₂eq',
                x=0.5, y=0.5,
                font=dict(size=18, color='#1e293b'),
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Alt bilgi kutusu
    st.markdown("""
    <div class="info-box">
        <p>📌 <strong>Not:</strong> Veriler, Türkiye Ulusal Envanter Raporu (NIR 2024) ve TÜİK resmi istatistiklerinden derlenmiştir.  
        Emisyon değerleri LULUCF sektörü hariç tutularak hesaplanmıştır.</p>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# TAB 2: YAPAY ZEKA PROJEKSİYONU
# =============================================================================

with tab2:
    st.markdown("""
    <div class="section-header">
        <span class="icon">🤖</span>
        <h2>Yapay Zeka Destekli Emisyon Projeksiyonu</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col_ayar, col_sonuc = st.columns([1, 3])
    
    with col_ayar:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("<h3>⚙️ Model Ayarları</h3>", unsafe_allow_html=True)
        
        hedef_sektor = st.selectbox(
            "Sektör Seçimi",
            ["Toplam Emisyon", "Enerji", "Endüstri", "Tarım", "Atık"],
            index=0
        )
        
        # Sektör-sütun eşleştirmesi
        sektor_sutun_map = {
            "Toplam Emisyon": toplam_sutun,
            "Enerji": enerji_sutun,
            "Endüstri": ippu_sutun,
            "Tarım": tarim_sutun,
            "Atık": atik_sutun
        }
        secili_sutun = sektor_sutun_map[hedef_sektor]
        
        model_derece = st.radio(
            "Model Tipi",
            ["Doğrusal (1. derece)", "Kuadratik (2. derece)", "Kübik (3. derece)"],
            index=1
        )
        derece_map = {"Doğrusal (1. derece)": 1, "Kuadratik (2. derece)": 2, "Kübik (3. derece)": 3}
        derece = derece_map[model_derece]
        
        hedef_yil = st.slider(
            "Projeksiyon Yılı",
            min_value=2025,
            max_value=2050,
            value=2035
        )
        
        tahmin_btn = st.button("📊 Projeksiyonu Hesapla", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_sonuc:
        if tahmin_btn or True:  # Her zaman göster
            from sklearn.preprocessing import PolynomialFeatures
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_absolute_error
            
            # Veri hazırlığı
            X = df_envanter['Year'].values.reshape(-1, 1)
            y = df_envanter[secili_sutun].values
            
            # Model eğitimi
            poly = PolynomialFeatures(degree=derece)
            X_poly = poly.fit_transform(X)
            model = LinearRegression()
            model.fit(X_poly, y)
            
            y_pred = model.predict(X_poly)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            # Gelecek projeksiyonu
            gelecek_yillar = np.arange(son_yil + 1, hedef_yil + 1).reshape(-1, 1)
            gelecek_poly = poly.transform(gelecek_yillar)
            gelecek_tahmin = model.predict(gelecek_poly)
            
            # NDC yörüngesi
            ndc_yillar = np.arange(son_yil + 1, 2031)
            ndc_tahmin = np.linspace(y[-1], 695, len(ndc_yillar))
            
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown(f"<h3>📈 {hedef_sektor} - Projeksiyon Sonuçları</h3>", unsafe_allow_html=True)
            
            # Grafik
            fig = go.Figure()
            
            # Gerçekleşen veriler
            fig.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=y,
                mode='markers',
                name='Gerçekleşen',
                marker=dict(color=RENKLER['birincil'], size=10, symbol='circle'),
                hovertemplate='Yıl: %{x}<br>Emisyon: %{y:.1f} Mt<extra></extra>'
            ))
            
            # Model trendi
            fig.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=y_pred,
                mode='lines',
                name='Model Trendi',
                line=dict(color=RENKLER['bilgi'], width=2),
            ))
            
            # BAU projeksiyonu
            fig.add_trace(go.Scatter(
                x=gelecek_yillar.flatten(),
                y=gelecek_tahmin,
                mode='lines',
                name='Referans Senaryo (BAU)',
                line=dict(color=RENKLER['tehlike'], width=3, dash='dash'),
            ))
            
            # NDC hedefi
            if hedef_sektor == "Toplam Emisyon":
                fig.add_trace(go.Scatter(
                    x=ndc_yillar,
                    y=ndc_tahmin,
                    mode='lines',
                    name='NDC Hedef Yörüngesi',
                    line=dict(color=RENKLER['basari'], width=3, dash='dot'),
                ))
                
                # 2030 hedef noktası
                fig.add_trace(go.Scatter(
                    x=[2030],
                    y=[695],
                    mode='markers+text',
                    name='NDC 2030',
                    marker=dict(color=RENKLER['basari'], size=14, symbol='star'),
                    text=['695 Mt'],
                    textposition='top center',
                    textfont=dict(size=12, color=RENKLER['basari'])
                ))
            
            # Hedef yıl tahmini
            hedef_tahmin = model.predict(poly.transform([[hedef_yil]]))[0]
            fig.add_trace(go.Scatter(
                x=[hedef_yil],
                y=[hedef_tahmin],
                mode='markers+text',
                name=f'{hedef_yil} Tahmini',
                marker=dict(color=RENKLER['uyari'], size=14, symbol='diamond'),
                text=[f'{hedef_tahmin:.0f} Mt'],
                textposition='top center',
                textfont=dict(size=12, color=RENKLER['uyari'])
            ))
            
            fig.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Emisyon (Mt CO₂ eşdeğeri)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                hovermode="x unified",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=450,
                xaxis=dict(gridcolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrikler
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("R² Skoru", f"{r2:.4f}", help="Model uyum kalitesi (1'e yakın = iyi)")
            with col_m2:
                st.metric("Ortalama Hata", f"{mae:.1f} Mt", help="Ortalama Mutlak Hata")
            with col_m3:
                st.metric(f"{hedef_yil} Tahmini", f"{hedef_tahmin:.0f} Mt")
            with col_m4:
                if hedef_sektor == "Toplam Emisyon":
                    fark = hedef_tahmin - 695
                    st.metric("NDC'den Sapma", f"{fark:+.0f} Mt", delta_color="inverse")
            
            st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 3: PİYASA SİMÜLASYONU
# =============================================================================

with tab3:
    st.markdown("""
    <div class="section-header">
        <span class="icon">🏭</span>
        <h2>Ajan Tabanlı Piyasa Simülasyonu</h2>
    </div>
    """, unsafe_allow_html=True)
    
    senaryo_sonuclari = senaryo_sonuclari_yukle()
    
    if senaryo_sonuclari:
        st.markdown("""
        <div class="info-box">
            <p>✅ Senaryo sonuçları başarıyla yüklendi.  Aşağıda farklı politika senaryolarının karşılaştırmalı analizi yer almaktadır.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_sim1, col_sim2 = st.columns(2)
        
        with col_sim1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h3>📉 Emisyon Karşılaştırması</h3>", unsafe_allow_html=True)
            
            fig_emisyon = go.Figure()
            
            renk_map = {
                "Referans Senaryo (BAU)": '#94a3b8',
                "Yumuşak ETS": '#3b82f6',
                "Sıkı ETS": '#22c55e',
                "ETS + Teşvik": '#8b5cf6'
            }
            
            for senaryo_adi, df in senaryo_sonuclari.items():
                if senaryo_adi in secili_senaryolar or not secili_senaryolar:
                    fig_emisyon.add_trace(go.Scatter(
                        x=df['Yil'],
                        y=df['Toplam_Emisyon'],
                        mode='lines+markers',
                        name=senaryo_adi,
                        line=dict(color=renk_map.get(senaryo_adi, '#666'), width=3),
                        marker=dict(size=6)
                    ))
            
            fig_emisyon.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Emisyon (Mt CO₂eq)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis=dict(gridcolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0')
            )
            
            st.plotly_chart(fig_emisyon, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_sim2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h3>💰 Karbon Fiyatı Gelişimi</h3>", unsafe_allow_html=True)
            
            fig_fiyat = go.Figure()
            
            for senaryo_adi, df in senaryo_sonuclari.items():
                if senaryo_adi in secili_senaryolar or not secili_senaryolar:
                    fig_fiyat.add_trace(go.Scatter(
                        x=df['Yil'],
                        y=df['Karbon_Fiyati'],
                        mode='lines+markers',
                        name=senaryo_adi,
                        line=dict(color=renk_map.get(senaryo_adi, '#666'), width=3),
                        marker=dict(size=6)
                    ))
            
            fig_fiyat.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Fiyat ($/ton CO₂)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis=dict(gridcolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0')
            )
            
            st.plotly_chart(fig_fiyat, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Özet Tablo
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("<h3>📋 Senaryo Karşılaştırma Tablosu (2035)</h3>", unsafe_allow_html=True)
        
        bau_emisyon = senaryo_sonuclari.get("Referans Senaryo (BAU)", pd.DataFrame({'Toplam_Emisyon': [0]}))['Toplam_Emisyon'].iloc[-1]
        
        tablo_verileri = []
        for senaryo_adi, df in senaryo_sonuclari.items():
            emisyon = df['Toplam_Emisyon'].iloc[-1]
            azaltim = ((bau_emisyon - emisyon) / bau_emisyon * 100) if bau_emisyon > 0 else 0
            tablo_verileri.append({
                'Senaryo': senaryo_adi,
                'Emisyon (2035)': f"{emisyon:.1f} Mt",
                'Azaltım (BAU\'ya göre)': f"%{azaltim:.1f}",
                'Karbon Fiyatı': f"${df['Karbon_Fiyati'].iloc[-1]:.0f}/ton",
                'Dönüşen Tesis': f"{int(df['Temiz_Tesis'].iloc[-1]) if 'Temiz_Tesis' in df.columns else '-'}"
            })
        
        st.dataframe(
            pd.DataFrame(tablo_verileri),
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div class="warning-box">
            <p>⚠️ Senaryo sonuçları bulunamadı.  Lütfen simülasyonu çalıştırın:</p>
        </div>
        """, unsafe_allow_html=True)
        st.code("python src/piyasa_simulasyonu_v2.py", language="bash")

# =============================================================================
# TAB 4: BÖLGESEL ANALİZ
# =============================================================================

with tab4:
    st.markdown("""
    <div class="section-header">
        <span class="icon">🗺️</span>
        <h2>Bölgesel Emisyon Dağılımı</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if df_il is not None and not df_il.empty:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        
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
        
        son_toplam = son_veri[toplam_sutun]
        
        df_harita = df_il.copy()
        df_harita['Emisyon'] = df_harita['Sanayi_Payi'] * son_toplam
        df_harita['lat'] = df_harita['Il_Adi'].map(lambda x: il_koordinatlar.get(x, (39.0, 35.0))[0])
        df_harita['lon'] = df_harita['Il_Adi'].map(lambda x: il_koordinatlar.get(x, (39.0, 35.0))[1])
        
        fig_map = px.scatter_mapbox(
            df_harita,
            lat='lat',
            lon='lon',
            size='Emisyon',
            color='Emisyon',
            hover_name='Il_Adi',
            hover_data={'Emisyon': ':.2f', 'lat': False, 'lon': False},
            color_continuous_scale=[
                [0, '#d1fae5'],
                [0.5, '#fbbf24'],
                [1, '#dc2626']
            ],
            size_max=50,
            zoom=5,
            center={"lat": 39.0, "lon": 35.0}
        )
        
        fig_map.update_layout(
            mapbox_style="carto-positron",
            height=500,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(
                title="Emisyon (Mt)",
                tickformat=".1f"
            )
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
        
        # Bölge tablosu
        st.markdown("<h3>📊 İl Bazlı Emisyon Sıralaması</h3>", unsafe_allow_html=True)
        
        df_goster = df_harita[['Il_Adi', 'Bolge', 'Sanayi_Payi', 'Emisyon']].copy()
        df_goster = df_goster.sort_values('Emisyon', ascending=False)
        df_goster['Sanayi_Payi'] = (df_goster['Sanayi_Payi'] * 100).round(2).astype(str) + '%'
        df_goster['Emisyon'] = df_goster['Emisyon'].round(2).astype(str) + ' Mt'
        df_goster.columns = ['İl', 'Bölge', 'Sanayi Payı', 'Emisyon']
        
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Bölgesel veri bulunamadı.")

# =============================================================================
# TAB 5: RAPOR VE İNDİRME
# =============================================================================

with tab5:
    st.markdown("""
    <div class="section-header">
        <span class="icon">📋</span>
        <h2>Analiz Raporu ve Veri İndirme</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("""
    ### 📊 Yönetici Özeti
    
    Bu rapor, Türkiye'nin sera gazı emisyonlarının mevcut durumunu, gelecek projeksiyonlarını ve 
    farklı politika senaryolarının karşılaştırmalı analizini sunmaktadır. 
    """)
    
    col_ozet1, col_ozet2 = st.columns(2)
    
    with col_ozet1:
        st.markdown(f"""
        #### 📈 Mevcut Durum
        - **Toplam Emisyon ({son_yil}):** {son_veri[toplam_sutun]:.1f} Mt CO₂eq
        - **Enerji Sektörü Payı:** %{(son_veri[enerji_sutun]/son_veri[toplam_sutun]*100):.1f}
        - **1990'dan Bu Yana Artış:** +%{((son_veri[toplam_sutun]-ilk_veri[toplam_sutun])/ilk_veri[toplam_sutun]*100):.0f}
        """)
    
    with col_ozet2:
        st.markdown("""
        #### 🎯 Hedefler ve Taahhütler
        - **NDC 2030 Hedefi:** 695 Mt CO₂eq
        - **Net Sıfır Hedef Yılı:** 2053
        - **ETS Başlangıcı:** 2026
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 📚 Metodoloji
    
    Bu çalışmada üç temel metodoloji kullanılmıştır:
    
    1.  **Polinom Regresyon Analizi:** Geçmiş verilere dayalı trend tahmini
    2. **Ajan Tabanlı Modelleme (ABM):** Firma davranışlarının simülasyonu
    3. **Senaryo Analizi:** Farklı politika seçeneklerinin değerlendirilmesi
    
    ### 📖 Kaynak Referansları
    
    - IPCC (2006).  Guidelines for National Greenhouse Gas Inventories
    - T.C. Çevre Bakanlığı (2024). Turkish NIR 1990-2022
    - Yu et al. (2020). Modeling the ETS from an agent-based perspective
    - Climate Action Tracker (2024). Türkiye Country Assessment
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # İndirme bölümü
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### 📥 Veri İndirme")
    
    col_indir1, col_indir2, col_indir3 = st.columns(3)
    
    with col_indir1:
        envanter_csv = df_envanter.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📊 Envanter Verileri (CSV)",
            data=envanter_csv,
            file_name="tr_zero_envanter_verileri.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_indir2:
        if senaryo_sonuclari:
            tum_senaryolar = pd.concat([
                df.assign(Senaryo=isim) for isim, df in senaryo_sonuclari.items()
            ])
            senaryo_csv = tum_senaryolar.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="🏭 Senaryo Sonuçları (CSV)",
                data=senaryo_csv,
                file_name="tr_zero_senaryo_sonuclari.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col_indir3:
        if df_il is not None:
            il_csv = df_il.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="🗺️ Bölgesel Veriler (CSV)",
                data=il_csv,
                file_name="tr_zero_bolgesel_veriler.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("""
<div class="footer">
    <p><strong>TR-ZERO</strong> | Ulusal İklim Karar Destek Sistemi v3.0</p>
    <p>Endüstri Mühendisliği Bitirme Tezi | 2024</p>
    <p style="margin-top: 0.5rem; font-size: 0.8rem;">
        Veri Kaynakları: UNFCCC NIR 2024 • TÜİK • IEA • Climate Action Tracker
    </p>
</div>
""", unsafe_allow_html=True)