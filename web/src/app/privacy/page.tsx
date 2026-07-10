"use client";

import React from "react";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import { Shield, Lock, EyeOff, Server, Globe } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="relative min-h-screen flex flex-col justify-between overflow-hidden">
      {/* Background Top Glow Effect */}
      <div className="top-glow-glow" />

      {/* Header */}
      <SiteHeader />

      {/* Main Content */}
      <main className="relative z-10 flex-1 max-w-4xl w-full mx-auto px-6 py-12 md:py-16">
        {/* Title Header */}
        <div className="flex flex-col items-center text-center space-y-4 mb-12">
          <div className="relative flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-950/50 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
            <Shield className="w-7 h-7 text-[#00F076]" />
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 to-transparent" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Gizlilik Politikası
          </h1>
          <p className="text-zinc-500 text-sm font-medium">
            Son Güncelleme: 10 Temmuz 2026
          </p>
        </div>

        {/* Policy Box (Glassmorphic Container) */}
        <div className="relative overflow-hidden rounded-2xl bg-zinc-900/40 backdrop-blur-md border border-zinc-800/80 px-8 py-10 sm:p-12 shadow-2xl flex flex-col gap-10">
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
          <div className="absolute -left-32 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />

          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">1.</span> Giriş
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              EcoTrace ekibi olarak, gizliliğinize büyük önem veriyoruz. EcoTrace, Python tabanlı projelerinizin CPU ve RAM enerji tüketimini ölçerek karbon ayak izinizi hesaplayan açık kaynaklı bir kütüphanedir. Bu politika, web sitemiz ve kütüphanemiz aracılığıyla işlenen veya işlenmeyen veriler hakkında sizi bilgilendirmeyi amaçlar.
            </p>
          </section>

          {/* Highlights Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800/60 flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
                <Lock className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">Tamamen Yerel</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">Tüm hesaplamalar ve ölçümler kendi bilgisayarınızda veya sunucunuzda gerçekleşir.</p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800/60 flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
                <EyeOff className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">Sıfır Telemetri</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">Kodlarınız, değişkenleriniz veya enerji metrikleriniz asla dışarıya sızdırılmaz.</p>
              </div>
            </div>
          </div>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">2.</span> Sıfır Veri Toplama Politikası (Zero Telemetry)
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Kütüphanemizin mimarisi, gizliliği varsayılan olarak koruyacak şekilde tasarlanmıştır:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400 text-sm sm:text-base">
              <li>
                <strong className="text-zinc-200">Yerel Çalışma:</strong> EcoTrace kütüphanesi çalıştırıldığında, donanım kaynaklarınızın (CPU, RAM) anlık güç tüketim verilerini işletim sistemi API'leri üzerinden yerel olarak sorgular.
              </li>
              <li>
                <strong className="text-zinc-200">Veri Gönderimi Yoktur:</strong> Bu veriler hiçbir şekilde bizim tarafımızdan işletilen bir bulut sunucusuna veya üçüncü şahıs analiz araçlarına iletilmez.
              </li>
              <li>
                <strong className="text-zinc-200">Kullanıcı Kontrolü:</strong> Üretilen raporlar (JSON veya HTML formatındaki emisyon çıktıları) tamamen sizin denetiminiz altındadır ve yerel diskinizde depolanır.
              </li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">3.</span> Web Sitesi Ziyaretçi Verileri
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Web sitemizi ziyaret ettiğinizde gizliliğiniz korunmaya devam eder:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400 text-sm sm:text-base">
              <li>
                <strong className="text-zinc-200">Anonim Analitik:</strong> Web portalımızda kullanıcıların ilgisini çeken bölümleri anlamak amacıyla yalnızca çerez içermeyen, IP adreslerini maskeleyen ve kişisel bilgi barındırmayan anonim trafik analizi yapılabilir.
              </li>
              <li>
                <strong className="text-zinc-200">Yerel Tarayıcı Depolama:</strong> Karbon bütçesi hesaplama aracımızda girdiğiniz değerler, sayfayı yenilediğinizde kaybolmaması adına sadece tarayıcınızın <code className="text-emerald-400 font-mono text-xs">localStorage</code> özelliğinde yerel olarak tutulabilir. Sunucularımıza gönderilmez.
              </li>
            </ul>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">4.</span> Üçüncü Taraf Bağlantıları
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Portalımız GitHub, PyPI (Python Package Index) ve ReadTheDocs gibi platformlara bağlantılar içerebilir. Bu platformlar kendilerine ait gizlilik ve kullanım sözleşmelerine tabidir. İlgili bağlantılara tıkladığınızda o servislerin veri politikalarını incelemenizi öneririz.
            </p>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">5.</span> Açık Kaynak Şeffaflığı
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              EcoTrace projesinin şeffaflığı bizim en büyük güvencemizdir. Kodlarımızın hiçbir gizli izleme veya veri toplama mekanizması içermediğini doğrulamak için dilediğiniz zaman GitHub üzerindeki açık kaynak kodlarımızı denetleyebilirsiniz.
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">6.</span> İletişim
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Bu gizlilik politikası ile ilgili herhangi bir sorunuz, öneriniz veya endişeniz olması durumunda lütfen resmi GitHub depomuz üzerinden bir issue açarak bizimle iletişime geçmekten çekinmeyin.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <SiteFooter />
    </div>
  );
}
