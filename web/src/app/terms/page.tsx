"use client";

import React from "react";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import { Scale, FileText, CheckCircle, AlertTriangle, RefreshCw } from "lucide-react";

export default function TermsPage() {
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
            <Scale className="w-7 h-7 text-[#00F076]" />
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 to-transparent" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Kullanım Şartları
          </h1>
          <p className="text-zinc-500 text-sm font-medium">
            Son Güncelleme: 10 Temmuz 2026
          </p>
        </div>

        {/* Terms Box (Glassmorphic Container) */}
        <div className="relative overflow-hidden rounded-2xl bg-zinc-900/40 backdrop-blur-md border border-zinc-800/80 px-8 py-10 sm:p-12 shadow-2xl flex flex-col gap-10">
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
          <div className="absolute -left-32 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />

          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">1.</span> Kabul Edilme
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Bu web sitesini veya EcoTrace açık kaynaklı Python kütüphanesini kullanarak, burada belirtilen tüm kullanım koşullarını kabul etmiş bulunmaktasınız. Şartları kısmen veya tamamen kabul etmiyorsanız, yazılımı veya web sitesini kullanmamalısınız.
            </p>
          </section>

          {/* Highlights Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800/60 flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">MIT Lisanslı</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">Özgürce modifiye edebilir, dağıtabilir ve ticari projelerinizde kullanabilirsiniz.</p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800/60 flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">Sorumluluk Sınırı</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">Hesaplamalar tahmini değerlerdir, ticari garantiler veya mutlak doğruluk taahhüt edilmez.</p>
              </div>
            </div>
          </div>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">2.</span> Lisans ve Açık Kaynak İzinleri
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              EcoTrace Python kütüphanesi ve ilişkili tüm araçlar <strong className="text-zinc-200">MIT Lisansı</strong> ile lisanslanmıştır. Bu lisans kapsamında:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400 text-sm sm:text-base">
              <li>
                Yazılımı ticari ve ticari olmayan amaçlarla ücretsiz olarak kullanabilir, kopyalayabilir, değiştirebilir ve dağıtabilirsiniz.
              </li>
              <li>
                Telif hakkı bildirimi ve izin bildirimi, yazılımın tüm kopyalarına veya önemli bölümlerine dahil edilmelidir.
              </li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">3.</span> Kullanım Sorumlulukları ve Sınırları
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              EcoTrace, yazılım projelerinizin karbon emisyonlarını ve enerji tüketimlerini tahmin etmek için tasarlanmıştır. Ancak:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400 text-sm sm:text-base">
              <li>
                <strong className="text-zinc-200">Tahmini Değerler:</strong> Hesaplanan değerler donanım mimarinize, işletim sisteminize ve kullanılan veri setlerine bağlı olarak değişkenlik gösterebilir. Sunulan tüm sonuçlar bilgilendirme amaçlı "tahmini" değerlerdir.
              </li>
              <li>
                <strong className="text-zinc-200">Garanti Yoktur:</strong> Yazılım, "olduğu gibi" (as is) esasıyla sunulur. Hata içermeme, kesintisiz çalışma veya belirli bir amaca uygunluk konusunda açık veya zımni hiçbir garanti verilmez.
              </li>
              <li>
                <strong className="text-zinc-200">Yükümlülük Sınırı:</strong> EcoTrace ekibi veya katkıda bulunanlar; yazılımın kullanımından veya kullanılamamasından kaynaklanan hiçbir zarardan (veri kaybı, kâr kaybı veya sistem kesintileri dahil) sorumlu tutulamaz.
              </li>
            </ul>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">4.</span> Fikri Mülkiyet
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              EcoTrace markası, logoları, web sitesi tasarımı ve içeriği EcoTrace projesine ve geliştiricilerine aittir. MIT lisanslı kaynak kodlar haricindeki marka ve tasarımlar izinsiz kopyalanamaz veya EcoTrace ekibinin resmi temsilcisi gibi kullanılamaz.
            </p>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">5.</span> Değişiklikler ve Güncellemeler
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Bu kullanım şartlarını zaman zaman güncelleme hakkını saklı tutarız. Güncellemeler bu sayfada yayınlandığı andan itibaren geçerlilik kazanır. Web sitemizi veya kütüphanemizi kullanmaya devam etmeniz, güncellenen şartları kabul ettiğiniz anlamına gelir.
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-[#00F076]">6.</span> İletişim
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              Kullanım şartları hakkında her türlü soru, bildirim veya lisans sorgularınız için GitHub üzerindeki resmi kanallarımız veya issue şablonlarımız aracılığıyla bize ulaşabilirsiniz.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <SiteFooter />
    </div>
  );
}
