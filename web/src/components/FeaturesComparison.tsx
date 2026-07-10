"use client";

import React from "react";
import { Terminal, Shield, Check, X, Minus } from "lucide-react";
import { motion, Variants } from "framer-motion";

/* ────────────────────────────────────────────────────────────── */
/*  GitHub SVG Icon (inline, no package dependency)              */
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
/*  Feature Card data                                            */
/* ────────────────────────────────────────────────────────────── */
const FEATURES = [
  {
    id: "zero-code",
    icon: Terminal,
    iconCustom: null,
    title: "Zero-Code Profiling",
    description:
      "Hiçbir kod değiştirmeden veya arka plan servisi kurmadan Python betiklerinizi ölçün.",
    badge: null,
  },
  {
    id: "budget",
    icon: Shield,
    iconCustom: null,
    title: "Carbon Budget Mode",
    description:
      "Projelerinize kesin bir karbon limiti koyun. Limit aşılırsa sistem sizi otomatik uyarsın.",
    badge: "Yeni",
  },
  {
    id: "cicd",
    icon: null,
    iconCustom: GitHubIcon,
    title: "CI/CD Gate Integration",
    description:
      "Karbon bütçenizi GitHub Actions pipeline'ınız içinde otomatik olarak denetleyin ve karbon yoğun kodların merge edilmesini engelleyin.",
    badge: null,
  },
];

/* ────────────────────────────────────────────────────────────── */
/*  Comparison Table data                                         */
/* ────────────────────────────────────────────────────────────── */
const TABLE_COLUMNS = [
  { key: "feature", label: "Feature", isFeature: true },
  { key: "ecotrace", label: "EcoTrace", version: "v1.4.0", highlight: true },
  { key: "codecarbon", label: "CodeCarbon", version: "v3.2.8", highlight: false },
  {
    key: "carbontracker",
    label: "CarbonTracker",
    version: "v2.4.5",
    highlight: false,
  },
];

type CellValue =
  | { type: "text"; value: string; green?: boolean }
  | { type: "check" }
  | { type: "cross" };

interface TableRow {
  feature: string;
  ecotrace: CellValue;
  codecarbon: CellValue;
  carbontracker: CellValue;
}

const TABLE_ROWS: TableRow[] = [
  {
    feature: "Sampling Interval",
    ecotrace: { type: "text", value: "50ms", green: true },
    codecarbon: { type: "text", value: "15s" },
    carbontracker: { type: "text", value: "Per Epoch" },
  },
  {
    feature: "Isolation",
    ecotrace: { type: "text", value: "Process-scoped", green: true },
    codecarbon: { type: "text", value: "System-wide" },
    carbontracker: { type: "text", value: "System-wide" },
  },
  {
    feature: "Budget Enforcement",
    ecotrace: { type: "check" },
    codecarbon: { type: "cross" },
    carbontracker: { type: "cross" },
  },
  {
    feature: "CI/CD Gate",
    ecotrace: { type: "check" },
    codecarbon: { type: "cross" },
    carbontracker: { type: "cross" },
  },
];

