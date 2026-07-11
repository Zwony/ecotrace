"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, Variants } from "framer-motion";
import { useLanguage } from "@/context/LanguageContext";

export default function SiteHeader() {
  const { language, setLanguage, t } = useLanguage();

  const headerVariants: Variants = {
    hidden: { opacity: 0, y: -20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "tween",
        ease: "easeOut",
        duration: 0.8,
        delay: 2.2, // Splash ekranından sonra süzülerek gelmesi için gecikme
      },
    },
  };

  return (
    <motion.header 
      variants={headerVariants}
      initial="hidden"
      animate="show"
      className="relative z-10 w-full max-w-7xl mx-auto px-6 h-20 flex items-center justify-between border-b border-emerald-950/20"
    >
      {/* Brand Logo */}
      <Link href="/" className="flex items-center gap-3 group cursor-pointer">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-950/50 border border-emerald-500/30 overflow-hidden shadow-[0_0_15px_rgba(16,185,129,0.15)] group-hover:border-emerald-400/50 transition-colors duration-300">
          <Image src="/logo.png" alt="EcoTrace Logo" width={24} height={24} className="group-hover:scale-110 transition-transform duration-300" />
          <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 to-transparent" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white font-sans group-hover:text-[#00F076] transition-colors duration-300">
          Ecotrace
        </span>
      </Link>

      {/* Desktop Menu */}
      <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
        <Link href="/story" className="hover:text-[#00F076] transition-colors">
          {t("header.story")}
        </Link>
        <Link href="/#features" className="hover:text-[#00F076] transition-colors">
          {t("header.features")}
        </Link>
        <a 
          href="https://ecotrace.readthedocs.io/en/latest/" 
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-[#00F076] transition-colors"
        >
          {t("header.docs")}
        </a>
      </nav>

      {/* CTA Button */}
      <div className="flex items-center gap-4">
        {/* Language Switcher TR/EN */}
        <div className="flex items-center bg-zinc-900/80 border border-zinc-800/80 rounded-lg p-1 relative select-none">
          <button
            onClick={() => setLanguage("tr")}
            className={`relative z-10 w-9 py-1 text-[11px] font-bold tracking-wider rounded-md text-center transition-colors duration-300 cursor-pointer ${
              language === "tr" ? "text-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            TR
          </button>
          <button
            onClick={() => setLanguage("en")}
            className={`relative z-10 w-9 py-1 text-[11px] font-bold tracking-wider rounded-md text-center transition-colors duration-300 cursor-pointer ${
              language === "en" ? "text-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            EN
          </button>
          {/* Sliding background pill */}
          <motion.div
            className="absolute top-1 bottom-1 rounded-md bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)]"
            layout
            transition={{ type: "spring", stiffness: 380, damping: 30 }}
            style={{
              left: language === "tr" ? "4px" : "40px",
              width: "36px",
            }}
          />
        </div>

        <a
          href="https://github.com/Zwony/ecotrace"
          target="_blank"
          rel="noopener noreferrer"
          className="text-zinc-400 hover:text-white transition-colors"
          aria-label="GitHub Repository"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
            <path d="M9 18c-4.51 2-5-2-7-2" />
          </svg>
        </a>

        <a 
          href="https://pypi.org/project/ecotrace/"
          target="_blank"
          rel="noopener noreferrer"
          id="nav-get-started"
          className="relative overflow-hidden px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-500 text-black hover:bg-[#00F076] transition-all duration-300 shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_25px_rgba(0,240,118,0.4)]"
        >
          {t("header.getStarted")}
        </a>
      </div>
    </motion.header>
  );
}
