"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type Language = "tr" | "en";

interface TranslationDictionary {
  header: {
    story: string;
    features: string;
    docs: string;
    getStarted: string;
  };
  footer: {
    resources: string;
    community: string;
    legal: string;
    docs: string;
    architecture: string;
    apiRef: string;
    vsCodeExt: string;
    privacy: string;
    terms: string;
    mitLicense: string;
    ctaText: string;
    contribute: string;
    sponsor: string;
    designedBy: string;
  };
  home: {
    vBadge: string;
    headlinePart1: string;
    headlineGlow: string;
    headlinePart2: string;
    subtitle: string;
    btnStart: string;
    btnDocs: string;
    copied: string;
    licence: string;
    python: string;
    regions: string;
    sampling: string;
    cicd: string;
    livePreview: string;
  };
  calculator: {
    titleBadge: string;
    titlePart1: string;
    titleGlow: string;
    desc: string;
    panelLabel: string;
    runtimeLabel: string;
    efficiency: string;
    lessCO2: string;
    baseline: string;
    vsPython: string;
    monthlyTraffic: string;
    trafficUnit: string;
    avgExecTime: string;
    estimatesNote: string;
    estMonthlyCO2: string;
    maxThreshold: string;
    thresholdUnit: string;
    treesOffset: string;
    offsetUnit: string;
    moreTrees: string;
    activeRuntime: string;
  };
  features: {
    badge: string;
    titlePart1: string;
    titleGlow: string;
    desc: string;
    feat1Title: string;
    feat1Desc: string;
    feat2Title: string;
    feat2Desc: string;
    feat3Title: string;
    feat3Desc: string;
    whyTitle: string;
    whyGlow: string;
    colFeature: string;
    colEco: string;
    colCode: string;
    colCarbon: string;
    rowFreq: string;
    rowFreqValEco: string;
    rowFreqValCode: string;
    rowFreqValCarbon: string;
    rowIso: string;
    rowIsoValEco: string;
    rowIsoValCode: string;
    rowIsoValCarbon: string;
    rowLimit: string;
    rowGate: string;
    footnote: string;
    whyDesc: string;
    newBadge: string;
  };
  story: {
    badge: string;
    heroHeadlinePart1: string;
    heroHeadlineGlow: string;
    heroHeadlinePart2: string;
    heroSubtitle: string;
    factBadge: string;
    factTitlePart1: string;
    factTitleGlow: string;
    factDesc: string;
    factStat1Val: string;
    factStat1Lbl: string;
    factStat2Val: string;
    factStat2Lbl: string;
    factImgLabel: string;
    missionBadge: string;
    missionTitlePart1: string;
    missionTitleGlow: string;
    missionDesc: string;
    missionTag1: string;
    missionTag2: string;
    missionTag3: string;
    missionTag4: string;
    ctaTitlePart1: string;
    ctaTitleGlow: string;
    ctaDesc: string;
    ctaBtnInstall: string;
    ctaBtnGit: string;
    ctaFooter: string;
  };
  privacy: {
    title: string;
    lastUpdated: string;
    sec1Title: string;
    sec1Desc: string;
    highlight1Title: string;
    highlight1Desc: string;
    highlight2Title: string;
    highlight2Desc: string;
    sec2Title: string;
    sec2Desc: string;
    sec2Bullet1Title: string;
    sec2Bullet1Desc: string;
    sec2Bullet2Title: string;
    sec2Bullet2Desc: string;
    sec2Bullet3Title: string;
    sec2Bullet3Desc: string;
    sec3Title: string;
    sec3Desc: string;
    sec3Bullet1Title: string;
    sec3Bullet1Desc: string;
    sec3Bullet2Title: string;
    sec3Bullet2Desc: string;
    sec4Title: string;
    sec4Desc: string;
    sec5Title: string;
    sec5Desc: string;
    sec6Title: string;
    sec6Desc: string;
  };
  terms: {
    title: string;
    lastUpdated: string;
    sec1Title: string;
    sec1Desc: string;
    highlight1Title: string;
    highlight1Desc: string;
    highlight2Title: string;
    highlight2Desc: string;
    sec2Title: string;
    sec2Desc: string;
    sec2Bullet1: string;
    sec2Bullet2: string;
    sec3Title: string;
    sec3Desc: string;
    sec3Bullet1Title: string;
    sec3Bullet1Desc: string;
    sec3Bullet2Title: string;
    sec3Bullet2Desc: string;
    sec3Bullet3Title: string;
    sec3Bullet3Desc: string;
    sec4Title: string;
    sec4Desc: string;
    sec5Title: string;
    sec5Desc: string;
    sec6Title: string;
    sec6Desc: string;
  };
}