function CellDisplay({ cell }: { cell: CellValue }) {
  if (cell.type === "check") {
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/15 border border-emerald-500/30">
        <Check className="w-3.5 h-3.5 text-[#00F076]" />
      </span>
    );
  }
  if (cell.type === "cross") {
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-zinc-800/60 border border-zinc-700/40">
        <X className="w-3.5 h-3.5 text-zinc-600" />
      </span>
    );
  }
  return (
    <span
      className={`font-mono text-sm font-semibold ${
        cell.green ? "text-[#00F076]" : "text-zinc-500"
      }`}
    >
      {cell.value}
    </span>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Main Component                                               */
/* ────────────────────────────────────────────────────────────── */
export default function FeaturesComparison() {
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
    <section id="features" className="relative z-10 w-full max-w-7xl mx-auto px-6 py-24 flex flex-col gap-20">

      {/* ── PART 1: Features Grid ──────────────────────────────── */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.1 }}
        className="flex flex-col gap-10"
      >
        {/* Section header */}
        <motion.div variants={itemVariants} className="flex flex-col items-center text-center gap-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-xs font-medium text-emerald-400 uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00F076]" />
            Temel Özellikler
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Geliştirici Öncelikli{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
              Ölçüm Araçları
            </span>
          </h2>
          <p className="text-zinc-400 max-w-xl text-base leading-relaxed">
            Üretime hazır projelerde çalışmak için tasarlandı — kurulum yok,
            ek bağımlılık yok.
          </p>
        </motion.div>

        {/* Cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {FEATURES.map((feat) => {
            const Icon = feat.icon;
            const IconCustom = feat.iconCustom;
            return (
              <motion.div
                variants={itemVariants}
                key={feat.id}
                className="group relative flex flex-col gap-5 p-7 rounded-2xl bg-zinc-900 border border-zinc-800/80 hover:border-emerald-500/40 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(0,0,0,0.4),0_0_0_1px_rgba(0,240,118,0.05)] cursor-default overflow-hidden"
              >
                {/* Hover glow layer */}
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/[0.03] via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none rounded-2xl" />

                {/* Icon */}
                <div className="relative w-11 h-11 rounded-xl bg-emerald-950/60 border border-emerald-500/20 flex items-center justify-center group-hover:border-emerald-500/40 group-hover:bg-emerald-950/80 transition-all duration-300">
                  {Icon && (
                    <Icon className="w-5 h-5 text-[#00F076]" />
                  )}
                  {IconCustom && (
                    <IconCustom className="w-5 h-5 text-[#00F076]" />
                  )}
                  {/* Icon ambient glow */}
                  <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 shadow-[0_0_15px_rgba(0,240,118,0.2)]" />
                </div>

                {/* Title + badge */}
                <div className="flex items-center gap-2.5">
                  <h3 className="font-bold text-base text-white tracking-tight group-hover:text-emerald-50 transition-colors duration-200">
                    {feat.title}
                  </h3>
                  {feat.badge && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/15 text-[#00F076] border border-emerald-500/25">
                      {feat.badge}
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-sm text-zinc-400 leading-relaxed group-hover:text-zinc-300 transition-colors duration-200">
                  {feat.description}
                </p>

                {/* Bottom edge glow on hover */}
                <div className="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* ── PART 2: Comparison Table ───────────────────────────── */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.1 }}
        className="flex flex-col gap-10"
      >
        {/* Section header */}
        <motion.div variants={itemVariants} className="flex flex-col items-center text-center gap-3">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Why{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
              EcoTrace?
            </span>
          </h2>
          <p className="text-zinc-500 text-sm max-w-md leading-relaxed">
            Açık kaynaklı alternatiflere kıyasla gerçek zamanlı, süreç bazlı
            izolasyon ve bütçe yönetimi.
          </p>
        </motion.div>

        {/* Table card */}
        <motion.div variants={itemVariants} className="rounded-2xl border border-zinc-800/60 bg-zinc-950/60 backdrop-blur-sm overflow-hidden shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
          {/* Top edge accent */}
          <div className="h-px w-full bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              {/* Head */}
              <thead>
                <tr>
                  {TABLE_COLUMNS.map((col) => (
                    <th
                      key={col.key}
                      className={`px-6 py-4 text-left first:rounded-tl-none ${
                        col.highlight
                          ? "bg-emerald-900/20 border-x border-emerald-500/10"
                          : col.isFeature
                          ? ""
                          : "border-r border-zinc-800/60"
                      }`}
                    >
                      {col.isFeature ? (
                        <span className="text-xs font-bold uppercase tracking-widest text-zinc-600">
                          {col.label}
                        </span>
                      ) : (
                        <div className="flex flex-col gap-0.5">
                          <span className={`text-sm font-bold ${col.highlight ? "text-white" : "text-zinc-400"}`}>
                            {col.label}
                          </span>
                          <span className={`text-xs font-mono font-medium ${col.highlight ? "text-[#00F076]" : "text-zinc-600"}`}>
                            {col.version}
                          </span>
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>

              {/* Body */}
              <tbody>
                {TABLE_ROWS.map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className="border-t border-zinc-800/40 hover:bg-white/[0.015] transition-colors duration-150 group/row"
                  >
                    {/* Feature name */}
                    <td className="px-6 py-4 text-sm font-medium text-zinc-300 whitespace-nowrap">
                      {row.feature}
                    </td>

                    {/* EcoTrace column (highlighted) */}
                    <td className="px-6 py-4 bg-emerald-900/20 border-x border-emerald-500/10">
                      <div className="flex items-center justify-start">
                        <CellDisplay cell={row.ecotrace} />
                      </div>
                    </td>

                    {/* CodeCarbon column */}
                    <td className="px-6 py-4 border-r border-zinc-800/60">
                      <div className="flex items-center justify-start">
                        <CellDisplay cell={row.codecarbon} />
                      </div>
                    </td>

                    {/* CarbonTracker column */}
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-start">
                        <CellDisplay cell={row.carbontracker} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Bottom edge */}
          <div className="h-px w-full bg-gradient-to-r from-transparent via-zinc-700/30 to-transparent" />
        </motion.div>

        {/* Table footnote */}
        <motion.p variants={itemVariants} className="text-right text-[11px] text-zinc-600 italic">
          * Data reflects base configurations and architectural differences as of the documented releases.
        </motion.p>
      </motion.div>
    </section>
  );
}
