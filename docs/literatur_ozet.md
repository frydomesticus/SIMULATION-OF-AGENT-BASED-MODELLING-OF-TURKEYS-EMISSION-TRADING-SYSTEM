# 📚 TR-ZERO: Literatür Tarama Özeti

**Son Güncelleme:** 28 Aralık 2025

---

## 📖 İçindekiler

1. [Emisyon Ticaret Sistemleri (ETS)](#1-emisyon-ticaret-sistemleri-ets)
2. [Ajan Tabanlı Modelleme (ABM)](#2-ajan-tabanlı-modelleme-abm)
3. [Türkiye İklim Politikaları](#3-türkiye-iklim-politikaları)
4. [Karbon Piyasası Simülasyonları](#4-karbon-piyasası-simülasyonları)
5. [Metodoloji Kaynakları](#5-metodoloji-kaynakları)

---

## 1. Emisyon Ticaret Sistemleri (ETS)

### 1.1 Temel Kaynaklar

| # | Referans | Konu | Katkı | Yıl |
|---|----------|------|-------|-----|
| 1 | **EU ETS Directive 2003/87/EC** | AB ETS kuralları | Cap & Trade mekanizması, tahsisat kuralları | 2003 |
| 2 | **ICAP (2024). Status Report** | Küresel ETS durumu | 36 ETS sistemi karşılaştırması | 2024 |
| 3 | **World Bank (2024). Carbon Pricing Dashboard** | Karbon fiyatlandırması | Global fiyat trendleri | 2024 |
| 4 | **Ellerman et al. (2010). Pricing Carbon** | EU ETS analizi | İlk dönem dersleri | 2010 |
| 5 | **Schmalensee & Stavins (2017). Lessons from SO₂** | Cap-trade tasarımı | ABD deneyimi | 2017 |

### 1.2 ETS Tasarım Özellikleri

| Özellik | EU ETS | Çin ETS | Kore ETS | TR-ETS (Taslak) |
|---------|--------|---------|----------|-----------------|
| Başlangıç | 2005 | 2021 | 2015 | 2026 (Pilot) |
| Kapsam | Enerji + Sanayi | Enerji | Enerji + Sanayi | Enerji + Sanayi |
| Cap Azaltma | %4.3/yıl (Faz 4) | Yoğunluk bazlı | %2/yıl | %2-4/yıl (önerilen) |
| Ücretsiz Tahsisat | %57 (2021) | %100 | %97 (Faz 1) | ~%70-100 |
| Fiyat (2024) | ~€80/ton | ~$12/ton | ~$10/ton | $20-50/ton (tahmin) |

---

## 2. Ajan Tabanlı Modelleme (ABM)

### 2.1 Temel ABM Kaynakları

| # | Referans | Konu | Metodoloji | Yıl |
|---|----------|------|------------|-----|
| 1 | **Yu et al. (2020). EJOR** | ETS simülasyonu | Heterojen ajanlar, piyasa-clearing | 2020 |
| 2 | **Zhou et al. (2016). Springer** | Politika değerlendirme | Multi-agent karbon piyasası | 2016 |
| 3 | **Tang et al. (2022). Energy Policy** | Firma davranışı | Karar mekanizması, MAC analizi | 2022 |
| 4 | **Bonabeau (2002). PNAS** | ABM temelleri | Kompleks sistem modellemesi | 2002 |
| 5 | **Farmer & Foley (2009). Nature** | Ekonomi-ABM | Makro-ekonomik ABM | 2009 |

### 2.2 ABM Framework Karşılaştırması

| Framework | Dil | Özellik | Kullanım Alanı |
|-----------|-----|---------|----------------|
| **Mesa** (Python) | Python | Basit, esnek | Sosyal simülasyon, piyasa |
| **NetLogo** | Logo | Görsel, eğitim | Ekoloji, sosyal dinamik |
| **GAMA** | Java | CBS entegrasyonu | Şehir, ulaşım |
| **Repast** | Java/Python | Büyük ölçek | Ekonomi, sağlık |

> **TR-ZERO Seçimi:** Mesa (Python) - Veri bilimi kütüphaneleri ile entegrasyon, hızlı prototipleme

### 2.3 📗 Elsevier/ScienceDirect - ETS & ABM Makaleleri (Güncel)

| # | Makale | Dergi | Konu | DOI | Yıl |
|---|--------|-------|------|-----|-----|
| 1 | **Yu, S., Fan, Y., Zhu, L., Eichhammer, W.** "Modeling the emission trading scheme from an agent-based perspective: System dynamics emerging from firms' coordination among abatement options" | European Journal of Operational Research | ABM + ETS, Firma koordinasyonu, Azaltım seçenekleri | [10.1016/j.ejor.2020.03.080](https://doi.org/10.1016/j.ejor.2020.03.080) | 2020 |
| 2 | **Tang, L., Wu, J., Yu, L., Bao, Q.** "Carbon allowance auction design of China's emissions trading scheme: A multi-agent-based approach" | Energy Policy | Açık artırma tasarımı, Multi-agent | [10.1016/j.enpol.2017.09.041](https://doi.org/10.1016/j.enpol.2017.09.041) | 2017 |
| 3 | **Chappin, E.J.L., Dijkema, G.P.J.** "Agent-based modelling of energy infrastructure transitions" | International Journal of Critical Infrastructures | Enerji altyapısı, Geçiş simülasyonu | [10.1504/IJCIS.2010.033341](https://doi.org/10.1504/IJCIS.2010.033341) | 2010 |
| 4 | **de Vries, L.J., Chappin, E.J.L.,"; A.** "EMLab-Generation: An experimentation environment for electricity policy analysis" | Energy Policy | EU enerji politikası, ABM | [10.1016/j.enpol.2012.09.067](https://doi.org/10.1016/j.enpol.2012.09.067) | 2013 |
| 5 | **Gerst, M.D., Wang, P., Roventini, A., et al.** "Agent-based modeling of climate policy: An introduction to the ENGAGE multi-level model framework" | Environmental Modelling & Software | İklim politikası, Çok seviyeli ABM | [10.1016/j.envsoft.2013.05.012](https://doi.org/10.1016/j.envsoft.2013.05.012) | 2013 |
| 6 | **Iychettira, K.K., Hakvoort, R.A., Linares, P., de Jeu, R.** "Towards a comprehensive policy for electricity from renewable energy: Designing for social welfare" | Applied Energy | Yenilenebilir enerji politikası, ABM | [10.1016/j.apenergy.2017.07.063](https://doi.org/10.1016/j.apenergy.2017.07.063) | 2017 |
| 7 | **Zhang, Y.J., Wei, Y.M.** "An overview of current research on EU ETS: Evidence from its operating mechanism and economic effect" | Applied Energy | EU ETS analizi, Ekonomik etkiler | [10.1016/j.apenergy.2010.06.015](https://doi.org/10.1016/j.apenergy.2010.06.015) | 2010 |
| 8 | **Goulder, L.H., Schein, A.R.** "Carbon taxes versus cap and trade: A critical review" | Climate Change Economics | Carbon vergi vs ETS karşılaştırma | [10.1142/S2010007813500036](https://doi.org/10.1142/S2010007813500036) | 2013 |
| 9 | **Lin, B., Jia, Z.** "What will China's carbon emission trading market affect with only electricity sector involvement? A CGE based study" | Energy Economics | Çin ETS, Elektrik sektörü, CGE | [10.1016/j.eneco.2019.06.019](https://doi.org/10.1016/j.eneco.2019.06.019) | 2019 |
| 10 | **Cludius, J., de Bruyn, S., Schumacher, K., Vergeer, R.** "Ex-post investigation of cost pass-through in the EU ETS" | Energy Policy | Maliyet aktarımı, EU ETS | [10.1016/j.enpol.2019.111063](https://doi.org/10.1016/j.enpol.2019.111063) | 2020 |

### 2.4 📘 Güncel ABM-ETS Makaleleri (2021-2024)

| # | Makale | Dergi | Ana Bulgu | Yıl |
|---|--------|-------|-----------|-----|
| 1 | **Liu, X. et al.** "Agent-based simulation of China's carbon market" | Journal of Cleaner Production | Çin karbon piyasası pazar dinamikleri | 2023 |
| 2 | **Wang, Q. et al.** "Carbon trading and green technology innovation" | Technological Forecasting and Social Change | ETS ve yeşil inovasyon ilişkisi | 2024 |
| 3 | **Chen, L. et al.** "Energy-emission trading coupling analysis" | Energy | Enerji-emisyon bağlantısı | 2023 |
| 4 | **Huang, Y. et al.** "Multi-agent reinforcement learning for ETS" | Applied Energy | Yapay zeka destekli ETS simülasyonu | 2024 |
| 5 | **Zhao, X. et al.** "Carbon market price forecasting with ABM" | Energy Economics | Fiyat tahmini, ABM yaklaşımı | 2023 |

### 2.5 🔑 TR-ZERO İçin Kritik Referanslar (Metodoloji Temeli)

| Öncelik | Referans | Neden Kritik? | Kullanım Alanı |
|---------|----------|---------------|----------------|
| ⭐⭐⭐ | **Yu et al. (2020) EJOR** | Ana metodoloji referansı, firma koordinasyon modeli | Ajan karar mekanizması |
| ⭐⭐⭐ | **Tang et al. (2017) Energy Policy** | Açık artırma tasarımı, multi-agent | Piyasa operatörü tasarımı |
| ⭐⭐⭐ | **EU ETS Directive** | Mekanizma tasarımı | Cap & Trade kuralları |
| ⭐⭐ | **Chappin & Dijkema (2010)** | ABM enerji altyapısı | Model mimarisi |
| ⭐⭐ | **Zhang & Wei (2010)** | EU ETS kapsamlı analiz | Karşılaştırma referansı |
| ⭐ | **Lin & Jia (2019)** | Çin ETS CGE | Ekonomik etki karşılaştırma |

---

## 3. Türkiye İklim Politikaları

### 3.1 Resmi Kaynaklar

| # | Kaynak | İçerik | Link |
|---|--------|--------|------|
| 1 | **NIR 2024** | Ulusal Envanter Raporu | [UNFCCC](https://unfccc.int/documents/627786) |
| 2 | **BTR 2024** | İki Yıllık Şeffaflık Raporu | [iklim.gov.tr](https://iklim.gov.tr) |
| 3 | **TR-ETS Taslak (2025)** | ETS Yönetmelik Taslağı | [iklim.gov.tr](https://iklim.gov.tr/taslaklar-i-2124) |
| 4 | **INDC/NDC 2015, 2023** | Ulusal Katkı Beyanları | [UNFCCC](https://unfccc.int) |
| 5 | **İklim Kanunu Taslağı (2024)** | Çerçeve mevzuat | [TBMM](https://www.tbmm.gov.tr) |

### 3.2 Türkiye Emisyon Verileri

| Yıl | Toplam Emisyon (Mt CO₂e) | Enerji | Sanayi | Tarım | Atık |
|-----|--------------------------|--------|--------|-------|------|
| 1990 | 219.8 | 139.5 | 35.2 | 32.4 | 12.7 |
| 2000 | 297.0 | 195.1 | 47.3 | 35.0 | 19.6 |
| 2010 | 401.9 | 274.1 | 64.7 | 36.2 | 26.9 |
| 2020 | 506.1 | 330.1 | 84.3 | 42.0 | 49.7 |
| 2022 | 515.5 | 333.8 | 88.2 | 42.5 | 51.0 |

> **Kaynak:** TÜİK Sera Gazı Emisyon İstatistikleri, 2024

---

## 4. Karbon Piyasası Simülasyonları

### 4.1 İlgili Çalışmalar

| # | Referans | Ülke/Bölge | Model Tipi | Sonuçlar |
|---|----------|------------|------------|----------|
| 1 | **Cludius et al. (2020)** | EU | Ekonometri | ETS fayda-maliyet analizi |
| 2 | **Zhang et al. (2019)** | Çin | CGE + ABM | Sektörel etki analizi |
| 3 | **OECD (2020)** | Türkiye | CGE | Karbon vergi senaryoları |
| 4 | **EBRD (2024)** | Türkiye | Sektörel | Çimento dekarbonizasyonu |
| 5 | **IEA (2024)** | Türkiye | Enerji modeli | Net-sıfır yol haritası |

### 4.2 Literatürdeki Boşluklar

| Boşluk | Açıklama | TR-ZERO Katkısı |
|--------|----------|-----------------|
| ❌ Türkiye için ABM yok | CGE modelleri hakim | ✅ İlk Türkiye ABM ETS simülasyonu |
| ❌ İl bazlı analiz eksik | Ulusal toplam veriler | ✅ 81 il için dağılım katsayıları |
| ❌ Tesis düzeyi eksik | Sektör toplamları | ✅ 40 büyük tesis modellemesi |
| ❌ Hibrit model yok | Tek paradigma | ✅ ABM + SD + Dispatch entegrasyonu |

---

## 5. Metodoloji Kaynakları

### 5.1 Emisyon Faktörleri

| Kaynak | Kullanım | Referans |
|--------|----------|----------|
| **IPCC 2006 Guidelines** | Standart EF değerleri | Vol.2, Ch.2 Stationary Combustion |
| **EPA Emission Factors (2021)** | ABD EF değerleri | AP-42 |
| **NIR Turkey 2024** | Türkiye özel EF | UNFCCC submission |

### 5.2 MAC Eğrileri

| Kaynak | Kapsam | Değer Aralığı |
|--------|--------|---------------|
| **McKinsey GHG Cost Curve (2009)** | Global, sektörel | -$100 ile +$100/tCO₂ |
| **EBRD Turkey Cement (2024)** | Türkiye çimento | $20-80/tCO₂ |
| **IEA ETP (2023)** | Teknoloji bazlı | Sektöre göre değişken |

---

## 📑 Önerilen Okuma Listesi (16 Ocak İçin)

### Kritik (Mutlaka Okunmalı)
1. Yu et al. (2020) - ABM ETS metodolojisiniz için temel
2. EU ETS Directive - Mekanizma tasarımı
3. NIR Turkey 2024 - Veri kaynağınız

### Önemli (Göz atılmalı)
4. Zhou et al. (2016) - Multi-agent referansı
5. ICAP Status Report 2024 - Global karşılaştırma
6. EBRD Turkey Cement 2024 - Sektör örneği

### Faydalı (Varsa)
7. McKinsey GHG Cost Curve
8. Tang et al. (2022)
9. OECD Turkey Carbon Pricing

---

## 📚 BibTeX Referansları

```bibtex
% =============================================================================
% ANA METODOLOJI REFERANSLARI (TR-ZERO için kritik)
% =============================================================================

@article{yu2020modeling,
  title={Modeling the emission trading scheme from an agent-based perspective: System dynamics emerging from firms' coordination among abatement options},
  author={Yu, Songmin and Fan, Ying and Zhu, Lei and Eichhammer, Wolfgang},
  journal={European Journal of Operational Research},
  volume={286},
  number={3},
  pages={1113--1128},
  year={2020},
  publisher={Elsevier},
  doi={10.1016/j.ejor.2020.03.080}
}

@article{tang2017carbon,
  title={Carbon allowance auction design of China's emissions trading scheme: A multi-agent-based approach},
  author={Tang, Ling and Wu, Jiaqian and Yu, Lean and Bao, Qin},
  journal={Energy Policy},
  volume={102},
  pages={30--40},
  year={2017},
  publisher={Elsevier},
  doi={10.1016/j.enpol.2017.09.041}
}

@incollection{zhou2016multi,
  title={Multi-agent-based Simulation for Policy Evaluation of Carbon Emissions},
  author={Zhou, Peng and others},
  booktitle={Agent-Based Approaches in Economics and Social Complex Systems},
  publisher={Springer},
  year={2016},
  doi={10.1007/978-981-10-2669-0_29}
}

% =============================================================================
% ETS SİSTEMLERİ VE POLİTİKA ANALİZİ
% =============================================================================

@article{zhang2010overview,
  title={An overview of current research on EU ETS: Evidence from its operating mechanism and economic effect},
  author={Zhang, Yue-Jun and Wei, Yi-Ming},
  journal={Applied Energy},
  volume={87},
  number={6},
  pages={1804--1814},
  year={2010},
  publisher={Elsevier},
  doi={10.1016/j.apenergy.2010.06.015}
}

@article{cludius2020cost,
  title={Ex-post investigation of cost pass-through in the EU ETS--an analysis for six sectors},
  author={Cludius, Johanna and de Bruyn, Sander and Schumacher, Katja and Vergeer, Robert},
  journal={Energy Policy},
  volume={140},
  pages={111063},
  year={2020},
  publisher={Elsevier},
  doi={10.1016/j.enpol.2019.111063}
}

@article{lin2019china,
  title={What will China's carbon emission trading market affect with only electricity sector involvement? A CGE based study},
  author={Lin, Boqiang and Jia, Zhijie},
  journal={Energy Economics},
  volume={78},
  pages={301--311},
  year={2019},
  publisher={Elsevier},
  doi={10.1016/j.eneco.2019.06.019}
}

@article{goulder2013carbon,
  title={Carbon taxes versus cap and trade: A critical review},
  author={Goulder, Lawrence H and Schein, Andrew R},
  journal={Climate Change Economics},
  volume={4},
  number={3},
  pages={1350010},
  year={2013},
  publisher={World Scientific},
  doi={10.1142/S2010007813500036}
}

% =============================================================================
% ABM METODOLOJİSİ
% =============================================================================

@article{chappin2010agent,
  title={Agent-based modelling of energy infrastructure transitions},
  author={Chappin, Emile JL and Dijkema, Gerard PJ},
  journal={International Journal of Critical Infrastructures},
  volume={6},
  number={2},
  pages={106--130},
  year={2010},
  publisher={Inderscience},
  doi={10.1504/IJCIS.2010.033341}
}

@article{devries2013emlab,
  title={EMLab-Generation: An experimentation environment for electricity policy analysis},
  author={de Vries, Laurens J and Chappin, Emile JL and"; A."},
  journal={Energy Policy},
  volume={55},
  pages={50--58},
  year={2013},
  publisher={Elsevier},
  doi={10.1016/j.enpol.2012.09.067}
}

@article{gerst2013agent,
  title={Agent-based modeling of climate policy: An introduction to the ENGAGE multi-level model framework},
  author={Gerst, Michael D and Wang, Peng and Roventini, Andrea and Fagiolo, Giorgio and Dosi, Giovanni and Howarth, Richard B and Borsuk, Mark E},
  journal={Environmental Modelling \& Software},
  volume={44},
  pages={62--75},
  year={2013},
  publisher={Elsevier},
  doi={10.1016/j.envsoft.2013.05.012}
}

@article{bonabeau2002agent,
  title={Agent-based modeling: Methods and techniques for simulating human systems},
  author={Bonabeau, Eric},
  journal={Proceedings of the National Academy of Sciences},
  volume={99},
  number={suppl 3},
  pages={7280--7287},
  year={2002},
  publisher={National Academy of Sciences},
  doi={10.1073/pnas.082080899}
}

% =============================================================================
% TÜRKİYE VERİ KAYNAKLARI
% =============================================================================

@techreport{icap2024status,
  title={Emissions Trading Worldwide: Status Report 2024},
  author={{International Carbon Action Partnership}},
  institution={ICAP},
  year={2024},
  url={https://icapcarbonaction.com/en/publications}
}

@techreport{turkey_nir2024,
  title={Turkish Greenhouse Gas Inventory 1990-2022: National Inventory Report},
  author={{Republic of Turkey Ministry of Environment, Urbanization and Climate Change}},
  institution={UNFCCC},
  year={2024},
  url={https://unfccc.int/documents/627786}
}

@techreport{ebrd2024cement,
  title={A Low Carbon Pathway for the Cement Sector in the Republic of Türkiye},
  author={{European Bank for Reconstruction and Development}},
  institution={EBRD},
  year={2024},
  url={https://www.ebrd.com/}
}

@misc{tuik2024sera,
  title={Sera Gazı Emisyon İstatistikleri, 1990-2023},
  author={{Türkiye İstatistik Kurumu}},
  year={2024},
  url={https://data.tuik.gov.tr/}
}

% =============================================================================
% METODOLOJİ VE EMİSYON FAKTÖRLERİ
% =============================================================================

@book{ipcc2006guidelines,
  title={2006 IPCC Guidelines for National Greenhouse Gas Inventories},
  author={{Intergovernmental Panel on Climate Change}},
  year={2006},
  publisher={IGES},
  url={https://www.ipcc-nggip.iges.or.jp/public/2006gl/}
}

@techreport{mckinsey2009mac,
  title={Pathways to a Low-Carbon Economy: Version 2 of the Global Greenhouse Gas Abatement Cost Curve},
  author={{McKinsey \& Company}},
  institution={McKinsey},
  year={2009}
}
```

---

*Bu doküman, TR-ZERO projesi kapsamında hazırlanmıştır.*
*Son güncelleme: 28 Aralık 2025*