const translations: Record<Language, TranslationDictionary> = {
  en: {
    header: {
      story: "Our Story",
      features: "Features",
      docs: "Documentation",
      getStarted: "Get Started",
    },
    footer: {
      resources: "Resources",
      community: "Community",
      legal: "Legal",
      docs: "Docs",
      architecture: "Architecture",
      apiRef: "API Reference",
      vsCodeExt: "VS Code Extension",
      privacy: "Privacy",
      terms: "Terms",
      mitLicense: "MIT License",
      ctaText: "Enforce your carbon budgets in your CI/CD pipeline today.",
      contribute: "Contribute to Project",
      sponsor: "Become a Sponsor",
      designedBy: "Designed & Developed by",
    },
    home: {
      vBadge: "v1.4.0 Feature Release",
      headlinePart1: "High-Precision",
      headlineGlow: "Energy and Emission",
      headlinePart2: "Instrumentation",
      subtitle: "A lightweight Python library for granular carbon footprint tracking. Track the digital footprint of your projects with zero configuration.",
      btnStart: "Get Started",
      btnDocs: "View Documentation",
      copied: "Copied!",
      licence: "MIT Licensed",
      python: "Python 3.9+",
      regions: "50+ Global Regions",
      sampling: "50ms Sampling",
      cicd: "CI/CD Compatible",
      livePreview: "Live Preview",
    },
    calculator: {
      titleBadge: "Live Calculator",
      titlePart1: "Interactive Carbon",
      titleGlow: "Budget Calculator",
      desc: "Enter your project parameters and calculate your estimated carbon footprint in real-time.",
      panelLabel: "Project Parameters",
      runtimeLabel: "Language / Runtime",
      efficiency: "Efficiency",
      lessCO2: "less CO2",
      baseline: "baseline",
      vsPython: " vs Python",
      monthlyTraffic: "Monthly Traffic (Requests)",
      trafficUnit: "reqs/month",
      avgExecTime: "Average Execution Time",
      estimatesNote: "Estimates are based on an average grid carbon intensity of 350 gCO₂/kWh and verified manufacturer TDP measurements.",
      estMonthlyCO2: "Estimated Monthly CO₂",
      maxThreshold: "Max threshold",
      thresholdUnit: "kg/month",
      treesOffset: "Trees Required to Offset",
      offsetUnit: "trees/year",
      moreTrees: "more",
      activeRuntime: "Active Runtime",
    },
    features: {
      badge: "Key Features",
      titlePart1: "Developer-First",
      titleGlow: "Measurement Tools",
      desc: "Designed for production-ready projects — no setup, no extra dependencies.",
      feat1Title: "Zero-Code Profiling",
      feat1Desc: "Measure your Python scripts without changing code or setting up background services.",
      feat2Title: "Carbon Budget Mode",
      feat2Desc: "Set a strict carbon limit for your projects. Get alerted automatically if the limit is exceeded.",
      feat3Title: "CI/CD Gate Integration",
      feat3Desc: "Automatically audit your carbon budget within your GitHub Actions pipeline and prevent carbon-heavy code from being merged.",
      whyTitle: "Why",
      whyGlow: "EcoTrace?",
      whyDesc: "Real-time, process-scoped isolation and budget management compared to open-source alternatives.",
      colFeature: "Feature",
      colEco: "EcoTrace",
      colCode: "CodeCarbon",
      colCarbon: "CarbonTracker",
      rowFreq: "Sampling Frequency",
      rowFreqValEco: "50ms",
      rowFreqValCode: "15s",
      rowFreqValCarbon: "Per Epoch",
      rowIso: "Isolation",
      rowIsoValEco: "Process-scoped",
      rowIsoValCode: "System-wide",
      rowIsoValCarbon: "System-wide",
      rowLimit: "Budget Limiting",
      rowGate: "CI/CD Gate",
      footnote: "* Data reflects baseline configurations and architectural differences as of documented versions.",
      newBadge: "New",
    },
    story: {
      badge: "Our Story",
      heroHeadlinePart1: "There Is No Cloud.",
      heroHeadlineGlow: "Only Real Energy",
      heroHeadlinePart2: "Consumed.",
      heroSubtitle: "Every line of code we write, every loop running on a server has a physical weight. The software world is assumed innocent because it is invisible; but the reality is much darker.",
      factBadge: "Critical Fact",
      factTitlePart1: "A Threat Greater Than the",
      factTitleGlow: "Aviation Sector",
      factDesc: "Global data centers and software infrastructures now generate more carbon emissions (CO2) than the entire aviation industry. The internet devours 416 Terawatt-hours of electricity every year, most of which comes from fossil fuels. Every unoptimized line of code is not just a server cost, but digital waste dumped into the environment.",
      factStat1Val: "416 TWh",
      factStat1Lbl: "Annual internet energy consumption",
      factStat2Val: "4%+",
      factStat2Lbl: "Software share of global CO₂",
      factImgLabel: " Global data center — 24/7 active",
      missionBadge: "Mission",
      missionTitlePart1: "EcoTrace's Mission:",
      missionTitleGlow: "Measuring the Invisible",
      missionDesc: "Developers don't aim to harm the environment; they just lack the right metrics. We built EcoTrace for exactly this: to make carbon measurement as standard, effortless, and transparent as unit testing. The future of software must not only be fast, but green.",
      missionTag1: "Zero Configuration",
      missionTag2: "CI/CD Ready",
      missionTag3: "Process-Scoped",
      missionTag4: "Open Source",
      ctaTitlePart1: "Be a part of the",
      ctaTitleGlow: "change.",
      ctaDesc: "Standardize software carbon measurement by adding a single line of code to your project. A greener digital future is possible.",
      ctaBtnInstall: "Install Now",
      ctaBtnGit: "Inspect on GitHub",
      ctaFooter: "MIT Licensed · Fully Open Source · Zero Data Collection",
    },
    privacy: {
      title: "Privacy Policy",
      lastUpdated: "Last Updated: July 10, 2026",
      sec1Title: "Introduction",
      sec1Desc: "At EcoTrace, we deeply value your privacy. EcoTrace is an open-source library that measures CPU and RAM energy consumption to calculate your project's carbon footprint. This policy explains what information is processed (or not processed) by our website and library.",
      highlight1Title: "Fully Local",
      highlight1Desc: "All calculations and measurements take place locally on your own computer or server.",
      highlight2Title: "Zero Telemetry",
      highlight2Desc: "Your code, variables, and energy metrics are never sent outside your environment.",
      sec2Title: "Zero Telemetry Policy",
      sec2Desc: "Our library is designed to protect your privacy by default:",
      sec2Bullet1Title: "Local Execution:",
      sec2Bullet1Desc: "When executed, the EcoTrace library queries your hardware (CPU, RAM) power draw locally via operating system APIs.",
      sec2Bullet2Title: "No Data Transmission:",
      sec2Bullet2Desc: "We do not transmit this data to any cloud servers or third-party analytical tools operated by us.",
      sec2Bullet3Title: "User Control:",
      sec2Bullet3Desc: "All reports (JSON or HTML formats) remain strictly on your local disk under your control.",
      sec3Title: "Website Visitor Data",
      sec3Desc: "When visiting our website, your privacy is fully protected:",
      sec3Bullet1Title: "Anonymous Analytics:",
      sec3Bullet1Desc: "We only conduct cookie-free, anonymized traffic audits (masking IP addresses) to analyze section popularities without compiling personal data.",
      sec3Bullet2Title: "Local Browser Storage:",
      sec3Bullet2Desc: "Input values on our carbon calculator are saved in your browser's localStorage for state persistence. They are never sent to our servers.",
      sec4Title: "Third-Party Links",
      sec4Desc: "Our portal may contain links to external sites like GitHub, PyPI, and ReadTheDocs. These platforms operate under their own privacy agreements. We encourage you to review their policies upon clicking.",
      sec5Title: "Open Source Transparency",
      sec5Desc: "EcoTrace is built on trust. You can audit our codebase on GitHub at any time to verify that no tracking or collection mechanisms exist.",
      sec6Title: "Contact Us",
      sec6Desc: "If you have any questions, suggestions, or concerns about this policy, please feel free to reach out by opening an issue on our official GitHub repository.",
    },
    terms: {
      title: "Terms of Use",
      lastUpdated: "Last Updated: July 10, 2026",
      sec1Title: "Acceptance of Terms",
      sec1Desc: "By using this website or the EcoTrace open-source library, you accept and agree to follow these Terms of Use. If you do not agree to these terms, you must discontinue using our software and website.",
      highlight1Title: "MIT Licensed",
      highlight1Desc: "You are free to modify, distribute, and integrate the code into commercial projects.",
      highlight2Title: "Limitation of Liability",
      highlight2Desc: "All calculations are estimates. No commercial warranties or guarantees of absolute precision are provided.",
      sec2Title: "License and Open Source Permissibility",
      sec2Desc: "The EcoTrace library and its assets are licensed under the MIT License:",
      sec2Bullet1: "You may use, copy, modify, and distribute this software for commercial and non-commercial purposes without fee.",
      sec2Bullet2: "The copyright and permission notices must be included in all copies or substantial portions of the software.",
      sec3Title: "Responsibilities and Limits of Use",
      sec3Desc: "EcoTrace estimates carbon and energy footprints for software projects. However:",
      sec3Bullet1Title: "Estimated Outputs:",
      sec3Bullet1Desc: "Calculated emissions vary depending on your hardware, OS, and dataset. Results are strictly informational estimates.",
      sec3Bullet2Title: "No Warranties:",
      sec3Bullet2Desc: "The software is provided 'as is'. We offer no warranties, express or implied, regarding bug-free or uninterrupted operation.",
      sec3Bullet3Title: "Limitation of Liability:",
      sec3Bullet3Desc: "The EcoTrace team and contributors will not be liable for any damages (including data loss, profit loss, or system downtime) arising from using this software.",
      sec4Title: "Intellectual Property",
      sec4Desc: "The EcoTrace brand, logos, and website layouts belong to the creators. Other than open-source assets covered by the MIT license, designs may not be copied or used to imply official endorsement without permission.",
      sec5Title: "Modifications and Updates",
      sec5Desc: "We reserve the right to amend these terms at any time. Changes take effect immediately upon publication on this page. Your continued use of the website or library confirms your agreement.",
      sec6Title: "Contact Us",
      sec6Desc: "For any questions or licensing inquiries regarding these terms, please open an issue or reach out through our official GitHub repository.",
    },
  },
  tr: {
    header: {
      story: "Hikayemiz",
      features: "Özellikler",
      docs: "Dokümantasyon",
      getStarted: "Başlayın",
    },
    footer: {
      resources: "Kaynaklar",
      community: "Topluluk",
      legal: "Yasal",
      docs: "Dokümanlar",
      architecture: "Mimari",
      apiRef: "API Referansı",
      vsCodeExt: "VS Code Eklentisi",
      privacy: "Gizlilik",
      terms: "Şartlar",
      mitLicense: "MIT Lisansı",
      ctaText: "Karbon bütçelerinizi hemen bugün CI/CD pipeline'ınızda zorunlu kılın.",
      contribute: "Projeye Katkı Sağlayın",
      sponsor: "Sponsor Olun",
      designedBy: "Tasarlayan & Geliştiren",
    },
    home: {
      vBadge: "Ecotrace",
      headlinePart1: "Yüksek Hassasiyetli",
      headlineGlow: "Enerji ve Emisyon",
      headlinePart2: "Enstrümantasyonu",
      subtitle: "Granüler karbon ayak izi ölçümü için hafif bir Python kütüphanesi. Sıfır konfigürasyon ile projelerinizin dijital ayak izini takip edin.",
      btnStart: "Başla",
      btnDocs: "Dokümantasyonu Görüntüle",
      copied: "Kopyalandı!",
      licence: "MIT Lisanslı",
      python: "Python 3.9+",
      regions: "50+ Global Bölge",
      sampling: "50ms Örnekleme",
      cicd: "CI/CD Uyumlu",
      livePreview: "Live Preview",
    },
    calculator: {
      titleBadge: "Canlı Hesaplayıcı",
      titlePart1: "İnteraktif Karbon",
      titleGlow: "Bütçe Hesaplayıcı",
      desc: "Proje parametrelerinizi girin ve gerçek zamanlı olarak tahmini karbon ayak izinizi hesaplayın.",
      panelLabel: "Proje Parametreleri",
      runtimeLabel: "Kullanılan Dil / Runtime",
      efficiency: "Verimlilik",
      lessCO2: "daha az CO2",
      baseline: "baz çizgi",
      vsPython: " vs Python",
      monthlyTraffic: "Aylık Trafik (İstek)",
      trafficUnit: "istek/ay",
      avgExecTime: "Ortalama Çalışma Süresi",
      estimatesNote: "Tahminler, ortalama 350 gCO₂/kWh şebeke karbon yoğunluğu ve doğrulama yapılmış üretici TDP ölçümlerine dayanmaktadır.",
      estMonthlyCO2: "Tahmini Aylık CO₂",
      maxThreshold: "Maks. eşik",
      thresholdUnit: "kg/ay",
      treesOffset: "Ofset İçin Gereken Ağaç",
      offsetUnit: "ağaç/yıl",
      moreTrees: "daha",
      activeRuntime: "Aktif Runtime",
    },
    features: {
      badge: "Temel Özellikler",
      titlePart1: "Geliştirici Öncelikli",
      titleGlow: "Ölçüm Araçları",
      desc: "Üretime hazır projelerde çalışmak için tasarlandı — kurulum yok, ek bağımlılık yok.",
      feat1Title: "Zero-Code Profiling",
      feat1Desc: "Hiçbir kod değiştirmeden veya arka plan servisi kurmadan Python betiklerinizi ölçün.",
      feat2Title: "Karbon Bütçesi Modu",
      feat2Desc: "Projelerinize kesin bir karbon limiti koyun. Limit aşılırsa sistem sizi otomatik uyarsın.",
      feat3Title: "CI/CD Gate Entegrasyonu",
      feat3Desc: "Karbon bütçenizi GitHub Actions pipeline'ınız içinde otomatik olarak denetleyin ve karbon yoğun kodların merge edilmesini engelleyin.",
      whyTitle: "Neden",
      whyGlow: "EcoTrace?",
      whyDesc: "Açık kaynaklı alternatiflere kıyasla gerçek zamanlı, süreç bazlı izolasyon ve bütçe yönetimi.",
      colFeature: "Özellik",
      colEco: "EcoTrace",
      colCode: "CodeCarbon",
      colCarbon: "CarbonTracker",
      rowFreq: "Örnekleme Sıklığı",
      rowFreqValEco: "50ms",
      rowFreqValCode: "15s",
      rowFreqValCarbon: "Epoch Başına",
      rowIso: "İzolasyon",
      rowIsoValEco: "Process-scoped",
      rowIsoValCode: "Sistem Geneli",
      rowIsoValCarbon: "Sistem Geneli",
      rowLimit: "Bütçe Sınırlandırma",
      rowGate: "CI/CD Gate",
      footnote: "* Veriler, belgelenen sürümler itibarıyla temel konfigürasyonları ve mimari farkları yansıtmaktadır.",
      newBadge: "Yeni",
    },
    story: {
      badge: "Hikayemiz",
      heroHeadlinePart1: "Bulut Diye Bir Şey Yok.",
      heroHeadlineGlow: "Sadece Tüketilen",
      heroHeadlinePart2: "Gerçek Enerji Var.",
      heroSubtitle: "Yazdığımız her satır kodun, sunucularda çalışan her döngünün fiziksel bir ağırlığı var. Yazılım dünyası görünmez olduğu için masum sanılıyor; ancak gerçekler çok daha karanlık.",
      factBadge: "Kritik Gerçek",
      factTitlePart1: "Havacılık Sektöründen",
      factTitleGlow: "Daha Büyük Bir Tehdit",
      factDesc: "Küresel veri merkezleri ve yazılım altyapıları, bugün tüm havacılık sektöründen daha fazla karbon emisyonu (CO2) üretiyor. İnternet her yıl 416 Terawatt-saat elektrik yutuyor ve bunun büyük kısmı fosil yakıtlardan elde ediliyor. Optimizasyon yapılmayan her kod, sadece sunucu masrafı değil, çevreye atılan dijital bir çöptür.",
      factStat1Val: "416 TWh",
      factStat1Lbl: "Yıllık internet enerji tüketimi",
      factStat2Val: "%4+",
      factStat2Lbl: "Global CO₂'nin yazılım payı",
      factImgLabel: " Global veri merkezi — 7/24 aktif",
      missionBadge: "Misyon",
      missionTitlePart1: "EcoTrace'in Misyonu:",
      missionTitleGlow: "Görünmezi Ölçmek",
      missionDesc: "Geliştiricilerin çevreye zarar vermek gibi bir amacı yok, sadece ellerinde doğru metrikler yok. EcoTrace'i tam olarak bunun için inşa ettik. Karbon ölçümünü birim testi (unit test) kadar standart, zahmetsiz ve şeffaf hale getirmek. Yazılımın geleceği sadece hızlı değil, aynı zamanda yeşil olmak zorunda.",
      missionTag1: "Sıfır Konfigürasyon",
      missionTag2: "CI/CD Ready",
      missionTag3: "Process-Scoped",
      missionTag4: "Açık Kaynak",
      ctaTitlePart1: "Sen de değişimin",
      ctaTitleGlow: "bir parçası ol.",
      ctaDesc: "Projenize tek satır kod ekleyerek yazılım karbon ölçümünü standart hale getirin. Daha yeşil bir dijital gelecek mümkün.",
      ctaBtnInstall: "Hemen Kur",
      ctaBtnGit: "GitHub'da İncele",
      ctaFooter: "MIT Lisanslı · Tamamen Açık Kaynak · 0 Veri Toplama",
    },
    privacy: {
      title: "Gizlilik Politikası",
      lastUpdated: "Son Güncelleme: 10 Temmuz 2026",
      sec1Title: "1. Giriş",
      sec1Desc: "EcoTrace ekibi olarak, gizliliğinize büyük önem veriyoruz. EcoTrace, Python tabanlı projelerinizin CPU ve RAM enerji tüketimini ölçerek karbon ayak izinizi hesaplayan açık kaynaklı bir kütüphanedir. Bu politika, web sitemiz ve kütüphanemiz aracılığıyla işlenen veya işlenmeyen veriler hakkında sizi bilgilendirmeyi amaçlar.",
      highlight1Title: "Tamamen Yerel",
      highlight1Desc: "Tüm hesaplamalar ve ölçümler kendi bilgisayarınızda veya sunucunuzda gerçekleşir.",
      highlight2Title: "Sıfır Telemetri",
      highlight2Desc: "Kodlarınız, değişkenleriniz veya enerji metrikleriniz asla dışarıya sızdırılmaz.",
      sec2Title: "2. Sıfır Veri Toplama Politikası (Zero Telemetry)",
      sec2Desc: "Kütüphanemizin mimarisi, gizliliği varsayılan olarak koruyacak şekilde tasarlanmıştır:",
      sec2Bullet1Title: "Yerel Çalışma:",
      sec2Bullet1Desc: "EcoTrace kütüphanesi çalıştırıldığında, donanım kaynaklarınızın (CPU, RAM) anlık güç tüketim verilerini işletim sistemi API'leri üzerinden yerel olarak sorgular.",
      sec2Bullet2Title: "Veri Gönderimi Yoktur:",
      sec2Bullet2Desc: "Bu veriler hiçbir şekilde bizim tarafımızdan işletilen bir bulut sunucusuna veya üçüncü şahıs analiz araçlarına iletilmez.",
      sec2Bullet3Title: "Kullanıcı Kontrolü:",
      sec2Bullet3Desc: "Üretilen raporlar (JSON veya HTML formatındaki emisyon çıktıları) tamamen sizin denetiminiz altındadır ve yerel diskinizde depolanır.",
      sec3Title: "3. Web Sitesi Ziyaretçi Verileri",
      sec3Desc: "Web sitemizi ziyaret ettiğinizde gizliliğiniz korunmaya devam eder:",
      sec3Bullet1Title: "Anonim Analitik:",
      sec3Bullet1Desc: "Web portalımızda kullanıcıların ilgisini çeken bölümleri anlamak amacıyla yalnızca çerez içermeyen, IP adreslerini maskeleyen ve kişisel bilgi barındırmayan anonim trafik analizi yapılabilir.",
      sec3Bullet2Title: "Yerel Tarayıcı Depolama:",
      sec3Bullet2Desc: "Karbon bütçesi hesaplama aracımızda girdiğiniz değerler, sayfayı yenilediğinizde kaybolmaması adına sadece tarayıcınızın localStorage özelliğinde yerel olarak tutulabilir. Sunucularımıza gönderilmez.",
      sec4Title: "4. Üçüncü Taraf Bağlantıları",
      sec4Desc: "Portalımız GitHub, PyPI (Python Package Index) ve ReadTheDocs gibi platformlara bağlantılar içerebilir. Bu platformlar kendilerine ait gizlilik ve kullanım sözleşmelerine tabidir. İlgili bağlantılara tıkladığınızda o servislerin veri politikalarını incelemenizi öneririz.",
      sec5Title: "5. Açık Kaynak Şeffaflığı",
      sec5Desc: "EcoTrace projesinin şeffaflığı bizim en büyük güvencemizdir. Kodlarımızın hiçbir gizli izleme veya veri toplama mekanizması içermediğini doğrulamak için dilediğiniz zaman GitHub üzerindeki açık kaynak kodlarımızı denetleyebilirsiniz.",
      sec6Title: "6. İletişim",
      sec6Desc: "Bu gizlilik politikası ile ilgili herhangi bir sorunuz, öneriniz veya endişeniz olması durumunda lütfen resmi GitHub depomuz üzerinden bir issue açarak bizimle iletişime geçmekten çekinmeyin.",
    },
    terms: {
      title: "Kullanım Şartları",
      lastUpdated: "Son Güncelleme: 10 Temmuz 2026",
      sec1Title: "1. Kabul Edilme",
      sec1Desc: "Bu web sitesini veya EcoTrace açık kaynaklı Python kütüphanesini kullanarak, burada belirtilen tüm kullanım koşullarını kabul etmiş bulunmaktasınız. Şartları kısmen veya tamamen kabul etmiyorsanız, yazılımı veya web sitesini kullanmamalısınız.",
      highlight1Title: "MIT Lisanslı",
      highlight1Desc: "Özgürce modifiye edebilir, dağıtabilir ve ticari projelerinizde kullanabilirsiniz.",
      highlight2Title: "Sorumluluk Sınırı",
      highlight2Desc: "Hesaplamalar tahmini değerlerdir, ticari garantiler veya mutlak doğruluk taahhüt edilmez.",
      sec2Title: "2. Lisans ve Açık Kaynak İzinleri",
      sec2Desc: "EcoTrace Python kütüphanesi ve ilişkili tüm araçlar MIT Lisansı ile lisanslanmıştır. Bu lisans kapsamında:",
      sec2Bullet1: "Yazılımı ticari ve ticari olmayan amaçlarla ücretsiz olarak kullanabilir, kopyalayabilir, değiştirebilir ve dağıtabilirsiniz.",
      sec2Bullet2: "Telif hakkı bildirimi ve izin bildirimi, yazılımın tüm kopyalarına veya önemli bölümlerine dahil edilmelidir.",
      sec3Title: "3. Kullanım Sorumlulukları ve Sınırları",
      sec3Desc: "EcoTrace, yazılım projelerinizin karbon emisyonlarını ve enerji tüketimlerini tahmin etmek için tasarlanmıştır. Ancak:",
      sec3Bullet1Title: "Tahmini Değerler:",
      sec3Bullet1Desc: "Hesaplanan değerler donanım mimarinize, işletim sisteminize ve kullanılan veri setlerine bağlı olarak değişkenlik gösterebilir. Sunulan tüm sonuçlar bilgilendirme amaçlı 'tahmini' değerlerdir.",
      sec3Bullet2Title: "Garanti Yoktur:",
      sec3Bullet2Desc: "Yazılım, 'olduğu gibi' (as is) esasıyla sunulur. Hata içermeme, kesintisiz çalışma veya belirli bir amaca uygunluk konusunda açık veya zımni hiçbir garanti verilmez.",
      sec3Bullet3Title: "Yükümlülük Sınırı:",
      sec3Bullet3Desc: "EcoTrace ekibi veya katkıda bulunanlar; yazılımın kullanımından veya kullanılamamasından kaynaklanan hiçbir zarardan (veri kaybı, kâr kaybı veya sistem kesintileri dahil) sorumlu tutulamaz.",
      sec4Title: "4. Fikri Mülkiyet",
      sec4Desc: "EcoTrace markası, logoları, web sitesi tasarımı ve içeriği EcoTrace projesine ve geliştiricilerine aittir. MIT lisanslı kaynak kodlar haricindeki marka ve tasarımlar izinsiz kopyalanamaz veya EcoTrace ekibinin resmi temsilcisi gibi kullanılamaz.",
      sec5Title: "5. Değişiklikler ve Güncellemeler",
      sec5Desc: "Bu kullanım şartlarını zaman zaman güncelleme hakkını saklı tutarız. Güncellemeler bu sayfada yayınlandığı andan itibaren geçerlilik kazanır. Web sitemizi veya kütüphanemizi kullanmaya devam etmeniz, güncellenen şartları kabul ettiğiniz anlamına gelir.",
      sec6Title: "6. İletişim",
      sec6Desc: "Kullanım şartları hakkında her türlü soru, bildirim veya lisans sorgularınız için GitHub üzerindeki resmi kanallarımız veya issue şablonlarımız aracılığıyla bize ulaşabilirsiniz.",
    },
  },
};

interface LanguageContextProps {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (keyPath: string) => string;
}

const LanguageContext = createContext<LanguageContextProps | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>("en");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const savedLang = localStorage.getItem("language") as Language;
    if (savedLang === "tr" || savedLang === "en") {
      setLanguageState(savedLang);
    } else {
      // Default to "en" as requested by user
      setLanguageState("en");
    }
    setMounted(true);
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem("language", lang);
    if (typeof document !== "undefined") {
      document.documentElement.lang = lang;
    }
  };

  useEffect(() => {
    if (mounted && typeof document !== "undefined") {
      document.documentElement.lang = language;
    }
  }, [language, mounted]);

  const t = (keyPath: string): string => {
    const keys = keyPath.split(".");
    let current: any = translations[language];

    for (const key of keys) {
      if (current && typeof current === "object" && key in current) {
        current = current[key];
      } else {
        // Fallback to English if key doesn't exist in active language
        let fallback: any = translations["en"];
        for (const fKey of keys) {
          if (fallback && typeof fallback === "object" && fKey in fallback) {
            fallback = fallback[fKey];
          } else {
            return keyPath;
          }
        }
        return typeof fallback === "string" ? fallback : keyPath;
      }
    }

    return typeof current === "string" ? current : keyPath;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
