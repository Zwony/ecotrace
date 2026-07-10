"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";

export default function SplashScreen() {
  const [show, setShow] = useState(true);

  useEffect(() => {
    // 2 saniye boyunca ekranda kalacak
    const timer = setTimeout(() => {
      setShow(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="splash"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#050806]"
        >
          {/* Logo Animasyonu */}
          <motion.div
            initial={{ scale: 0.5, opacity: 0, rotate: -10 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            transition={{
              type: "tween",
              ease: "easeOut",
              duration: 1,
            }}
            className="relative flex items-center justify-center w-32 h-32 rounded-3xl bg-emerald-950/40 border border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.2)]"
          >
            <Image src="/logo.png" alt="EcoTrace Logo" width={80} height={80} className="drop-shadow-[0_0_30px_rgba(0,240,118,0.4)]" />
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent rounded-3xl pointer-events-none" />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
