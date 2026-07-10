"use client";

import React from "react";
import { ExternalLink, BookOpen, Code2, Shield, Scale } from "lucide-react";

/* ────────────────────────────────────────────────────────────── */
/*  Inline Discord SVG                                           */
/* ────────────────────────────────────────────────────────────── */
function DiscordIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

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
    heading: "Resources",
    links: [
      { label: "Docs", href: "https://ecotrace.readthedocs.io/en/latest/", icon: BookOpen },
      { label: "Architecture", href: "https://ecotrace.readthedocs.io/en/latest/ARCHITECTURE/", icon: null },
      { label: "API Reference", href: "https://ecotrace.readthedocs.io/en/latest/api/", icon: null },
    ],
  },
  {
    heading: "Community",
    links: [
      { label: "Discord", href: "https://discord.gg/hs58XXb3Uq", iconCustom: DiscordIcon },
      { label: "GitHub", href: "https://github.com/CanKStar0/ecotrace", iconCustom: GitHubIcon },
      { label: "VS Code Extension", href: "#", icon: Code2 },
    ],
  },
  {
    heading: "Legal",
    links: [
      { label: "MIT License", href: "https://github.com/CanKStar0/ecotrace/blob/main/LICENSE", icon: Scale },
      { label: "Privacy", href: "#", icon: null },
      { label: "Terms", href: "#", icon: null },
    ],
  },
];

/* ────────────────────────────────────────────────────────────── */
/*  Main Footer Component                                        */
/* ────────────────────────────────────────────────────────────── */
export default function SiteFooter() {
  return (
    <footer className="relative z-10 w-full">

      {/* ── CTA Banner ──────────────────────────────────────────── */}
      <div className="w-full max-w-7xl mx-auto px-6 pb-16">
        <div className="relative overflow-hidden rounded-2xl bg-zinc-900 border border-zinc-800/60 px-8 sm:px-12 py-10 flex flex-col sm:flex-row items-center justify-between gap-8">
          {/* Ambient glow — left */}
          <div className="absolute -left-24 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/8 blur-[80px] rounded-full pointer-events-none" />
          {/* Ambient glow — right */}
          <div className="absolute -right-24 top-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/6 blur-[80px] rounded-full pointer-events-none" />
          {/* Top edge glow line */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />

          {/* Left: Headline */}
          <p className="relative text-xl sm:text-2xl font-extrabold text-white tracking-tight leading-snug max-w-md">
            Enforce carbon budgets in your{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-[#00F076]">
              CI/CD pipeline
            </span>{" "}
            today.
          </p>

          {/* Right: CTA Button */}
          <a
            id="cta-discord"
            href="https://discord.gg/hs58XXb3Uq"
            target="_blank"
            rel="noopener noreferrer"
            className="relative flex-shrink-0 flex items-center gap-3 px-6 py-3.5 rounded-xl font-semibold text-sm bg-emerald-500 text-black hover:bg-[#00F076] transition-all duration-300 shadow-[0_4px_20px_rgba(16,185,129,0.3)] hover:shadow-[0_4px_30px_rgba(0,240,118,0.5)] group"
          >
            <DiscordIcon className="w-5 h-5 flex-shrink-0" />
            Join Discord Community
            <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-opacity" />
          </a>
        </div>
      </div>

      {/* ── Links grid + signature ───────────────────────────────── */}
      <div className="w-full max-w-7xl mx-auto px-6 border-t border-zinc-800/50">

        {/* 3-column link grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-10 py-12">
          {FOOTER_COLS.map((col) => (
            <div key={col.heading} className="flex flex-col gap-4">
              <h4 className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                {col.heading}
              </h4>
              <ul className="flex flex-col gap-2.5">
                {col.links.map((link) => {
                  const Icon = "icon" in link ? link.icon : null;
                  const IconCustom = "iconCustom" in link ? link.iconCustom : null;
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
            </div>
          ))}
        </div>

        {/* Bottom signature row */}
        <div className="py-6 border-t border-zinc-800/40 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-zinc-600 font-medium">
            © 2026 EcoTrace.{" "}
            <a
              href="https://github.com/CanKStar0/ecotrace/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-400 transition-colors duration-200"
            >
              MIT License
            </a>
            .
          </p>
          <p className="text-xs font-medium">
            <span className="text-zinc-600">Designed &amp; Developed by </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-zinc-300 to-zinc-400 font-semibold tracking-wide">
              Canpolat Kaya
            </span>
          </p>
        </div>
      </div>
    </footer>
  );
}
