"use client";

import React, { useState } from "react";
import CarbonCalculator from "@/components/CarbonCalculator";
import FeaturesComparison from "@/components/FeaturesComparison";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";
import { motion, Variants } from "framer-motion";
import Image from "next/image";
import {
  Copy,
  Check,
  Terminal,
  ArrowRight,
  BookOpen,
  Zap,
  Globe,
  Scale,
  GitMerge,
} from "lucide-react";

export default function Home() {
  const [copied, setCopied] = useState(false);
  const command = "pip install ecotrace";

  // Framer Motion variants for premium, smooth fade-up stagger
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15, // Sırayla gelme (stagger)
        delayChildren: 2.2,    // Başlangıçta splash screen bitene kadar bekle
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 30 }, // Aşağıdan yukarı süzülme (fade-up)
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "tween",
        ease: "easeOut", // Çok akıcı, oyuncaklı olmayan (spring yok) ciddi geçiş
        duration: 0.8,
      },
    },
  };

  const terminalVariants: Variants = {
    hidden: { opacity: 0, x: 20 },
    show: {
      opacity: 1,
      x: 0,
      transition: {
        type: "tween",
        ease: "easeOut",
        duration: 1,
        delay: 2.7,
      },
    },
  };

  // Sürekli yavaş yukarı-aşağı yüzme animasyonu (Floating Chips için)
  const floatVariantsA = {
    animate: {
      y: [0, -10, 0],
      transition: { duration: 3, repeat: Infinity, ease: "easeInOut" as const },
    },
  };
  const floatVariantsB = {
    animate: {
      y: [0, 8, 0],
      transition: { duration: 3.4, repeat: Infinity, ease: "easeInOut" as const, delay: 0.6 },
    },
  };

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
      {/* Çok katmanlı yeşil ortam ışıkları — Eco hissiyatı */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        {/* Ana üst glow */}
        <div className="top-glow-glow" />
        {/* Sol orta yeşil orb */}
        <div className="absolute top-1/3 -left-32 w-[400px] h-[400px] bg-emerald-500/8 blur-[120px] rounded-full" />
        {/* Sağ alt yeşil orb */}
        <div className="absolute bottom-0 right-0 w-[350px] h-[350px] bg-emerald-400/6 blur-[100px] rounded-full" />
        {/* Merkez çok soluk halo */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[500px] bg-emerald-500/4 blur-[160px] rounded-full" />
      </div>

      {/* Header / Navbar */}
      <SiteHeader />

      {/* Hero Section */}
      <main className="relative z-10 flex-1 flex items-center max-w-7xl w-full mx-auto px-6 py-12 md:py-20 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center w-full">

          {/* Left Column: Content */}
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="lg:col-span-7 flex flex-col items-start text-left space-y-8"
          >

            {/* Version Badge */}
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-xs font-medium text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F076] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00F076]"></span>
              </span>
              v1.4.0 Feature Release
            </motion.div>

            {/* Headline */}
            <motion.h1 variants={itemVariants} className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] text-white">
              Yüksek Hassasiyetli <br className="hidden sm:inline" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-[#00F076] to-emerald-500 drop-shadow-[0_0_30px_rgba(0,240,118,0.2)]">
                Enerji ve Emisyon
              </span> <br />
              Enstrümantasyonu
            </motion.h1>

            {/* Subtitle */}
            <motion.p variants={itemVariants} className="text-zinc-400 text-base sm:text-lg max-w-xl leading-relaxed">
              Granüler karbon ayak izi ölçümü için hafif bir Python kütüphanesi. Sıfır konfigürasyon ile projelerinizin dijital ayak izini takip edin.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
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
            </motion.div>

            {/* Copyable Pip Command */}
            <motion.div variants={itemVariants} className="w-full sm:w-auto">
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
            </motion.div>

            {/* Social Proof Row */}
            <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <span className="flex items-center gap-1.5 text-xs text-zinc-500">
                <Scale className="w-3.5 h-3.5 text-zinc-600" />
                MIT Lisanslı
              </span>
              <span className="w-px h-3 bg-zinc-800" />
              <span className="flex items-center gap-1.5 text-xs text-zinc-500">
                <svg className="w-3.5 h-3.5 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 0v20M2 12h20"/>
                </svg>
                Python 3.9+
              </span>
              <span className="w-px h-3 bg-zinc-800" />
              <span className="flex items-center gap-1.5 text-xs text-zinc-500">
                <Globe className="w-3.5 h-3.5 text-zinc-600" />
                50+ Global Bölge
              </span>
            </motion.div>

          </motion.div>

          {/* Right Column: Terminal Visualization */}
          <motion.div 
            variants={terminalVariants}
            initial="hidden"
            animate="show"
            className="lg:col-span-5 relative flex justify-center w-full"
          >
            {/* Ambient glow — derin, geniş, bulanık zümrüt ortam ışığı */}
            <div className="absolute inset-0 -z-10">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-500/20 rounded-full blur-3xl opacity-20" />
            </div>

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

            {/* Floating Chip A — Sol alt köşe (50ms Örnekleme) */}
            <motion.div
              animate={floatVariantsA.animate}
              className="absolute -bottom-4 -left-4 z-20 flex items-center gap-2 px-3 py-2 rounded-xl bg-zinc-900/80 border border-zinc-700/60 backdrop-blur-sm shadow-[0_8px_32px_rgba(0,0,0,0.4)] pointer-events-none"
            >
              <Zap className="w-3.5 h-3.5 text-[#00F076]" />
              <span className="text-[11px] font-semibold text-zinc-200 whitespace-nowrap">50ms Örnekleme</span>
            </motion.div>

            {/* Floating Chip B — Sağ üst köşe (CI/CD Uyumlu) */}
            <motion.div
              animate={floatVariantsB.animate}
              className="absolute -top-4 -right-4 z-20 flex items-center gap-2 px-3 py-2 rounded-xl bg-zinc-900/80 border border-emerald-500/20 backdrop-blur-sm shadow-[0_8px_32px_rgba(0,0,0,0.4)] pointer-events-none"
            >
              <GitMerge className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[11px] font-semibold text-zinc-200 whitespace-nowrap">CI/CD Uyumlu</span>
            </motion.div>

          </motion.div>

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
