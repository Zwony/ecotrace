"use client";

import React, { useState, useMemo, useId } from "react";
import { TreePine, Wind, ChevronDown, Zap } from "lucide-react";
import { motion, Variants } from "framer-motion";

/* ──────────────────────────────────────────────────────────────
   Emission constants  (kgCO2 per request-ms @ median hardware)
   Source: ecotrace internal benchmarks + Electricity Map global avg
   ────────────────────────────────────────────────────────────── */
const RUNTIME_CONFIG: Record<
  string,
  { label: string; efficiency: number; color: string }
> = {
  python: {
    label: "Python",
    efficiency: 1.0,
    color: "#3b82f6",
  },
  rust: {
    label: "Rust",
    efficiency: 0.15,
    color: "#f97316",
  },
  go: {
    label: "Go",
    efficiency: 0.35,
    color: "#06b6d4",
  },
  nodejs: {
    label: "Node.js",
    efficiency: 0.55,
    color: "#a3e635",
  },
};

/** kgCO2 = requests × duration_ms × base_factor × runtime_factor */
const BASE_FACTOR = 4.2e-9; // kg CO2 per request-ms on avg server hardware (350g/kWh grid)
const KG_CO2_PER_TREE_YEAR = 21; // average tree absorbs 21 kg CO2/year

function formatNumber(n: number, decimals = 2): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return n.toFixed(decimals);
}

/* ────────────────────────────────────────────────────────────── */
/*  Custom Slider                                                 */
/* ────────────────────────────────────────────────────────────── */
interface SliderProps {
  id: string;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (v: number) => void;
  displayFormat?: (v: number) => string;
}

