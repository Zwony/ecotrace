"use client";

import React, { useState } from "react";
import CarbonCalculator from "@/components/CarbonCalculator";
import FeaturesComparison from "@/components/FeaturesComparison";
import SiteFooter from "@/components/SiteFooter";
import Image from "next/image";
import {
  Copy,
  Check,
  Terminal,
  ArrowRight,
  BookOpen,
  Leaf
} from "lucide-react";

export default function Home() {
  const [copied, setCopied] = useState(false);
  const command = "pip install ecotrace";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Kopyalama başarısız:", err);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-between overflow-hidden">
      {/* Background Top Glow Effect */}
      <div className="top-glow-glow" />

      {/* Header / Navbar */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 h-20 flex items-center justify-between border-b border-emerald-950/20">
        <div className="flex items-center gap-3">
          {/* Custom Bio-mimesis Logo Icon */}
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-950/50 border border-emerald-500/30 overflow-hidden shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <Leaf className="w-5 h-5 text-[#00F076]" />
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 to-transparent" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white font-sans">
            Ecotrace
          </span>
        </div>

        {/* Desktop Menu */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
          <a href="#features" className="hover:text-[#00F076] transition-colors">
            Özellikler
          </a>
          <a href="https://ecotrace.readthedocs.io/en/latest/" className="hover:text-[#00F076] transition-colors">
            Dokümantasyon
          </a>
        </nav>

        {/* CTA Button */}
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/Zwony/ecotrace"
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
              <path d="M9 18c-4.51 2-5-2-7-2" />
            </svg>
          </a>

          <button>
            <a href="https://pypi.org/project/ecotrace/"
              id="nav-get-started"
              className="relative overflow-hidden px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-500 text-black hover:bg-[#00F076] transition-all duration-300 shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_25px_rgba(0,240,118,0.4)]"
            >
              Başlayın
            </a>
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex-1 flex items-center max-w-7xl w-full mx-auto px-6 py-12 md:py-20 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center w-full">

          {/* Left Column: Content */}
          <div className="lg:col-span-7 flex flex-col items-start text-left space-y-8">

            {/* Version Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-xs font-medium text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F076] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00F076]"></span>
              </span>
              v3.0 Hyper-Efficiency Engine Aktif
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] text-white">
              Yüksek Hassasiyetli <br className="hidden sm:inline" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-[#00F076] to-emerald-500 drop-shadow-[0_0_30px_rgba(0,240,118,0.2)]">
                Enerji ve Emisyon
              </span> <br />
              Enstrümantasyonu
            </h1>

            {/* Subtitle */}
            <p className="text-zinc-400 text-base sm:text-lg max-w-xl leading-relaxed">
              Granüler karbon ayak izi ölçümü için hafif bir Python kütüphanesi. Sıfır konfigürasyon ile projelerinizin dijital ayak izini takip edin.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
              <a
                id="hero-get-started"
                href="#calculator"
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold bg-emerald-500 text-black hover:bg-[#00F076] transition-all duration-300 shadow-[0_4px_20px_rgba(16,185,129,0.3)] hover:shadow-[0_4px_25px_rgba(0,240,118,0.5)] group cursor-pointer"
              >
                Başla
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </a>

              <a
                id="hero-view-docs"
                href="https://ecotrace.readthedocs.io/en/latest/"
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold bg-white/5 text-zinc-300 hover:text-white hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 transition-all duration-300 backdrop-blur-sm cursor-pointer"
              >
                <BookOpen className="w-4 h-4 text-emerald-400" />
                Dokümantasyonu Görüntüle
              </a>
            </div>

            {/* Copyable Pip Command */}
            <div className="w-full sm:w-auto">
              <div
                onClick={handleCopy}
                className="group flex items-center justify-between gap-4 pl-4 pr-3 py-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-emerald-500/30 cursor-pointer transition-all duration-300 backdrop-blur-sm shadow-inner"
              >
                <div className="flex items-center gap-2.5 font-mono text-sm text-zinc-300 select-all">
                  <Terminal className="w-4 h-4 text-emerald-500" />
                  <span>{command}</span>
                </div>
                <div className="relative">
                  <button
                    id="copy-pip-command"
                    className={`p-1.5 rounded-md ${copied ? "bg-emerald-500/20 text-[#00F076]" : "bg-zinc-800 text-zinc-400 hover:text-white"} transition-colors`}
                  >
                    {copied ? <Check className="w-4 h-4 copy-pulse" /> : <Copy className="w-4 h-4" />}
                  </button>

                  {/* Tooltip Alert */}
                  <div className={`absolute -top-11 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-black text-xs font-semibold rounded-md shadow-lg transition-all duration-200 pointer-events-none whitespace-nowrap ${copied ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1"}`}>
                    Kopyalandı!
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Terminal Visualization */}
          <div className="lg:col-span-5 relative flex justify-center w-full">
            {/* Background Glow behind terminal */}
            <div className="absolute inset-0 bg-emerald-500/10 blur-[80px] rounded-full -z-10 transform scale-75 lg:scale-100" />

            {/* macOS Futuristic Terminal */}
            <div className="glass-terminal rounded-2xl w-full max-w-lg overflow-hidden flex flex-col relative z-10 transition-transform duration-500 hover:scale-[1.02]">
              {/* Terminal Window Header */}
              <div className="h-11 px-4 flex items-center justify-between border-b border-white/5 bg-zinc-900/40">
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded-full bg-[#FF5F56] border border-[#E0443E]/20" />
                  <div className="w-3.5 h-3.5 rounded-full bg-[#FFBD2E] border border-[#DEA123]/20" />
                  <div className="w-3.5 h-3.5 rounded-full bg-[#27C93F] border border-[#1AAB29]/20" />
                </div>
                <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-500 tracking-wider">
                  <Terminal className="w-3 h-3 text-emerald-600" />
                  <span>ecotrace ~ bash</span>
                </div>
                <div className="w-12" /> {/* spacer to balance */}
              </div>

              {/* Terminal Content Box */}
              <div className="relative bg-zinc-950 aspect-[4/3] w-full overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/demo.gif"
                  alt="EcoTrace Demo"
                  className="w-full h-full object-cover"
                />

                {/* Cybernetic overlay */}
                <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-500/30 text-[9px] font-mono text-[#00F076] uppercase tracking-widest pointer-events-none">
                  Live Preview
                </div>
              </div>
            </div>
          </div>

        </div>
      </main>

      {/* Carbon Budget Calculator Section */}
      <div className="relative z-10">
        <div className="w-full max-w-7xl mx-auto px-6">
          <div className="h-px bg-gradient-to-r from-transparent via-emerald-900/40 to-transparent" />
        </div>
        <CarbonCalculator />
        <div className="w-full max-w-7xl mx-auto px-6">
          <div className="h-px bg-gradient-to-r from-transparent via-emerald-900/40 to-transparent" />
        </div>
      </div>

      {/* Features & Comparison Section */}
      <div className="relative z-10">
        <FeaturesComparison />
      </div>

      {/* Site Footer */}
      <SiteFooter />
    </div>
  );
}
