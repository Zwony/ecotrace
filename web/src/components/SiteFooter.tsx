"use client";

import React from "react";
import { ExternalLink, BookOpen, Code2, Scale, GitMerge, Heart } from "lucide-react";
import { motion, Variants } from "framer-motion";

/* ────────────────────────────────────────────────────────────── */
/*  Inline GitHub SVG                                            */
/* ────────────────────────────────────────────────────────────── */
function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Footer link columns                                          */
/* ────────────────────────────────────────────────────────────── */
const FOOTER_COLS = [
  {
    heading: "Kaynaklar",
    links: [
      { label: "Dokümanlar", href: "https://ecotrace.readthedocs.io/en/latest/", icon: BookOpen, iconCustom: null },
      { label: "Mimari", href: "https://ecotrace.readthedocs.io/en/latest/ARCHITECTURE/", icon: null, iconCustom: null },
      { label: "API Referansı", href: "https://ecotrace.readthedocs.io/en/latest/api/", icon: null, iconCustom: null },
    ],
  },
  {
    heading: "Topluluk",
    links: [
      { label: "GitHub", href: "https://github.com/Zwony/ecotrace", icon: null, iconCustom: GitHubIcon },
      { label: "VS Code Eklentisi", href: "https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor", icon: Code2, iconCustom: null },
    ],
  },
  {
    heading: "Yasal",
    links: [
      { label: "MIT Lisansı", href: "https://github.com/Zwony/ecotrace/blob/main/LICENSE", icon: Scale, iconCustom: null },
      { label: "Gizlilik", href: "/privacy", icon: null, iconCustom: null },
      { label: "Şartlar", href: "/terms", icon: null, iconCustom: null },
    ],
  },
];

/* ────────────────────────────────────────────────────────────── */
/*  Main Footer Component                                        */
/* ────────────────────────────────────────────────────────────── */
export default function SiteFooter() {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
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
    <footer className="relative z-10 w-full">

      {/* ── CTA Banner ──────────────────────────────────────────── */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.1 }}
        className="w-full max-w-7xl mx-auto px-6 pb-16"
      >
        <motion.div variants={itemVariants} className="relative overflow-hidden rounded-2xl bg-zinc-900 border border-zinc-800/60 px-8 sm:px-12 py-10 flex flex-col gap-8">
          {/* Ambient glows */}
          <div className="absolute -left-24 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/8 blur-[80px] rounded-full pointer-events-none" />
          <div className="absolute -right-24 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/6 blur-[80px] rounded-full pointer-events-none" />
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />

          {/* Headline */}
          <p className="relative text-xl sm:text-2xl font-extrabold text-white tracking-tight leading-snug max-w-xl">
            Karbon bütçelerinizi hemen bugün{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
              CI/CD pipeline
            </span>
            &apos;ınızda zorunlu kılın.
          </p>

          {/* Two action buttons side-by-side */}
          <div className="relative flex flex-col sm:flex-row gap-4">
            {/* Contribute */}
            <a
              id="cta-contribute"
              href="https://github.com/Zwony/ecotrace/blob/main/CONTRIBUTING.MD"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-semibold text-sm bg-emerald-500 text-black hover:bg-[#00F076] transition-all duration-300 shadow-[0_4px_20px_rgba(16,185,129,0.25)] hover:shadow-[0_4px_30px_rgba(0,240,118,0.45)] group"
            >
              <GitMerge className="w-4 h-4 flex-shrink-0" />
              Projeye Katkı Sağlayın
              <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-100 transition-opacity" />
            </a>

            {/* Sponsor */}
            <a
              id="cta-sponsor"
              href="https://github.com/sponsors/Zwony"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-semibold text-sm bg-white/5 text-zinc-200 hover:text-white hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 transition-all duration-300 backdrop-blur-sm group"
            >
              <Heart className="w-4 h-4 flex-shrink-0 text-pink-400 group-hover:text-pink-300 transition-colors" />
              Sponsor Olun
              <ExternalLink className="w-3 h-3 opacity-50 group-hover:opacity-80 transition-opacity" />
            </a>
          </div>
        </motion.div>
      </motion.div>

      {/* ── Links grid + signature ───────────────────────────────── */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.1 }}
        className="w-full max-w-7xl mx-auto px-6 border-t border-zinc-800/50"
      >

        {/* 3-column link grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-10 py-12">
          {FOOTER_COLS.map((col) => (
            <motion.div variants={itemVariants} key={col.heading} className="flex flex-col gap-4">
              <h4 className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                {col.heading}
              </h4>
              <ul className="flex flex-col gap-2.5">
                {col.links.map((link) => {
                  const Icon = link.icon;
                  const IconCustom = link.iconCustom;
                  return (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        target={link.href.startsWith("http") ? "_blank" : undefined}
                        rel={link.href.startsWith("http") ? "noopener noreferrer" : undefined}
                        className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-[#00F076] transition-colors duration-200 group"
                      >
                        {Icon && (
                          <Icon className="w-3.5 h-3.5 text-zinc-600 group-hover:text-emerald-500 transition-colors duration-200 flex-shrink-0" />
                        )}
                        {IconCustom && (
                          <IconCustom className="w-3.5 h-3.5 text-zinc-600 group-hover:text-emerald-500 transition-colors duration-200 flex-shrink-0" />
                        )}
                        {link.label}
                      </a>
                    </li>
                  );
                })}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Bottom signature row */}
        <motion.div variants={itemVariants} className="py-6 border-t border-zinc-800/40 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-zinc-600 font-medium">
            © 2026 EcoTrace.{" "}
            <a
              href="https://github.com/Zwony/ecotrace/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-400 transition-colors duration-200"
            >
              MIT License
            </a>
            .
          </p>
          <p className="text-xs font-medium">
            <span className="text-zinc-600">Tasarlayan &amp; Geliştiren: </span>
            <a
              href="https://github.com/CanKStar0"
              target="_blank"
              rel="noopener noreferrer"
              className="text-transparent bg-clip-text bg-gradient-to-r from-zinc-300 to-zinc-400 font-semibold tracking-wide hover:from-emerald-300 hover:to-[#00F076] transition-all duration-300"
            >
              Canpolat Kaya
            </a>
          </p>
        </motion.div>
      </motion.div>
    </footer>
  );
}