function Slider({
  id,
  label,
  unit,
  min,
  max,
  step,
  value,
  onChange,
  displayFormat,
}: SliderProps) {
  const pct = ((value - min) / (max - min)) * 100;
  const display = displayFormat ? displayFormat(value) : String(value);

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-sm font-medium text-zinc-300">
          {label}
        </label>
        <span className="font-mono text-sm font-semibold text-[#00F076] bg-emerald-950/50 border border-emerald-500/20 px-2.5 py-0.5 rounded-md tabular-nums">
          {display}
          <span className="text-zinc-500 font-normal ml-1 text-xs">{unit}</span>
        </span>
      </div>

      <div className="relative h-6 flex items-center">
        {/* Track background */}
        <div className="absolute w-full h-1.5 rounded-full bg-zinc-800" />
        {/* Filled track */}
        <div
          className="absolute h-1.5 rounded-full transition-all duration-75"
          style={{
            width: `${pct}%`,
            background:
              "linear-gradient(90deg, #059669 0%, #00F076 100%)",
          }}
        />
        {/* Native range */}
        <input
          id={id}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="slider-thumb absolute w-full h-full opacity-0 cursor-pointer z-10"
        />
        {/* Thumb */}
        <div
          className="absolute w-4 h-4 rounded-full bg-[#00F076] border-2 border-zinc-900 shadow-[0_0_10px_rgba(0,240,118,0.5)] pointer-events-none transition-all duration-75"
          style={{ left: `calc(${pct}% - 8px)` }}
        />
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Hexagonal grid background SVG (inline, no external deps)     */
/* ────────────────────────────────────────────────────────────── */
function HexGrid() {
  return (
    <svg
      className="absolute inset-0 w-full h-full opacity-[0.07] pointer-events-none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <pattern
          id="hex-pattern"
          x="0"
          y="0"
          width="52"
          height="60"
          patternUnits="userSpaceOnUse"
        >
          <polygon
            points="26,2 50,15 50,45 26,58 2,45 2,15"
            fill="none"
            stroke="#10b981"
            strokeWidth="0.8"
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#hex-pattern)" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Animated Counter                                              */
/* ────────────────────────────────────────────────────────────── */
function MetricValue({ value, unit }: { value: string; unit: string }) {
  return (
    <div className="flex items-end gap-2 leading-none">
      <span className="font-mono font-black text-5xl sm:text-6xl tracking-tight text-white drop-shadow-[0_0_20px_rgba(0,240,118,0.3)] tabular-nums transition-all duration-200">
        {value}
      </span>
      <span className="font-mono text-base font-medium text-[#00F076] mb-1 opacity-80">
        {unit}
      </span>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────── */
/*  Main Calculator Component                                     */
/* ────────────────────────────────────────────────────────────── */
export default function CarbonCalculator() {
  const uid = useId();
  const [runtime, setRuntime] = useState("python");
  const [traffic, setTraffic] = useState(500_000); // monthly requests
  const [duration, setDuration] = useState(200); // avg ms
  const [dropdownOpen, setDropdownOpen] = useState(false);

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

  const metrics = useMemo(() => {
    const cfg = RUNTIME_CONFIG[runtime];
    const co2 = traffic * duration * BASE_FACTOR * cfg.efficiency;
    const trees = Math.ceil(co2 / KG_CO2_PER_TREE_YEAR);
    return { co2, trees };
  }, [runtime, traffic, duration]);

  const runtimeCfg = RUNTIME_CONFIG[runtime];

  return (
    <motion.section 
      id="calculator" 
      variants={containerVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
      className="relative z-10 w-full max-w-7xl mx-auto px-6 py-24"
    >
      {/* Section header */}
      <motion.div variants={itemVariants} className="flex flex-col items-center text-center mb-16 gap-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-xs font-medium text-emerald-400 uppercase tracking-widest">
          <Zap className="w-3 h-3" />
          Canlı Hesaplayıcı
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
          İnteraktif Karbon{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
            Bütçe Hesaplayıcı
          </span>
        </h2>
        <p className="text-zinc-400 max-w-xl text-base leading-relaxed">
          Proje parametrelerinizi girin ve gerçek zamanlı olarak tahmini
          karbon ayak izinizi hesaplayın.
        </p>
      </motion.div>

      {/* Card */}
      <div className="relative rounded-3xl border border-emerald-500/10 bg-zinc-900/40 backdrop-blur-sm overflow-hidden shadow-[0_30px_80px_rgba(0,0,0,0.5)]">
        {/* Subtle top-edge glow */}
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
          {/* ── LEFT: Controls ─────────────────────────────────── */}
          <motion.div variants={itemVariants} className="flex flex-col gap-8 p-8 sm:p-10 lg:border-r border-emerald-500/10">
            {/* Section label */}
            <div className="flex items-center gap-2">
              <div className="w-1 h-4 rounded-full bg-[#00F076]" />
              <span className="text-xs font-bold uppercase tracking-widest text-[#00F076]">
                Proje Parametreleri
              </span>
            </div>

            {/* Runtime dropdown */}
            <div className="flex flex-col gap-2.5">
              <label className="text-sm font-medium text-zinc-300">
                Kullanılan Dil / Runtime
              </label>
              <div className="relative">
                <button
                  id={`${uid}-dropdown`}
                  onClick={() => setDropdownOpen((o) => !o)}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-zinc-800/60 border border-zinc-700/60 hover:border-emerald-500/40 text-white text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: runtimeCfg.color }}
                    />
                    <span>{runtimeCfg.label}</span>
                    <span className="text-xs text-zinc-500 font-normal ml-1">
                      (Verimlilik:{" "}
                      <span
                        className="font-semibold"
                        style={{ color: runtimeCfg.color }}
                      >
                        {Math.round((1 - runtimeCfg.efficiency) * 100)}% daha az CO2
                      </span>
                      {runtime !== "python" && " vs Python"}
                      {runtime === "python" && " — baz çizgi"}
                    </span>
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${dropdownOpen ? "rotate-180" : ""}`}
                  />
                </button>

                {/* Dropdown menu */}
                {dropdownOpen && (
                  <div className="absolute top-full left-0 right-0 mt-2 rounded-xl bg-zinc-900 border border-zinc-700/60 shadow-[0_20px_40px_rgba(0,0,0,0.5)] z-50 overflow-hidden">
                    {Object.entries(RUNTIME_CONFIG).map(([key, cfg]) => (
                      <button
                        key={key}
                        onClick={() => {
                          setRuntime(key);
                          setDropdownOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 px-4 py-3 text-sm text-left transition-colors duration-150 ${
                          runtime === key
                            ? "bg-emerald-950/50 text-white"
                            : "text-zinc-400 hover:bg-zinc-800/60 hover:text-white"
                        }`}
                      >
                        <div
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ backgroundColor: cfg.color }}
                        />
                        <span className="font-medium">{cfg.label}</span>
                        {runtime === key && (
                          <span className="ml-auto text-[#00F076] text-xs">✓</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Sliders */}
            <div className="flex flex-col gap-6 pt-2">
              <Slider
                id={`${uid}-traffic`}
                label="Aylık Trafik (İstek)"
                unit="istek/ay"
                min={10_000}
                max={50_000_000}
                step={10_000}
                value={traffic}
                onChange={setTraffic}
                displayFormat={(v) => formatNumber(v, 0)}
              />
              <Slider
                id={`${uid}-duration`}
                label="Ortalama Çalışma Süresi"
                unit="ms"
                min={1}
                max={5000}
                step={1}
                value={duration}
                onChange={setDuration}
              />
            </div>

            {/* Efficiency hint */}
            <div className="flex items-start gap-3 p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/10 mt-auto">
              <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[#00F076] text-xs font-bold">i</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Tahminler, ortalama{" "}
                <span className="text-zinc-200 font-medium">350 gCO₂/kWh</span>{" "}
                şebeke karbon yoğunluğu ve doğrulama yapılmış üretici TDP
                ölçümlerine dayanmaktadır.
              </p>
            </div>
          </motion.div>

          {/* ── RIGHT: Output panel ────────────────────────────── */}
          <motion.div variants={itemVariants} className="relative flex flex-col justify-center p-8 sm:p-10 overflow-hidden bg-zinc-950/30">
            {/* Hex grid texture */}
            <HexGrid />

            {/* Corner border accent */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-emerald-500/8 to-transparent pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-emerald-500/5 to-transparent pointer-events-none" />

            {/* Panel content */}
            <div className="relative z-10 flex flex-col gap-10">
              {/* Metric 1: CO2 */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <Wind className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                    Tahmini Aylık CO₂
                  </span>
                </div>
                <MetricValue
                  value={formatNumber(metrics.co2, metrics.co2 < 1 ? 4 : 2)}
                  unit="kg CO₂"
                />
                {/* Mini bar */}
                <div className="h-1 rounded-full bg-zinc-800 w-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min((metrics.co2 / 500) * 100, 100)}%`,
                      background: `linear-gradient(90deg, #059669, #00F076)`,
                      boxShadow: "0 0 8px rgba(0,240,118,0.4)",
                    }}
                  />
                </div>
                <p className="text-xs text-zinc-600">
                  Maks. eşik:{" "}
                  <span className="text-zinc-400 font-medium">500 kg/ay</span>
                </p>
              </div>

              {/* Divider */}
              <div className="h-px bg-gradient-to-r from-transparent via-emerald-500/15 to-transparent" />

              {/* Metric 2: Trees */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <TreePine className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                    Ofset İçin Gereken Ağaç
                  </span>
                </div>
                <MetricValue
                  value={formatNumber(metrics.trees, 0)}
                  unit="ağaç/yıl"
                />
                {/* Tree icons row */}
                <div className="flex items-center gap-1 flex-wrap mt-1" aria-hidden>
                  {Array.from({ length: Math.min(metrics.trees, 20) }).map(
                    (_, i) => (
                      <TreePine
                        key={i}
                        className="w-4 h-4 text-emerald-600 opacity-70"
                      />
                    )
                  )}
                  {metrics.trees > 20 && (
                    <span className="text-xs text-zinc-500 font-mono ml-1">
                      +{formatNumber(metrics.trees - 20, 0)} daha
                    </span>
                  )}
                </div>
              </div>

              {/* Divider */}
              <div className="h-px bg-gradient-to-r from-transparent via-emerald-500/15 to-transparent" />

              {/* Runtime badge */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-600">Aktif Runtime</span>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-800/80 border border-zinc-700/40">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: runtimeCfg.color, boxShadow: `0 0 6px ${runtimeCfg.color}` }}
                  />
                  <span
                    className="text-xs font-bold font-mono"
                    style={{ color: runtimeCfg.color }}
                  >
                    {runtimeCfg.label}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.section>
  );
}
