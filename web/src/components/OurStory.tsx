"use client";

import React from "react";
import { motion, Variants } from "framer-motion";
import { ArrowRight } from "lucide-react";

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Animation Variants                                           */
/* ────────────────────────────────────────────────────────────── */
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.18,
      delayChildren: 0.05,
    },
  },
};

const fadeUpVariants: Variants = {
  hidden: { opacity: 0, y: 40 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: "tween",
      ease: "easeOut",
      duration: 0.85,
    },
  },
};

const fadeLeftVariants: Variants = {
  hidden: { opacity: 0, x: -40 },
  show: {
    opacity: 1,
    x: 0,
    transition: { type: "tween", ease: "easeOut", duration: 0.9 },
  },
};

const fadeRightVariants: Variants = {
  hidden: { opacity: 0, x: 40 },
  show: {
    opacity: 1,
    x: 0,
    transition: { type: "tween", ease: "easeOut", duration: 0.9 },
  },
};

/* ────────────────────────────────────────────────────────────── */
/*  Viewport helper                                              */
/* ────────────────────────────────────────────────────────────── */
const vp = { once: true, amount: 0.2 };

/* ────────────────────────────────────────────────────────────── */
/*  Main Component                                               */
/* ────────────────────────────────────────────────────────────── */
export default function OurStory() {
  return (
    <section className="relative w-full overflow-hidden bg-[#050806]">

      {/* ── Ambient background glows ──────────────────────────── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-emerald-500/5 blur-[120px] rounded-full" />
        <div className="absolute top-1/2 -left-40 w-[500px] h-[500px] bg-emerald-500/4 blur-[140px] rounded-full" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-emerald-500/3 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 py-28 flex flex-col gap-32">

        {/* ════════════════════════════════════════════════════════
            BÖLÜM 1 — VURUCU GİRİŞ (Hero Story)
        ════════════════════════════════════════════════════════ */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={vp}
          className="flex flex-col items-center text-center gap-8 max-w-4xl mx-auto"
        >
          {/* Üst badge */}
          <motion.div
            variants={fadeUpVariants}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-950/50 border border-emerald-500/20 text-xs font-semibold text-emerald-400 uppercase tracking-widest"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#00F076]" />
            Hikayemiz
          </motion.div>

          {/* Devasa başlık */}
          <motion.h1
            variants={fadeUpVariants}
            className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold tracking-tight leading-[1.08] text-white"
          >
            Bulut Diye Bir Şey Yok.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-br from-emerald-300 via-[#00F076] to-emerald-600 drop-shadow-[0_0_40px_rgba(0,240,118,0.2)]">
              Sadece Tüketilen
            </span>{" "}
            Gerçek Enerji Var.
          </motion.h1>

          {/* Alt metin */}
          <motion.p
            variants={fadeUpVariants}
            className="text-zinc-400 text-lg sm:text-xl leading-relaxed max-w-2xl"
          >
            Yazdığımız her satır kodun, sunucularda çalışan her döngünün fiziksel
            bir ağırlığı var. Yazılım dünyası görünmez olduğu için masum sanılıyor;
            ancak gerçekler çok daha karanlık.
          </motion.p>

          {/* Süslü ayırıcı çizgi */}
          <motion.div
            variants={fadeUpVariants}
            className="w-24 h-px bg-gradient-to-r from-transparent via-emerald-500/60 to-transparent"
          />
        </motion.div>

        {/* ════════════════════════════════════════════════════════
            BÖLÜM 2 — İKİLİ IZGARA (Z-Pattern)
        ════════════════════════════════════════════════════════ */}

        {/* — Blok 1: Solda Metin, Sağda Görsel — */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">

          {/* Sol: Metin */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="show"
            viewport={vp}
            className="flex flex-col gap-6"
          >
            <motion.div
              variants={fadeLeftVariants}
              className="inline-flex w-fit items-center gap-2 px-3 py-1 rounded-full bg-red-950/30 border border-red-500/20 text-xs font-semibold text-red-400 uppercase tracking-widest"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
              Kritik Gerçek
            </motion.div>

            <motion.h2
              variants={fadeLeftVariants}
              className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight"
            >
              Havacılık Sektöründen{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-400">
                Daha Büyük Bir Tehdit
              </span>
            </motion.h2>

            <motion.p
              variants={fadeLeftVariants}
              className="text-zinc-400 text-base leading-relaxed"
            >
              Küresel veri merkezleri ve yazılım altyapıları, bugün tüm havacılık
              sektöründen daha fazla karbon emisyonu (CO2) üretiyor. İnternet her yıl
              <span className="text-zinc-200 font-semibold"> 416 Terawatt-saat </span>
              elektrik yutuyor ve bunun büyük kısmı fosil yakıtlardan elde ediliyor.
              Optimizasyon yapılmayan her kod, sadece sunucu masrafı değil, çevreye
              atılan dijital bir çöptür.
            </motion.p>

            {/* İstatistik kartları */}
            <motion.div variants={fadeLeftVariants} className="grid grid-cols-2 gap-4 mt-2">
              {[
                { value: "416 TWh", label: "Yıllık internet enerji tüketimi" },
                { value: "%4+", label: "Global CO₂'nin yazılım payı" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="flex flex-col gap-1 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/60 backdrop-blur-sm"
                >
                  <span className="font-mono font-black text-2xl text-white">
                    {stat.value}
                  </span>
                  <span className="text-xs text-zinc-500 leading-snug">{stat.label}</span>
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* Sağ: Görsel */}
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={vp}
            variants={fadeRightVariants}
            className="relative group"
          >
            {/* Glow halkası */}
            <div className="absolute -inset-1 bg-gradient-to-br from-emerald-500/20 via-transparent to-transparent rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="relative rounded-2xl overflow-hidden border border-zinc-800/60 shadow-[0_30px_80px_rgba(0,0,0,0.6)]">
              {/* Görsel */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=1000&auto=format&fit=crop"
                alt="Veri merkezi sunucu rafları"
                className="w-full h-72 sm:h-96 object-cover"
              />
              {/* Zümrüt temayla uyum için karanlık-yeşil overlay */}
              <div className="absolute inset-0 bg-gradient-to-tr from-zinc-950/80 via-emerald-950/20 to-transparent mix-blend-multiply" />
              {/* Alt köşe bilgi kartı */}
              <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-lg bg-zinc-950/80 border border-zinc-700/40 backdrop-blur-sm">
                <p className="text-[11px] font-mono text-zinc-400">
                  📍 Global veri merkezi — 7/24 aktif
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* ── Bölüm arası ince çizgi ── */}
        <div className="w-full h-px bg-gradient-to-r from-transparent via-zinc-800/60 to-transparent" />

        {/* — Blok 2: Solda Görsel, Sağda Metin — */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">

          {/* Sol: Görsel */}
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={vp}
            variants={fadeLeftVariants}
            className="relative group order-2 lg:order-1"
          >
            <div className="absolute -inset-1 bg-gradient-to-br from-emerald-500/20 via-transparent to-transparent rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="relative rounded-2xl overflow-hidden border border-zinc-800/60 shadow-[0_30px_80px_rgba(0,0,0,0.6)]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"
                alt="Doğa ve teknoloji birlikteliği — dünya görünümü"
                className="w-full h-72 sm:h-96 object-cover"
              />
              {/* Yeşil-karanlık filtre overlay */}
              <div className="absolute inset-0 bg-gradient-to-tl from-zinc-950/70 via-emerald-950/30 to-transparent mix-blend-multiply" />
              {/* Köşe etiketi */}
              <div className="absolute top-4 right-4 px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/30 backdrop-blur-sm">
                <p className="text-[11px] font-mono text-[#00F076] font-semibold tracking-wide">
                  🌍 Sürdürülebilir Yazılım
                </p>
              </div>
            </div>
          </motion.div>

          {/* Sağ: Metin */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="show"
            viewport={vp}
            className="flex flex-col gap-6 order-1 lg:order-2"
          >
            <motion.div
              variants={fadeRightVariants}
              className="inline-flex w-fit items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/50 border border-emerald-500/20 text-xs font-semibold text-emerald-400 uppercase tracking-widest"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#00F076]" />
              Misyon
            </motion.div>

            <motion.h2
              variants={fadeRightVariants}
              className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight"
            >
              EcoTrace&apos;in Misyonu:{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
                Görünmezi Ölçmek
              </span>
            </motion.h2>

            <motion.p
              variants={fadeRightVariants}
              className="text-zinc-400 text-base leading-relaxed"
            >
              Geliştiricilerin çevreye zarar vermek gibi bir amacı yok, sadece
              ellerinde doğru metrikler yok.
              <span className="text-zinc-200 font-medium"> EcoTrace</span>&apos;i tam
              olarak bunun için inşa ettik. Karbon ölçümünü
              <span className="text-zinc-200 font-medium"> birim testi (unit test) </span>
              kadar standart, zahmetsiz ve şeffaf hale getirmek. Yazılımın geleceği
              sadece hızlı değil, aynı zamanda
              <span className="text-[#00F076] font-semibold"> yeşil olmak zorunda.</span>
            </motion.p>

            {/* Değer pilleri */}
            <motion.div variants={fadeRightVariants} className="flex flex-wrap gap-2.5">
              {["Sıfır Konfigürasyon", "CI/CD Ready", "Process-Scoped", "Açık Kaynak"].map(
                (tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1.5 text-xs font-semibold rounded-full bg-emerald-950/40 border border-emerald-500/20 text-emerald-300"
                  >
                    {tag}
                  </span>
                )
              )}
            </motion.div>
          </motion.div>
        </div>

        {/* ════════════════════════════════════════════════════════
            BÖLÜM 3 — KAPANIŞ VE AKSİYON (CTA)
        ════════════════════════════════════════════════════════ */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={vp}
          className="flex justify-center"
        >
          <motion.div
            variants={fadeUpVariants}
            className="relative w-full max-w-3xl overflow-hidden rounded-3xl border border-emerald-500/15 bg-zinc-900/60 backdrop-blur-sm px-8 sm:px-16 py-14 flex flex-col items-center text-center gap-8"
          >
            {/* İç arka plan parlamalar */}
            <div className="pointer-events-none absolute inset-0" aria-hidden>
              <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-64 h-32 bg-emerald-500/10 blur-[60px] rounded-full" />
              <div className="absolute -bottom-8 left-1/4 w-48 h-24 bg-emerald-500/6 blur-[50px] rounded-full" />
            </div>
            {/* Üst kenar çizgisi */}
            <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />

            {/* İkon */}
            <motion.div
              variants={fadeUpVariants}
              className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-950/60 border border-emerald-500/25 shadow-[0_0_30px_rgba(16,185,129,0.15)]"
            >
              <svg
                className="w-8 h-8 text-[#00F076]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M7 12.5c1 1.5 2.5 2.5 5 2.5s4-1 5-2.5" />
                <path d="M8.5 9a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z" fill="currentColor" />
                <path d="M15.5 9a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z" fill="currentColor" />
              </svg>
            </motion.div>

            <motion.div variants={fadeUpVariants} className="flex flex-col gap-3">
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
                Sen de değişimin{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
                  bir parçası ol.
                </span>
              </h2>
              <p className="text-zinc-400 text-base leading-relaxed max-w-lg">
                Projenize tek satır kod ekleyerek yazılım karbon ölçümünü standart hale
                getirin. Daha yeşil bir dijital gelecek mümkün.
              </p>
            </motion.div>

            {/* CTA Butonları */}
            <motion.div
              variants={fadeUpVariants}
              className="flex flex-col sm:flex-row items-center gap-4"
            >
              <a
                href="/"
                className="flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl font-semibold text-sm bg-emerald-500 text-black hover:bg-[#00F076] transition-all duration-300 shadow-[0_4px_20px_rgba(16,185,129,0.35)] hover:shadow-[0_4px_28px_rgba(0,240,118,0.55)] group"
              >
                Hemen Kur
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </a>

              <a
                href="https://github.com/Zwony/ecotrace"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl font-semibold text-sm bg-white/5 text-zinc-200 hover:text-white hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 transition-all duration-300 backdrop-blur-sm group"
              >
                <GitHubIcon className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
                GitHub&apos;da İncele
              </a>
            </motion.div>

            {/* Alt imza */}
            <motion.p variants={fadeUpVariants} className="text-xs text-zinc-600">
              MIT Lisanslı · Tamamen Açık Kaynak · 0 Veri Toplama
            </motion.p>
          </motion.div>
        </motion.div>

      </div>
    </section>
  );
}
