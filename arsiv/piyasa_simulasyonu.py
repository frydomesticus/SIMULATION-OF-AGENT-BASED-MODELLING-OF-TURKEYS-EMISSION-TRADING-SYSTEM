from mesa import Agent, Model
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import pandas as pd
import random

# --- 1. GELİŞMİŞ AJAN TANIMI (Universal Agent) ---
class UniversalAgent(Agent):
    def __init__(self, uid, model, sektor):
        super().__init__(model)
        self.sektor = sektor
        self.durum = "Kirleten" # Başlangıç durumu
        
        # SKDM İÇİN: %40 İhtimalle İhracatçı Olma (Sanayi ise)
        self.ihracatci = True if random.random() < 0.4 and sektor in ["Enerji", "Sanayi"] else False
        
        # SEKTÖREL VERİLER (Maliyet ve Limitler)
        if sektor == "Enerji":
            # Enerji: Vergiye duyarlı
            self.limit = 90
            self.yatirim_bedeli = 200
            self.duyarli_oldugu = "Vergi"
            self.base_cost = 40
            self.emission = 0.9
        elif sektor == "Sanayi": # Çimento/Demir-Çelik
            # Sanayi: Vergiye duyarlı, limiti daha yüksek
            self.limit = 110
            self.yatirim_bedeli = 250
            self.duyarli_oldugu = "Vergi"
            self.base_cost = 60
            self.emission = 0.6
        elif sektor == "Tarım":
            # Tarım: Sadece Teşvike duyarlı
            self.limit = 999 # Batmaz
            self.yatirim_bedeli = 300
            self.duyarli_oldugu = "Teşvik"
            self.base_cost = 30
            self.emission = 0.5
        
        # Yatırımın yıllık maliyeti (Amortisman)
        self.yatirim_taksiti = self.yatirim_bedeli / 10 

    def step(self):
        # 1. VERGİ YÜKÜNÜ HESAPLA (SKDM Dahil)
        if self.ihracatci:
            # İhracatçı ise TR veya AB vergisinden yüksek olanı öder
            vergi_yuku = max(self.model.tax, self.model.ab_tax)
        else:
            vergi_yuku = self.model.tax
        
        # 2. TEŞVİK DESTEĞİNİ AL
        devlet_destegi = self.model.tesvik
        
        # 3. KARAR MEKANİZMASI (MAC Analizi)
        if self.duyarli_oldugu == "Vergi":
            # Maliyet A: Eski teknoloji + Yüksek Vergi
            maliyet_eski = self.base_cost + (self.emission * vergi_yuku)
            
            # Maliyet B: Yatırım Yap + Düşük Vergi + Yatırım Taksiti
            maliyet_yeni = self.base_cost + (self.emission * 0.2 * vergi_yuku) + self.yatirim_taksiti
            
            if self.durum == "Kirleten":
                # Yatırım karlı mı?
                if maliyet_yeni < maliyet_eski and maliyet_yeni < self.limit:
                    self.durum = "Temiz" # YEŞİL DÖNÜŞÜM!
                # Karlı değilse ve eski maliyet limiti aşıyorsa BATAR
                elif maliyet_eski >= self.limit:
                    self.durum = "Kapalı"
                    
        elif self.duyarli_oldugu == "Teşvik":
            # Tarım sadece devlet desteği yeterliyse dönüşür
            if devlet_destegi >= (self.yatirim_bedeli * 0.6): # %60 Hibe varsa
                self.durum = "Temiz"

# --- 2. MODEL TANIMI ---
class EkonomiModeli(Model):
    def __init__(self, rate, ab_tax, tesvik):
        super().__init__()
        self.tax = 0
        self.rate = rate
        self.ab_tax = ab_tax
        self.tesvik = tesvik
        
        # Ajanları Yarat
        for i in range(50): UniversalAgent(i, self, "Enerji")
        for i in range(30): UniversalAgent(i, self, "Sanayi")
        for i in range(20): UniversalAgent(i, self, "Tarım")
            
        self.dc = DataCollector(model_reporters={
            "Vergi": lambda m: m.tax,
            "Sanayi (Kirleten)": lambda m: sum([1 for a in m.agents if a.sektor in ["Enerji","Sanayi"] and a.durum=="Kirleten"]),
            "Sanayi (Dönüşen)": lambda m: sum([1 for a in m.agents if a.sektor in ["Enerji","Sanayi"] and a.durum=="Temiz"]),
            "Tarım (Dönüşen)": lambda m: sum([1 for a in m.agents if a.sektor=="Tarım" and a.durum=="Temiz"]),
            "Batan": lambda m: sum([1 for a in m.agents if a.durum=="Kapalı"])
        })

    def step(self):
        self.dc.collect(self)
        self.tax += self.rate
        self.agents.shuffle().do("step")

# --- 3. ÇALIŞTIRMA VE TEST ---
def simulasyonu_baslat():
    print("--- 🚀 Gelişmiş Piyasa Simülasyonu Başlatılıyor ---")
    print("Senaryo: Vergi Artışı=5$, AB SKDM=90$, Tarım Teşviki=200$")
    
    model = EkonomiModeli(rate=5, ab_tax=90, tesvik=200)
    
    for i in range(25):
        model.step()
        
    df = model.dc.get_model_vars_dataframe()
    
    # Grafik Çiz
    plt.figure(figsize=(10,6))
    plt.stackplot(df.index, 
                  df["Sanayi (Kirleten)"], 
                  df["Sanayi (Dönüşen)"],
                  df["Tarım (Dönüşen)"],
                  labels=['Kirleten Sanayi', 'Yeşil Sanayi (Vergi Etkisi)', 'Yeşil Tarım (Teşvik Etkisi)'],
                  colors=['gray', 'green', 'orange'], alpha=0.7)
    
    plt.plot(df["Vergi"], 'r--', label="Vergi Seviyesi ($)", linewidth=2)
    plt.title("Çoklu Sektör ve Politika Etki Analizi")
    plt.xlabel("Yıl")
    plt.ylabel("Ajan Sayısı")
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.show()
    print("✅ Simülasyon tamamlandı. Grafik oluşturuldu.")

if __name__ == "__main__":
    simulasyonu_baslat()