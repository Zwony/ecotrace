# 🚀 EcoTrace v0.5.2 — The Unified Monitoring Update

**Release Date:** 28.03.2026 (The Definitive 0.5.x Release)  
**Version:** v0.5.2  
**Focus:** Unified CPU+GPU Monitoring & Core-Aware Performance Insights

---

## 🌟 What's New

### 🛰️ Unified Multi-Resource Monitoring
We've unified the core tracking logic. The standard `@track` decorator and `measure()` API now automatically detect and monitor your **GPU** alongside the CPU. 
- **Aggregated Carbon**: Rapor artık CPU ve GPU emisyonlarını toplayarak tek bir "Toplam Karbon Ayak İzi" sunuyor.
- **Zero Configuration**: Eğer sistemde GPU varsa, EcoTrace bunu otomatik algılar ve izlemeye başlar.

### 📊 Automated Visual Reporting
Raporlama motoru artık hiçbir parametre gerektirmeden tam otomatik çalışıyor.
- **Auto-Snapshoting**: `generate_pdf_report()` çağrıldığında o ana kadar toplanan tüm CPU ve GPU örnekleri grafik olarak rapora eklenir.
- **High-Res Visuals**: Yüksek çözünürlüklü kullanım grafikleri artık her raporda standart olarak sunuluyor.

### 🧠 Smart "Core-Aware" Insights
20 çekirdekli i7-13700H gibi güçlü işlemcilerde oluşan yanlış "Düşük CPU" (Low CPU) uyarıları giderildi.
- **Dynamic Thresholding**: Analiz motoru artık çekirdek sayısına göre dinamik eşikler hesaplıyor.
- **Realistic Advice**: "Single-Thread Intensive" gibi daha teknik ve gerçekçi performans tavsiyeleri eklendi.

---

## 🛠️ Internal Improvements
- **Context Manager Nesting**: CPU ve GPU monitörleri artık birbirini bloklamadan iç içe çalışabiliyor.
- **Unified Accumulation**: Tüm izleme yöntemleri (`track`, `track_block`, `measure`) ortak bir karbon toplama mantığına çekildi.
- **Wait Stability**: Async izlemelerdekiTrailing sample kayıpları giderildi.

---

## 🚀 How to Upgrade
```bash
pip install --upgrade ecotrace
```

*Crafted for maximum precision, minimum effort, and a carbon-aware future.*
