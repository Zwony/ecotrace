"use client";

import React from "react";
import { motion, Variants } from "framer-motion";
import { useLanguage } from "@/context/LanguageContext";
import { Cpu, Activity } from "lucide-react";

/* ────────────────────────────────────────────────────────────── */
/*  Inline OS SVG Icons                                           */
/* ────────────────────────────────────────────────────────────── */
function WindowsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M0 3.449L9.75 2.1v9.45H0V3.449zM0 12.45h9.75v9.45L0 20.551v-8.1zM10.8 1.95L24 0v11.55H10.8V1.95zM10.8 12.45H24v11.55l-13.2-1.95v-9.6z" />
    </svg>
  );
}

function AppleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 4.17c.66-.81 1.11-1.93.99-3.06-1 .04-2.22.67-2.94 1.5-.63.73-1.18 1.87-1.03 2.97 1.12.09 2.27-.56 2.98-1.41z" />
    </svg>
  );
}

function LinuxIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 .007c-2.414 0-4.664.912-6.31 2.562C4.053 4.21 3.141 6.46 3.141 8.874c0 .878.136 1.728.388 2.536-1.048.91-1.975 2.016-2.736 3.276a1.5 1.5 0 00-.094 1.48c.245.498.75.82 1.306.82h1.832c.57-.01 1.123-.238 1.53-.637.75-.736 1.637-1.3 2.613-1.66A6.29 6.29 0 0012 15.75c1.436 0 2.768-.48 3.83-1.282.977.36 1.865.924 2.614 1.66.408.4.96.627 1.53.637h1.832c.556 0 1.06-.322 1.306-.82a1.5 1.5 0 00-.094-1.48c-.76-1.26-1.688-2.366-2.736-3.276.252-.808.388-1.658.388-2.536 0-2.414-.912-4.664-2.562-6.305C16.664.92 14.414.007 12 .007zm0 2.2c1.788 0 3.456.685 4.67 1.913 1.228 1.228 1.913 2.896 1.913 4.68 0 .6-.076 1.185-.224 1.745-.37-.234-.783-.403-1.21-.502a5.545 5.545 0 00-.91-.186 6.3 6.3 0 00-8.478 0 5.545 5.545 0 00-.91.186c-.427.1-.84.268-1.21.502a6.38 6.38 0 01-.224-1.745c0-1.784.685-3.452 1.913-4.68A6.52 6.52 0 0112 2.207zm-2.07 4.25c-.53 0-.96.43-.96.96v.12c0 .53.43.96.96.96h.12c.53 0 .96-.43.96-.96v-.12c0-.53-.43-.96-.96-.96h-.12zm4.14 0c-.53 0-.96.43-.96.96v.12c0 .53.43.96.96.96h.12c.53 0 .96-.43.96-.96v-.12c0-.53-.43-.96-.96-.96h-.12zm-3.29 4.3c.784.444 1.674.683 2.583.683.91 0 1.8-.239 2.583-.683a.4.4 0 01.397.683 5.92 5.92 0 01-3.143 1.077c-1.127 0-2.2-.382-3.143-1.077a.4.4 0 01.123-.683.4.4 0 01.274 0z" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Main CompatibilityInfo Component                              */
/* ────────────────────────────────────────────────────────────── */
export default function CompatibilityInfo() {
  const { t } = useLanguage();

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 35 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "tween",
        ease: "easeOut",
        duration: 0.8,
      },
    },
  };

  return (
    <section className="relative z-10 w-full max-w-7xl mx-auto px-6 py-20">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.2 }}
        className="flex flex-col gap-14"
      >
        {/* Section Header */}
        <motion.div variants={itemVariants} className="flex flex-col items-center text-center gap-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-xs font-medium text-emerald-400 uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00F076] animate-pulse" />
            {t("compatibility.titleBadge")}
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            {t("compatibility.titlePart1")}{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
              {t("compatibility.titleGlow")}
            </span>
          </h2>
          <p className="text-zinc-400 max-w-2xl text-base leading-relaxed">
            {t("compatibility.desc")}
          </p>
        </motion.div>

        {/* Info Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Card 1: Lightweight & Cross-Platform */}
          <motion.div
            variants={itemVariants}
            className="group relative flex flex-col gap-6 p-8 sm:p-10 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 hover:border-emerald-500/30 backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(0,0,0,0.5)] overflow-hidden"
          >
            {/* Top decorative glow */}
            <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />
            <div className="absolute -left-20 -top-20 w-40 h-40 bg-emerald-500/5 blur-[60px] rounded-full pointer-events-none" />

            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/50 border border-emerald-500/25 flex items-center justify-center text-[#00F076] shadow-[0_0_15px_rgba(0,240,118,0.15)] group-hover:border-emerald-500/50 group-hover:shadow-[0_0_20px_rgba(0,240,118,0.3)] transition-all duration-300">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                {t("compatibility.cardPlatformTitle")}
              </h3>
            </div>

            <p className="text-zinc-400 text-sm sm:text-base leading-relaxed">
              {t("compatibility.cardPlatformDesc")}
            </p>

            {/* Platform Badges Row */}
            <div className="mt-4 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-950/60 border border-zinc-800/80 text-zinc-300 group-hover:border-emerald-500/30 group-hover:text-white transition-all duration-300">
                <WindowsIcon className="w-4 h-4 text-zinc-400 group-hover:text-emerald-400 transition-colors" />
                <span className="text-xs font-mono font-medium">Windows</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-950/60 border border-zinc-800/80 text-zinc-300 group-hover:border-emerald-500/30 group-hover:text-white transition-all duration-300">
                <LinuxIcon className="w-4 h-4 text-zinc-400 group-hover:text-emerald-400 transition-colors" />
                <span className="text-xs font-mono font-medium">Linux</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-950/60 border border-zinc-800/80 text-zinc-300 group-hover:border-emerald-500/30 group-hover:text-white transition-all duration-300">
                <AppleIcon className="w-4 h-4 text-zinc-400 group-hover:text-emerald-400 transition-colors" />
                <span className="text-xs font-mono font-medium">macOS</span>
              </div>
            </div>
          </motion.div>

          {/* Card 2: Continuous Precision */}
          <motion.div
            variants={itemVariants}
            className="group relative flex flex-col gap-6 p-8 sm:p-10 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 hover:border-emerald-500/30 backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(0,0,0,0.5)] overflow-hidden"
          >
            {/* Top decorative glow */}
            <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />
            <div className="absolute -right-20 -bottom-20 w-40 h-40 bg-emerald-500/5 blur-[60px] rounded-full pointer-events-none" />

            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/50 border border-emerald-500/25 flex items-center justify-center text-[#00F076] shadow-[0_0_15px_rgba(0,240,118,0.15)] group-hover:border-emerald-500/50 group-hover:shadow-[0_0_20px_rgba(0,240,118,0.3)] transition-all duration-300">
                <Activity className="w-6 h-6 animate-pulse" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                {t("compatibility.cardSamplingTitle")}
              </h3>
            </div>

            <p className="text-zinc-400 text-sm sm:text-base leading-relaxed">
              {t("compatibility.cardSamplingDesc")}
            </p>

            {/* Animated Waveform Visual */}
            <div className="mt-2 relative w-full h-16 bg-zinc-950/55 border border-zinc-850 rounded-xl overflow-hidden flex items-center justify-center px-4">
              <svg className="w-full h-full text-emerald-500/30" viewBox="0 0 400 80" fill="none">
                {/* Static background grid lines */}
                <line x1="0" y1="20" x2="400" y2="20" stroke="rgba(255,255,255,0.02)" strokeWidth="1" />
                <line x1="0" y1="40" x2="400" y2="40" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
                <line x1="0" y1="60" x2="400" y2="60" stroke="rgba(255,255,255,0.02)" strokeWidth="1" />
                
                {/* Dynamic animated high-frequency sampling wave */}
                <motion.path
                  animate={{
                    d: [
                      "M 0 40 Q 20 20, 40 40 T 80 40 T 120 40 T 160 40 T 200 40 T 240 40 T 280 40 T 320 40 T 360 40 T 400 40",
                      "M 0 40 Q 20 60, 40 40 T 80 40 T 120 20 T 160 60 T 200 30 T 240 50 T 280 20 T 320 60 T 360 30 T 400 40",
                      "M 0 40 Q 20 30, 40 40 T 80 50 T 120 60 T 160 20 T 200 50 T 240 30 T 280 60 T 320 20 T 360 50 T 400 40",
                      "M 0 40 Q 20 20, 40 40 T 80 40 T 120 40 T 160 40 T 200 40 T 240 40 T 280 40 T 320 40 T 360 40 T 400 40",
                    ],
                  }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  stroke="#00F076"
                  strokeWidth="2"
                  strokeLinecap="round"
                  className="drop-shadow-[0_0_8px_rgba(0,240,118,0.5)]"
                />
              </svg>
              {/* Status Badge */}
              <div className="absolute top-2 right-3 flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/30 text-[9px] font-mono text-[#00F076] uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00F076] animate-ping" />
                <span>50ms Sampling</span>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}
