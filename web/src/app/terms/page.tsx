"use client";

import React from "react";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import { Scale, CheckCircle, AlertTriangle } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

export default function TermsPage() {
  const { t } = useLanguage();

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
            {t("terms.title")}
          </h1>
          <p className="text-zinc-500 text-sm font-medium">
            {t("terms.lastUpdated")}
          </p>
        </div>

        {/* Terms Box (Glassmorphic Container) */}
        <div className="relative overflow-hidden rounded-2xl bg-zinc-900/40 backdrop-blur-md border border-zinc-800/80 px-8 py-10 sm:p-12 shadow-2xl flex flex-col gap-10">
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
          <div className="absolute -left-32 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />

          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {t("terms.sec1Title")}
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              {t("terms.sec1Desc")}
            </p>
          </section>

          {/* Highlights Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800/60 flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">{t("terms.highlight1Title")}</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">{t("terms.highlight1Desc")}</p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800/60 flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">{t("terms.highlight2Title")}</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">{t("terms.highlight2Desc")}</p>
              </div>
            </div>
          </div>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {t("terms.sec2Title")}
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              {t("terms.sec2Desc")}
            </p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400 text-sm sm:text-base">
              <li>
                {t("terms.sec2Bullet1")}
              </li>
              <li>
                {t("terms.sec2Bullet2")}
              </li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {t("terms.sec3Title")}
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              {t("terms.sec3Desc")}
            </p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400 text-sm sm:text-base">
              <li>
                <strong className="text-zinc-200">{t("terms.sec3Bullet1Title")}</strong> {t("terms.sec3Bullet1Desc")}
              </li>
              <li>
                <strong className="text-zinc-200">{t("terms.sec3Bullet2Title")}</strong> {t("terms.sec3Bullet2Desc")}
              </li>
              <li>
                <strong className="text-zinc-200">{t("terms.sec3Bullet3Title")}</strong> {t("terms.sec3Bullet3Desc")}
              </li>
            </ul>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {t("terms.sec4Title")}
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              {t("terms.sec4Desc")}
            </p>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {t("terms.sec5Title")}
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              {t("terms.sec5Desc")}
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {t("terms.sec6Title")}
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed sm:text-base">
              {t("terms.sec6Desc")}
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <SiteFooter />
    </div>
  );
}
